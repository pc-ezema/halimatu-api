from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List

from sqlalchemy import String

# Add these to your existing admin schemas

class AdminProfileUpdate(BaseModel):
    """Update admin profile"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)

class AdminChangePassword(BaseModel):
    """Change admin password"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        errors = []
        
        if len(v) < 8:
            errors.append("at least 8 characters")
        if len(v) > 128:
            errors.append("no more than 128 characters")
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one number")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        return v
    
    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError("Passwords do not match")
        return v

class AdminProfileResponse(BaseModel):
    """Admin profile response"""
    id: int
    name: str
    email: str
    role: Optional[RoleResponse]
    status: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: str
    
# Role Schemas
class RoleCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)

class RoleResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Permission Schemas
class PermissionResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Admin Schemas
class AdminCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_id: Optional[int] = None

class AdminUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    status: Optional[str] = None

class AdminChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    role: Optional[RoleResponse]
    status: str
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse

# Assign Permission
class AssignPermissionRequest(BaseModel):
    permission_ids: List[int]

# Message Response
class MessageResponse(BaseModel):
    message: str

class UserBasicResponse(BaseModel):
    """Basic user info for admin listing"""
    id: int
    student_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    phone_number: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    country: Optional[str]
    status: str
    profile_picture: Optional[str]
    email_verified_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserDetailResponse(BaseModel):
    """Detailed user info for admin"""
    id: int
    student_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: str
    phone_number: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    country: Optional[str]
    status: str
    profile_picture: Optional[str]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login: Optional[datetime]
    last_ip: Optional[str]
    password_changed_at: Optional[datetime]
    email_verified_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ResendPasswordRequest(BaseModel):
    """Request to reset user password"""
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('new_password')
    def validate_password(cls, v):
        errors = []
        
        if len(v) < 8:
            errors.append("at least 8 characters")
        if len(v) > 128:
            errors.append("no more than 128 characters")
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one number")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        return v

class UserStatsResponse(BaseModel):
    """User statistics"""
    total: int
    active: int
    inactive: int
    verified: int

class AdminDashboardStatsResponse(BaseModel):
    """Complete admin dashboard statistics"""
    # User stats
    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    
    # Subscription stats
    total_subscriptions: int
    active_subscriptions: int
    expired_subscriptions: int
    cancelled_subscriptions: int
    
    # Revenue stats
    total_revenue: float
    monthly_recurring_revenue: float
    
    # Plans breakdown
    plans_breakdown: List[dict]
    
    class Config:
        from_attributes = True