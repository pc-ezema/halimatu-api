from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import UploadFile
from app.models.course import Course, CourseStatus
from app.models.topic import Topic
from app.models.class_model import Class, ClassStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User
from app.utils.image_upload import ImageUpload

class CourseService:
    
    # ==================== COURSE CRUD ====================

    @staticmethod
    def create_course(db: Session, course_data: dict, image_file: UploadFile = None) -> Course:
        """Create a new course with optional image"""
        # Create course
        course = Course(**course_data)
        db.add(course)
        db.commit()
        db.refresh(course)
        
        # Save image if provided
        if image_file:
            image_url = ImageUpload.save_course_image(image_file, course.id)
            course.image = image_url
            db.commit()
            db.refresh(course)
        
        return course
    
    @staticmethod
    def get_courses(db: Session, skip: int = 0, limit: int = 100, status: str = None) -> List[Course]:
        """Get all courses"""
        query = db.query(Course)
        if status:
            query = query.filter(Course.status == status)
        return query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_course(db: Session, course_id: int) -> Course:
        """Get course by ID"""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")
        return course
    
    @staticmethod
    def update_course(db: Session, course_id: int, course_data: dict, image_file: UploadFile = None) -> Course:
        """Update a course with optional image"""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")
        
        # Update text fields
        for key, value in course_data.items():
            if value is not None:
                setattr(course, key, value)
        
        # Handle image update
        if image_file:
            # Delete old image if exists
            if course.image:
                ImageUpload.delete_course_image(course.image)
            
            # Save new image
            image_url = ImageUpload.save_course_image(image_file, course.id)
            course.image = image_url
        
        db.commit()
        db.refresh(course)
        return course
    
    @staticmethod
    def delete_course(db: Session, course_id: int) -> Dict:
        """Delete a course"""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")
        
        db.delete(course)
        db.commit()
        return {"message": "Course deleted successfully"}
    
    # ==================== TOPIC CRUD ====================
    
    @staticmethod
    def create_topic(db: Session, course_id: int, title: str) -> Topic:
        """Create a new topic for a course"""
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Course not found")
        
        # Get order count
        order_count = db.query(Topic).filter(Topic.course_id == course_id).count()
        
        topic = Topic(
            title=title,
            course_id=course_id,
            order=order_count + 1
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic
    
    @staticmethod
    def get_topics(db: Session, course_id: int) -> List[Topic]:
        """Get all topics for a course"""
        return db.query(Topic).filter(Topic.course_id == course_id).order_by(Topic.order).all()
    
    @staticmethod
    def get_topic(db: Session, topic_id: int) -> Topic:
        """Get topic by ID"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        return topic
    
    @staticmethod
    def update_topic(db: Session, topic_id: int, title: str = None, order: int = None) -> Topic:
        """Update a topic"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        
        if title is not None:
            topic.title = title
        if order is not None:
            topic.order = order
        
        db.commit()
        db.refresh(topic)
        return topic
    
    @staticmethod
    def delete_topic(db: Session, topic_id: int) -> Dict:
        """Delete a topic"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        
        db.delete(topic)
        db.commit()
        return {"message": "Topic deleted successfully"}
    
    # ==================== CLASS CRUD ====================
    
    @staticmethod
    def create_class(db: Session, topic_id: int, class_data: dict) -> Class:
        """Create a new class for a topic"""
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            raise ValueError("Topic not found")
        
        new_class = Class(topic_id=topic_id, **class_data)
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        return new_class
    
    @staticmethod
    def get_classes(db: Session, topic_id: int = None) -> List[Class]:
        """Get classes, optionally filtered by topic"""
        query = db.query(Class)
        if topic_id:
            query = query.filter(Class.topic_id == topic_id)
        return query.order_by(Class.start_date).all()
    
    @staticmethod
    def get_class(db: Session, class_id: int) -> Class:
        """Get class by ID"""
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise ValueError("Class not found")
        return class_obj
    
    @staticmethod
    def update_class(db: Session, class_id: int, class_data: dict) -> Class:
        """Update a class"""
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise ValueError("Class not found")
        
        for key, value in class_data.items():
            if value is not None:
                setattr(class_obj, key, value)
        
        db.commit()
        db.refresh(class_obj)
        return class_obj
    
    @staticmethod
    def delete_class(db: Session, class_id: int) -> Dict:
        """Delete a class"""
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise ValueError("Class not found")
        
        db.delete(class_obj)
        db.commit()
        return {"message": "Class deleted successfully"}
    
    # ==================== ENROLLMENT ====================
    
    @staticmethod
    def enroll_user(db: Session, user_id: int, course_id: int) -> Enrollment:
        """Enroll a user in a course"""
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id, Course.status == CourseStatus.PUBLISHED).first()
        if not course:
            raise ValueError("Course not available")
        
        # Check if already enrolled
        existing = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        
        if existing:
            raise ValueError("Already enrolled in this course")
        
        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment
    
    @staticmethod
    def get_user_enrollments(db: Session, user_id: int) -> List[Dict]:
        """Get user's enrolled courses"""
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).all()
        
        result = []
        for e in enrollments:
            result.append({
                "id": e.id,
                "course_id": e.course_id,
                "course_title": e.course.title,
                "status": e.status,
                "progress": e.progress,
                "enrolled_at": e.enrolled_at,
                "completed_at": e.completed_at
            })
        return result
    
    @staticmethod
    def update_progress(db: Session, user_id: int, course_id: int, progress: float) -> Enrollment:
        """Update user's progress in a course"""
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        enrollment.progress = progress
        enrollment.updated_at = datetime.utcnow()
        
        if progress >= 100 and enrollment.status != EnrollmentStatus.COMPLETED:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(enrollment)
        return enrollment
    
    @staticmethod
    def get_course_stats(db: Session, course_id: int) -> Dict:
        """Get course statistics"""
        total_enrolled = db.query(Enrollment).filter(Enrollment.course_id == course_id).count()
        active_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        ).count()
        completed_enrolled = db.query(Enrollment).filter(
            Enrollment.course_id == course_id,
            Enrollment.status == EnrollmentStatus.COMPLETED
        ).count()
        
        return {
            "total_enrolled": total_enrolled,
            "active_enrolled": active_enrolled,
            "completed_enrolled": completed_enrolled,
            "completion_rate": round((completed_enrolled / total_enrolled * 100) if total_enrolled > 0 else 0, 2)
        }