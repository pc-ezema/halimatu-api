from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database.database import Base
import enum

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"

class PrivateTutorRequest(Base):
    __tablename__ = "private_tutor_requests"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contact Information
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Request Details
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    # Student Info
    student_level = Column(String(100), nullable=True)  # e.g., "Primary", "Secondary", "University", "Adult"
    preferred_schedule = Column(String(200), nullable=True)  # e.g., "Weekdays evening", "Weekends", "Flexible"
    
    # Status
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<PrivateTutorRequest {self.full_name} - {self.subject}>"