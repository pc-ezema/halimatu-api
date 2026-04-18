from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class NotificationType(str, Enum):
    SYSTEM = "system"
    COURSE = "course"
    SUBSCRIPTION = "subscription"
    CERTIFICATE = "certificate"
    PAYMENT = "payment"
    REMINDER = "reminder"
    ACHIEVEMENT = "achievement"

class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"

# Notification Schemas
class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    type: NotificationType = NotificationType.SYSTEM
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class NotificationResponse(BaseModel):
    id: int
    notification_id: str
    title: str
    message: str
    type: NotificationType
    action_url: Optional[str]
    action_text: Optional[str]
    status: NotificationStatus
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SendNotificationRequest(BaseModel):
    """Request to send notification to users"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    type: NotificationType = NotificationType.SYSTEM
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    user_ids: Optional[List[int]] = None  # Specific users (if None, send to all)
    role: Optional[str] = None  # Send to users with specific role (student, instructor, etc.)

class BulkNotificationResponse(BaseModel):
    """Response for bulk notification sending"""
    total_sent: int
    total_failed: int
    failed_users: List[dict] = []
    message: str

class NotificationCountResponse(BaseModel):
    total: int
    unread: int

class MarkReadRequest(BaseModel):
    notification_ids: Optional[List[int]] = None  # None means mark all as read

class MessageResponse(BaseModel):
    message: str

class NotificationListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    notifications: List[NotificationResponse]

    class Config:
        from_attributes = True