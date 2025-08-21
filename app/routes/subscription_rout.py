from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth, database
from app.subscription_service import SubscriptionService
from app import schemas
from typing import List
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Subscription"])

@router.get("/plans", response_model=List[schemas.SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(database.get_db)):
    """Get all available subscription plans"""
    plans = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.is_active == True).all()
    return [
        schemas.SubscriptionPlanResponse(
            id=plan.id,
            name=plan.name,
            price=plan.price,
            duration_days=plan.duration_days,
            max_chats_per_month=plan.max_chats_per_month,
            max_documents=plan.max_documents,
            max_hr_documents=plan.max_hr_documents,
            max_video_uploads=plan.max_video_uploads,
            features=plan.features,
            is_active=plan.is_active
        )
        for plan in plans
    ]

@router.get("/user/subscription", response_model=schemas.UserSubscriptionResponse)
async def get_user_subscription(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get current user's subscription information"""
    if not current_user.subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    return schemas.UserSubscriptionResponse(
        id=current_user.subscription.id,
        plan_name=current_user.subscription.plan.name,
        start_date=current_user.subscription.start_date,
        end_date=current_user.subscription.end_date,
        status=current_user.subscription.status,
        payment_status=current_user.subscription.payment_status,
        features=current_user.subscription.plan.features
    )

@router.get("/user/usage", response_model=schemas.UsageResponse)
async def get_user_usage(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get current user's usage information"""
    limits = SubscriptionService.get_user_limits(current_user, db)
    usage = SubscriptionService.get_current_usage(current_user, db)
    
    return schemas.UsageResponse(
        month_year=usage.month_year,
        chats_used=usage.chats_used,
        documents_uploaded=usage.documents_uploaded,
        hr_documents_uploaded=usage.hr_documents_uploaded,
        video_uploads=usage.video_uploads,
        max_chats=limits["max_chats_per_month"],
        max_documents=limits["max_documents"],
        max_hr_documents=limits["max_hr_documents"],
        max_video_uploads=limits["max_video_uploads"]
    )

@router.post("/subscribe")
async def subscribe_to_plan(
    subscription_data: schemas.UserSubscriptionCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Subscribe user to a plan (simplified - no actual payment processing)"""
    # Check if plan exists
    plan = db.query(models.SubscriptionPlan).filter(
        models.SubscriptionPlan.id == subscription_data.plan_id,
        models.SubscriptionPlan.is_active == True
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Check if user already has an active subscription
    if current_user.subscription and current_user.subscription.status == "active":
        raise HTTPException(status_code=400, detail="User already has an active subscription")
    
    # Create subscription (in real app, this would happen after payment confirmation)
    from datetime import timedelta, datetime, timezone
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=plan.duration_days)
    
    subscription = models.UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        start_date=start_date,
        end_date=end_date,
        status="active",
        payment_status="completed"  # Simplified - assume payment is completed
    )
    
    db.add(subscription)
    
    # Update user subscription status
    current_user.is_subscribed = True
    current_user.subscription_end_date = end_date
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User {current_user.id} subscribed to plan {plan.name}")
    
    return {
        "message": f"Successfully subscribed to {plan.name} plan",
        "plan_name": plan.name,
        "end_date": end_date,
        "features": plan.features
    }

@router.post("/cancel")
async def cancel_subscription(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Cancel current user's subscription"""
    if not current_user.subscription or current_user.subscription.status != "active":
        raise HTTPException(status_code=400, detail="No active subscription to cancel")
    
    # Cancel subscription
    current_user.subscription.status = "cancelled"
    current_user.is_subscribed = False
    current_user.subscription_end_date = None
    
    db.commit()
    
    logger.info(f"User {current_user.id} cancelled subscription")
    
    return {"message": "Subscription cancelled successfully"}

@router.get("/user/profile", response_model=schemas.UserProfileResponse)
async def get_user_profile(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get comprehensive user profile with subscription and usage info"""
    subscription_info = SubscriptionService.get_user_subscription_info(current_user, db)
    
    return schemas.UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        fullname=current_user.fullname,
        email=current_user.email,
        phone=current_user.phone,
        user_type=current_user.user_type,
        is_subscribed=subscription_info["is_subscribed"],
        subscription_end_date=subscription_info.get("subscription_end_date"),
        current_usage=schemas.UsageResponse(
            month_year=subscription_info["current_usage"]["month_year"],
            chats_used=subscription_info["current_usage"]["chats_used"],
            documents_uploaded=subscription_info["current_usage"]["documents_uploaded"],
            hr_documents_uploaded=subscription_info["current_usage"]["hr_documents_uploaded"],
            video_uploads=subscription_info["current_usage"]["video_uploads"],
            max_chats=subscription_info["limits"]["max_chats_per_month"],
            max_documents=subscription_info["limits"]["max_documents"],
            max_hr_documents=subscription_info["limits"]["max_hr_documents"],
            max_video_uploads=subscription_info["limits"]["max_video_uploads"]
        )
    )

@router.post("/initialize-plans")
async def initialize_subscription_plans(db: Session = Depends(database.get_db)):
    """Initialize default subscription plans (admin only)"""
    try:
        SubscriptionService.create_subscription_plans(db)
        return {"message": "Subscription plans initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing subscription plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize subscription plans")
