from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CourseStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ClassStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# ==================== TOPIC SCHEMAS ====================
class TopicCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)

class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    order: Optional[int] = None

class TopicResponse(BaseModel):
    id: int
    title: str
    order: int
    course_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== CLASS SCHEMAS ====================
class ClassCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    meeting_link: str = Field(..., min_length=5)
    meeting_password: Optional[str] = None
    start_date: datetime
    end_date: datetime

class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    meeting_link: Optional[str] = None
    meeting_password: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[ClassStatus] = None

class ClassResponse(BaseModel):
    id: int
    name: str
    meeting_link: str
    meeting_password: Optional[str]
    start_date: datetime
    end_date: datetime
    status: ClassStatus
    topic_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== COURSE SCHEMAS ====================
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    price: int = Field(0, ge=0)
    image: Optional[str] = None
    duration_months: Optional[int] = None
    instructor: Optional[str] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    price: Optional[int] = Field(None, ge=0)
    status: Optional[CourseStatus] = None
    image: Optional[str] = None
    duration_months: Optional[int] = None
    instructor: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    price: int
    status: CourseStatus
    image: Optional[str]
    duration_months: Optional[int]
    instructor: Optional[str]
    total_topics: int = 0
    total_enrolled: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    topics: List[TopicResponse] = []
    
    class Config:
        from_attributes = True

# ==================== ENROLLMENT SCHEMAS ====================
class EnrollmentResponse(BaseModel):
    id: int
    course_id: int
    course_title: str
    status: str
    progress: float
    enrolled_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UpdateProgressRequest(BaseModel):
    progress: float = Field(..., ge=0, le=100)

# ==================== MESSAGE RESPONSE ====================
class MessageResponse(BaseModel):
    message: str