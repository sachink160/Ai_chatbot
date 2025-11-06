from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.auth import get_current_user
from app.database import get_db
from app import models, schemas
from app.settings_service import SettingsService
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Master Settings"])


@router.post("/master-settings", response_model=schemas.MasterSettingsResponse, status_code=status.HTTP_201_CREATED)
def create_setting(
    setting: schemas.MasterSettingsCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new API key setting for the current user
    """
    try:
        # Check if setting with same name already exists for this user
        existing = SettingsService.get_user_setting(current_user.id, setting.name, db)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Setting with name '{setting.name}' already exists for this user"
            )
        
        new_setting = SettingsService.set_user_setting(
            user_id=current_user.id,
            name=setting.name,
            value=setting.value,
            db=db,
            is_active=setting.is_active
        )
        
        logger.info(f"Created setting '{setting.name}' for user {current_user.id}")
        return schemas.MasterSettingsResponse(
            id=new_setting.id,
            user_id=new_setting.user_id,
            name=new_setting.name,
            value=new_setting.value,
            is_active=new_setting.is_active,
            created_at=new_setting.created_at,
            updated_at=new_setting.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create setting: {str(e)}"
        )


@router.get("/master-settings", response_model=List[schemas.MasterSettingsResponse])
def get_all_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_inactive: Optional[bool] = False
):
    """
    Get all settings for the current user
    """
    try:
        if include_inactive:
            # Get all settings including inactive ones
            settings = db.query(models.MasterSettings).filter(
                models.MasterSettings.user_id == current_user.id
            ).all()
        else:
            # Get only active settings
            settings = SettingsService.get_all_user_settings(current_user.id, db)
        
        return [
            schemas.MasterSettingsResponse(
                id=s.id,
                user_id=s.user_id,
                name=s.name,
                value=s.value,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in settings
        ]
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settings: {str(e)}"
        )


@router.get("/master-settings/{setting_name}", response_model=schemas.MasterSettingsResponse)
def get_setting(
    setting_name: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific setting by name for the current user
    """
    try:
        setting = SettingsService.get_user_setting(current_user.id, setting_name, db)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_name}' not found for this user"
            )
        
        return schemas.MasterSettingsResponse(
            id=setting.id,
            user_id=setting.user_id,
            name=setting.name,
            value=setting.value,
            is_active=setting.is_active,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch setting: {str(e)}"
        )


@router.put("/master-settings/{setting_name}", response_model=schemas.MasterSettingsResponse)
def update_setting(
    setting_name: str,
    setting_update: schemas.MasterSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing setting by name for the current user
    """
    try:
        # Check if setting exists
        existing = db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == current_user.id,
            models.MasterSettings.name == setting_name
        ).first()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_name}' not found for this user"
            )
        
        # Update the setting
        updated_setting = SettingsService.update_user_setting(
            user_id=current_user.id,
            name=setting_name,
            value=setting_update.value,
            is_active=setting_update.is_active,
            db=db
        )
        
        if not updated_setting:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update setting"
            )
        
        logger.info(f"Updated setting '{setting_name}' for user {current_user.id}")
        return schemas.MasterSettingsResponse(
            id=updated_setting.id,
            user_id=updated_setting.user_id,
            name=updated_setting.name,
            value=updated_setting.value,
            is_active=updated_setting.is_active,
            created_at=updated_setting.created_at,
            updated_at=updated_setting.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )


@router.delete("/master-settings/{setting_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setting(
    setting_name: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete (soft delete) a setting by name for the current user
    Sets is_active=False instead of hard deleting
    """
    try:
        # Check if setting exists
        existing = db.query(models.MasterSettings).filter(
            models.MasterSettings.user_id == current_user.id,
            models.MasterSettings.name == setting_name
        ).first()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_name}' not found for this user"
            )
        
        # Soft delete the setting
        deleted = SettingsService.delete_user_setting(current_user.id, setting_name, db)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete setting"
            )
        
        logger.info(f"Deleted setting '{setting_name}' for user {current_user.id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete setting: {str(e)}"
        )


@router.post("/master-settings/{setting_name}/activate", response_model=schemas.MasterSettingsResponse)
def activate_setting(
    setting_name: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activate a setting (set is_active=True)
    """
    try:
        updated_setting = SettingsService.update_user_setting(
            user_id=current_user.id,
            name=setting_name,
            is_active=True,
            db=db
        )
        
        if not updated_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_name}' not found for this user"
            )
        
        logger.info(f"Activated setting '{setting_name}' for user {current_user.id}")
        return schemas.MasterSettingsResponse(
            id=updated_setting.id,
            user_id=updated_setting.user_id,
            name=updated_setting.name,
            value=updated_setting.value,
            is_active=updated_setting.is_active,
            created_at=updated_setting.created_at,
            updated_at=updated_setting.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating setting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate setting: {str(e)}"
        )

