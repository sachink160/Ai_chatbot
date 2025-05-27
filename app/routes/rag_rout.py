from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth, database, utils
import os
from uuid import uuid4
from llama_index.core import load_index_from_storage

router = APIRouter(tags=["Rag Talk with Documents"])

UPLOAD_DIR = "docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    filename = f"{uuid4()}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    doc = models.Document(filename=filename, path=path, owner=current_user, user_id=current_user.id)
    db.add(doc)
    db.commit()
    return {"message": "File uploaded", "document_id": doc.id}


@router.get("/documents")
def list_docs(current_user: models.User = Depends(auth.get_current_user)):
    # return current_user.documents
    return [{"id": doc.id, "filename": doc.filename} for doc in current_user.documents]

@router.post("/ask")
def ask_question(body: schemas.Question, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    doc = db.query(models.Document).filter_by(id=body.document_id, user_id=current_user.id).first()
    if not doc:
        raise HTTPException(404, detail="Document not found")

    try:
        index = utils.load_or_create_index(doc.path, current_user.id, doc.id)

        # ✅ Use better control over query behavior
        query_engine = index.as_query_engine(
            similarity_top_k=5,  # Fetch 5 chunks
            response_mode="compact"  # Compact + LLM summarization
        )

        response = query_engine.query(body.question)
        return {"answer": str(response)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
