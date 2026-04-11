from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User, UserStatusEnum
from app.models.refresh_token import RefreshToken
from app.config.settings import settings
from app.services.otp_service import generate_otp  # Changed import
from app.utils.student_id_generator import StudentIDGenerator

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure Argon2 - Most secure password hashing
pwd_context = CryptContext(
    schemes=["argon2"],  # Use Argon2 as the primary scheme
    deprecated="auto",
    # Argon2 configuration for optimal security vs performance
    argon2__rounds=2,           # Number of iterations (adjust based on your server)
    argon2__memory_cost=1024,   # Memory cost in KB (1024 = 1GB)
    argon2__parallelism=2,      # Number of parallel threads
    argon2__hash_len=32,        # Length of the hash in bytes
    argon2__salt_len=16         # Length of the salt in bytes
)

def hash_password(password: str) -> str:
    """Hash a password using Argon2 - No length limitations!"""
    try:
        # Argon2 has no practical length limit
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Error hashing password: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using Argon2"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        return False

def create_access_token(user_id: int) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(db: Session, user_id: int) -> str:
    """Create and store refresh token"""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.secret_key,  # You might want a separate refresh key
        algorithm=settings.algorithm
    )
    
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expire,
        is_revoked=False
    )
    db.add(refresh_token)
    db.commit()
    return token

def register_user(db: Session, user_data: dict) -> User:
    """Register a new user"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data['email']).first()
    if existing_user:
        raise ValueError("Email already registered")
    
    # Check if phone number already exists
    if user_data.get('phone_number'):
        existing_phone = db.query(User).filter(User.phone_number == user_data['phone_number']).first()
        if existing_phone:
            raise ValueError("Phone number already registered")
        
    # Generate unique student ID
    try:
        student_id = StudentIDGenerator.generate_unique_student_id(db)
    except Exception as e:
        raise ValueError(f"Failed to generate student ID: {str(e)}")
    
    # Create new user - No password length limitations with Argon2!
    hashed_pwd = hash_password(user_data['password'])
    
    user = User(
        student_id=student_id,  # Auto-generated unique ID
        first_name=user_data['first_name'],
        middle_name=user_data.get('middle_name'),
        last_name=user_data['last_name'],
        email=user_data['email'],
        phone_number=user_data.get('phone_number'),
        date_of_birth=user_data.get('date_of_birth'),
        gender=user_data.get('gender'),
        country=user_data.get('country'),
        hashed_password=hashed_pwd,
        consent_agreement=user_data['consent_agreement'],
        status=UserStatusEnum.PENDING_VERIFICATION,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.services.notification_service import NotificationService
    NotificationService.notify_welcome(db, user.id, user.get_full_name())
    
    return user

def login_user(db: Session, email: str, password: str, ip_address: str = None, background_tasks=None) -> Dict:
    """Login user and return tokens - Auto-resend OTP if email not verified"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise ValueError("Invalid credentials")
    
    # Check if account is locked
    if user.is_account_locked():
        raise ValueError("Account is locked. Please try again later or reset your password")
    
    # Check if email is verified - If not, resend OTP automatically
    if not user.email_verified_at:
        # Generate new OTP
        otp_code = generate_otp(db, user.id, "email_verification")
        
        # Send OTP via email if background_tasks is provided
        if background_tasks:
            from app.services.email_service import send_otp_email
            background_tasks.add_task(send_otp_email, user.email, otp_code)
        
        raise ValueError("Email not verified. A new verification code has been sent to your email.")
    
    # Check if account is active
    if user.status != UserStatusEnum.ACTIVE:
        raise ValueError("Account is inactive. Please contact support")
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_login_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
        db.commit()
        raise ValueError("Invalid credentials")
    
    # Reset failed login attempts on success
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    user.last_ip = ip_address
    
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(db, user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user
    }

def refresh_access_token(db: Session, refresh_token: str) -> Dict:
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        
        user_id = int(payload.get("sub"))
        
        # Check if user exists
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Check if refresh token exists and is not revoked
        token_record = db.query(RefreshToken).filter(
            and_(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not token_record:
            raise ValueError("Invalid or expired refresh token")
        
        # Create new access token
        new_access_token = create_access_token(user_id)
        
        # Return serializable user data (not the SQLAlchemy object)
        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "student_id": user.student_id,
                "first_name": user.first_name,
                "middle_name": user.middle_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "email_verified_at": user.email_verified_at,
                "profile_picture": user.profile_picture,
                "date_of_birth": user.date_of_birth,
                "gender": user.gender,
                "country": user.country,
                "status": user.status,
                "created_at": user.created_at
            }
        }
        
    except JWTError as e:
        raise ValueError("Invalid refresh token")
    except ExpiredSignatureError as e:
        raise ValueError("Refresh token has expired")
    except Exception as e:
        raise ValueError(f"Invalid refresh token: {str(e)}")
    
def get_current_user(db: Session, token: str) -> User:
    """Get current user from access token"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Check if email is verified
        if not user.email_verified_at:
            raise ValueError("Email not verified")
        
        return user
        
    except jwt.JWTError:
        raise ValueError("Invalid access token")

def revoke_all_user_tokens(db: Session, user_id: int):
    """Revoke all refresh tokens for a user"""
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({"is_revoked": True})
    db.commit()