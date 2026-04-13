from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import case, func, or_
from fastapi import UploadFile
from app.models.course import Course, CourseStatus
from app.models.topic import Topic
from app.models.class_model import Class, ClassStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User
from app.utils.image_upload import ImageUpload
from app.models.topic_progress import TopicProgress
from app.models.class_progress import ClassProgress  # Keep for tracking individual class completion


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
    
    @staticmethod
    def get_all_enrollments_with_details(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: str = None,
        course_id: int = None,
        user_id: int = None,
        search: str = None
    ) -> Dict:
        """Get all enrollments with user and course details"""
        query = db.query(Enrollment).join(User).join(Course)
        
        # Apply filters
        if status:
            query = query.filter(Enrollment.status == status)
        
        if course_id:
            query = query.filter(Enrollment.course_id == course_id)
        
        if user_id:
            query = query.filter(Enrollment.user_id == user_id)
        
        if search:
            query = query.filter(
                or_(
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.student_id.ilike(f"%{search}%"),
                    Course.title.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        enrollments = query.order_by(Enrollment.enrolled_at.desc()).offset(skip).limit(limit).all()
        
        # Format results
        result = []
        for enrollment in enrollments:
            result.append({
                "id": enrollment.id,
                "enrollment_id": getattr(enrollment, 'enrollment_id', None),
                "user": {
                    "id": enrollment.user.id,
                    "student_id": enrollment.user.student_id,
                    "name": enrollment.user.get_full_name(),
                    "email": enrollment.user.email,
                    "phone_number": enrollment.user.phone_number,
                    "status": enrollment.user.status,
                    "profile_picture": enrollment.user.profile_picture,
                },
                "course": {
                    "id": enrollment.course.id,
                    "title": enrollment.course.title,
                    "description": enrollment.course.description,
                    "price": enrollment.course.price,
                    "image": enrollment.course.image,
                    "status": enrollment.course.status,
                    "duration_months": enrollment.course.duration_months,
                    "total_topics": len(enrollment.course.topics) if hasattr(enrollment.course, 'topics') else 0
                },
                "status": enrollment.status,
                "progress": enrollment.progress,
                "enrolled_at": enrollment.enrolled_at,
                "completed_at": enrollment.completed_at,
                "last_accessed_at": getattr(enrollment, 'last_accessed_at', None)
            })
        
        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "enrollments": result
        }
    
    @staticmethod
    def get_enrollment_by_id_with_details(db: Session, enrollment_id: int) -> Dict:
        """Get single enrollment with user and course details"""
        enrollment = db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()
        
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        return {
            "id": enrollment.id,
            "enrollment_id": getattr(enrollment, 'enrollment_id', None),
            "user": {
                "id": enrollment.user.id,
                "student_id": enrollment.user.student_id,
                "name": enrollment.user.get_full_name(),
                "email": enrollment.user.email,
                "phone_number": enrollment.user.phone_number,
                "status": enrollment.user.status,
                "profile_picture": enrollment.user.profile_picture,
            },
            "course": {
                "id": enrollment.course.id,
                "title": enrollment.course.title,
                "description": enrollment.course.description,
                "price": enrollment.course.price,
                "image": enrollment.course.image,
                "status": enrollment.course.status,
                "duration_months": enrollment.course.duration_months,
                "total_topics": len(enrollment.course.topics) if hasattr(enrollment.course, 'topics') else 0
            },
            "status": enrollment.status,
            "progress": enrollment.progress,
            "enrolled_at": enrollment.enrolled_at,
            "completed_at": enrollment.completed_at,
            "last_accessed_at": getattr(enrollment, 'last_accessed_at', None)
        }
    
    @staticmethod
    def get_enrollment_stats_by_course(db: Session, course_id: int = None) -> Dict:
        """Get enrollment statistics grouped by course"""
        query = db.query(
            Course.id,
            Course.title,
            func.count(Enrollment.id).label('total_enrollments'),
            func.sum(case((Enrollment.status == EnrollmentStatus.ACTIVE, 1), else_=0)).label('active_enrollments'),
            func.sum(case((Enrollment.status == EnrollmentStatus.COMPLETED, 1), else_=0)).label('completed_enrollments'),
            func.avg(Enrollment.progress).label('average_progress')
        ).join(Enrollment, Course.id == Enrollment.course_id)
        
        if course_id:
            query = query.filter(Course.id == course_id)
        
        results = query.group_by(Course.id).all()
        
        stats = []
        for result in results:
            stats.append({
                "course_id": result.id,
                "course_title": result.title,
                "total_enrollments": result.total_enrollments,
                "active_enrollments": result.active_enrollments or 0,
                "completed_enrollments": result.completed_enrollments or 0,
                "average_progress": round(result.average_progress or 0, 2),
                "completion_rate": round((result.completed_enrollments or 0) / (result.total_enrollments or 1) * 100, 2)
            })
        
        return stats
    
    @staticmethod
    def get_recent_enrollments(db: Session, limit: int = 10) -> List[Dict]:
        """Get recent enrollments"""
        enrollments = db.query(Enrollment).order_by(
            Enrollment.enrolled_at.desc()
        ).limit(limit).all()
        
        result = []
        for enrollment in enrollments:
            result.append({
                "id": enrollment.id,
                "user_name": enrollment.user.get_full_name(),
                "user_email": enrollment.user.email,
                "course_title": enrollment.course.title,
                "status": enrollment.status,
                "progress": enrollment.progress,
                "enrolled_at": enrollment.enrolled_at
            })
        
        return result

    @staticmethod
    def get_user_topic_progress(db: Session, user_id: int, topic_id: int) -> bool:
        """Check if user has completed a topic"""
        from app.models.topic_progress import TopicProgress
        progress = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic_id,
            TopicProgress.is_completed == True
        ).first()
        return progress is not None

    @staticmethod
    def get_user_class_progress(db: Session, user_id: int, class_id: int) -> bool:
        """Check if user has completed a class"""
        from app.models.class_progress import ClassProgress
        progress = db.query(ClassProgress).filter(
            ClassProgress.user_id == user_id,
            ClassProgress.class_id == class_id,
            ClassProgress.is_completed == True
        ).first()
        return progress is not None

    @staticmethod
    def mark_topic_complete(db: Session, user_id: int, topic_id: int, is_completed: bool = True) -> Dict:
        """Mark a topic as completed for a user"""
        from app.models.topic_progress import TopicProgress
        
        progress = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic_id
        ).first()
        
        if not progress:
            progress = TopicProgress(
                user_id=user_id,
                topic_id=topic_id,
                is_completed=is_completed
            )
            db.add(progress)
        else:
            progress.is_completed = is_completed
            if is_completed:
                progress.completed_at = datetime.utcnow()
        
        db.commit()
        
        # Update overall course progress
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if topic:
            CourseService.update_course_progress_from_topics(db, user_id, topic.course_id)
        
        return {"message": f"Topic marked as {'completed' if is_completed else 'incomplete'}"}

    @staticmethod
    def update_course_progress_from_topics(db: Session, user_id: int, course_id: int) -> float:
        """Calculate course progress based on completed topics"""
        from app.models.topic_progress import TopicProgress
        
        topics = db.query(Topic).filter(Topic.course_id == course_id).all()
        if not topics:
            return 0
        
        completed_count = 0
        for topic in topics:
            progress = db.query(TopicProgress).filter(
                TopicProgress.user_id == user_id,
                TopicProgress.topic_id == topic.id,
                TopicProgress.is_completed == True
            ).first()
            if progress:
                completed_count += 1
        
        progress_percentage = (completed_count / len(topics)) * 100
        
        # Update enrollment progress
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        
        if enrollment:
            enrollment.progress = progress_percentage
            if progress_percentage >= 100:
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.completed_at = datetime.utcnow()
            db.commit()
        
        return progress_percentage

    @staticmethod
    def mark_class_complete(db: Session, user_id: int, class_id: int, is_completed: bool = True) -> Dict:
        """Mark a class as completed and update topic progress accordingly"""
        
        # Get the class and its topic
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        if not class_obj:
            raise ValueError("Class not found")
        
        topic_id = class_obj.topic_id
        
        # Update or create class progress
        class_progress = db.query(ClassProgress).filter(
            ClassProgress.user_id == user_id,
            ClassProgress.class_id == class_id
        ).first()
        
        if not class_progress:
            class_progress = ClassProgress(
                user_id=user_id,
                class_id=class_id,
                is_completed=is_completed
            )
            db.add(class_progress)
        else:
            class_progress.is_completed = is_completed
            if is_completed:
                class_progress.completed_at = datetime.utcnow()
        
        db.flush()
        
        # Check if all classes in this topic are completed
        all_classes = db.query(Class).filter(Class.topic_id == topic_id).all()
        completed_classes = db.query(ClassProgress).filter(
            ClassProgress.user_id == user_id,
            ClassProgress.class_id.in_([c.id for c in all_classes]),
            ClassProgress.is_completed == True
        ).count()
        
        # If all classes are completed, mark the topic as completed
        if completed_classes == len(all_classes) and len(all_classes) > 0:
            topic_progress = db.query(TopicProgress).filter(
                TopicProgress.user_id == user_id,
                TopicProgress.topic_id == topic_id
            ).first()
            
            if not topic_progress:
                topic_progress = TopicProgress(
                    user_id=user_id,
                    topic_id=topic_id,
                    is_completed=True,
                    completed_at=datetime.utcnow()
                )
                db.add(topic_progress)
            elif not topic_progress.is_completed:
                topic_progress.is_completed = True
                topic_progress.completed_at = datetime.utcnow()
            
            db.flush()
            
            # Update overall course progress
            topic = db.query(Topic).filter(Topic.id == topic_id).first()
            if topic:
                CourseService.update_course_progress_from_topics(db, user_id, topic.course_id)
        
        db.commit()
        
        return {
            "message": f"Class marked as {'completed' if is_completed else 'incomplete'}",
            "topic_completed": completed_classes == len(all_classes) and len(all_classes) > 0
        }

    @staticmethod
    def get_topic_completion_status(db: Session, user_id: int, topic_id: int) -> Dict:
        """Get completion status for a topic and its classes"""
        
        # Get all classes in this topic
        classes = db.query(Class).filter(Class.topic_id == topic_id).all()
        
        # Get completed classes
        completed_class_ids = set()
        class_progress_list = db.query(ClassProgress).filter(
            ClassProgress.user_id == user_id,
            ClassProgress.class_id.in_([c.id for c in classes]),
            ClassProgress.is_completed == True
        ).all()
        
        for progress in class_progress_list:
            completed_class_ids.add(progress.class_id)
        
        # Prepare class status
        classes_status = []
        for cls in classes:
            classes_status.append({
                "id": cls.id,
                "name": cls.name,
                "meeting_link": cls.meeting_link,
                "start_date": cls.start_date,
                "end_date": cls.end_date,
                "is_completed": cls.id in completed_class_ids
            })
        
        # Check if topic is completed
        topic_progress = db.query(TopicProgress).filter(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id == topic_id,
            TopicProgress.is_completed == True
        ).first()
        
        is_topic_completed = topic_progress is not None
        completed_classes_count = len(completed_class_ids)
        total_classes = len(classes)
        
        return {
            "topic_id": topic_id,
            "is_completed": is_topic_completed,
            "completed_classes": completed_classes_count,
            "total_classes": total_classes,
            "progress_percentage": (completed_classes_count / total_classes * 100) if total_classes > 0 else 100 if is_topic_completed else 0,
            "classes": classes_status
        }

    @staticmethod
    def get_course_with_progress(db: Session, user_id: int, course_id: int) -> Dict:
        """Get course details with topic and class progress"""
        
        course = CourseService.get_course(db, course_id)
        topics = CourseService.get_topics(db, course_id)
        
        topics_with_progress = []
        completed_topics = 0
        
        for topic in topics:
            topic_status = CourseService.get_topic_completion_status(db, user_id, topic.id)
            topics_with_progress.append({
                "id": topic.id,
                "title": topic.title,
                "order": topic.order,
                "is_completed": topic_status["is_completed"],
                "progress_percentage": topic_status["progress_percentage"],
                "completed_classes": topic_status["completed_classes"],
                "total_classes": topic_status["total_classes"],
                "classes": topic_status["classes"]
            })
            
            if topic_status["is_completed"]:
                completed_topics += 1
        
        total_topics = len(topics)
        course_progress = (completed_topics / total_topics * 100) if total_topics > 0 else 0
        
        return {
            "course": course,
            "topics": topics_with_progress,
            "progress": {
                "completed_topics": completed_topics,
                "total_topics": total_topics,
                "percentage": course_progress
            }
        }