from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth, database
from app.Agent import hr_tools
import os
from uuid import uuid4
from llama_index.core import load_index_from_storage
from app.logger import get_logger
logger = get_logger(__name__)

router = APIRouter(
    tags=["Hr Rag Documents"],
    prefix="/hr"
    )

UPLOAD_DIR = "hr_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    try:
        # Check subscription limits
        from app.subscription_service import SubscriptionService
        hr_doc_check = SubscriptionService.can_upload_hr_document(current_user, db)
        
        if not hr_doc_check["can_use"]:
            raise HTTPException(
                status_code=403, 
                detail=f"HR document upload limit reached. You have uploaded {hr_doc_check['hr_documents_uploaded']}/{hr_doc_check['max_hr_documents']} HR documents this month. Please upgrade your subscription for more uploads."
            )
        
        filename = f"{uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(file.file.read())
        doc = models.Hr_Document(filename=filename, path=path, owner=current_user, user_id=current_user.id)
        db.add(doc)
        
        # Increment usage
        SubscriptionService.increment_hr_document_usage(current_user, db)
        
        db.commit()
        return {
            "message": "Hr File uploaded", 
            "document_id": doc.id,
            "usage": {
                "hr_documents_uploaded": hr_doc_check["hr_documents_uploaded"] + 1,
                "max_hr_documents": hr_doc_check["max_hr_documents"],
                "remaining": hr_doc_check["remaining"] - 1
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/documents")
def list_docs(current_user: models.User = Depends(auth.get_current_user)):
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "is_active": doc.is_active
        }
        for doc in current_user.hrdocuments
    ]


@router.post("/documents/{doc_id}/deactivate")
def deactivate_document(doc_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    doc = db.query(models.Hr_Document).filter(models.Hr_Document.id == doc_id, models.Hr_Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.is_active = 0
    db.commit()
    return {"message": f"Deactivated document: {doc.filename}"}



@router.post("/documents/{doc_id}/activate")
def activate_document(
    doc_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Step 1: Fetch the specific document for the user
    doc = db.query(models.Hr_Document).filter(
        models.Hr_Document.id == doc_id,
        models.Hr_Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Step 2: Deactivate all of this user's documents
    db.query(models.Hr_Document).filter(
        models.Hr_Document.user_id == current_user.id
    ).update({"is_active": 0})

    # Step 3: Activate the requested document
    doc.is_active = 1

    db.commit()
    return {"message": f"Activated document: {doc.filename}"}


@router.post("/ask")
async def ask_question(
    body: schemas.Hr_Question,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    active_doc = db.query(models.Hr_Document).filter_by(
        user_id=current_user.id,
        is_active=1
    ).first()

    if not active_doc:
        raise HTTPException(status_code=404, detail="No active HR document found.")

    try:
        index = hr_tools.load_or_create_hr_index(
            filepath=active_doc.path,
            user_id=current_user.id,
            document_id=active_doc.id
        )

        query_engine = index.as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",  # summary-based answer
            use_async=True
        )

        response = await query_engine.aquery(body.question)  # Use `await` + `aquery`

        return {
            "question": body.question,
            "answer": str(response),
            "document": active_doc.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
