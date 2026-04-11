from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class CertificateStatus(str, Enum):
    PENDING = "pending"
    ISSUED = "issued"
    REVOKED = "revoked"

class GenerateCertificateRequest(BaseModel):
    enrollment_id: int

class UpdateCertificateRequest(BaseModel):
    status: Optional[CertificateStatus] = None
    grade: Optional[str] = None

class CertificateResponse(BaseModel):
    id: int
    certificate_id: str
    certificate_number: str
    user_id: int
    user_name: str
    user_email: str
    user_student_id: Optional[str]
    course_id: int
    course_title: str
    course_image: Optional[str]
    full_name: str
    grade: Optional[str]
    duration: Optional[str]
    progress: Optional[float] = 0
    status: CertificateStatus
    issue_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RecentPendingCertificate(BaseModel):
    id: int
    certificate_number: str
    user_name: str
    course_title: str
    progress: float
    created_at: datetime

class CertificateStatsResponse(BaseModel):
    total_issued: int
    total_pending: int
    total_revoked: int
    total_certificates: int
    pending_approval: int
    recent_certificates: List[RecentPendingCertificate]  # Changed from recent_pending to recent_certificates

class MessageResponse(BaseModel):
    message: str