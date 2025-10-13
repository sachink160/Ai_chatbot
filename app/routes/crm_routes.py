from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from app import models, database, auth

# Use a router prefix so final path is /crm/metrics
router = APIRouter(prefix="/crm", tags=["CRM"])


def admin_required(current_user: models.User = Depends(auth.get_current_user)) -> models.User:
    if not current_user or (current_user.user_type or '').lower() != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.get("/metrics", response_model=dict)
def get_crm_metrics(
    _: models.User = Depends(admin_required),
    db: Session = Depends(database.get_db)
):
    now = datetime.now(timezone.utc)
    month_year = now.strftime('%Y-%m')

    # Users
    total_users = db.query(models.User).count()
    admin_users = db.query(models.User).filter(models.User.user_type == 'admin').count()

    # Active subscriptions (by User flags and end_date)
    active_subscribed_users = db.query(models.User).filter(
        models.User.is_subscribed == True,
        models.User.subscription_end_date != None,
        models.User.subscription_end_date > now
    ).count()

    # Active subscriptions (by UserSubscription table)
    active_user_subscriptions = db.query(models.UserSubscription).filter(
        models.UserSubscription.status == 'active',
        models.UserSubscription.end_date > now
    ).count()

    # Expiring soon (next 7 days)
    expiring_soon = db.query(models.UserSubscription).filter(
        models.UserSubscription.status == 'active',
        models.UserSubscription.end_date > now,
        models.UserSubscription.end_date <= now + timedelta(days=7)
    ).count()

    # New users last 7 days
    seven_days_ago = now - timedelta(days=7)
    # If User has no created_at, use subscription created as proxy; otherwise, try created_at field if available
    try:
        from sqlalchemy import and_
        new_users_last_7_days = db.query(models.User).filter(models.User.created_at >= seven_days_ago).count()  # type: ignore[attr-defined]
    except Exception:
        new_users_last_7_days = db.query(models.UserSubscription).filter(models.UserSubscription.created_at >= seven_days_ago).count()

    # Churned in last 30 days (ended subscriptions)
    thirty_days_ago = now - timedelta(days=30)
    churned_last_30_days = db.query(models.UserSubscription).filter(
        models.UserSubscription.status != 'active',
        models.UserSubscription.end_date <= now,
        models.UserSubscription.end_date >= thirty_days_ago
    ).count()

    # Usage summary for current month
    usage_rows = db.query(models.UsageTracking).filter(models.UsageTracking.month_year == month_year).all()
    chats_used = sum(u.chats_used or 0 for u in usage_rows)
    documents_uploaded = sum(u.documents_uploaded or 0 for u in usage_rows)
    hr_documents_uploaded = sum(u.hr_documents_uploaded or 0 for u in usage_rows)
    video_uploads = sum(u.video_uploads or 0 for u in usage_rows)
    dynamic_prompt_documents_uploaded = sum(u.dynamic_prompt_documents_uploaded or 0 for u in usage_rows)

    # Top users by chats this month (top 5)
    top_users_by_chats = (
        db.query(models.UsageTracking, models.User)
          .join(models.User, models.UsageTracking.user_id == models.User.id)
          .filter(models.UsageTracking.month_year == month_year)
          .order_by(models.UsageTracking.chats_used.desc())
          .limit(5)
          .all()
    )
    top_users = [
        {
            "user_id": u.id,
            "username": u.username,
            "chats_used": ut.chats_used,
            "documents_uploaded": ut.documents_uploaded,
        }
        for ut, u in top_users_by_chats
    ]

    # Plan breakdown (active subscriptions by plan)
    plan_rows = (
        db.query(models.SubscriptionPlan.name, models.UserSubscription)
          .join(models.UserSubscription, models.SubscriptionPlan.id == models.UserSubscription.plan_id)
          .filter(models.UserSubscription.status == 'active', models.UserSubscription.end_date > now)
          .all()
    )
    plans = defaultdict(int)
    for plan_name, _sub in plan_rows:
        plans[plan_name] += 1

    # Free vs Paid
    paid_users = active_user_subscriptions
    free_users = max(total_users - paid_users, 0)

    # Daily signups last 7 days (approx using subscription create; if user.created_at exists, that is preferred)
    daily_signups = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        try:
            count = db.query(models.User).filter(models.User.created_at >= datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),  # type: ignore[attr-defined]
                                              models.User.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)).count()  # type: ignore[attr-defined]
        except Exception:
            count = db.query(models.UserSubscription).filter(models.UserSubscription.created_at >= datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
                                                            models.UserSubscription.created_at < datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)).count()
        daily_signups.append({"date": day.isoformat(), "count": count})

    # Content totals
    total_documents = db.query(models.Document).count()
    total_hr_docs = db.query(models.Hr_Document).count()
    total_dynamic_prompt_docs = db.query(models.ProcessedDocument).count()

    return {
        "users": {
            "total": total_users,
            "admins": admin_users,
            "subscribed_active": active_subscribed_users,
            "new_last_7_days": new_users_last_7_days,
            "free_users": free_users,
            "paid_users": paid_users,
        },
        "subscriptions": {
            "active": active_user_subscriptions,
            "expiring_7_days": expiring_soon,
            "churned_30_days": churned_last_30_days,
            "plans": dict(plans),
        },
        "usage_month": month_year,
        "usage": {
            "chats_used": chats_used,
            "documents_uploaded": documents_uploaded,
            "hr_documents_uploaded": hr_documents_uploaded,
            "video_uploads": video_uploads,
            "dynamic_prompt_documents_uploaded": dynamic_prompt_documents_uploaded,
        },
        "top_users": top_users,
        "daily_signups": daily_signups,
        "content_totals": {
            "documents": total_documents,
            "hr_documents": total_hr_docs,
            "dynamic_prompt_documents": total_dynamic_prompt_docs,
        },
    }


