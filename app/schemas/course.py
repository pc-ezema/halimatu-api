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

class TopicWithProgressResponse(TopicResponse):
    is_completed: bool = False
    progress_percentage: float = 0
    classes: List['ClassWithProgressResponse'] = []
    
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

class ClassWithProgressResponse(ClassResponse):
    is_completed: bool = False
    
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
    total_classes: int = 0
    is_enrolled: bool = False
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    is_enrolled: bool = False
    enrollment_status: Optional[str] = None
    progress: float = 0
    topics: List[TopicWithProgressResponse] = []
    
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

class MarkTopicCompleteRequest(BaseModel):
    topic_id: int
    is_completed: bool = True

# ==================== MESSAGE RESPONSE ====================
class MessageResponse(BaseModel):
    message: str

class EnrollmentUserInfo(BaseModel):
    """User information for enrollment"""
    id: int
    student_id: str
    name: str
    email: str
    phone_number: Optional[str]
    status: str
    profile_picture: Optional[str]
    
    class Config:
        from_attributes = True

class EnrollmentCourseInfo(BaseModel):
    """Course information for enrollment"""
    id: int
    title: str
    description: Optional[str]
    price: int
    image: Optional[str]
    status: str
    duration_months: Optional[int]
    total_topics: int = 0
    
    class Config:
        from_attributes = True

class EnrollmentDetailResponse(BaseModel):
    """Detailed enrollment response with user and course info"""
    id: int
    enrollment_id: Optional[str] = None
    user: EnrollmentUserInfo
    course: EnrollmentCourseInfo
    status: str
    progress: float
    enrolled_at: datetime
    completed_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EnrollmentListResponse(BaseModel):
    """Paginated enrollment list response"""
    total: int
    page: int
    limit: int
    total_pages: int
    enrollments: List[EnrollmentDetailResponse]

class MarkClassCompleteRequest(BaseModel):
    """Request to mark a class as complete"""
    is_completed: bool = True

class MarkTopicCompleteRequest(BaseModel):
    """Request to mark a topic as complete"""
    is_completed: bool = True