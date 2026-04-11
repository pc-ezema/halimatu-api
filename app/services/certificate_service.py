from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.certificate import Certificate, CertificateStatus
import uuid
import random

class CertificateService:
    
    @staticmethod
    def generate_certificate_number() -> str:
        """Generate unique certificate number"""
        year = datetime.now().year
        random_num = random.randint(10000, 99999)
        unique_id = str(uuid.uuid4()).split('-')[0].upper()
        return f"CERT-{year}-{random_num}-{unique_id}"
    
    @staticmethod
    def generate_certificate_id() -> str:
        """Generate unique certificate ID"""
        return str(uuid.uuid4()).upper()
    
    @staticmethod
    def refresh_or_create_certificate(db: Session, enrollment_id: int) -> Certificate:
        """
        Refresh certificate based on current enrollment progress.
        - Creates new certificate if none exists
        - Updates existing certificate if progress changed
        """
        # Get enrollment
        enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        # Check if certificate already exists
        existing_certificate = db.query(Certificate).filter(
            Certificate.user_id == enrollment.user_id,
            Certificate.course_id == enrollment.course_id
        ).first()
        
        # Determine grade based on progress
        if enrollment.progress >= 100:
            grade = "Distinction"
        elif enrollment.progress >= 85:
            grade = "Merit"
        elif enrollment.progress >= 70:
            grade = "Pass"
        else:
            grade = "In Progress"
        
        duration = f"{enrollment.course.duration_months} months" if enrollment.course.duration_months else None
        
        if existing_certificate:
            # Update existing certificate
            existing_certificate.grade = grade
            existing_certificate.duration = duration
            existing_certificate.full_name = enrollment.user.get_full_name()
            
            # If progress is 100% and certificate is pending, keep it pending
            # If progress is not 100%, ensure status is not issued
            if enrollment.progress < 100 and existing_certificate.status == CertificateStatus.ISSUED:
                existing_certificate.status = CertificateStatus.PENDING
                existing_certificate.issue_date = None
            
            db.commit()
            db.refresh(existing_certificate)
            return existing_certificate
        else:
            # Create new certificate
            certificate = Certificate(
                certificate_id=CertificateService.generate_certificate_id(),
                certificate_number=CertificateService.generate_certificate_number(),
                user_id=enrollment.user_id,
                course_id=enrollment.course_id,
                enrollment_id=enrollment_id,
                full_name=enrollment.user.get_full_name(),
                grade=grade,
                duration=duration,
                status=CertificateStatus.PENDING
            )
            
            db.add(certificate)
            db.commit()
            db.refresh(certificate)
            return certificate
    
    @staticmethod
    def refresh_all_certificates(db: Session) -> Dict:
        """Refresh all certificates based on current enrollments"""
        enrollments = db.query(Enrollment).all()
        updated = []
        created = []
        failed = []
        
        for enrollment in enrollments:
            try:
                certificate = CertificateService.refresh_or_create_certificate(db, enrollment.id)
                
                if certificate.created_at == certificate.updated_at:
                    created.append({
                        "enrollment_id": enrollment.id,
                        "certificate_id": certificate.id,
                        "user_name": enrollment.user.get_full_name(),
                        "course_title": enrollment.course.title,
                        "progress": enrollment.progress,
                        "grade": certificate.grade
                    })
                else:
                    updated.append({
                        "enrollment_id": enrollment.id,
                        "certificate_id": certificate.id,
                        "user_name": enrollment.user.get_full_name(),
                        "course_title": enrollment.course.title,
                        "progress": enrollment.progress,
                        "grade": certificate.grade
                    })
            except Exception as e:
                failed.append({
                    "enrollment_id": enrollment.id,
                    "error": str(e)
                })
        
        return {
            "total_enrollments": len(enrollments),
            "created": len(created),
            "updated": len(updated),
            "failed": len(failed),
            "created_list": created,
            "updated_list": updated,
            "failed_list": failed
        }
    
    @staticmethod
    def auto_generate_certificate(db: Session, enrollment_id: int) -> Optional[Certificate]:
        """Auto-generate or update certificate when progress is updated"""
        enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        # Only create/update if progress is 100%
        if enrollment.progress >= 100:
            return CertificateService.refresh_or_create_certificate(db, enrollment_id)
        
        # For progress < 100, just update existing certificate if it exists
        existing = db.query(Certificate).filter(
            Certificate.user_id == enrollment.user_id,
            Certificate.course_id == enrollment.course_id
        ).first()
        
        if existing:
            # Update grade based on progress
            if enrollment.progress >= 85:
                grade = "Merit"
            elif enrollment.progress >= 70:
                grade = "Pass"
            else:
                grade = "In Progress"
            
            existing.grade = grade
            existing.duration = f"{enrollment.course.duration_months} months" if enrollment.course.duration_months else None
            
            # If progress is not 100% and certificate was issued, revert to pending
            if existing.status == CertificateStatus.ISSUED:
                existing.status = CertificateStatus.PENDING
                existing.issue_date = None
            
            db.commit()
            db.refresh(existing)
            return existing
        
        return None
    
    @staticmethod
    def issue_certificate(db: Session, certificate_id: int) -> Certificate:
        """Issue a pending certificate (Admin action)"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise ValueError("Certificate not found")
        
        if certificate.status != CertificateStatus.PENDING:
            raise ValueError("Only pending certificates can be issued")
        
        # Check if progress is 100%
        enrollment = db.query(Enrollment).filter(Enrollment.id == certificate.enrollment_id).first()
        if enrollment and enrollment.progress < 100:
            raise ValueError("Cannot issue certificate. Course progress is not 100%")
        
        certificate.status = CertificateStatus.ISSUED
        certificate.issue_date = datetime.utcnow()
        
        db.commit()
        db.refresh(certificate)
        
        return certificate
    
    @staticmethod
    def revoke_certificate(db: Session, certificate_id: int) -> Certificate:
        """Revoke an issued certificate (Admin action)"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise ValueError("Certificate not found")
        
        if certificate.status != CertificateStatus.ISSUED:
            raise ValueError("Only issued certificates can be revoked")
        
        certificate.status = CertificateStatus.REVOKED
        
        db.commit()
        db.refresh(certificate)
        
        return certificate
    
    @staticmethod
    def get_all_certificates(db: Session, skip: int = 0, limit: int = 50, 
                             status: str = None, search: str = None,
                             course_id: int = None, user_id: int = None) -> Dict:
        """Get all certificates with filters"""
        query = db.query(Certificate).join(User).join(Course)
        
        if status:
            query = query.filter(Certificate.status == status)
        
        if course_id:
            query = query.filter(Certificate.course_id == course_id)
        
        if user_id:
            query = query.filter(Certificate.user_id == user_id)
        
        if search:
            query = query.filter(
                or_(
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.student_id.ilike(f"%{search}%"),
                    Course.title.ilike(f"%{search}%"),
                    Certificate.certificate_number.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        certificates = query.order_by(Certificate.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        for cert in certificates:
            # Get enrollment progress
            progress = 0
            if cert.enrollment:
                progress = cert.enrollment.progress
            
            result.append({
                "id": cert.id,
                "certificate_id": cert.certificate_id,
                "certificate_number": cert.certificate_number,
                "user_id": cert.user_id,
                "user_name": cert.user.get_full_name(),
                "user_email": cert.user.email,
                "user_student_id": cert.user.student_id,
                "course_id": cert.course_id,
                "course_title": cert.course.title,
                "course_image": cert.course.image,
                "full_name": cert.full_name,
                "grade": cert.grade,
                "duration": cert.duration,
                "progress": progress,
                "status": cert.status,
                "issue_date": cert.issue_date,
                "created_at": cert.created_at,
                "updated_at": cert.updated_at
            })
        
        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "certificates": result
        }
    
    @staticmethod
    def get_user_certificates(db: Session, user_id: int, status: str = None) -> List[Certificate]:
        """Get certificates for a specific user"""
        query = db.query(Certificate).filter(Certificate.user_id == user_id)
        if status:
            query = query.filter(Certificate.status == status)
        return query.order_by(Certificate.issue_date.desc()).all()
    
    @staticmethod
    def get_certificate_stats(db: Session) -> Dict:
        """Get certificate statistics"""
        total_issued = db.query(Certificate).filter(Certificate.status == CertificateStatus.ISSUED).count()
        total_pending = db.query(Certificate).filter(Certificate.status == CertificateStatus.PENDING).count()
        total_revoked = db.query(Certificate).filter(Certificate.status == CertificateStatus.REVOKED).count()
        total_certificates = db.query(Certificate).count()
        
        # Get recent pending certificates
        recent_pending = db.query(Certificate).filter(
            Certificate.status == CertificateStatus.PENDING
        ).order_by(Certificate.created_at.desc()).limit(5).all()
        
        recent_certificates_list = []  # Changed variable name
        for cert in recent_pending:
            recent_certificates_list.append({
                "id": cert.id,
                "certificate_number": cert.certificate_number,
                "user_name": cert.user.get_full_name(),
                "course_title": cert.course.title,
                "progress": cert.enrollment.progress if cert.enrollment else 0,
                "created_at": cert.created_at
            })
        
        return {
            "total_issued": total_issued,
            "total_pending": total_pending,
            "total_revoked": total_revoked,
            "total_certificates": total_certificates,
            "pending_approval": total_pending,
            "recent_certificates": recent_certificates_list  # Changed key name
        }

    @staticmethod
    def get_certificate_by_id(db: Session, certificate_id: int) -> Certificate:
        """Get certificate by ID"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise ValueError("Certificate not found")
        return certificate
    
    @staticmethod
    def delete_certificate(db: Session, certificate_id: int) -> None:
        """Permanently delete a certificate"""
        certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
        if not certificate:
            raise ValueError("Certificate not found")
        
        db.delete(certificate)
        db.commit()