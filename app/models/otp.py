from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from datetime import datetime

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), nullable=False)
    purpose = Column(String(50), nullable=False)  # email_verification, password_reset
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="otps")
    
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def is_expired(self):
        """Check if OTP has expired"""
        return datetime.utcnow() > self.expires_at