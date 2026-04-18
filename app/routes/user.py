from ast import List
from pyclbr import Class

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.database import get_db
from app.schemas.user import *
from app.services.user_service import UserService
from app.services.auth_service import get_current_user
from app.config.limiter import limiter
from app.config.settings import settings
from app.schemas.subscription import PlanWithUserStatusResponse, SubscribeRequest, SubscriptionResponse
from app.services.subscription_service import SubscriptionService
from app.services.flutterwave_service import flutterwave
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import Subscription
from typing import List

from app.schemas.course import (
    ClassResponse, CourseResponse, CourseDetailResponse, 
    EnrollmentResponse, MarkClassCompleteRequest, MarkTopicCompleteRequest, UpdateProgressRequest,
    MessageResponse
)
from app.services.course_service import CourseService
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.schemas.certificate import CertificateResponse
from app.services.certificate_service import CertificateService
from app.schemas.notification import *
from app.services.notification_service import NotificationService
from app.models.class_model import ClassStatus
from app.models.topic import Topic


router = APIRouter(prefix="/api/user", tags=["User"])
security = HTTPBearer()

@router.get("/profile", response_model=UserProfileResponse)
@limiter.limit("30/minute")
def get_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user profile"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        user = UserService.get_profile(db, current_user.id)
        
        return UserProfileResponse(
            id=user.id,
            student_id=user.student_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            country=user.country,
            profile_picture=user.profile_picture,
            email_verified_at=user.email_verified_at,
            status=user.status,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.put("/profile", response_model=UserProfileResponse)
@limiter.limit("20/minute")
def update_profile(
    request: Request,
    data: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update user profile (email cannot be updated)"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        # Convert to dict, excluding None values
        profile_data = {k: v for k, v in data.model_dump().items() if v is not None}
        
        user = UserService.update_profile(db, current_user.id, profile_data)
        
        return UserProfileResponse(
            id=user.id,
            student_id=user.student_id,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
            email=user.email,
            phone_number=user.phone_number,
            date_of_birth=user.date_of_birth,
            gender=user.gender,
            country=user.country,
            profile_picture=user.profile_picture,
            email_verified_at=user.email_verified_at,
            status=user.status,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("10/minute")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Change user password"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.update_password(
            db, 
            current_user.id, 
            data.current_password, 
            data.new_password,
            data.confirm_password
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/upload-profile-picture", response_model=MessageResponse)
@limiter.limit("10/minute")
def upload_profile_picture(
    request: Request,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Upload profile picture"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.upload_profile_picture(db, current_user.id, file)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )

@router.delete("/profile-picture", response_model=MessageResponse)
@limiter.limit("10/minute")
def remove_profile_picture(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Remove profile picture"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.remove_profile_picture(db, current_user.id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove profile picture"
        )

@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout current session"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.logout(db, current_user.id, token)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/logout-all", response_model=MessageResponse)
def logout_all_devices(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout from all devices"""
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        result = UserService.logout_all_devices(db, current_user.id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout from all devices failed"
        )

@router.get("/me", response_model=UserProfileResponse)
@limiter.limit("30/minute")
def get_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get the currently authenticated user's information
    """
    try:
        token = credentials.credentials
        current_user = get_current_user(db, token)
        
        return UserProfileResponse(
            id=current_user.id,
            student_id=current_user.student_id,
            first_name=current_user.first_name,
            middle_name=current_user.middle_name,
            last_name=current_user.last_name,
            email=current_user.email,
            phone_number=current_user.phone_number,
            date_of_birth=current_user.date_of_birth,
            gender=current_user.gender,
            country=current_user.country,
            status=current_user.status,
            profile_picture=current_user.profile_picture,
            email_verified_at=current_user.email_verified_at,
            created_at=current_user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
    
# ==================== SUBSCRIPTION PLANS ====================
@router.get("/plans", response_model=List[PlanWithUserStatusResponse])
@limiter.limit("30/minute")
def get_plans(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get all available subscription plans with user's subscription status
    Only shows plans if there are published courses available
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        # Get all active plans
        plans = SubscriptionService.get_plans(db, include_inactive=False)
        
        # If no plans available but courses exist
        if not plans:
            return []  # Return empty list, no plans configured yet
        
        # Get user's active subscription
        active_subscription = SubscriptionService.get_user_active_subscription(db, user.id)
        
        # Prepare response with subscription status
        result = []
        for plan in plans:
            # Calculate values safely
            is_current = False
            sub_status = None
            sub_end_date = None
            days_rem = 0
            
            if active_subscription:
                is_current = active_subscription.plan_id == plan.id
                if is_current:
                    sub_status = active_subscription.status.value if hasattr(active_subscription.status, 'value') else str(active_subscription.status)
                    sub_end_date = active_subscription.end_date
                    days_rem = active_subscription.days_remaining()
            
            plan_dict = {
                "id": plan.id,
                "name": plan.name,
                "type": plan.type.value if hasattr(plan.type, 'value') else str(plan.type),
                "duration_months": plan.duration_months,
                "original_price": float(plan.original_price),
                "discounted_price": float(plan.discounted_price),
                "discount_percentage": int(plan.discount_percentage),
                "description": plan.description,
                "features": plan.features or [],
                "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
                "sort_order": int(plan.sort_order),
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "is_current_plan": is_current,
                "subscription_status": sub_status,
                "subscription_end_date": sub_end_date,
                "days_remaining": days_rem
            }
            result.append(plan_dict)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        print(f"Error in get_plans: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/plans/{plan_id}", response_model=PlanWithUserStatusResponse)
@limiter.limit("30/minute")
def get_plan(
    request: Request,
    plan_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get a specific plan by ID with user's subscription status"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        plan = SubscriptionService.get_plan(db, plan_id)
        if plan.status.value != "active":
            raise HTTPException(status_code=404, detail="Plan not available")
        
        # Get user's active subscription
        active_subscription = SubscriptionService.get_user_active_subscription(db, user.id)
        
        # Calculate values safely
        is_current = False
        sub_status = None
        sub_end_date = None
        days_rem = 0
        
        if active_subscription:
            is_current = active_subscription.plan_id == plan.id
            if is_current:
                sub_status = active_subscription.status.value if hasattr(active_subscription.status, 'value') else str(active_subscription.status)
                sub_end_date = active_subscription.end_date
                days_rem = active_subscription.days_remaining()
        
        return {
            "id": plan.id,
            "name": plan.name,
            "type": plan.type.value if hasattr(plan.type, 'value') else str(plan.type),
            "duration_months": plan.duration_months,
            "original_price": float(plan.original_price),
            "discounted_price": float(plan.discounted_price),
            "discount_percentage": int(plan.discount_percentage),
            "description": plan.description,
            "features": plan.features or [],
            "status": plan.status.value if hasattr(plan.status, 'value') else str(plan.status),
            "sort_order": int(plan.sort_order),
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "is_current_plan": is_current,
            "subscription_status": sub_status,
            "subscription_end_date": sub_end_date,
            "days_remaining": days_rem
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# ==================== USER SUBSCRIPTIONS ====================
@router.get("/my-subscriptions", response_model=List[SubscriptionResponse])  # Change to List
@limiter.limit("30/minute")
def get_my_subscriptions(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user's subscription history"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        subscriptions = SubscriptionService.get_user_subscriptions(db, user.id)
        
        # Return the list directly
        return subscriptions
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/my-active-subscription", response_model=Optional[SubscriptionResponse])
@limiter.limit("30/minute")
def get_my_active_subscription(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user's active subscription"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        subscription = SubscriptionService.get_user_active_subscription(db, user.id)
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/my-subscription-status")
@limiter.limit("30/minute")
def get_my_subscription_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user's subscription status (simplified)"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        active_sub = SubscriptionService.get_user_active_subscription(db, user.id)
        
        if active_sub:
            days_left = active_sub.days_remaining()
            return {
                "has_active_subscription": True,
                "subscription_id": active_sub.subscription_id,
                "plan_id": active_sub.plan_id,
                "plan_name": active_sub.plan.name,
                "plan_type": active_sub.plan.type,
                "amount_paid": active_sub.amount_paid,
                "start_date": active_sub.start_date,
                "end_date": active_sub.end_date,
                "days_remaining": days_left,
                "auto_renew": active_sub.auto_renew,
                "is_expiring_soon": days_left <= 7,
                "status": active_sub.status
            }
        else:
            return {
                "has_active_subscription": False,
                "message": "No active subscription found"
            }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== SUBSCRIPTION PAYMENT ====================
class InitiatePaymentRequest(BaseModel):
    plan_id: int

class VerifyPaymentRequest(BaseModel):
    tx_ref: str

@router.post("/subscribe/initiate", response_model=dict)
@limiter.limit("5/minute")
def initiate_subscription(
    request: Request,
    data: InitiatePaymentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Initiate a new subscription payment
    Returns payment details for Flutterwave inline checkout
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        # Check if user already has active subscription
        active_sub = SubscriptionService.get_user_active_subscription(db, user.id)
        if active_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already have an active {active_sub.plan.name} subscription. Please cancel it first if you want to change plans."
            )
        
        result = SubscriptionService.create_pending_payment(db, user.id, data.plan_id)
        
        return {
            "status": "success",
            "data": {
                "tx_ref": result["tx_ref"],
                "amount": result["amount"],
                "currency": result["currency"],
                "customer": {
                    "email": result["user"]["email"],
                    "name": result["user"]["name"],
                    "phonenumber": result["user"]["phone"]
                },
                "customizations": {
                    "title": "Halimatu LMS",
                    "description": f"Subscription to {result['plan']['name']} Plan",
                    "logo": "https://res.cloudinary.com/ddj0k8gdw/image/upload/v1769389099/Halimatu-Academy-Images/logo_3_1_bmduex.png"
                },
                "plan": result["plan"]
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscribe/verify", response_model=dict)
@limiter.limit("10/minute")
def verify_payment(
    request: Request,
    data: VerifyPaymentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Verify payment status with Flutterwave
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        # Get payment record
        payment = db.query(Payment).filter(
            Payment.transaction_id == data.tx_ref,
            Payment.user_id == user.id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")
        
        # Verify with Flutterwave
        verification = flutterwave.verify_payment(data.tx_ref)
        
        if verification["status"] == "success":
            # Update payment status
            payment.status = PaymentStatus.COMPLETED
            payment.paid_at = datetime.utcnow()
            payment.payment_details = verification
            payment.flutterwave_reference = verification.get("flw_ref")
            db.commit()
            
            return {
                "status": "success",
                "message": "Payment verified successfully",
                "amount": verification.get("amount"),
                "flw_ref": verification.get("flw_ref")
            }
        else:
            return {
                "status": "pending",
                "message": "Payment not yet completed. Please check again.",
                "tx_ref": data.tx_ref
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscribe/activate", response_model=dict)
@limiter.limit("5/minute")
def activate_subscription(
    request: Request,
    data: VerifyPaymentRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Activate subscription after successful payment
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = SubscriptionService.confirm_payment_and_activate_subscription(
            db, data.tx_ref, user.id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== CANCEL SUBSCRIPTION ====================
@router.post("/subscriptions/{subscription_id}/cancel", response_model=dict)
@limiter.limit("5/minute")
def cancel_subscription(
    request: Request,
    subscription_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Cancel user's active subscription
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = SubscriptionService.cancel_subscription(db, subscription_id, user.id)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscriptions/{subscription_id}/toggle-auto-renew", response_model=dict)
@limiter.limit("5/minute")
def toggle_auto_renew(
    request: Request,
    subscription_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Toggle auto-renew for a subscription
    """
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == user.id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if subscription.status != "active":
            raise HTTPException(status_code=400, detail="Only active subscriptions can be modified")
        
        subscription.auto_renew = not subscription.auto_renew
        db.commit()
        
        return {
            "status": "success",
            "auto_renew": subscription.auto_renew,
            "message": f"Auto-renew {'enabled' if subscription.auto_renew else 'disabled'}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== VIEW COURSES ====================

@router.get("/courses", response_model=List[CourseResponse])
@limiter.limit("30/minute")
def get_available_courses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get all published courses for users"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        courses = CourseService.get_courses(db, skip, limit, "published")
        
        # Get user's enrollments
        enrollments = {e.course_id: e for e in db.query(Enrollment).filter(Enrollment.user_id == user.id).all()}
        
        result = []
        for course in courses:
            enrollment = enrollments.get(course.id)
            result.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "price": course.price,
                "status": course.status.value if hasattr(course.status, 'value') else str(course.status),  # Add status
                "image": course.image,
                "duration_months": getattr(course, 'duration_months', 0),
                "instructor": getattr(course, 'instructor', None),
                "total_topics": len(course.topics),
                "total_enrolled": course.total_students if hasattr(course, 'total_students') else 0,
                "total_classes": sum(len(t.classes) for t in course.topics),
                "is_enrolled": enrollment is not None,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
@limiter.limit("30/minute")
def get_course_details(
    request: Request,
    course_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get course details with topics, classes, and completion status"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        course = CourseService.get_course(db, course_id)
        
        # Check if user is enrolled
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id
        ).first()
        
        topics = CourseService.get_topics(db, course_id)
        
        # Get topics with progress and their classes
        topics_with_progress = []
        for topic in topics:
            # Check if topic is completed
            topic_completed = CourseService.get_user_topic_progress(db, user.id, topic.id)
            
            # Get classes for this topic with progress
            classes = CourseService.get_classes(db, topic.id)
            classes_with_progress = []
            for cls in classes:
                class_completed = CourseService.get_user_class_progress(db, user.id, cls.id)
                classes_with_progress.append({
                    "id": cls.id,
                    "name": cls.name,
                    "meeting_link": cls.meeting_link,
                    "meeting_password": cls.meeting_password,
                    "start_date": cls.start_date,
                    "end_date": cls.end_date,
                    "status": cls.status,
                    "topic_id": cls.topic_id,
                    "created_at": cls.created_at,
                    "is_completed": class_completed
                })
            
            topics_with_progress.append({
                "id": topic.id,
                "title": topic.title,
                "order": topic.order,
                "course_id": topic.course_id,
                "created_at": topic.created_at,
                "is_completed": topic_completed,
                "progress_percentage": 100 if topic_completed else 0,
                "classes": classes_with_progress
            })
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "image": course.image,
            "instructor": getattr(course, 'instructor', None),
            "duration_months": getattr(course, 'duration_months', 0),
            "status": course.status,
            "total_topics": len(topics),
            "total_classes": sum(len(t.classes) for t in topics),
            "total_enrolled": course.total_enrolled if hasattr(course, 'total_enrolled') else 0,
            "is_enrolled": enrollment is not None,
            "enrollment_status": enrollment.status if enrollment else None,
            "progress": enrollment.progress if enrollment else 0,
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "topics": topics_with_progress
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/topics/{topic_id}/complete", response_model=MessageResponse)
@limiter.limit("20/minute")
def mark_topic_complete(
    request: Request,
    topic_id: int,
    data: MarkTopicCompleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Mark a topic as completed"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = CourseService.mark_topic_complete(db, user.id, topic_id, data.is_completed)
        return MessageResponse(message=result["message"])
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.post("/classes/{class_id}/complete", response_model=MessageResponse)
@limiter.limit("20/minute")
def mark_class_complete(
    request: Request,
    class_id: int,
    data: MarkClassCompleteRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Mark a class as completed - automatically updates topic and course progress"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = CourseService.mark_class_complete(db, user.id, class_id, data.is_completed)
        
        message = result["message"]
        if result.get("topic_completed"):
            message += " 🎉 Topic completed!"
        
        return MessageResponse(message=message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses/{course_id}/progress", response_model=dict)
@limiter.limit("30/minute")
def get_course_progress(
    request: Request,
    course_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get detailed course progress with topic and class completion"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = CourseService.get_course_with_progress(db, user.id, course_id)
        
        return {
            "course_id": result["course"].id,
            "course_title": result["course"].title,
            "progress_percentage": result["progress"]["percentage"],
            "completed_topics": result["progress"]["completed_topics"],
            "total_topics": result["progress"]["total_topics"],
            "topics": result["topics"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# ==================== ENROLLMENT ====================

@router.get("/my-enrollments", response_model=List[EnrollmentResponse])
@limiter.limit("30/minute")
def get_my_enrollments(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get user's enrolled courses"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        enrollments = CourseService.get_user_enrollments(db, user.id)
        return enrollments
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/update-progress/{course_id}", response_model=EnrollmentResponse)
@limiter.limit("20/minute")
def update_progress(
    request: Request,
    course_id: int,
    data: UpdateProgressRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Update course progress"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        enrollment = CourseService.update_progress(db, user.id, course_id, data.progress)
        
        return {
            "id": enrollment.id,
            "course_id": enrollment.course_id,
            "course_title": enrollment.course.title,
            "status": enrollment.status,
            "progress": enrollment.progress,
            "enrolled_at": enrollment.enrolled_at,
            "completed_at": enrollment.completed_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# ==================== USER CERTIFICATES ====================

@router.get("/my-certificates", response_model=List[CertificateResponse])
@limiter.limit("30/minute")
def get_my_certificates(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user's certificates"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        certificates = CertificateService.get_user_certificates(db, user.id, "issued")
        
        result = []
        for cert in certificates:
            result.append({
                "id": cert.id,
                "certificate_id": cert.certificate_id,
                "certificate_number": cert.certificate_number,
                "user_id": cert.user_id,
                "user_name": cert.user.get_full_name(),
                "user_email": cert.user.email,
                "course_id": cert.course_id,
                "course_title": cert.course.title,
                "course_image": cert.course.image,
                "full_name": cert.full_name,
                "grade": cert.grade,
                "score": cert.score,
                "duration": cert.duration,
                "status": cert.status,
                "issue_date": cert.issue_date,
                "created_at": cert.created_at
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/my-certificates/{certificate_id}", response_model=CertificateResponse)
@limiter.limit("30/minute")
def get_my_certificate(
    request: Request,
    certificate_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get specific certificate for current user"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        certificate = CertificateService.get_certificate_by_id(db, certificate_id)
        if certificate.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "certificate_number": certificate.certificate_number,
            "user_id": certificate.user_id,
            "user_name": certificate.user.get_full_name(),
            "user_email": certificate.user.email,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "course_image": certificate.course.image,
            "full_name": certificate.full_name,
            "grade": certificate.grade,
            "score": certificate.score,
            "duration": certificate.duration,
            "status": certificate.status,
            "issue_date": certificate.issue_date,
            "created_at": certificate.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== NOTIFICATION MANAGEMENT ====================

@router.get("/notifications", response_model=NotificationListResponse)
@limiter.limit("30/minute")
def get_my_notifications(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current user's notifications"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        result = NotificationService.get_user_notifications(
            db, user.id, skip, limit, status
        )
        
        return result
            
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/notifications/counts", response_model=NotificationCountResponse)
@limiter.limit("30/minute")
def get_notification_counts(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get notification counts"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        counts = NotificationService.get_notification_counts(db, user.id)
        return counts
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/notifications/mark-read", response_model=MessageResponse)
@limiter.limit("20/minute")
def mark_notifications_read(
    request: Request,
    data: MarkReadRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Mark notifications as read"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        count = NotificationService.mark_as_read(db, user.id, data.notification_ids)
        
        if data.notification_ids:
            message = f"{count} notification(s) marked as read"
        else:
            message = f"All {count} notifications marked as read"
        
        return MessageResponse(message=message)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/notifications/{notification_id}", response_model=MessageResponse)
@limiter.limit("20/minute")
def delete_notification(
    request: Request,
    notification_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Delete a notification"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        success = NotificationService.delete_notification(db, user.id, notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return MessageResponse(message="Notification deleted successfully")
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/notifications", response_model=MessageResponse)
@limiter.limit("10/minute")
def delete_all_notifications(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Delete all notifications for current user"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        count = NotificationService.delete_all_notifications(db, user.id)
        
        return MessageResponse(message=f"{count} notification(s) deleted")
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/upcoming-classes", response_model=List[ClassResponse])
@limiter.limit("30/minute")
def get_my_upcoming_classes(
    request: Request,
    limit: int = 10,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get upcoming classes for courses the user is enrolled in"""
    try:
        token = credentials.credentials
        user = get_current_user(db, token)
        
        # Get user's enrolled courses
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == user.id,
            Enrollment.status == EnrollmentStatus.ACTIVE
        ).all()
        
        course_ids = [e.course_id for e in enrollments]
        
        if not course_ids:
            return []
        
        # Get upcoming classes from those courses
        upcoming_classes = db.query(Class).join(Topic).filter(
            Topic.course_id.in_(course_ids),
            Class.start_date > datetime.utcnow(),
            Class.status == ClassStatus.SCHEDULED
        ).order_by(Class.start_date.asc()).limit(limit).all()
        
        result = []
        for cls in upcoming_classes:
            result.append({
                "id": cls.id,
                "class_id": cls.class_id,
                "name": cls.name,
                "description": cls.description,
                "meeting_link": cls.meeting_link,
                "meeting_password": cls.meeting_password,
                "start_date": cls.start_date,
                "end_date": cls.end_date,
                "status": cls.status,
                "topic_id": cls.topic_id,
                "topic_title": cls.topic.title,
                "course_id": cls.topic.course_id,
                "course_title": cls.topic.course.title,
                "created_at": cls.created_at
            })
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))