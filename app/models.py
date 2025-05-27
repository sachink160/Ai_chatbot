import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
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
    documents = relationship("Document", back_populates="owner")  # Add this line
    hrdocuments = relationship("Hr_Document", back_populates="owner", cascade="all, delete-orphan")  # Add this line
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

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
