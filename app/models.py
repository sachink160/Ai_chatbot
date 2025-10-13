import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Float
import json
from sqlalchemy import Column, String
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    fullname = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    user_type = Column(String)
    password = Column(String)
    is_subscribed = Column(Boolean, default=False)
    subscription_end_date = Column(DateTime, nullable=True)
    documents = relationship("Document", back_populates="owner")  # Add this line
    hrdocuments = relationship("Hr_Document", back_populates="owner", cascade="all, delete-orphan")  # Add this line
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    usage = relationship("UsageTracking", back_populates="user", cascade="all, delete-orphan")
    dynamic_prompts = relationship("DynamicPrompt", cascade="all, delete-orphan")
    processed_documents = relationship("ProcessedDocument", cascade="all, delete-orphan")
    resumes = relationship("Resume", cascade="all, delete-orphan")
    job_requirements = relationship("JobRequirement", cascade="all, delete-orphan")
    resume_matches = relationship("ResumeMatch", cascade="all, delete-orphan")

class OutstandingToken(Base):
    __tablename__ = "outstanding_tokens"
    jti = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    token_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"
    jti = Column(String, primary_key=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)   
    path = Column(String)
    user_id = Column(String, ForeignKey("users.id"))  # Changed from Integer to String
    owner = relationship("User", back_populates="documents")

class StringList(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None or value == "":
            return []
        return json.loads(value)
class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    message = Column(String)
    response = Column(String)
    tool_used = Column(StringList)  # List of tool names
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="chat_history")

User.chat_history = relationship(
    "ChatHistory", back_populates="user", cascade="all, delete-orphan"
)


class Hr_Document(Base):
    __tablename__ = "hr_documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    path = Column(String)
    user_id = Column(String, ForeignKey("users.id"))
    is_active = Column(Integer, default=0)  # 0 = inactive, 1 = active
    owner = relationship("User", back_populates="hrdocuments")

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    price = Column(Float)
    duration_days = Column(Integer)
    max_chats_per_month = Column(Integer)
    max_documents = Column(Integer)
    max_hr_documents = Column(Integer)
    max_video_uploads = Column(Integer)
    max_dynamic_prompt_documents = Column(Integer, default=5)  # Default 5 documents for dynamic prompts
    features = Column(String)  # JSON string of features
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    plan_id = Column(String, ForeignKey("subscription_plans.id"))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    status = Column(String, default="active")  # active, expired, cancelled
    payment_status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan")

class UsageTracking(Base):
    __tablename__ = "usage_tracking"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    month_year = Column(String)  # Format: "2024-01"
    chats_used = Column(Integer, default=0)
    documents_uploaded = Column(Integer, default=0)
    hr_documents_uploaded = Column(Integer, default=0)
    video_uploads = Column(Integer, default=0)
    dynamic_prompt_documents_uploaded = Column(Integer, default=0)  # Track dynamic prompt document uploads
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="usage")

    # Optional counters for resume module (added safely; migrations recommended for production)
    # These attributes may not exist in the underlying DB if migrations haven't been applied.
    # Access via getattr/setattr with defaults elsewhere to avoid crashes.

class DynamicPrompt(Base):
    __tablename__ = "dynamic_prompts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String)
    prompt_template = Column(String, nullable=False)  # The actual prompt template
    gpt_model = Column(String, default="gpt-4o-mini")  # GPT model selection
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class ProcessedDocument(Base):
    __tablename__ = "processed_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    prompt_id = Column(String, ForeignKey("dynamic_prompts.id"))
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(String)  # Store extracted text
    processed_result = Column(String)  # Store the final processed result (JSON)
    file_type = Column(String)  # pdf, docx, txt, image, etc.
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    prompt = relationship("DynamicPrompt")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)
    extracted_text = Column(String)
    parsed_profile = Column(String)  # JSON string with structured resume info
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class JobRequirement(Base):
    __tablename__ = "job_requirements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    requirement_json = Column(String, nullable=False)  # JSON schema for skills, experience, keywords
    gpt_model = Column(String, default="gpt-4o-mini")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")

class ResumeMatch(Base):
    __tablename__ = "resume_matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    requirement_id = Column(String, ForeignKey("job_requirements.id"))
    resume_id = Column(String, ForeignKey("resumes.id"))
    score = Column(Float, default=0.0)
    rationale = Column(String)  # Explanation of the score
    match_metadata = Column(String)  # JSON with per-criterion scores
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    requirement = relationship("JobRequirement")
    resume = relationship("Resume")