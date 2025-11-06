"""
Settings Service - Manages user-specific API keys and settings
Falls back to .env file if not found in database
"""
import os
from typing import Optional, List
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app import models
from datetime import datetime

# Load .env file if DATABASE_URL is not already set (i.e., not in Docker)
if not os.getenv("DATABASE_URL"):
    load_dotenv()


class SettingsService:
    """Service to manage user-specific API keys and settings"""
    
    @staticmethod
    def get_user_setting(user_id: str, name: str, db: Session) -> Optional[models.MasterSettings]:
        """Get a specific setting for a user by name"""
        return db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == user_id,
            models.MasterSettings.name == name,
            models.MasterSettings.is_active == True
        ).first()
    
    @staticmethod
    def get_all_user_settings(user_id: str, db: Session) -> List[models.MasterSettings]:
        """Get all active settings for a user"""
        return db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == user_id,
            models.MasterSettings.is_active == True
        ).all()
    
    @staticmethod
    def get_api_key(key_name: str, user_id: Optional[str] = None, db: Optional[Session] = None, default: Optional[str] = None) -> Optional[str]:
        """
        Get API key from database (user-specific) or fallback to .env file
        
        Args:
            key_name: Name of the API key (e.g., 'OPENAI_API_KEY', 'HF_TOKEN')
            user_id: User ID to get user-specific key (optional)
            db: Database session (required if user_id is provided)
            default: Default value if not found in DB or .env
        
        Returns:
            API key value or None
        """
        # Try to get from database first (if user_id and db are provided)
        if user_id and db:
            setting = SettingsService.get_user_setting(user_id, key_name, db)
            if setting and setting.value:
                return setting.value
        
        # Fallback to .env file
        env_value = os.getenv(key_name, default)
        return env_value
    
    @staticmethod
    def get_openai_api_key(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get OpenAI API key for user or from .env"""
        return SettingsService.get_api_key('OPENAI_API_KEY', user_id, db)
    
    @staticmethod
    def get_pinecone_api_key(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get Pinecone API key for user or from .env"""
        return SettingsService.get_api_key('PINECONE_API_KEY', user_id, db)
    
    @staticmethod
    def get_pinecone_environment(user_id: Optional[str] = None, db: Optional[Session] = None, default: str = "us-east-1") -> str:
        """Get Pinecone environment for user or from .env"""
        return SettingsService.get_api_key('PINECONE_ENVIRONMENT', user_id, db, default) or default
    
    @staticmethod
    def get_pinecone_index_prefix(user_id: Optional[str] = None, db: Optional[Session] = None, default: str = "rag") -> str:
        """Get Pinecone index name prefix for user or from .env"""
        return SettingsService.get_api_key('PINECONE_INDEX_NAME_PREFIX', user_id, db, default) or default
    
    @staticmethod
    def get_hf_token(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get HuggingFace token for user or from .env"""
        return SettingsService.get_api_key('HF_TOKEN', user_id, db)
    
    @staticmethod
    def get_news_api_key(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get News API key for user or from .env"""
        return SettingsService.get_api_key('NEWS_API_KEY', user_id, db)
    
    @staticmethod
    def get_twilio_sid(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get Twilio SID for user or from .env"""
        return SettingsService.get_api_key('TWILIO_SID', user_id, db)
    
    @staticmethod
    def get_twilio_auth(user_id: Optional[str] = None, db: Optional[Session] = None) -> Optional[str]:
        """Get Twilio Auth token for user or from .env"""
        return SettingsService.get_api_key('TWILIO_AUTH', user_id, db)
    
    @staticmethod
    def get_to_whatsapp(user_id: Optional[str] = None, db: Optional[Session] = None, default: str = "whatsapp:+918460117496") -> str:
        """Get TO WhatsApp number for user or from .env"""
        return SettingsService.get_api_key('TO_WHATSAPP', user_id, db, default) or default
    
    @staticmethod
    def get_from_whatsapp(user_id: Optional[str] = None, db: Optional[Session] = None, default: str = "whatsapp:+14155238886") -> str:
        """Get FROM WhatsApp number for user or from .env"""
        return SettingsService.get_api_key('FROM_WHATSAPP', user_id, db, default) or default
    
    @staticmethod
    def set_user_setting(
        user_id: str,
        name: str,
        value: str,
        db: Session,
        is_active: bool = True
    ) -> models.MasterSettings:
        """
        Set or update a user's API key setting
        
        Args:
            user_id: User ID
            name: Setting name (e.g., 'OPENAI_API_KEY', 'HF_TOKEN')
            value: Setting value (the actual API key)
            db: Database session
            is_active: Whether the setting is active
        
        Returns:
            The created or updated MasterSettings object
        """
        # Check for existing setting (including inactive ones)
        setting = db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == user_id,
            models.MasterSettings.name == name
        ).first()
        
        if setting:
            # Update existing setting
            setting.value = value
            setting.is_active = is_active
            setting.updated_at = datetime.utcnow()
        else:
            # Create new setting
            setting = models.MasterSettings(
                user_id=user_id,
                name=name,
                value=value,
                is_active=is_active
            )
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        return setting
    
    @staticmethod
    def delete_user_setting(user_id: str, name: str, db: Session) -> bool:
        """
        Delete a user's setting (soft delete by setting is_active=False)
        
        Returns:
            True if setting was found and deactivated, False otherwise
        """
        setting = db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == user_id,
            models.MasterSettings.name == name
        ).first()
        
        if setting:
            setting.is_active = False
            setting.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_user_setting(
        user_id: str,
        name: str,
        value: Optional[str] = None,
        is_active: Optional[bool] = None,
        db: Optional[Session] = None
    ) -> Optional[models.MasterSettings]:
        """
        Update an existing user setting
        
        Args:
            user_id: User ID
            name: Setting name
            value: New value (optional, only updates if provided)
            is_active: New active status (optional, only updates if provided)
            db: Database session
        
        Returns:
            Updated MasterSettings object or None if not found
        """
        if not db:
            return None
            
        setting = db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == user_id,
            models.MasterSettings.name == name
        ).first()
        
        if not setting:
            return None
        
        if value is not None:
            setting.value = value
        if is_active is not None:
            setting.is_active = is_active
        
        setting.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(setting)
        return setting

