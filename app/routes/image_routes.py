from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app import models
from app.services.image_generation import generate_image, can_generate_image, ensure_user_output_dir
from app.subscription_service import SubscriptionService

router = APIRouter(tags=["AI Images"])


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    model: Optional[str] = "black-forest-labs/FLUX.1-dev"
    guidance_scale: Optional[float] = 7.5
    num_inference_steps: Optional[int] = 50
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    seed: Optional[int] = None


class ImageRecordResponse(BaseModel):
    id: str
    prompt: str
    negative_prompt: Optional[str]
    model: str
    guidance_scale: float
    num_inference_steps: int
    width: int
    height: int
    seed: Optional[str]
    output_path: str
    status: str
    error_message: Optional[str]


class ImageSubscriptionInfoResponse(BaseModel):
    can_use: bool
    ai_images_generated: int
    max_ai_images: int
    remaining: int


@router.post("/ai/images/generate", response_model=ImageRecordResponse)
def create_image(
    body: ImageGenerateRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        record = generate_image(
            db=db,
            user=current_user,
            prompt=body.prompt,
            negative_prompt=body.negative_prompt,
            model=body.model or "black-forest-labs/FLUX.1-dev",
            guidance_scale=body.guidance_scale or 7.5,
            num_inference_steps=body.num_inference_steps or 50,
            width=body.width or 1024,
            height=body.height or 1024,
            seed=body.seed,
        )
        return ImageRecordResponse(
            id=record.id,
            prompt=record.prompt,
            negative_prompt=record.negative_prompt,
            model=record.model,
            guidance_scale=record.guidance_scale,
            num_inference_steps=record.num_inference_steps,
            width=record.width,
            height=record.height,
            seed=record.seed,
            output_path=record.output_path,
            status=record.status,
            error_message=record.error_message,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Generation failed: {e}")


@router.get("/ai/images/history", response_model=List[ImageRecordResponse])
def list_images(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(models.ImageGeneration)
        .filter(models.ImageGeneration.user_id == current_user.id)
        .order_by(models.ImageGeneration.created_at.desc())
        .all()
    )
    return [
        ImageRecordResponse(
            id=r.id,
            prompt=r.prompt,
            negative_prompt=r.negative_prompt,
            model=r.model,
            guidance_scale=r.guidance_scale,
            num_inference_steps=r.num_inference_steps,
            width=r.width,
            height=r.height,
            seed=r.seed,
            output_path=r.output_path,
            status=r.status,
            error_message=r.error_message,
        )
        for r in records
    ]


@router.get("/ai/images/subscription", response_model=ImageSubscriptionInfoResponse)
def get_image_subscription_info(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get AI image subscription and usage information for the current user"""
    subscription_info = SubscriptionService.can_generate_ai_image(current_user, db)
    return ImageSubscriptionInfoResponse(
        can_use=subscription_info["can_use"],
        ai_images_generated=subscription_info["ai_images_generated"],
        max_ai_images=subscription_info["max_ai_images"],
        remaining=subscription_info["remaining"]
    )


@router.get("/ai/images/{image_id}/download")
def download_image(
    image_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(models.ImageGeneration)
        .filter(models.ImageGeneration.id == image_id)
        .filter(models.ImageGeneration.user_id == current_user.id)
        .first()
    )
    if not record or not record.output_path or not os.path.exists(record.output_path):
        raise HTTPException(status_code=404, detail="Image not found")
    filename = os.path.basename(record.output_path)
    return FileResponse(path=record.output_path, filename=filename)



@router.delete("/ai/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(models.ImageGeneration)
        .filter(models.ImageGeneration.id == image_id)
        .filter(models.ImageGeneration.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")

    # Best-effort file removal; proceed even if file deletion fails
    try:
        if record.output_path and os.path.exists(record.output_path):
            os.remove(record.output_path)
    except Exception:
        pass

    db.delete(record)
    db.commit()

    # 204 No Content
    return
