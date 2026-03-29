from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.database import get_db
from app.schemas.user import *
from app.services.user_service import UserService
from app.services.auth_service import get_current_user
from app.models.user import User
from app.config.limiter import limiter
from app.config.settings import settings

router = APIRouter(prefix="/api/user", tags=["User"])
security = HTTPBearer()

@router.get("/profile", response_model=UserProfileResponse)
@limiter.limit("30/minute")
def get_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user profile"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        user = UserService.get_profile(db, current_user.id)
        
        return UserProfileResponse(
            id=user.id,
            student_id=user.student_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            country=user.country,
            profile_picture=user.profile_picture,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.put("/profile", response_model=UserProfileResponse)
@limiter.limit("20/minute")
def update_profile(
    request: Request,
    data: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update user profile (email cannot be updated)"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        # Convert to dict, excluding None values
        profile_data = {k: v for k, v in data.model_dump().items() if v is not None}
        
        user = UserService.update_profile(db, current_user.id, profile_data)
        
        return UserProfileResponse(
            id=user.id,
            student_id=user.student_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            country=user.country,
            profile_picture=user.profile_picture,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Change user password"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.update_password(
            db, 
            current_user.id, 
            data.current_password, 
            data.new_password,
            data.confirm_password
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/upload-profile-picture", response_model=MessageResponse)
@limiter.limit("10/minute")
def upload_profile_picture(
    request: Request,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Upload profile picture"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.upload_profile_picture(db, current_user.id, file)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )

@router.delete("/profile-picture", response_model=MessageResponse)
@limiter.limit("10/minute")
def remove_profile_picture(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Remove profile picture"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.remove_profile_picture(db, current_user.id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove profile picture"
        )

@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout current session"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.logout(db, current_user.id, token)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/logout-all", response_model=MessageResponse)
def logout_all_devices(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout from all devices"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.logout_all_devices(db, current_user.id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all devices failed"
        )