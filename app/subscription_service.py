from sqlalchemy.orm import Session
from app import models
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
from app.logger import get_logger

logger = get_logger(__name__)

class SubscriptionService:
    
    @staticmethod
    def get_free_tier_limits() -> Dict[str, int]:
        """Get free tier limits"""
        return {
            "max_chats_per_month": 10,
            "max_documents": 2,
            "max_hr_documents": 2,
            "max_video_uploads": 1,
            "max_dynamic_prompt_documents": 5  # Default 5 documents for dynamic prompts
        }
    
    @staticmethod
    def get_user_limits(user: models.User, db: Session) -> Dict[str, int]:
        """Get user's current limits based on subscription status"""
        if user.is_subscribed and user.subscription_end_date:
            # Convert subscription_end_date to timezone-aware if it's naive
            end_date = user.subscription_end_date
            if end_date.tzinfo is None:
                # If naive, assume UTC
                end_date = end_date.replace(tzinfo=timezone.utc)
            
            if end_date > datetime.now(timezone.utc):
                # User has active subscription
                if user.subscription:
                    plan = user.subscription.plan
                    return {
                        "max_chats_per_month": plan.max_chats_per_month,
                        "max_documents": plan.max_documents,
                        "max_hr_documents": plan.max_hr_documents,
                        "max_video_uploads": plan.max_video_uploads,
                        "max_dynamic_prompt_documents": getattr(plan, 'max_dynamic_prompt_documents', 5)
                    }
        
        # Return free tier limits
        return SubscriptionService.get_free_tier_limits()
    
    @staticmethod
    def get_current_usage(user: models.User, db: Session) -> models.UsageTracking:
        """Get or create current month usage tracking"""
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        
        usage = db.query(models.UsageTracking).filter(
            models.UsageTracking.user_id == user.id,
            models.UsageTracking.month_year == current_month
        ).first()
        
        if not usage:
            usage = models.UsageTracking(
                user_id=user.id,
                month_year=current_month
            )
            db.add(usage)
            db.commit()
            db.refresh(usage)
        
        return usage
    
    @staticmethod
    def can_use_chat(user: models.User, db: Session) -> Dict[str, Any]:
        """Check if user can use chat service"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        can_use = usage.chats_used < limits["max_chats_per_month"]
        
        return {
            "can_use": can_use,
            "chats_used": usage.chats_used,
            "max_chats": limits["max_chats_per_month"],
            "remaining": max(0, limits["max_chats_per_month"] - usage.chats_used)
        }
    
    @staticmethod
    def can_upload_document(user: models.User, db: Session) -> Dict[str, Any]:
        """Check if user can upload document"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        can_use = usage.documents_uploaded < limits["max_documents"]
        
        return {
            "can_use": can_use,
            "documents_uploaded": usage.documents_uploaded,
            "max_documents": limits["max_documents"],
            "remaining": max(0, limits["max_documents"] - usage.documents_uploaded)
        }
    
    @staticmethod
    def can_upload_hr_document(user: models.User, db: Session) -> Dict[str, Any]:
        """Check if user can upload HR document"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        can_use = usage.hr_documents_uploaded < limits["max_hr_documents"]
        
        return {
            "can_use": can_use,
            "hr_documents_uploaded": usage.hr_documents_uploaded,
            "max_hr_documents": limits["max_hr_documents"],
            "remaining": max(0, limits["max_hr_documents"] - usage.hr_documents_uploaded)
        }
    
    @staticmethod
    def can_upload_video(user: models.User, db: Session) -> Dict[str, Any]:
        """Check if user can upload video"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        can_use = usage.video_uploads < limits["max_video_uploads"]
        
        return {
            "can_use": can_use,
            "video_uploads": usage.video_uploads,
            "max_video_uploads": limits["max_video_uploads"],
            "remaining": max(0, limits["max_video_uploads"] - usage.video_uploads)
        }
    
    @staticmethod
    def increment_chat_usage(user: models.User, db: Session):
        """Increment chat usage for current month"""
        usage = SubscriptionService.get_current_usage(user, db)
        usage.chats_used += 1
        db.commit()
        logger.info(f"Incremented chat usage for user {user.id}")
    
    @staticmethod
    def increment_document_usage(user: models.User, db: Session):
        """Increment document usage for current month"""
        usage = SubscriptionService.get_current_usage(user, db)
        usage.documents_uploaded += 1
        db.commit()
        logger.info(f"Incremented document usage for user {user.id}")
    
    @staticmethod
    def increment_hr_document_usage(user: models.User, db: Session):
        """Increment HR document usage for current month"""
        usage = SubscriptionService.get_current_usage(user, db)
        usage.hr_documents_uploaded += 1
        db.commit()
        logger.info(f"Incremented HR document usage for user {user.id}")
    
    @staticmethod
    def increment_video_usage(user: models.User, db: Session):
        """Increment video usage for current month"""
        usage = SubscriptionService.get_current_usage(user, db)
        usage.video_uploads += 1
        db.commit()
        logger.info(f"Incremented video usage for user {user.id}")
    
    @staticmethod
    def can_upload_dynamic_prompt_document(user: models.User, db: Session) -> Dict[str, Any]:
        """Check if user can upload dynamic prompt document"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        uploaded_count = getattr(usage, 'dynamic_prompt_documents_uploaded', 0)
        max_count = limits.get("max_dynamic_prompt_documents", 5)
        
        can_use = uploaded_count < max_count
        
        return {
            "can_use": can_use,
            "dynamic_prompt_documents_uploaded": uploaded_count,
            "max_dynamic_prompt_documents": max_count,
            "remaining": max(0, max_count - uploaded_count)
        }
    
    @staticmethod
    def increment_dynamic_prompt_document_usage(user: models.User, db: Session):
        """Increment dynamic prompt document usage for current month"""
        usage = SubscriptionService.get_current_usage(user, db)
        if hasattr(usage, 'dynamic_prompt_documents_uploaded'):
            usage.dynamic_prompt_documents_uploaded += 1
        else:
            # If column doesn't exist yet, set it to 1
            setattr(usage, 'dynamic_prompt_documents_uploaded', 1)
        db.commit()
        logger.info(f"Incremented dynamic prompt document usage for user {user.id}")
    
    @staticmethod
    def create_subscription_plans(db: Session):
        """Create default subscription plans if they don't exist"""
        plans_data = [
            {
                "name": "Basic",
                "price": 9.99,
                "duration_days": 30,
                "max_chats_per_month": 100,
                "max_documents": 20,
                "max_hr_documents": 20,
                "max_video_uploads": 10,
                "max_dynamic_prompt_documents": 10,
                "features": json.dumps([
                    "100 AI chats per month",
                    "20 document uploads",
                    "20 HR document uploads",
                    "10 video uploads",
                    "10 dynamic prompt document uploads",
                    "Priority support"
                ])
            },
            {
                "name": "Pro",
                "price": 19.99,
                "duration_days": 30,
                "max_chats_per_month": 500,
                "max_documents": 100,
                "max_hr_documents": 100,
                "max_video_uploads": 50,
                "max_dynamic_prompt_documents": 50,
                "features": json.dumps([
                    "500 AI chats per month",
                    "100 document uploads",
                    "100 HR document uploads",
                    "50 video uploads",
                    "50 dynamic prompt document uploads",
                    "Advanced analytics",
                    "Priority support",
                    "Custom integrations"
                ])
            },
            {
                "name": "Enterprise",
                "price": 49.99,
                "duration_days": 30,
                "max_chats_per_month": 2000,
                "max_documents": 500,
                "max_hr_documents": 500,
                "max_video_uploads": 200,
                "max_dynamic_prompt_documents": 200,
                "features": json.dumps([
                    "2000 AI chats per month",
                    "500 document uploads",
                    "500 HR document uploads",
                    "200 video uploads",
                    "200 dynamic prompt document uploads",
                    "Advanced analytics",
                    "Priority support",
                    "Custom integrations",
                    "Dedicated account manager",
                    "API access"
                ])
            }
        ]
        
        for plan_data in plans_data:
            existing_plan = db.query(models.SubscriptionPlan).filter(
                models.SubscriptionPlan.name == plan_data["name"]
            ).first()
            
            if not existing_plan:
                plan = models.SubscriptionPlan(**plan_data)
                db.add(plan)
                logger.info(f"Created subscription plan: {plan_data['name']}")
        
        db.commit()
        logger.info("Subscription plans initialization completed")
    
    @staticmethod
    def get_user_subscription_info(user: models.User, db: Session) -> Dict[str, Any]:
        """Get comprehensive user subscription and usage information"""
        limits = SubscriptionService.get_user_limits(user, db)
        usage = SubscriptionService.get_current_usage(user, db)
        
        subscription_info = {
            "is_subscribed": user.is_subscribed,
            "subscription_end_date": user.subscription_end_date,
            "current_usage": {
                "month_year": usage.month_year,
                "chats_used": usage.chats_used,
                "documents_uploaded": usage.documents_uploaded,
                "hr_documents_uploaded": usage.hr_documents_uploaded,
                "video_uploads": usage.video_uploads,
                "dynamic_prompt_documents_uploaded": getattr(usage, 'dynamic_prompt_documents_uploaded', 0)
            },
            "limits": limits,
            "remaining": {
                "chats": max(0, limits["max_chats_per_month"] - usage.chats_used),
                "documents": max(0, limits["max_documents"] - usage.documents_uploaded),
                "hr_documents": max(0, limits["max_hr_documents"] - usage.hr_documents_uploaded),
                "video_uploads": max(0, limits["max_video_uploads"] - usage.video_uploads),
                "dynamic_prompt_documents": max(0, limits.get("max_dynamic_prompt_documents", 5) - getattr(usage, 'dynamic_prompt_documents_uploaded', 0))
            }
        }
        
        if user.subscription:
            subscription_info["plan"] = {
                "name": user.subscription.plan.name,
                "price": user.subscription.plan.price,
                "status": user.subscription.status,
                "payment_status": user.subscription.payment_status
            }
        
        return subscription_info

    @staticmethod
    def get_user_subscription_history(user: models.User, db: Session):
        """Return all subscriptions for a user ordered by start_date desc.

        Returns a list of UserSubscription ORM objects. Caller may map to
        response schemas as needed.
        """
        subs = db.query(models.UserSubscription).filter(
            models.UserSubscription.user_id == user.id
        ).order_by(models.UserSubscription.start_date.desc()).all()

        return subs
