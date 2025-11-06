import os
import io
from datetime import datetime, timezone
from typing import Optional, Tuple

from PIL import Image
from huggingface_hub import InferenceClient  # type: ignore
from sqlalchemy.orm import Session

from app import models
from app.logger import get_logger
from app.settings_service import SettingsService
from app.subscription_service import SubscriptionService

logger = get_logger(__name__)


DEFAULT_MODEL = "black-forest-labs/FLUX.1-dev"
DEFAULT_LIMIT_PER_MONTH = 3  # Free/default quota (fallback)


def _get_hf_token(user_id: Optional[str] = None, db: Optional[Session] = None) -> str:
    """Get HF token from user settings (DB) or fallback to .env"""
    token = SettingsService.get_hf_token(user_id, db)
    if not token:
        raise ValueError("HF_TOKEN not found in user settings or environment variables.")
    return token


def _get_client(user_id: Optional[str] = None, db: Optional[Session] = None) -> InferenceClient:
    """Get InferenceClient with user-specific API key or fallback to .env"""
    return InferenceClient(provider="nebius", api_key=_get_hf_token(user_id, db))


def get_user_image_month_count(user_id: str, db: Session) -> int:
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    start = datetime.strptime(current_month + "-01", "%Y-%m-%d")
    # naive datetime used for compatibility across existing codebase
    count = (
        db.query(models.ImageGeneration)
        .filter(models.ImageGeneration.user_id == user_id)
        .filter(models.ImageGeneration.created_at >= start)
        .count()
    )
    return count


def can_generate_image(user: models.User, db: Session) -> Tuple[bool, int, int, int]:
    """Return (can_use, used, max_allowed, remaining).
    
    Uses subscription service to get limits based on user's subscription plan.
    Falls back to DEFAULT_LIMIT_PER_MONTH if subscription service is unavailable.
    """
    try:
        # Use subscription service to get limits
        subscription_info = SubscriptionService.can_generate_ai_image(user, db)
        used = subscription_info["ai_images_generated"]
        max_allowed = subscription_info["max_ai_images"]
        remaining = subscription_info["remaining"]
        can_use = subscription_info["can_use"]
        return (can_use, used, max_allowed, remaining)
    except Exception as e:
        logger.warning(f"Failed to get subscription limits, using fallback: {e}")
        # Fallback to counting from database
        used = get_user_image_month_count(user.id, db)
        max_allowed = DEFAULT_LIMIT_PER_MONTH
        remaining = max(0, max_allowed - used)
        return (used < max_allowed, used, max_allowed, remaining)


def ensure_user_output_dir(base_dir: str, user_id: str) -> str:
    user_dir = os.path.join(base_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def save_image(image: Image.Image, base_dir: str, user_id: str, filename: Optional[str] = None) -> str:
    user_dir = ensure_user_output_dir(base_dir, user_id)
    name = filename or f"flux_{int(datetime.utcnow().timestamp())}.png"
    path = os.path.join(user_dir, name)
    image.save(path)
    return path


def generate_image(
    db: Session,
    user: models.User,
    prompt: str,
    negative_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 50,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    output_base_dir: str = os.path.join("processed", "ai_images"),
) -> models.ImageGeneration:
    can_use, used, max_allowed, remaining = can_generate_image(user, db)
    if not can_use:
        raise PermissionError(
            f"Image generation limit reached. Used {used}/{max_allowed} this month."
        )

    client = _get_client(user.id, db)

    try:
        response = client.text_to_image(
            prompt,
            model=model,
            negative_prompt=negative_prompt or "",
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            width=width,
            height=height,
            seed=seed,
        )

        if isinstance(response, Image.Image):
            image = response
        else:
            image = Image.open(io.BytesIO(response))

        output_path = save_image(image, output_base_dir, user.id)

        record = models.ImageGeneration(
            user_id=user.id,
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            model=model,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            width=width,
            height=height,
            seed=str(seed) if seed is not None else None,
            output_path=output_path,
            status="completed",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        # Increment usage tracking via subscription service
        try:
            SubscriptionService.increment_ai_image_usage(user, db)
        except Exception as e:
            logger.warning(f"Failed to increment AI image usage: {e}")
        
        return record
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        record = models.ImageGeneration(
            user_id=user.id,
            prompt=prompt,
            negative_prompt=negative_prompt or "",
            model=model,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            width=width,
            height=height,
            seed=str(seed) if seed is not None else None,
            output_path="",
            status="failed",
            error_message=str(e),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        raise


