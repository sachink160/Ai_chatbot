from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models import User, DynamicPrompt, ProcessedDocument
from app.schemas import (
    DynamicPromptCreate, 
    DynamicPromptUpdate, 
    DynamicPromptResponse,
    DocumentProcessResponse,
    DocumentUploadRequest
)
from app.services.document_processor import DocumentProcessor
from app.config import OPENAI_API_KEY
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/dynamic-prompts", tags=["Dynamic Prompts"])

# Initialize document processor
document_processor = DocumentProcessor(OPENAI_API_KEY)

@router.post("/", response_model=DynamicPromptResponse)
async def create_dynamic_prompt(
    prompt_data: DynamicPromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dynamic prompt."""
    try:
        # Check if gpt_model column exists
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('dynamic_prompts')]
        has_gpt_model = 'gpt_model' in columns
        
        # Check if prompt name already exists for this user
        existing_prompt = db.query(DynamicPrompt).filter(
            DynamicPrompt.user_id == current_user.id,
            DynamicPrompt.name == prompt_data.name
        ).first()
        
        if existing_prompt:
            raise HTTPException(status_code=400, detail="Prompt name already exists")
        
        # Create new prompt
        if has_gpt_model:
            new_prompt = DynamicPrompt(
                user_id=current_user.id,
                name=prompt_data.name,
                description=prompt_data.description,
                prompt_template=prompt_data.prompt_template,
                gpt_model=prompt_data.gpt_model or "gpt-4o-mini"
            )
        else:
            # Create without gpt_model column
            new_prompt = DynamicPrompt(
                user_id=current_user.id,
                name=prompt_data.name,
                description=prompt_data.description,
                prompt_template=prompt_data.prompt_template
            )
            # Add gpt_model attribute manually
            new_prompt.gpt_model = prompt_data.gpt_model or "gpt-4o-mini"
        
        db.add(new_prompt)
        db.commit()
        db.refresh(new_prompt)
        
        logger.info(f"Created dynamic prompt '{prompt_data.name}' for user {current_user.id}")
        return new_prompt
        
    except Exception as e:
        logger.error(f"Error creating dynamic prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create prompt")

@router.get("/", response_model=List[DynamicPromptResponse])
async def get_user_prompts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all dynamic prompts for the current user."""
    try:
        # Check if gpt_model column exists
        from sqlalchemy import inspect
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('dynamic_prompts')]
        has_gpt_model = 'gpt_model' in columns
        
        if has_gpt_model:
            # Normal query with gpt_model column
            prompts = db.query(DynamicPrompt).filter(
                DynamicPrompt.user_id == current_user.id
            ).order_by(DynamicPrompt.created_at.desc()).all()
        else:
            # Query without gpt_model column and add default value
            prompts = db.query(
                DynamicPrompt.id,
                DynamicPrompt.user_id,
                DynamicPrompt.name,
                DynamicPrompt.description,
                DynamicPrompt.prompt_template,
                DynamicPrompt.is_active,
                DynamicPrompt.created_at,
                DynamicPrompt.updated_at
            ).filter(
                DynamicPrompt.user_id == current_user.id
            ).order_by(DynamicPrompt.created_at.desc()).all()
            
            # Convert to DynamicPrompt objects with default gpt_model
            prompt_objects = []
            for prompt_data in prompts:
                prompt_obj = DynamicPrompt()
                prompt_obj.id = prompt_data.id
                prompt_obj.user_id = prompt_data.user_id
                prompt_obj.name = prompt_data.name
                prompt_obj.description = prompt_data.description
                prompt_obj.prompt_template = prompt_data.prompt_template
                prompt_obj.gpt_model = "gpt-4o-mini"  # Default value
                prompt_obj.is_active = prompt_data.is_active
                prompt_obj.created_at = prompt_data.created_at
                prompt_obj.updated_at = prompt_data.updated_at
                prompt_objects.append(prompt_obj)
            prompts = prompt_objects
        
        return prompts
        
    except Exception as e:
        logger.error(f"Error fetching prompts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch prompts")

@router.get("/{prompt_id}", response_model=DynamicPromptResponse)
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dynamic prompt by ID."""
    try:
        prompt = db.query(DynamicPrompt).filter(
            DynamicPrompt.id == prompt_id,
            DynamicPrompt.user_id == current_user.id
        ).first()
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return prompt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching prompt {prompt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch prompt")

@router.put("/{prompt_id}", response_model=DynamicPromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt_data: DynamicPromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a dynamic prompt."""
    try:
        prompt = db.query(DynamicPrompt).filter(
            DynamicPrompt.id == prompt_id,
            DynamicPrompt.user_id == current_user.id
        ).first()
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Update fields if provided
        if prompt_data.name is not None:
            # Check if new name already exists
            existing_prompt = db.query(DynamicPrompt).filter(
                DynamicPrompt.user_id == current_user.id,
                DynamicPrompt.name == prompt_data.name,
                DynamicPrompt.id != prompt_id
            ).first()
            
            if existing_prompt:
                raise HTTPException(status_code=400, detail="Prompt name already exists")
            prompt.name = prompt_data.name
            
        if prompt_data.description is not None:
            prompt.description = prompt_data.description
            
        if prompt_data.prompt_template is not None:
            prompt.prompt_template = prompt_data.prompt_template
            
        if prompt_data.gpt_model is not None:
            prompt.gpt_model = prompt_data.gpt_model
            
        if prompt_data.is_active is not None:
            prompt.is_active = prompt_data.is_active
        
        prompt.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(prompt)
        
        logger.info(f"Updated dynamic prompt '{prompt.name}' for user {current_user.id}")
        return prompt
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt {prompt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")

@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dynamic prompt."""
    try:
        prompt = db.query(DynamicPrompt).filter(
            DynamicPrompt.id == prompt_id,
            DynamicPrompt.user_id == current_user.id
        ).first()
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        db.delete(prompt)
        db.commit()
        
        logger.info(f"Deleted dynamic prompt '{prompt.name}' for user {current_user.id}")
        return {"message": "Prompt deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete prompt")

@router.post("/upload-document")
async def upload_and_process_document(
    file: UploadFile = File(...),
    prompt_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document and process it with a specific prompt."""
    try:
        # Check subscription limits for dynamic prompt document uploads
        from app.subscription_service import SubscriptionService
        doc_check = SubscriptionService.can_upload_dynamic_prompt_document(current_user, db)
        
        if not doc_check["can_use"]:
            raise HTTPException(
                status_code=403, 
                detail=f"Dynamic prompt document upload limit reached. You have uploaded {doc_check['dynamic_prompt_documents_uploaded']}/{doc_check['max_dynamic_prompt_documents']} documents this month. Please upgrade your subscription for more uploads."
            )
        
        # Validate prompt exists and belongs to user
        prompt = db.query(DynamicPrompt).filter(
            DynamicPrompt.id == prompt_id,
            DynamicPrompt.user_id == current_user.id,
            DynamicPrompt.is_active == True
        ).first()
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found or not active")
        
        # Validate file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = ['.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.jfif', '.bmp', '.tiff', '.tif', '.webp', '.heic']
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = f"uploads/user_{current_user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, saved_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File uploaded: {file.filename} -> {file_path}")
        
        # Process document
        processed_doc = document_processor.process_document(
            db=db,
            user_id=current_user.id,
            prompt_id=prompt_id,
            file_path=file_path,
            original_filename=file.filename
        )
        
        # Increment usage after successful processing
        SubscriptionService.increment_dynamic_prompt_document_usage(current_user, db)
        
        return {
            "message": "Document processed successfully",
            "processed_document_id": processed_doc.id,
            "status": processed_doc.processing_status,
            "usage": {
                "dynamic_prompt_documents_uploaded": doc_check["dynamic_prompt_documents_uploaded"] + 1,
                "max_dynamic_prompt_documents": doc_check["max_dynamic_prompt_documents"],
                "remaining": doc_check["remaining"] - 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/processed-documents/", response_model=List[DocumentProcessResponse])
async def get_processed_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all processed documents for the current user."""
    try:
        documents = db.query(ProcessedDocument).filter(
            ProcessedDocument.user_id == current_user.id
        ).order_by(ProcessedDocument.created_at.desc()).all()
        
        return documents
        
    except Exception as e:
        logger.error(f"Error fetching processed documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch processed documents")

@router.get("/processed-documents/{document_id}", response_model=DocumentProcessResponse)
async def get_processed_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific processed document by ID."""
    try:
        document = db.query(ProcessedDocument).filter(
            ProcessedDocument.id == document_id,
            ProcessedDocument.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Processed document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching processed document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch processed document")

@router.get("/processed-documents/{document_id}/result")
async def get_processing_result(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the processing result for a specific document."""
    try:
        document = db.query(ProcessedDocument).filter(
            ProcessedDocument.id == document_id,
            ProcessedDocument.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Processed document not found")
        
        if document.processing_status != "completed":
            raise HTTPException(status_code=400, detail="Document processing not completed")
        
        # Parse the JSON result
        import json
        result = json.loads(document.processed_result) if document.processed_result else {}
        
        return {
            "document_id": document.id,
            "original_filename": document.original_filename,
            "processing_status": document.processing_status,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching processing result for {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch processing result")
