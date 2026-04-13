from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

class RequestStatus(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"


class ContactStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    REPLIED = "replied"

class TutorRequestCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    subject: str = Field(..., min_length=3, max_length=200)
    message: Optional[str] = None
    student_level: Optional[str] = Field(None, max_length=100)
    preferred_schedule: Optional[str] = Field(None, max_length=200)

class TutorRequestResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    subject: str
    message: Optional[str]
    student_level: Optional[str]
    preferred_schedule: Optional[str]
    status: RequestStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class UpdateRequestStatus(BaseModel):
    status: RequestStatus

class MessageResponse(BaseModel):
    message: str

class RequestStatsResponse(BaseModel):
    """Statistics for tutor requests"""
    total: int
    pending: int
    contacted: int
    completed: int


class ContactCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10)

class ContactResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    subject: str
    message: str
    status: ContactStatus
    created_at: datetime
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UpdateContactStatus(BaseModel):
    status: ContactStatus

class ContactStatsResponse(BaseModel):
    total: int
    unread: int
    read: int
    replied: int