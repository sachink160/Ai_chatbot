from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth, database
from app.Agent import hr_tools
import os
from uuid import uuid4
from llama_index.core import load_index_from_storage

router = APIRouter(
    tags=["Hr Rag Documents"],
    prefix="/hr"
    )

UPLOAD_DIR = "hr_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    try:
        filename = f"{uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            f.write(file.file.read())
        doc = models.Hr_Document(filename=filename, path=path, owner=current_user, user_id=current_user.id)
        db.add(doc)
        db.commit()
        return {"message": "Hr File uploaded", "document_id": doc.id}
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
def ask_question(
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

        # query_engine = index.as_query_engine(
        #     similarity_top_k=5,
        #     response_mode="compact"
        # )

        query_engine = index.as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",  # Better summarization
            use_async=True
        )
        
        response = query_engine.query(body.question)

        # return {
        #     "question": body.question,
        #     "answer": str(response),
        #     "document": active_doc.filename
        # }
        
        return {
            "question": body.question,
            "answer": str(response),
            # "source_nodes": [n.node.get_content() for n in response.source_nodes],
            "document": active_doc.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
