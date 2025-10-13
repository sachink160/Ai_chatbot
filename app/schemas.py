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
    dynamic_prompt_documents_uploaded: Optional[int] = 0
    max_chats: int
    max_documents: int
    max_hr_documents: int
    max_video_uploads: int
    max_dynamic_prompt_documents: Optional[int] = 5

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

class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


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

# Dynamic Prompt Schemas
class DynamicPromptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_template: str
    gpt_model: Optional[str] = "gpt-4o-mini"

class DynamicPromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    gpt_model: Optional[str] = None
    is_active: Optional[bool] = None

class DynamicPromptResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    prompt_template: str
    gpt_model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Document Processing Schemas
class DocumentProcessRequest(BaseModel):
    prompt_id: str
    file_path: str
    original_filename: str

class DocumentProcessResponse(BaseModel):
    id: str
    prompt_id: str
    original_filename: str
    file_type: str
    processing_status: str
    extracted_text: Optional[str] = None
    processed_result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

class DocumentUploadRequest(BaseModel):
    prompt_id: str

# Resume module schemas
class ResumeUploadResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    created_at: datetime

class JobRequirementCreate(BaseModel):
    title: str
    description: str | None = None
    requirement_json: str  # JSON string with criteria, skills, keywords
    gpt_model: str | None = "gpt-4o-mini"

class JobRequirementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    requirement_json: str | None = None
    gpt_model: str | None = None
    is_active: bool | None = None

class JobRequirementResponse(BaseModel):
    id: str
    title: str
    description: str | None
    requirement_json: str
    gpt_model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ResumeMatchResponse(BaseModel):
    id: str
    requirement_id: str
    resume_id: str
    score: float
    rationale: str | None
    match_metadata: str | None
    created_at: datetime