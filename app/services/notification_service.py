from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.notification import Notification, NotificationStatus, NotificationType
import uuid

class NotificationService:
    
    @staticmethod
    def generate_notification_id() -> str:
        """Generate unique notification ID"""
        return str(uuid.uuid4()).replace('-', '')[:12].upper()
    
    @staticmethod
    def create_notification(db: Session, notification_data: dict) -> Notification:
        """Create a new notification"""
        notification_data['notification_id'] = NotificationService.generate_notification_id()
        
        notification = Notification(**notification_data)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return notification
    
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 50, 
                                status: str = None) -> Dict:
        """Get user's notifications"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if status:
            query = query.filter(Notification.status == status)
        
        total = query.count()
        notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "notifications": notifications
        }
    
    @staticmethod
    def mark_as_read(db: Session, user_id: int, notification_ids: List[int] = None) -> int:
        """Mark notifications as read"""
        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        )
        
        if notification_ids:
            query = query.filter(Notification.id.in_(notification_ids))
        
        updated_count = query.update({"status": NotificationStatus.READ, "read_at": datetime.utcnow()})
        db.commit()
        
        return updated_count
    
    @staticmethod
    def delete_notification(db: Session, user_id: int, notification_id: int) -> bool:
        """Delete a notification"""
        result = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.id == notification_id
        ).delete()
        
        db.commit()
        return result > 0
    
    @staticmethod
    def delete_all_notifications(db: Session, user_id: int) -> int:
        """Delete all notifications for a user"""
        result = db.query(Notification).filter(Notification.user_id == user_id).delete()
        db.commit()
        return result
    
    @staticmethod
    def get_notification_counts(db: Session, user_id: int) -> Dict:
        """Get notification counts"""
        total = db.query(Notification).filter(Notification.user_id == user_id).count()
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.status == NotificationStatus.UNREAD
        ).count()
        
        return {
            "total": total,
            "unread": unread
        }
    
    # ==================== AUTO-GENERATED NOTIFICATIONS ====================
    
    @staticmethod
    def notify_course_completion(db: Session, user_id: int, course_title: str, enrollment_id: int):
        """Send notification when user completes a course"""
        notification_data = {
            "user_id": user_id,
            "title": "Course Completed!",
            "message": f"Congratulations! You have successfully completed '{course_title}'. Your certificate is ready.",
            "type": NotificationType.COURSE,
            "action_url": f"/user/courses/{enrollment_id}",
            "action_text": "View Course"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_certificate_issued(db: Session, user_id: int, course_title: str, certificate_number: str):
        """Send notification when certificate is issued"""
        notification_data = {
            "user_id": user_id,
            "title": "Certificate Issued!",
            "message": f"Your certificate for '{course_title}' has been issued. Certificate number: {certificate_number}",
            "type": NotificationType.CERTIFICATE,
            "action_url": "/user/my-certificates",
            "action_text": "View Certificate"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_subscription_activated(db: Session, user_id: int, plan_name: str, end_date: datetime):
        """Send notification when subscription is activated"""
        notification_data = {
            "user_id": user_id,
            "title": "Subscription Activated",
            "message": f"Your {plan_name} subscription has been activated. It will expire on {end_date.strftime('%Y-%m-%d')}.",
            "type": NotificationType.SUBSCRIPTION,
            "action_url": "/user/my-subscriptions",
            "action_text": "View Subscription"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_subscription_expiring(db: Session, user_id: int, plan_name: str, days_left: int):
        """Send notification when subscription is about to expire"""
        notification_data = {
            "user_id": user_id,
            "title": "Subscription Expiring Soon",
            "message": f"Your {plan_name} subscription will expire in {days_left} days. Renew now to continue accessing courses.",
            "type": NotificationType.SUBSCRIPTION,
            "action_url": "/user/subscription/plans",
            "action_text": "Renew Now"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_payment_success(db: Session, user_id: int, amount: float, plan_name: str):
        """Send notification when payment is successful"""
        notification_data = {
            "user_id": user_id,
            "title": "Payment Successful",
            "message": f"Your payment of ₦{amount:,.2f} for {plan_name} was successful.",
            "type": NotificationType.PAYMENT,
            "action_url": "/user/my-subscriptions",
            "action_text": "View Details"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_enrollment_confirmation(db: Session, user_id: int, course_title: str):
        """Send notification when user enrolls in a course"""
        notification_data = {
            "user_id": user_id,
            "title": "Enrollment Confirmed",
            "message": f"You have successfully enrolled in '{course_title}'. Start learning today!",
            "type": NotificationType.COURSE,
            "action_url": "/user/my-enrollments",
            "action_text": "My Courses"
        }
        return NotificationService.create_notification(db, notification_data)
    
    @staticmethod
    def notify_welcome(db: Session, user_id: int, user_name: str):
        """Send welcome notification to new users"""
        notification_data = {
            "user_id": user_id,
            "title": "Welcome to HALĪMATU SA'DIYYAH ISlamic Academy!",
            "message": f"Welcome {user_name}! We're excited to have you. Start exploring our courses today.",
            "type": NotificationType.SYSTEM,
            "action_url": "/user/courses",
            "action_text": "Browse Courses"
        }
        return NotificationService.create_notification(db, notification_data)