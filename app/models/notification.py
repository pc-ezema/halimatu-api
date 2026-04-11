from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum

class NotificationType(str, enum.Enum):
    SYSTEM = "system"
    COURSE = "course"
    SUBSCRIPTION = "subscription"
    CERTIFICATE = "certificate"
    PAYMENT = "payment"
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"

class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # User who receives the notification
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="notifications")
    
    # Notification details
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.SYSTEM)
    
    # Action/Link (optional)
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    
    # Status
    status = Column(Enum(NotificationStatus), default=NotificationStatus.UNREAD)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Notification {self.title} - {self.status}>"