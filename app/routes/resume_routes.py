from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import os
import uuid
import json
from typing import List

from app.auth import get_current_user
from app.database import get_db
from app.logger import get_logger
from app.models import User, Resume, JobRequirement
from app.schemas import (
    ResumeUploadResponse,
    JobRequirementCreate,
    JobRequirementUpdate,
    JobRequirementResponse,
    ResumeMatchResponse,
)
from app.services.resume_service import ResumeService
from app.subscription_service import SubscriptionService
from app.config import OPENAI_API_KEY

logger = get_logger(__name__)
router = APIRouter(prefix="/resumes", tags=["Resume Matching"])

resume_service = ResumeService(OPENAI_API_KEY)


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Reuse document upload limits for free tier; customize as needed
    doc_check = SubscriptionService.can_upload_document(current_user, db)
    if not doc_check["can_use"]:
        raise HTTPException(status_code=403, detail="Resume upload limit reached for your plan.")

    allowed = [".pdf", ".docx", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed)}")

    upload_dir = f"uploads/user_{current_user.id}/resumes"
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    saved_name = f"{file_id}{ext}"
    file_path = os.path.join(upload_dir, saved_name)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    resume = resume_service.ingest_resume(
        db=db,
        user_id=current_user.id,
        file_path=file_path,
        original_filename=file.filename,
    )

    SubscriptionService.increment_document_usage(current_user, db)
    return {
        "id": resume.id,
        "original_filename": resume.original_filename,
        "file_type": resume.file_type,
        "created_at": resume.created_at,
    }


@router.post("/requirements", response_model=JobRequirementResponse)
async def create_requirement(
    payload: JobRequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Validate JSON shape early
        json.loads(payload.requirement_json)
    except Exception:
        raise HTTPException(status_code=400, detail="requirement_json must be a valid JSON string")

    req = JobRequirement(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        requirement_json=payload.requirement_json,
        gpt_model=payload.gpt_model or "gpt-4o-mini",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("/requirements", response_model=List[JobRequirementResponse])
async def list_requirements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(JobRequirement).filter(JobRequirement.user_id == current_user.id).order_by(JobRequirement.created_at.desc()).all()


@router.put("/requirements/{requirement_id}", response_model=JobRequirementResponse)
async def update_requirement(
    requirement_id: str,
    payload: JobRequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.query(JobRequirement).filter(JobRequirement.id == requirement_id, JobRequirement.user_id == current_user.id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if payload.title is not None:
        req.title = payload.title
    if payload.description is not None:
        req.description = payload.description
    if payload.requirement_json is not None:
        try:
            json.loads(payload.requirement_json)
        except Exception:
            raise HTTPException(status_code=400, detail="requirement_json must be valid JSON string")
        req.requirement_json = payload.requirement_json
    if payload.gpt_model is not None:
        req.gpt_model = payload.gpt_model
    if payload.is_active is not None:
        req.is_active = payload.is_active

    db.commit()
    db.refresh(req)
    return req


@router.post("/match", response_model=List[ResumeMatchResponse])
async def match_resumes(
    requirement_id: str = Form(...),
    resume_ids: str = Form(...),  # comma-separated list of resume IDs
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.query(JobRequirement).filter(JobRequirement.id == requirement_id, JobRequirement.user_id == current_user.id, JobRequirement.is_active == True).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found or inactive")

    ids = [x.strip() for x in resume_ids.split(",") if x.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No resume IDs provided")

    matches = resume_service.match_resumes(db=db, user_id=current_user.id, requirement=req, resume_ids=ids)
    return matches


@router.get("/resumes", response_model=List[ResumeUploadResponse])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).all()
    # Map to response schema shape
    return [
        {
            "id": r.id,
            "original_filename": r.original_filename,
            "file_type": r.file_type,
            "created_at": r.created_at,
        }
        for r in rows
    ]


# History: list previous matches for the current user (optionally filter by requirement)
@router.get("/matches", response_model=List[ResumeMatchResponse])
async def list_matches(
    requirement_id: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(ResumeMatch).filter(ResumeMatch.user_id == current_user.id)
    if requirement_id:
        q = q.filter(ResumeMatch.requirement_id == requirement_id)
    q = q.order_by(ResumeMatch.created_at.desc()).limit(max(1, min(limit, 200)))
    rows = q.all()
    # FastAPI will auto-convert ORM to schema due to response_model; just return rows
    return rows
