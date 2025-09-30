from fastapi import APIRouter, UploadFile, Depends, File, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth, database, utils
import os
from uuid import uuid4
from llama_index.core import load_index_from_storage
from langchain_openai import ChatOpenAI

from llama_index.llms.langchain import LangChainLLM
from langchain_ollama import ChatOllama
from app.logger import get_logger
logger = get_logger(__name__)
router = APIRouter(tags=["Rag Talk with Documents"])

UPLOAD_DIR = "docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    logger.info(f"Document upload attempt by user {current_user.id}: {file.filename}")
    
    try:
        # Check subscription limits
        from app.subscription_service import SubscriptionService
        doc_check = SubscriptionService.can_upload_document(current_user, db)
        
        if not doc_check["can_use"]:
            logger.warning(f"Document upload limit reached for user {current_user.id}")
            raise HTTPException(
                status_code=403, 
                detail=f"Document upload limit reached. You have uploaded {doc_check['documents_uploaded']}/{doc_check['max_documents']} documents this month. Please upgrade your subscription for more uploads."
            )
        
        filename = f"{uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(path, "wb") as f:
            f.write(file.file.read())
        
        # Create document record
        doc = models.Document(filename=filename, path=path, owner=current_user, user_id=current_user.id)
        db.add(doc)
        
        # Increment usage
        SubscriptionService.increment_document_usage(current_user, db)
        
        db.commit()
        
        logger.info(f"Document uploaded successfully: {file.filename} -> {filename} (ID: {doc.id})")
        from app.logger import log_business_event
        log_business_event("document_upload", str(current_user.id), {
            "original_filename": file.filename,
            "stored_filename": filename,
            "document_id": doc.id,
            "file_size": file.size if hasattr(file, 'size') else 'unknown'
        })
        
        return {
            "message": "File uploaded", 
            "document_id": doc.id,
            "usage": {
                "documents_uploaded": doc_check["documents_uploaded"] + 1,
                "max_documents": doc_check["max_documents"],
                "remaining": doc_check["remaining"] - 1
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed for user {current_user.id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="File upload failed")


@router.get("/documents")
def list_docs(current_user: models.User = Depends(auth.get_current_user)):
    # return current_user.documents
    return [{"id": doc.id, "filename": doc.filename} for doc in current_user.documents]

# @router.post("/ask")
# def ask_question(body: schemas.Question, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
#     doc = db.query(models.Document).filter_by(id=body.document_id, user_id=current_user.id).first()
#     if not doc:
#         raise HTTPException(404, detail="Document not found")

#     try:
#         index = utils.load_or_create_index(doc.path, current_user.id, doc.id)

#         # ✅ Use better control over query behavior
#         query_engine = index.as_query_engine(
#             similarity_top_k=5,  # Fetch 5 chunks
#             response_mode="compact"  # Compact + LLM summarization
#         )

#         response = query_engine.query(body.question)
#         return {"answer": str(response)}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


CRITICAL_ISSUES_PROMPT = """
You are a senior legal and compliance analyst.

Read the following document and extract all *critical legal or compliance issues*.

A *critical issue* is anything that:
1. May trigger legal disputes or regulatory non-compliance
2. Involves unclear, missing, or disputed payment terms or obligations
3. Contains ambiguous or vague language that could be misinterpreted
4. Impacts liability, indemnity, refund, or termination rights
5. Poses operational, financial, or compliance risks

Output requirements:
- Provide a numbered list of clear, concise issues
- Each issue should be self-contained and actionable
- Include clause numbers or headings if referenced
- Do NOT provide summaries, explanations, or commentary

DOCUMENT:

SERVICE AGREEMENT

1. Services: The Vendor shall provide marketing consulting services to the Client. The scope will be discussed verbally as needed.

2. Payment: The Client agrees to pay the Vendor an amount to be determined later, based on mutual satisfaction.

3. Termination: Either party may terminate the agreement with "reasonable notice." What qualifies as reasonable is not defined.

4. Refunds: Refunds will be handled case-by-case. The Vendor is not obligated to return funds if the Client is dissatisfied.

5. Liability: The Vendor shall not be liable for any damages, including but not limited to direct or indirect losses, even if caused by negligence.

6. Governing Law: This agreement shall be governed by the laws of an applicable jurisdiction.

7. Confidentiality: Both parties agree to keep "sensitive information" private, though no definition of "sensitive" is provided.

"""

PROMPT_TEMPLATES = {
    "critical_issues": CRITICAL_ISSUES_PROMPT,
    "summarize": "Summarize the main points of the document.",
    "action_items": "Extract all action items from the document.",
    "custom": "{custom_query}"
}
def build_prompt(prompt_type: str, custom_query: str = "") -> str:
    if prompt_type == "custom" and custom_query:
        return custom_query
    return PROMPT_TEMPLATES.get(prompt_type, "Answer the following question:")

@router.post("/ask")
def ask_question(
    body: schemas.Question_r,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    doc = db.query(models.Document).filter_by(id=body.document_id, user_id=current_user.id).first()
    if not doc:
        raise HTTPException(404, detail="Document not found")

    try:
        index = utils.load_or_create_index(doc.path, current_user.id, doc.id)

        # Build the prompt
        prompt = build_prompt(getattr(body, "prompt_type", "summarize"), getattr(body, "custom_query", ""))
        
        chat_llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=1024)
        # chat_llm = ChatOllama(model="llama3", temperature=0.7)
        llama_llm = LangChainLLM(llm=chat_llm)
        # Combine prompt and user question if both are present
        user_question = getattr(body, "question", "")
        final_query = f"{prompt}\n{user_question}" if user_question else prompt

        query_engine = index.as_query_engine(
            llm=llama_llm,
            similarity_top_k=5,
            response_mode="compact"
        )

        response = query_engine.query(final_query)
        return {"answer": str(response)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")