import json
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.database import get_db
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from uuid import uuid4
from llama_index.llms.langchain import LangChainLLM
from llama_index.core import StorageContext

from app.Agent.tools import graph
from datetime import datetime, timezone
from app import models, database, auth, utils
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
        # Check if user has an active document for RAG
        active_doc = db.query(models.ChatDocument).filter_by(
            user_id=current_user.id,
            is_active=True
        ).first()
        
        final_query = query
        
        # If active document exists, use RAG
        if active_doc:
            try:
                logger.info(f"Using RAG with active document: {active_doc.filename}")
                
                # Load or create index for this document
                index = utils.load_or_create_chat_index(active_doc.path, current_user.id, active_doc.id)
                
                # Create query engine
                chat_llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=2048)
                llama_llm = LangChainLLM(llm=chat_llm)
                
                query_engine = index.as_query_engine(
                    llm=llama_llm,
                    similarity_top_k=5,
                    response_mode="compact"
                )
                
                # Get context from document
                rag_response = query_engine.query(f"Based on the document, answer this question: {query}")
                document_context = str(rag_response)
                
                # Enhance the query with document context
                final_query = f"""I have uploaded a document. Here's what it says about your question:
                
                {document_context}

                Now, based on this context from my document AND using your tools, please answer: {query}"""
                
                logger.info(f"Enhanced query with document context for user {current_user.id}")
                
            except Exception as e:
                logger.error(f"RAG processing error for user {current_user.id}: {e}")
                # Continue with normal chat if RAG fails
                final_query = f"Note: I couldn't process my document. {query}"
        
        config = {"configurable": {"thread_id": str(current_user.id)}}
        response = graph.invoke(
            {"messages": [{"role": "user", "content": final_query}]},
            config,
            stream_mode="values"
        )
        
        result_messages = response["messages"]
        tool_used = [msg.name for msg in result_messages if hasattr(msg, 'name')]
        
        # Mark document as used if RAG was used
        if active_doc:
            tool_used.append("document_rag")

        # ✅ Save chat history as plain string (not escaped JSON)
        chat_entry = models.ChatHistory(
            user_id=current_user.id,
            message=query,
            response=response["messages"][-1].content,
            tool_used=tool_used,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(chat_entry)
        
        # Increment usage
        SubscriptionService.increment_chat_usage(current_user, db)
        db.commit()
        logger.info(f"Saved chat history for user {current_user.id}")
        
        return {
            "response": response["messages"][-1].content,
            "usage": {
                "chats_used": chat_check["chats_used"] + 1,
                "max_chats": chat_check["max_chats"],
                "remaining": chat_check["remaining"] - 1
            },
            "document_used": active_doc.filename if active_doc else None
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

# Chat Document Management Endpoints

CHAT_DOC_DIR = "chat_docs"
os.makedirs(CHAT_DOC_DIR, exist_ok=True)

@router.post("/chat/upload-document")
async def upload_chat_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Upload a document to be used in chatbot context"""
    logger.info(f"Chat document upload by user {current_user.id}: {file.filename}")
    
    try:
        filename = f"{uuid4()}_{file.filename}"
        path = os.path.join(CHAT_DOC_DIR, filename)
        
        # Save file
        with open(path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create chat document record
        chat_doc = models.ChatDocument(
            filename=file.filename,
            path=path,
            user_id=current_user.id,
            is_active=False
        )
        db.add(chat_doc)
        db.commit()
        db.refresh(chat_doc)
        
        logger.info(f"Chat document uploaded: {file.filename} -> {filename} (ID: {chat_doc.id})")
        
        return {
            "message": "Document uploaded successfully",
            "document_id": chat_doc.id,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Chat document upload failed for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/chat/documents")
async def list_chat_documents(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """List all chat documents for the current user"""
    documents = db.query(models.ChatDocument).filter_by(user_id=current_user.id).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "is_active": doc.is_active,
            "created_at": doc.created_at
        }
        for doc in documents
    ]

@router.post("/chat/documents/{doc_id}/activate")
async def activate_chat_document(
    doc_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Activate a document for use in chat"""
    doc = db.query(models.ChatDocument).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not doc:
        raise HTTPException(404, detail="Document not found")
    
    # Deactivate all other documents for this user
    db.query(models.ChatDocument).filter_by(user_id=current_user.id).update({"is_active": False})
    
    # Activate this document
    doc.is_active = True
    db.commit()
    
    logger.info(f"Activated chat document {doc_id} for user {current_user.id}")
    
    return {"message": f"Document '{doc.filename}' is now active", "document_id": doc.id}

@router.post("/chat/documents/{doc_id}/deactivate")
async def deactivate_chat_document(
    doc_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Deactivate a document"""
    doc = db.query(models.ChatDocument).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not doc:
        raise HTTPException(404, detail="Document not found")
    
    doc.is_active = False
    db.commit()
    
    logger.info(f"Deactivated chat document {doc_id} for user {current_user.id}")
    
    return {"message": f"Document '{doc.filename}' is now inactive", "document_id": doc.id}

@router.delete("/chat/documents/{doc_id}")
async def delete_chat_document(
    doc_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Delete a chat document"""
    doc = db.query(models.ChatDocument).filter_by(id=doc_id, user_id=current_user.id).first()
    
    if not doc:
        raise HTTPException(404, detail="Document not found")
    
    # Delete the file
    if os.path.exists(doc.path):
        os.remove(doc.path)
    
    db.delete(doc)
    db.commit()
    
    logger.info(f"Deleted chat document {doc_id} for user {current_user.id}")
    
    return {"message": "Document deleted successfully"}