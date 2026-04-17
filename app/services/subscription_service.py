from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import random
import secrets

from app.models.user import User
from app.models.plan import Plan, PlanStatus, PlanType
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.services.flutterwave_service import flutterwave
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.services.course_service import CourseService

class SubscriptionService:
    
    # ==================== PLAN MANAGEMENT ====================
    @staticmethod
    def create_plan(db: Session, plan_data: dict) -> Plan:
        """Create a new subscription plan"""
        # Check if plan type already exists
        existing = db.query(Plan).filter(Plan.type == plan_data['type']).first()
        if existing:
            raise ValueError(f"Plan with type {plan_data['type']} already exists")
        
        # Calculate discount percentage if not provided
        if 'discount_percentage' not in plan_data or plan_data['discount_percentage'] is None:
            original = plan_data['original_price']
            discounted = plan_data['discounted_price']
            if original > 0:
                plan_data['discount_percentage'] = int(((original - discounted) / original) * 100)
            else:
                plan_data['discount_percentage'] = 0
        
        plan = Plan(**plan_data)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    
    @staticmethod
    def get_plans(db: Session, include_inactive: bool = False) -> List[Plan]:
        """Get all plans"""
        query = db.query(Plan)
        if not include_inactive:
            query = query.filter(Plan.status == PlanStatus.ACTIVE)
        return query.order_by(Plan.sort_order).all()
    
    @staticmethod
    def get_plan(db: Session, plan_id: int) -> Plan:
        """Get plan by ID"""
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        return plan
    
    @staticmethod
    def update_plan(db: Session, plan_id: int, plan_data: dict) -> Plan:
        """Update a plan"""
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        # Update only provided fields
        for key, value in plan_data.items():
            if value is not None:
                setattr(plan, key, value)
        
        # Recalculate discount percentage if prices changed
        if 'original_price' in plan_data or 'discounted_price' in plan_data:
            original = plan.original_price
            discounted = plan.discounted_price
            if original > 0:
                plan.discount_percentage = int(((original - discounted) / original) * 100)
        
        plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(plan)
        return plan
    
    @staticmethod
    def delete_plan(db: Session, plan_id: int) -> Dict:
        """Delete a plan (soft delete by deactivating)"""
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan not found")
        
        # Check if plan has active subscriptions
        active_sub = db.query(Subscription).filter(
            Subscription.plan_id == plan_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > datetime.utcnow()
        ).first()
        
        if active_sub:
            raise ValueError("Cannot delete plan with active subscriptions. Deactivate it instead.")
        
        plan.status = PlanStatus.INACTIVE
        db.commit()
        return {"message": f"Plan '{plan.name}' deactivated successfully"}
    
    # ==================== SUBSCRIPTION MANAGEMENT ====================
    
    @staticmethod
    def generate_subscription_id() -> str:
        """Generate unique subscription ID"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_num = random.randint(1000, 9999)
        return f"SUB-{date_str}-{random_num}"
    
    @staticmethod
    def generate_transaction_reference() -> str:
        """Generate unique transaction reference for Flutterwave"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = secrets.token_hex(4).upper()
        return f"HALIMATU-{timestamp}-{random_str}"
    
    @staticmethod
    def create_pending_payment(db: Session, user_id: int, plan_id: int) -> Dict:
        """
        Create a pending payment record and return payment details for frontend
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get plan
        plan = db.query(Plan).filter(Plan.id == plan_id, Plan.status == PlanStatus.ACTIVE).first()
        if not plan:
            raise ValueError("Plan not found or inactive")
        
        # Check for existing active subscription
        existing_sub = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > datetime.utcnow()
        ).first()
        
        if existing_sub:
            raise ValueError("User already has an active subscription")
        
        # Generate transaction reference
        tx_ref = SubscriptionService.generate_transaction_reference()
        
        # Create pending payment record
        payment = Payment(
            transaction_id=tx_ref,
            user_id=user_id,
            plan_id=plan_id,
            amount=plan.discounted_price,
            currency="NGN",
            payment_method=PaymentMethod.INLINE,
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()
        
        return {
            "tx_ref": tx_ref,
            "amount": plan.discounted_price,
            "currency": "NGN",
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "duration_months": plan.duration_months
            },
            "user": {
                "email": user.email,
                "name": user.get_full_name(),
                "phone": user.phone_number or ""
            }
        }
    
    @staticmethod
    def confirm_payment_and_activate_subscription(db: Session, tx_ref: str, user_id: int) -> Dict:
        """
        Verify payment and activate subscription (idempotent & safe)
        Enrolls user only in courses assigned to the subscribed plan
        """

        try:
            # 🔒 Start transaction

            # 1. Fetch payment
            payment = db.query(Payment).filter(
                Payment.transaction_id == tx_ref,
                Payment.user_id == user_id
            ).first()

            if not payment:
                raise ValueError("Payment record not found")

            # 2. If already completed → check subscription
            if payment.status == PaymentStatus.COMPLETED:
                if payment.subscription_id:
                    subscription = db.query(Subscription).filter(Subscription.id == payment.subscription_id).first()
                    # Get courses for this plan
                    courses = CourseService.get_courses_by_plan(db, subscription.plan_id, status="published")
                    
                    return {
                        "status": "success",
                        "message": "Payment already confirmed",
                        "subscription_id": payment.subscription_id,
                        "subscription": subscription,
                        "available_courses": courses,
                        "total_courses": len(courses)
                    }

            # 3. Verify payment with Flutterwave
            verification = flutterwave.verify_payment(tx_ref)

            if verification.get("status") != "success":
                return {
                    "status": "failed",
                    "message": "Payment verification failed",
                    "details": verification
                }

            # 4. Update payment
            payment.status = PaymentStatus.COMPLETED
            payment.paid_at = datetime.utcnow()
            payment.payment_details = verification
            payment.flutterwave_reference = verification.get("flw_ref")

            # 5. Fetch plan
            plan = db.query(Plan).filter(Plan.id == payment.plan_id).first()
            if not plan:
                raise ValueError("Plan not found")

            # 6. Prevent duplicate subscription
            existing_subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.plan_id == plan.id,
                Subscription.status == SubscriptionStatus.ACTIVE
            ).first()

            if existing_subscription:
                if not payment.subscription_id:
                    payment.subscription_id = existing_subscription.id
                    db.commit()

                # Get courses for existing plan
                courses = CourseService.get_courses_by_plan(db, plan.id, status="published")
                
                return {
                    "status": "success",
                    "message": "Active subscription already exists",
                    "subscription_id": existing_subscription.subscription_id,
                    "subscription": existing_subscription,
                    "available_courses": courses,
                    "total_courses": len(courses)
                }

            # 7. Create subscription
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=plan.duration_months * 30)

            subscription = Subscription(
                subscription_id=SubscriptionService.generate_subscription_id(),
                user_id=user_id,
                plan_id=plan.id,
                amount_paid=payment.amount,
                start_date=start_date,
                end_date=end_date,
                status=SubscriptionStatus.ACTIVE,
                auto_renew=False
            )

            db.add(subscription)
            db.flush()

            # After subscription is created
            if subscription:
                from app.services.notification_service import NotificationService
                NotificationService.notify_subscription_activated(
                    db, user_id, plan.name, subscription.end_date
                )
                NotificationService.notify_payment_success(
                    db, user_id, payment.amount, plan.name
                )

            # 8. Link payment → subscription
            payment.subscription_id = subscription.id

            # 9. Commit once to save subscription
            db.commit()

            # 10. 🎓 ENROLL USER ONLY IN COURSES ASSIGNED TO THIS PLAN
            enrolled_courses = []
            failed_courses = []
            
            # Get courses assigned to this plan
            plan_courses = CourseService.get_courses_by_plan(db, plan.id, status="published")
            
            for course in plan_courses:
                try:
                    # Check if already enrolled
                    existing_enrollment = db.query(Enrollment).filter(
                        Enrollment.user_id == user_id,
                        Enrollment.course_id == course.id
                    ).first()
                    
                    if not existing_enrollment:
                        # Create enrollment
                        enrollment = Enrollment(
                            user_id=user_id,
                            course_id=course.id,
                            status=EnrollmentStatus.ACTIVE,
                            progress=0.0
                        )
                        db.add(enrollment)

                        # Send enrollment notification
                        from app.services.notification_service import NotificationService
                        NotificationService.notify_enrollment_confirmation(
                            db, user_id, course.title
                        )
                        
                        enrolled_courses.append({
                            "id": course.id,
                            "title": course.title,
                            "enrollment_status": "created"
                        })
                    else:
                        enrolled_courses.append({
                            "id": course.id,
                            "title": course.title,
                            "enrollment_status": "already_enrolled"
                        })
                except Exception as e:
                    failed_courses.append({
                        "id": course.id,
                        "title": course.title,
                        "error": str(e)
                    })
            
            # Commit all enrollments
            db.commit()

            # 11. Refresh objects
            db.refresh(subscription)
            db.refresh(plan)

            return {
                "status": "success",
                "message": f"Payment confirmed and subscription activated. Enrolled in {len(enrolled_courses)} courses.",
                "subscription_id": subscription.subscription_id,
                "subscription": {
                    "id": subscription.id,
                    "subscription_id": subscription.subscription_id,
                    "user_id": subscription.user_id,
                    "plan_id": subscription.plan_id,
                    "amount_paid": subscription.amount_paid,
                    "start_date": subscription.start_date.isoformat(),
                    "end_date": subscription.end_date.isoformat(),
                    "status": subscription.status.value,
                    "auto_renew": subscription.auto_renew,
                    "created_at": subscription.created_at.isoformat() if subscription.created_at else None
                },
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "type": plan.type.value if hasattr(plan.type, 'value') else str(plan.type),
                    "duration_months": plan.duration_months,
                    "original_price": plan.original_price,
                    "discounted_price": plan.discounted_price,
                    "discount_percentage": plan.discount_percentage,
                    "description": plan.description,
                    "features": plan.features,
                    "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
                    "sort_order": plan.sort_order
                },
                "enrollment_summary": {
                    "total_courses_in_plan": len(plan_courses),
                    "successfully_enrolled": len(enrolled_courses),
                    "failed_enrollments": len(failed_courses),
                    "enrolled_courses": enrolled_courses,
                    "failed_courses": failed_courses if failed_courses else None
                },
                "available_courses": [
                    {
                        "id": course.id,
                        "title": course.title,
                        "description": course.description,
                        "price": course.price,
                        "is_enrolled": any(e["id"] == course.id for e in enrolled_courses),
                        "image": course.image,
                        "status": course.status
                    }
                    for course in plan_courses
                ]
            }

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_user_subscriptions(db: Session, user_id: int) -> List[Subscription]:
        """Get user's subscriptions"""
        return db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
    
    @staticmethod
    def get_user_active_subscription(db: Session, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription"""
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > datetime.utcnow()
        ).first()
    
    @staticmethod
    def cancel_subscription(db: Session, subscription_id: int, user_id: int) -> Dict:
        """Cancel a subscription"""
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError("Only active subscriptions can be cancelled")
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Subscription cancelled successfully"}
    
    @staticmethod
    def admin_cancel_subscription(db: Session, subscription_id: int) -> Dict:
        """Admin cancel a user's subscription"""
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        
        if not subscription:
            raise ValueError("Subscription not found")
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        db.commit()
        
        return {"message": f"Subscription {subscription.subscription_id} cancelled successfully"}
    
    @staticmethod
    def get_all_subscriptions(db: Session, skip: int = 0, limit: int = 100, status_filter: str = None) -> List[Subscription]:
        """Get all subscriptions (admin)"""
        query = db.query(Subscription)
        
        if status_filter:
            query = query.filter(Subscription.status == status_filter)
        
        return query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_subscription_stats(db: Session) -> Dict:
        """Get subscription statistics (admin)"""
        now = datetime.utcnow()
        
        # Total subscriptions
        total_subscriptions = db.query(Subscription).count()
        
        # Active subscriptions
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > now
        ).count()
        
        # Expired subscriptions
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.EXPIRED
        ).count()
        
        # Cancelled subscriptions
        cancelled_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.CANCELLED
        ).count()
        
        # Total revenue
        total_revenue = db.query(func.sum(Subscription.amount_paid)).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).scalar() or 0
        
        # Monthly recurring revenue (MRR)
        mrr = db.query(func.sum(Subscription.amount_paid)).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > now,
            Subscription.plan.has(type=PlanType.MONTHLY)
        ).scalar() or 0
        
        # Subscriptions by plan
        plans_stats = db.query(
            Plan.name,
            Plan.type,
            func.count(Subscription.id).label('count')
        ).outerjoin(Subscription, Plan.id == Subscription.plan_id).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > now
        ).group_by(Plan.id).all()
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": expired_subscriptions,
            "cancelled_subscriptions": cancelled_subscriptions,
            "total_revenue": total_revenue,
            "monthly_recurring_revenue": mrr,
            "plans_breakdown": [
                {"name": p.name, "type": p.type.value, "count": p.count}
                for p in plans_stats
            ]
        }
    
    @staticmethod
    def check_expired_subscriptions(db: Session) -> int:
        """Check and mark expired subscriptions"""
        expired_subs = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date <= datetime.utcnow()
        ).all()
        
        for sub in expired_subs:
            sub.status = SubscriptionStatus.EXPIRED
        
        db.commit()
        return len(expired_subs)
    
    @staticmethod
    def get_user_by_subscription(db: Session, subscription_id: int) -> Optional[User]:
        """Get user by subscription ID"""
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if subscription:
            return subscription.user
        return None
    
    @staticmethod
    def get_plan_subscribers(db: Session, plan_id: int) -> List[Subscription]:
        """Get all active subscribers for a plan"""
        return db.query(Subscription).filter(
            Subscription.plan_id == plan_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date > datetime.utcnow()
        ).all()