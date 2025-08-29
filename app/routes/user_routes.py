from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app import schemas, models, auth
from app.database import get_db
from app.logger import get_logger
logger = get_logger(__name__)

router = APIRouter(tags=["Auth"])

@router.post("/register", response_model=dict)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = models.User(
        username=user.username,
        fullname=user.fullname,
        email=user.email,
        phone=user.phone,
        user_type=user.user_type,
        password=auth.hash_password(user.password),
        is_subscribed=False,  # New users start with free tier
        subscription_end_date=None
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/login", response_model=schemas.LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = auth.create_access_token({"sub": user.username}, db)
    refresh_token = auth.create_refresh_token({"sub": user.username}, db)
    
    # Return user details along with tokens
    user_data = {
        "id": user.id,
        "username": user.username,
        "fullname": user.fullname,
        "email": user.email,
        "phone": user.phone,
        "user_type": user.user_type,
        "is_subscribed": user.is_subscribed,
        "subscription_end_date": user.subscription_end_date
    }
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "user": user_data
    }

@router.post("/refresh", response_model=schemas.TokenPair)
def refresh_token(body: schemas.TokenRefresh, db: Session = Depends(get_db)):
    payload = auth.decode_token(body.refresh_token)
    if not payload or auth.get_token_type(body.refresh_token) != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if auth.is_blacklisted(payload.get("jti"), db):
        raise HTTPException(status_code=401, detail="Token has been blacklisted")
    access_token = auth.create_access_token({"sub": payload["sub"]}, db)
    refresh_token = auth.create_refresh_token({"sub": payload["sub"]}, db)
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/logout")
def logout(body: schemas.TokenLogout, db: Session = Depends(get_db)):
    payload = auth.decode_token(body.refresh_token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    auth.blacklist_token(body.refresh_token, db)
    return {"message": "User logged out. Refresh token blacklisted."}

@router.get("/profile", response_model=schemas.UserProfileResponse)
def get_user_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Get comprehensive user profile with subscription and usage info"""
    from app.subscription_service import SubscriptionService
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
