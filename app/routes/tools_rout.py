import json
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage

from app.Agent.tools import graph
from datetime import datetime, timezone
from app import models, database, auth
from app.logger import get_logger
logger = get_logger(__name__)


router = APIRouter(tags=["Ai ChatBot"])


@router.post("/chat")
async def chat(
    query: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    logger.info(f"Received chat request from user {current_user.id}: {query}")
    
    # Check subscription limits
    from app.subscription_service import SubscriptionService
    chat_check = SubscriptionService.can_use_chat(current_user, db)
    
    if not chat_check["can_use"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Chat limit reached. You have used {chat_check['chats_used']}/{chat_check['max_chats']} chats this month. Please upgrade your subscription for more chats."
        )
    
    try:
        config = {"configurable": {"thread_id": str(current_user.id)}}
        response = graph.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config,
            stream_mode="values"
        )
        
        result_messages = response["messages"]
        tool_used = [msg.name for msg in result_messages if hasattr(msg, 'name')]

        # ✅ Save chat history as plain string (not escaped JSON)
        chat_entry = models.ChatHistory(
            user_id=current_user.id,
            message=query,
            response=response["messages"][-1].content,   # <-- FIXED
            tool_used=tool_used,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(chat_entry)
        
        # Increment usage
        SubscriptionService.increment_chat_usage(current_user, db)
        db.commit()
        logger.info(f"Saved chat history for user {current_user.id}")
        
        return {
            "response": response["messages"][-1].content,  # <-- FIXED
            "usage": {
                "chats_used": chat_check["chats_used"] + 1,
                "max_chats": chat_check["max_chats"],
                "remaining": chat_check["remaining"] - 1
            }
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history")
async def get_chat_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    history = (
        db.query(models.ChatHistory)
        .filter_by(user_id=current_user.id)
        .order_by(models.ChatHistory.timestamp.desc())
        .all()
    )
    return [
        {
            "message": h.message,
            "response": h.response,   # already plain text
            "tool_used": h.tool_used,
            "timestamp": h.timestamp
        }
        for h in history
    ]