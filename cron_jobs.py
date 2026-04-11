#!/usr/bin/env python
"""Cron job script for automated tasks"""
import sys
import os
from datetime import datetime, timedelta
import logging

# Add the project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.database.database import SessionLocal
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User

# Create logs directory if it doesn't exist
logs_dir = os.path.join(project_root, 'app', 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'cron_jobs.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CronJobService:
    
    @staticmethod
    def expire_subscriptions():
        """Mark expired subscriptions as EXPIRED and send notifications"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find active subscriptions that have expired
            expired_subs = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date <= now
            ).all()
            
            expired_count = 0
            for sub in expired_subs:
                sub.status = SubscriptionStatus.EXPIRED
                expired_count += 1
                logger.info(f"Expired subscription: {sub.subscription_id} for user {sub.user_id}")
                
                # Send expiry notification
                try:
                    from app.services.notification_service import NotificationService
                    NotificationService.notify_subscription_expired(
                        db, sub.user_id, sub.plan.name
                    )
                except Exception as e:
                    logger.error(f"Failed to send expiry notification for user {sub.user_id}: {e}")
            
            db.commit()
            
            if expired_count > 0:
                logger.info(f"Expired {expired_count} subscriptions and sent notifications")
            else:
                logger.info("No expired subscriptions found")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error expiring subscriptions: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    @staticmethod
    def send_expiry_warnings():
        """Send warnings for subscriptions expiring soon (7, 3, and 1 day before)"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            warning_days = [7, 3, 1]  # Send warnings 7, 3, and 1 day before expiry
            
            total_warnings_sent = 0
            
            for days in warning_days:
                warning_date = now + timedelta(days=days)
                
                # Find subscriptions expiring on the warning date
                expiring_subs = db.query(Subscription).join(User).filter(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date > now,
                    Subscription.end_date <= warning_date + timedelta(days=1),
                    Subscription.end_date > warning_date - timedelta(days=1)
                ).all()
                
                for sub in expiring_subs:
                    try:
                        from app.services.notification_service import NotificationService
                        NotificationService.notify_subscription_expiring(
                            db, sub.user_id, sub.plan.name, days
                        )
                        total_warnings_sent += 1
                        logger.info(f"Expiry warning sent to user {sub.user.email} for subscription {sub.subscription_id} (expires in {days} days)")
                    except Exception as e:
                        logger.error(f"Failed to send expiry warning to user {sub.user_id}: {e}")
            
            db.commit()
            logger.info(f"Sent {total_warnings_sent} expiry warnings")
            return total_warnings_sent
            
        except Exception as e:
            logger.error(f"Error sending expiry warnings: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    @staticmethod
    def check_subscription_access():
        """Disable enrollment access for users with expired subscriptions"""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find users with expired subscriptions
            expired_users = db.query(Subscription.user_id).filter(
                Subscription.status == SubscriptionStatus.EXPIRED
            ).distinct().all()
            
            expired_user_ids = [u[0] for u in expired_users]
            
            if not expired_user_ids:
                logger.info("No users with expired subscriptions found")
                return 0
            
            # Find active enrollments for these users
            affected_enrollments = db.query(Enrollment).filter(
                Enrollment.user_id.in_(expired_user_ids),
                Enrollment.status == EnrollmentStatus.ACTIVE
            ).all()
            
            updated_count = 0
            for enrollment in affected_enrollments:
                # Check if user has any active subscription
                has_active_sub = db.query(Subscription).filter(
                    Subscription.user_id == enrollment.user_id,
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.end_date > now
                ).first()
                
                if not has_active_sub:
                    enrollment.status = EnrollmentStatus.DROPPED
                    updated_count += 1
                    logger.info(f"Dropped enrollment for user {enrollment.user_id} in course {enrollment.course_id}")
            
            db.commit()
            logger.info(f"Updated {updated_count} enrollments due to expired subscriptions")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error checking subscription access: {e}")
            db.rollback()
            return 0
        finally:
            db.close()
    
    @staticmethod
    def cleanup_old_data():
        """Clean up old records (optional)"""
        db = SessionLocal()
        try:
            # Delete old completed enrollments (older than 1 year)
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            
            old_completed = db.query(Enrollment).filter(
                Enrollment.status == EnrollmentStatus.COMPLETED,
                Enrollment.completed_at <= one_year_ago
            ).count()
            
            # Delete expired subscriptions older than 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            old_expired_subs = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.EXPIRED,
                Subscription.end_date <= six_months_ago
            ).count()
            
            logger.info(f"Found {old_completed} old completed enrollments to clean up")
            logger.info(f"Found {old_expired_subs} old expired subscriptions to clean up")
            
            # Actually delete them
            db.query(Enrollment).filter(
                Enrollment.status == EnrollmentStatus.COMPLETED,
                Enrollment.completed_at <= one_year_ago
            ).delete()
            
            db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.EXPIRED,
                Subscription.end_date <= six_months_ago
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {old_completed} old completed enrollments")
            logger.info(f"Cleaned up {old_expired_subs} old expired subscriptions")
            
            return {
                "old_completed_enrollments": old_completed,
                "old_expired_subscriptions": old_expired_subs
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()
    
    @staticmethod
    def run_all_jobs():
        """Run all cron jobs"""
        logger.info("=" * 50)
        logger.info("Starting cron jobs...")
        logger.info("=" * 50)
        
        # 1. Send expiry warnings
        warnings_sent = CronJobService.send_expiry_warnings()
        logger.info(f"✓ Expiry warnings sent: {warnings_sent}")
        
        # 2. Expire subscriptions
        expired = CronJobService.expire_subscriptions()
        logger.info(f"✓ Expired subscriptions: {expired}")
        
        # 3. Check subscription access and update enrollments
        updated = CronJobService.check_subscription_access()
        logger.info(f"✓ Updated enrollments: {updated}")
        
        logger.info("=" * 50)
        logger.info("Cron jobs completed!")
        logger.info("=" * 50)
        
        return {
            "expiry_warnings_sent": warnings_sent,
            "expired_subscriptions": expired,
            "updated_enrollments": updated
        }

if __name__ == "__main__":
    # Run all jobs when script is executed directly
    result = CronJobService.run_all_jobs()
    print(f"Result: {result}")