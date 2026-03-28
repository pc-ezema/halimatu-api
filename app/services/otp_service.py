from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.otp import OTP

def generate_otp(db: Session, user_id: int, purpose: str, expiry_minutes: int = 10) -> str:
    """
    Generate OTP - Deletes all existing OTPs for this user and purpose first
    """
    # Delete all existing OTPs for this user and purpose
    db.query(OTP).filter(
        and_(
            OTP.user_id == user_id,
            OTP.purpose == purpose
        )
    ).delete()
    
    # Generate new 6-digit OTP
    code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    # Create new OTP
    otp = OTP(
        code=code,
        purpose=purpose,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(minutes=expiry_minutes)
    )
    
    db.add(otp)
    db.commit()
    
    return code

def verify_otp(db: Session, user_id: int, code: str, purpose: str) -> bool:
    """
    Verify OTP
    """
    # Find valid OTP
    otp = db.query(OTP).filter(
        and_(
            OTP.user_id == user_id,
            OTP.purpose == purpose,
            OTP.code == code,
            OTP.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not otp:
        return False
    
    # Delete the OTP after successful verification
    db.delete(otp)
    db.commit()
    
    return True

def get_valid_otp(db: Session, user_id: int, purpose: str):
    """Check if user has a valid OTP"""
    return db.query(OTP).filter(
        and_(
            OTP.user_id == user_id,
            OTP.purpose == purpose,
            OTP.expires_at > datetime.utcnow()
        )
    ).first()