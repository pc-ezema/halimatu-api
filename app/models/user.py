from datetime import date, datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Enum, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base

import enum

class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class UserStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class User(Base):
    __tablename__ = "users"

    # ID first (primary key)
    id = Column(Integer, primary_key=True, index=True)

    # Student ID - Auto-generated unique identifier
    student_id = Column(String(20), unique=True, index=True, nullable=False)

    # Personal Information
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)  # Nullable as requested
    last_name = Column(String(100), nullable=False)
    
    # Contact Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    
    # Demographic Information
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    country = Column(String(100), nullable=True)

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    
    # Account Status
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.PENDING_VERIFICATION)
    
    # Consent & Legal
    consent_agreement = Column(Boolean, default=False, nullable=False)

    # Profile
    profile_picture = Column(String(500), nullable=True)
    
    # Verification fields
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_ip = Column(String(45), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    otps = relationship("OTP", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")

    def get_full_name(self):
        """Return the user's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calculate user's age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    # Add these methods to User class
    def has_active_subscription(self) -> bool:
        """Check if user has an active subscription"""
        from datetime import datetime
        from app.models.subscription import SubscriptionStatus
        
        for sub in self.subscriptions:
            if sub.status == SubscriptionStatus.ACTIVE and sub.end_date > datetime.utcnow():
                return True
        return False

    def get_active_subscription(self):
        """Get user's active subscription"""
        from datetime import datetime
        from app.models.subscription import SubscriptionStatus
        
        for sub in self.subscriptions:
            if sub.status == SubscriptionStatus.ACTIVE and sub.end_date > datetime.utcnow():
                return sub
        return None

    def get_total_spent(self) -> float:
        """Get total amount user has spent"""
        return sum(payment.amount for payment in self.payments if payment.status == "completed")