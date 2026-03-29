from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.database import get_db
from app.schemas.auth import *
from app.services.auth_service import *
from app.services.otp_service import generate_otp, verify_otp
from app.services.email_service import send_otp_email, send_password_reset_email
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.config.limiter import limiter
from app.config.settings import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()

@router.post("/register", response_model=MessageResponse)
@limiter.limit("5/minute")
def register(
    request: Request,
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        # Register user
        user_data = data.model_dump()
        user = register_user(db, user_data)
        
        # Generate OTP
        otp_code = generate_otp(db, user.id, "email_verification")
        
        # Send OTP via email
        background_tasks.add_task(send_otp_email, user.email, otp_code)
        
        return {"message": "Registration successful. OTP sent to email."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp", response_model=MessageResponse)
@limiter.limit("5/minute")
def verify_otp_endpoint(
    request: Request,
    data: OTPVerifyRequest,
    db: Session = Depends(get_db),
):
    try:
        # Get user
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify OTP
        is_valid = verify_otp(db, user.id, data.code, "email_verification")
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        # Activate user
        user.is_active = True
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        user.status = "active"
        db.commit()
        
        return {"message": "Account verified successfully. You can now login."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        client_ip = request.client.host if request.client else None
        result = login_user(db, data.email, data.password, client_ip)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/resend-otp", response_model=MessageResponse)
@limiter.limit("2/minute")
def resend_otp(
    request: Request,
    data: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        # Get user
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user:
            # Return success for security
            return {"message": "If email exists, OTP will be sent"}
        
        # Check if already verified
        if data.purpose == "email_verification" and user.email_verified_at:
            raise HTTPException(status_code=400, detail="Email already verified")
        
        # Generate new OTP
        otp_code = generate_otp(db, user.id, data.purpose)
        
        # Send OTP
        if data.purpose == "email_verification":
            background_tasks.add_task(send_otp_email, user.email, otp_code)
        elif data.purpose == "password_reset":
            background_tasks.add_task(send_password_reset_email, user.email, otp_code)
        
        return {"message": "OTP sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user:
            return {"message": "If email exists, OTP will be sent"}
        
        # Check if email is verified
        if not user.email_verified_at:
            raise HTTPException(status_code=403, detail="Email not verified")
        
        # Generate OTP
        otp_code = generate_otp(db, user.id, "password_reset")
        
        # Send OTP
        background_tasks.add_task(send_password_reset_email, user.email, otp_code)
        
        return {"message": "If email exists, OTP will be sent"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("3/minute")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    try:
        # Get user
        user = db.query(User).filter(User.email == data.email).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify OTP
        is_valid = verify_otp(db, user.id, data.otp_code, "password_reset")
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        # Update password
        user.hashed_password = hash_password(data.new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        for token in user.refresh_tokens:
            token.is_revoked = True
        
        db.commit()
        
        return {"message": "Password reset successful. Please login with your new password."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/refresh", response_model=dict)
def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        result = refresh_access_token(db, data.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
