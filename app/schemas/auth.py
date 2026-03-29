from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, date
from typing import Optional
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

# Request Schemas
class RegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (8-128 characters)")
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$', description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[GenderEnum] = Field(None, description="Gender")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    city: Optional[str] = Field(None, max_length=100, description="City")
    consent_agreement: bool = Field(..., description="Terms agreement")
    
    @field_validator('password')
    def validate_password(cls, v):
        errors = []
        
        # Length checks
        if len(v) < 8:
            errors.append("at least 8 characters")
        if len(v) > 128:
            errors.append("no more than 128 characters")
        
        # Complexity checks
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one number")
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append("at least one special character")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        # Check for common weak passwords
        common_passwords = ['password123', 'admin123', '12345678', 'qwerty123', 'welcome1', 'letmein1']
        if v.lower() in common_passwords:
            raise ValueError("Password is too common. Please choose a stronger password.")
        
        return v
    
    @field_validator('consent_agreement')
    def validate_consent(cls, v):
        if not v:
            raise ValueError("You must agree to the terms and conditions")
        return v
    
class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResendOTPRequest(BaseModel):
    email: EmailStr
    purpose: str  # email_verification or password_reset

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (8-128 characters)")
    
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
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            errors.append("at least one special character")
        
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        
        return v
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    middle_name: Optional[str]
    last_name: str
    email: EmailStr
    phone_number: Optional[str]
    email_verified_at: Optional[datetime]
    profile_picture: Optional[str]
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    country: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Response Schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class MessageResponse(BaseModel):
    message: str