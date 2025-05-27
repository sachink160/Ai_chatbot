from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app import schemas, models, auth
from app.database import get_db

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
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/login", response_model=schemas.TokenPair)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = auth.create_access_token({"sub": user.username}, db)
    refresh_token = auth.create_refresh_token({"sub": user.username}, db)
    return {"access_token": access_token, "refresh_token": refresh_token}

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
