import os
import shutil
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.models.user import User
from app.services.auth_service import verify_password, hash_password
from app.config.settings import settings
import uuid

class UserService:
    
    @staticmethod
    def update_profile(db: Session, user_id: int, profile_data: dict) -> User:
        """Update user profile - email cannot be updated"""
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Fields that can be updated (excluding email)
        allowed_fields = [
            'first_name', 'middle_name', 'last_name', 
            'date_of_birth', 'gender', 'country',
        ]
        
        # Update only allowed fields
        for field in allowed_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(user, field, profile_data[field])
        
        # Handle phone number separately with uniqueness check
        if 'phone_number' in profile_data and profile_data['phone_number'] is not None:
            phone = profile_data['phone_number'].strip()
            
            # Check if phone number already exists for another user
            existing_user = db.query(User).filter(
                User.phone_number == phone,
                User.id != user_id,
                User.deleted_at.is_(None)
            ).first()
            
            if existing_user:
                raise ValueError("Phone number already registered to another account")
            
            user.phone_number = phone
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def update_password(db: Session, user_id: int, current_password: str, new_password: str, confirm_password: str) -> Dict:
        """Update user password with confirmation"""
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Check if new password and confirmation match
        if new_password != confirm_password:
            raise ValueError("New password and confirmation do not match")
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Check if new password is same as old password
        if verify_password(new_password, user.hashed_password):
            raise ValueError("New password must be different from current password")
        
        # Update password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        from app.models.refresh_token import RefreshToken
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        
        db.commit()
        
        return {"message": "Password updated successfully"}
    
    @staticmethod
    def upload_profile_picture(db: Session, user_id: int, file: UploadFile) -> Dict:
        """Upload profile picture to storage folder"""
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Validate file type
        allowed_extensions = ['jpg', 'jpeg', 'png']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        
        # Validate file size (max 5MB)
        file_size = 0
        contents = file.file.read()
        file_size = len(contents)
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise ValueError("File size too large. Maximum 5MB allowed")
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(settings.storage_path, "profile_pictures")
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # Delete old profile picture if exists
        if user.profile_picture:
            old_file_path = os.path.join(upload_dir, user.profile_picture.split('/')[-1])
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Update user with new profile picture path
        relative_path = f"/uploads/profile_pictures/{unique_filename}"
        user.profile_picture = relative_path
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture": relative_path
        }
    
    @staticmethod
    def remove_profile_picture(db: Session, user_id: int) -> Dict:
        """Remove user's profile picture"""
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise ValueError("User not found")
        
        if user.profile_picture:
            upload_dir = os.path.join(settings.storage_path, "profile_pictures")
            file_path = os.path.join(upload_dir, user.profile_picture.split('/')[-1])
            if os.path.exists(file_path):
                os.remove(file_path)
            
            user.profile_picture = None
            user.updated_at = datetime.utcnow()
            db.commit()
            
            return {"message": "Profile picture removed successfully"}
        
        return {"message": "No profile picture to remove"}
    
    @staticmethod
    def logout(db: Session, user_id: int, refresh_token: str) -> Dict:
        """Logout user by revoking refresh token"""
        from app.models.refresh_token import RefreshToken
        
        # Revoke the specific refresh token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).first()
        
        if token_record:
            token_record.is_revoked = True
            db.commit()
            
            return {"message": "Logged out successfully"}
        
        return {"message": "Session already expired"}
    
    @staticmethod
    def logout_all_devices(db: Session, user_id: int) -> Dict:
        """Logout user from all devices by revoking all refresh tokens"""
        from app.models.refresh_token import RefreshToken
        
        # Revoke all refresh tokens for this user
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        
        db.commit()
        
        return {"message": "Logged out from all devices successfully"}
    
    @staticmethod
    def get_profile(db: Session, user_id: int) -> User:
        """Get user profile"""
        user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
        
        if not user:
            raise ValueError("User not found")
        
        return user