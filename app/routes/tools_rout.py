import json
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage

from app.Agent.tools import graph
from datetime import datetime, timezone
from app import models, database, auth


router = APIRouter(tags=["Ai ChatBot"])


@router.post("/chat")
async def chat(
    query: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    
    try:
        # V1
        # import pdb
        # pdb.set_trace()
        
        config = {"configurable": {"thread_id": str(current_user.id)}}
        # response = graph.invoke({"messages": [{"role": "user", "content": query}]})
        response = graph.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config,
            stream_mode="values"
            )
        
        # V2
        # config = {"configurable": {"thread_id": f"{current_user.id}"}}
        # response_gen = graph.stream(
        #         {"messages": [{"role": "user", "content": query}]},
        #         config,
        #         stream_mode="values",
        #     )
        # response = list(response_gen) 
        # Optionally, determine which tool was used (if available)
        tool_used = "unknown"

        result_messages = response["messages"]
        # Extract tool names
        tool_used = [msg.name for msg in result_messages if isinstance(msg, ToolMessage)]
            
        # Save chat history
        chat_entry = models.ChatHistory(
            user_id=current_user.id,
            message=query,
            response=json.dumps(response["messages"][-1].content, default=str), 
            tool_used=tool_used,
            timestamp=datetime.now(timezone.utc),
            
        )
        db.add(chat_entry)
        db.commit()
        return {"response": response["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history")
async def get_chat_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    history = db.query(models.ChatHistory).filter_by(user_id=current_user.id).order_by(models.ChatHistory.timestamp.desc()).all()
    return [
        {
            "message": h.message,
            "response": h.response,
            "tool_used": h.tool_used,
            "timestamp": h.timestamp
        }
        for h in history
    ]