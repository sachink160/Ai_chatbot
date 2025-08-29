from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    fullname: str
    email: str
    phone: str
    user_type: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenLogout(BaseModel):
    refresh_token: str

# Subscription related schemas
class SubscriptionPlanCreate(BaseModel):
    name: str
    price: float
    duration_days: int
    max_chats_per_month: int
    max_documents: int
    max_hr_documents: int
    max_video_uploads: int
    features: str

class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    price: float
    duration_days: int
    max_chats_per_month: int
    max_documents: int
    max_hr_documents: int
    max_video_uploads: int
    features: str
    is_active: bool

class UserSubscriptionCreate(BaseModel):
    plan_id: str

class UserSubscriptionResponse(BaseModel):
    id: str
    plan_name: str
    start_date: datetime
    end_date: datetime
    status: str
    payment_status: str
    features: str

class UsageResponse(BaseModel):
    month_year: str
    chats_used: int
    documents_uploaded: int
    hr_documents_uploaded: int
    video_uploads: int
    max_chats: int
    max_documents: int
    max_hr_documents: int
    max_video_uploads: int

class UserProfileResponse(BaseModel):
    id: str
    username: str
    fullname: str
    email: str
    phone: str
    user_type: str
    is_subscribed: bool
    subscription_end_date: Optional[datetime]
    current_usage: Optional[UsageResponse]


class DocUploadResponse(BaseModel):
    doc_id: int
    filename: str

class QARequest(BaseModel):
    doc_id: int
    question: str

class Question(BaseModel):
    document_id: str
    question: str


class Question_r(BaseModel):
    document_id: str
    question: str = ""
    prompt_type: str = "summarize"
    custom_query: str = ""

class Hr_Question(BaseModel):
    question: str