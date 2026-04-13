from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.database.database import Base
import enum

class ContactStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"

class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # Contact Information
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    status = Column(Enum(ContactStatus), default=ContactStatus.UNREAD)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<ContactMessage {self.full_name} - {self.subject}>"