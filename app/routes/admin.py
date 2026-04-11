from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.schemas.admin import *
from app.schemas.subscription import *
from app.services.admin_service import RoleService, PermissionService, AdminUserService
from app.services.admin_auth_service import authenticate_admin, create_admin_token, get_current_admin, check_permission
from app.config.limiter import limiter
from app.decorators.permissions import admin_route
from app.models.admin import Admin

# Add these imports at the top
from app.schemas.subscription import (
    PlanCreate, PlanUpdate, PlanResponse,
    SubscriptionResponse
)
from app.services.subscription_service import SubscriptionService
from app.models.plan import Plan
from app.models.subscription import Subscription
from datetime import datetime, timedelta

from app.schemas.course import (
    CourseCreate, CourseStatus, CourseUpdate, CourseResponse, CourseDetailResponse,
    TopicCreate, TopicUpdate, TopicResponse,
    ClassCreate, ClassUpdate, ClassResponse,
    MessageResponse
)
from app.services.course_service import CourseService

from app.schemas.course import (
    EnrollmentDetailResponse, 
    EnrollmentListResponse,
    MessageResponse
)
from app.models.enrollment import Enrollment, EnrollmentStatus

from app.schemas.certificate import (
    CertificateResponse, CertificateStatsResponse,
    GenerateCertificateRequest, UpdateCertificateRequest,
    MessageResponse
)
from app.services.certificate_service import CertificateService


router = APIRouter(prefix="/api/admin", tags=["Admin"])
security = HTTPBearer()

# Permission dependency
def require_permission(permission_name: str):
    def permission_dependency(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ):
        token = credentials.credentials
        admin = get_current_admin(db, token)
        
        if not check_permission(admin, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission_name}"
            )
        return admin
    return permission_dependency

# ==================== ADMIN DASHBOARD & STATS ====================
@router.get("/dashboard/stats")
@admin_route("dashboard_view")
def get_admin_dashboard_stats(
    request: Request,
    admin: Admin = Depends(require_permission("dashboard_view")),
    db: Session = Depends(get_db),
):
    """Get complete admin dashboard statistics"""
    try:
        from app.services.subscription_service import SubscriptionService
        
        # User stats
        user_stats = AdminUserService.get_user_stats(db)
        
        # Subscription stats
        subscription_stats = SubscriptionService.get_subscription_stats(db)
        
        # Combine all stats
        return {
            "users": {
                "total": user_stats["total"],
                "active": user_stats["active"],
                "inactive": user_stats["inactive"],
                "verified": user_stats["verified"]
            },
            "subscriptions": {
                "total": subscription_stats["total_subscriptions"],
                "active": subscription_stats["active_subscriptions"],
                "expired": subscription_stats["expired_subscriptions"],
                "cancelled": subscription_stats["cancelled_subscriptions"]
            },
            "revenue": {
                "total": subscription_stats["total_revenue"],
                "mrr": subscription_stats["monthly_recurring_revenue"]
            },
            "plans_breakdown": subscription_stats["plans_breakdown"]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# ==================== ADMIN AUTHENTICATION ====================
@router.post("/login", response_model=AdminTokenResponse)
@limiter.limit("10/minute")
def admin_login(
    request: Request,
    data: AdminLogin,
    db: Session = Depends(get_db),
):
    """Admin login"""
    admin = authenticate_admin(db, data.email, data.password)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_admin_token(admin.id)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": AdminResponse(
            id=admin.id,
            name=admin.name,
            email=admin.email,
            role=RoleResponse(
                id=admin.role.id,
                name=admin.role.name,
                created_at=admin.role.created_at,
                updated_at=admin.role.updated_at
            ) if admin.role else None,
            status=admin.status,
            last_login=admin.last_login,
            created_at=admin.created_at
        )
    }

# ==================== ROLE MANAGEMENT ====================
@router.post("/roles", response_model=RoleResponse)
@admin_route("roles_create")
def create_role(
    request: Request,
    data: RoleCreate,
    admin: Admin = Depends(require_permission("roles_create")),
    db: Session = Depends(get_db),
):
    """Create a new role"""
    try:
        role = RoleService.create_role(db, data.name)
        return RoleResponse(
            id=role.id,
            name=role.name,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/roles", response_model=List[RoleResponse])
@admin_route("roles")
def get_roles(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin: Admin = Depends(require_permission("roles_read")),
    db: Session = Depends(get_db),
):
    """Get all roles"""
    roles = RoleService.get_roles(db, skip, limit)
    return [
        RoleResponse(
            id=role.id,
            name=role.name,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
        for role in roles
    ]

@router.get("/roles/{role_id}", response_model=RoleResponse)
@admin_route("roles_read")
def get_role(
    request: Request,
    role_id: int,
    admin: Admin = Depends(require_permission("roles_read")),
    db: Session = Depends(get_db),
):
    """Get role by ID"""
    try:
        role = RoleService.get_role(db, role_id)
        return RoleResponse(
            id=role.id,
            name=role.name,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/roles/{role_id}", response_model=RoleResponse)
@admin_route("roles_update")
def update_role(
    request: Request,
    role_id: int,
    data: RoleUpdate,
    admin: Admin = Depends(require_permission("roles_update")),
    db: Session = Depends(get_db),
):
    """Update a role"""
    try:
        role = RoleService.update_role(db, role_id, data.name)
        return RoleResponse(
            id=role.id,
            name=role.name,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/roles/{role_id}", response_model=MessageResponse)
@admin_route("roles_delete")
def delete_role(
    request: Request,
    role_id: int,
    admin: Admin = Depends(require_permission("roles_delete")),
    db: Session = Depends(get_db),
):
    """Delete a role"""
    try:
        result = RoleService.delete_role(db, role_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# ==================== PERMISSION MANAGEMENT ====================
@router.get("/permissions", response_model=List[PermissionResponse])
@admin_route("permissions")
def get_permissions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin: Admin = Depends(require_permission("permissions")),
    db: Session = Depends(get_db),
):
    """Get all permissions"""
    permissions = PermissionService.get_permissions(db, skip, limit)
    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            created_at=p.created_at
        )
        for p in permissions
    ]

@router.post("/roles/{role_id}/permissions", response_model=MessageResponse)
@admin_route("permissions_assign")
def assign_permissions_to_role(
    request: Request,
    role_id: int,
    data: AssignPermissionRequest,
    admin: Admin = Depends(require_permission("permissions_assign")),
    db: Session = Depends(get_db),
):
    """Assign permissions to a role"""
    try:
        result = PermissionService.assign_permissions_to_role(db, role_id, data.permission_ids)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/roles/{role_id}/permissions", response_model=List[PermissionResponse])
@admin_route("roles_permissions")
def get_role_permissions(
    request: Request,
    role_id: int,
    admin: Admin = Depends(require_permission("roles_permissions")),
    db: Session = Depends(get_db),
):
    """Get permissions for a role"""
    try:
        permissions = PermissionService.get_role_permissions(db, role_id)
        return [
            PermissionResponse(
                id=p.id,
                name=p.name,
                created_at=p.created_at
            )
            for p in permissions
        ]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# ==================== ADMIN USER MANAGEMENT ====================
@router.post("/admins", response_model=AdminResponse)
@admin_route("admins_create")
def create_admin(
    request: Request,
    data: AdminCreate,
    admin: Admin = Depends(require_permission("admins_create")),
    db: Session = Depends(get_db),
):
    """Create a new admin"""
    try:
        new_admin = AdminUserService.create_admin(
            db, data.name, data.email, data.password, data.role_id
        )
        return AdminResponse(
            id=new_admin.id,
            name=new_admin.name,
            email=new_admin.email,
            role=RoleResponse(
                id=new_admin.role.id,
                name=new_admin.role.name,
                created_at=new_admin.role.created_at,
                updated_at=new_admin.role.updated_at
            ) if new_admin.role else None,
            status=new_admin.status,
            last_login=new_admin.last_login,
            created_at=new_admin.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/admins", response_model=List[AdminResponse])
@admin_route("admins")
def get_admins(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    admin: Admin = Depends(require_permission("admins")),
    db: Session = Depends(get_db),
):
    """Get all admins"""
    admins = AdminUserService.get_admins(db, skip, limit)
    return [
        AdminResponse(
            id=admin_user.id,
            name=admin_user.name,
            email=admin_user.email,
            role=RoleResponse(
                id=admin_user.role.id,
                name=admin_user.role.name,
                created_at=admin_user.role.created_at,
                updated_at=admin_user.role.updated_at
            ) if admin_user.role else None,
            status=admin_user.status,
            last_login=admin_user.last_login,
            created_at=admin_user.created_at
        )
        for admin_user in admins
    ]

@router.get("/admins/me", response_model=AdminResponse)
def get_current_admin_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current admin profile"""
    token = credentials.credentials
    admin = get_current_admin(db, token)
    
    # Return the Pydantic model directly
    return AdminResponse(
        id=admin.id,
        name=admin.name,
        email=admin.email,
        role=RoleResponse(
            id=admin.role.id,
            name=admin.role.name,
            created_at=admin.role.created_at,
            updated_at=admin.role.updated_at
        ) if admin.role else None,
        status=admin.status,
        last_login=admin.last_login,
        created_at=admin.created_at
    )
@router.get("/admins/{admin_id}", response_model=AdminResponse)
@admin_route("admins_read")
def get_admin(
    request: Request,
    admin_id: int,
    admin: Admin = Depends(require_permission("admins_read")),
    db: Session = Depends(get_db),
):
    """Get admin by ID"""
    try:
        admin_user = AdminUserService.get_admin(db, admin_id)
        return AdminResponse(
            id=admin_user.id,
            name=admin_user.name,
            email=admin_user.email,
            role=RoleResponse(
                id=admin_user.role.id,
                name=admin_user.role.name,
                created_at=admin_user.role.created_at,
                updated_at=admin_user.role.updated_at
            ) if admin_user.role else None,
            status=admin_user.status,
            last_login=admin_user.last_login,
            created_at=admin_user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.put("/admins/{admin_id}", response_model=AdminResponse)
@admin_route("admins_update")
def update_admin(
    request: Request,
    admin_id: int,
    data: AdminUpdate,
    admin: Admin = Depends(require_permission("admins_update")),
    db: Session = Depends(get_db),
):
    """Update an admin"""
    try:
        updated_admin = AdminUserService.update_admin(
            db, admin_id, **data.model_dump(exclude_unset=True)
        )
        return AdminResponse(
            id=updated_admin.id,
            name=updated_admin.name,
            email=updated_admin.email,
            role=RoleResponse(
                id=updated_admin.role.id,
                name=updated_admin.role.name,
                created_at=updated_admin.role.created_at,
                updated_at=updated_admin.role.updated_at
            ) if updated_admin.role else None,
            status=updated_admin.status,
            last_login=updated_admin.last_login,
            created_at=updated_admin.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/admins/{admin_id}/change-password", response_model=MessageResponse)
@admin_route("admins_change_password")
def change_admin_password(
    request: Request,
    admin_id: int,
    data: AdminChangePassword,
    admin: Admin = Depends(require_permission("admins_change_password")),
    db: Session = Depends(get_db),
):
    """Change admin password"""
    try:
        # Verify current password
        target_admin = AdminUserService.get_admin(db, admin_id)
        from app.services.admin_auth_service import verify_password
        if not verify_password(data.current_password, target_admin.password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        result = AdminUserService.update_admin_password(db, admin_id, data.new_password)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/admins/{admin_id}/toggle-status", response_model=MessageResponse)
@admin_route("admins_toggle_status")
def toggle_admin_status(
    request: Request,
    admin_id: int,
    admin: Admin = Depends(require_permission("admins_toggle_status")),
    db: Session = Depends(get_db),
):
    """Toggle admin active status"""
    try:
        result = AdminUserService.toggle_admin_status(db, admin_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/admins/{admin_id}", response_model=MessageResponse)
@admin_route("admins_delete")
def delete_admin(
    request: Request,
    admin_id: int,
    admin: Admin = Depends(require_permission("admins_delete")),
    db: Session = Depends(get_db),
):
    """Delete an admin"""
    try:
        result = AdminUserService.delete_admin(db, admin_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
# ==================== REGULAR USER MANAGEMENT ====================
@router.get("/users", response_model=List[UserBasicResponse])
@admin_route("users")
def get_all_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    admin: Admin = Depends(require_permission("users")),
    db: Session = Depends(get_db),
):
    """Get all regular users"""
    try:
        users = AdminUserService.get_all_users(db, skip, limit, search)
        return [
            UserBasicResponse(
                id=user.id,
                student_id=user.student_id,
                first_name=user.first_name,
                middle_name=user.middle_name,
                last_name=user.last_name,
                email=user.email,
                phone_number=user.phone_number,
                status=user.status,
                date_of_birth=user.date_of_birth,
                gender=user.gender,
                country=user.country,
                email_verified_at=user.email_verified_at,
                profile_picture=user.profile_picture,
                created_at=user.created_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/users/stats", response_model=UserStatsResponse)
@admin_route("users_stats")
def get_user_stats(
    request: Request,
    admin: Admin = Depends(require_permission("users_stats")),
    db: Session = Depends(get_db),
):
    """Get user statistics"""
    try:
        stats = AdminUserService.get_user_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/users/{user_id}", response_model=UserDetailResponse)
@admin_route("users_view")
def get_user(
    request: Request,
    user_id: int,
    admin: Admin = Depends(require_permission("users_view")),
    db: Session = Depends(get_db),
):
    """Get user details by ID"""
    try:
        user = AdminUserService.get_user_by_id(db, user_id)
        return UserDetailResponse(
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
            status=user.status,
            profile_picture=user.profile_picture,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            last_login=user.last_login,
            last_ip=user.last_ip,
            password_changed_at=user.password_changed_at,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/users/{user_id}/resend-password", response_model=MessageResponse)
@admin_route("users_resend_password")
def resend_user_password(
    request: Request,
    user_id: int,
    data: ResendPasswordRequest,
    admin: Admin = Depends(require_permission("users_resend_password")),
    db: Session = Depends(get_db),
):
    """Reset user password"""
    try:
        result = AdminUserService.resend_user_password(db, user_id, data.new_password)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/users/{user_id}/toggle-status", response_model=MessageResponse)
@admin_route("users_toggle_status")
def toggle_user_status(
    request: Request,
    user_id: int,
    admin: Admin = Depends(require_permission("users_toggle_status")),
    db: Session = Depends(get_db),
):
    """Toggle user active status"""
    try:
        result = AdminUserService.toggle_user_status(db, user_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/users/{user_id}", response_model=MessageResponse)
@admin_route("users_delete")
def delete_user(
    request: Request,
    user_id: int,
    admin: Admin = Depends(require_permission("users_delete")),
    db: Session = Depends(get_db),
):
    """Delete a user (soft delete)"""
    try:
        result = AdminUserService.delete_user(db, user_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== PLAN MANAGEMENT ====================
@router.post("/plans", response_model=PlanResponse)
@admin_route("plans_create")
def create_plan(
    request: Request,
    data: PlanCreate,
    admin: Admin = Depends(require_permission("plans_create")),
    db: Session = Depends(get_db),
):
    """Create a new subscription plan (Admin only)"""
    try:
        # Check if plan type already exists
        existing = db.query(Plan).filter(Plan.type == data.type).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with type '{data.type}' already exists"
            )
        
        plan = SubscriptionService.create_plan(db, data.model_dump())
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/plans", response_model=List[PlanResponse])
@admin_route("plans")
def admin_get_plans(
    request: Request,
    include_inactive: bool = False,
    admin: Admin = Depends(require_permission("plans")),
    db: Session = Depends(get_db),
):
    """Get all subscription plans (Admin only)"""
    try:
        query = db.query(Plan)
        if not include_inactive:
            query = query.filter(Plan.status == "active")
        plans = query.order_by(Plan.sort_order).all()
        return plans
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/plans/{plan_id}", response_model=PlanResponse)
@admin_route("plans_view")
def admin_get_plan(
    request: Request,
    plan_id: int,
    admin: Admin = Depends(require_permission("plans_view")),
    db: Session = Depends(get_db),
):
    """Get a specific plan by ID (Admin only)"""
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/plans/{plan_id}", response_model=PlanResponse)
@admin_route("plans_update")
def admin_update_plan(
    request: Request,
    plan_id: int,
    data: PlanUpdate,
    admin: Admin = Depends(require_permission("plans_update")),
    db: Session = Depends(get_db),
):
    """Update a subscription plan (Admin only)"""
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)
        
        plan.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(plan)
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/plans/{plan_id}", response_model=MessageResponse)
@admin_route("plans_delete")
def admin_delete_plan(
    request: Request,
    plan_id: int,
    admin: Admin = Depends(require_permission("plans_delete")),
    db: Session = Depends(get_db),
):
    """Delete (deactivate) a subscription plan (Admin only)"""
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        
        # Check if plan has active subscriptions
        active_subs = db.query(Subscription).filter(
            Subscription.plan_id == plan_id,
            Subscription.status == "active",
            Subscription.end_date > datetime.utcnow()
        ).first()
        
        if active_subs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete plan with active subscriptions. Deactivate it instead."
            )
        
        # Soft delete - deactivate
        plan.status = "inactive"
        db.commit()
        
        return MessageResponse(message=f"Plan '{plan.name}' deactivated successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== SUBSCRIPTION MANAGEMENT (Admin) ====================
@router.get("/subscriptions", response_model=List[SubscriptionResponse])
@admin_route("subscriptions")
def admin_get_subscriptions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    admin: Admin = Depends(require_permission("subscriptions")),
    db: Session = Depends(get_db),
):
    """Get all user subscriptions (Admin only)"""
    try:
        query = db.query(Subscription)
        
        if status_filter:
            query = query.filter(Subscription.status == status_filter)
        
        subscriptions = query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/subscriptions/stats")
@admin_route("subscriptions_stats")
def admin_get_subscription_stats(
    request: Request,
    admin: Admin = Depends(require_permission("subscriptions_stats")),
    db: Session = Depends(get_db),
):
    """Get subscription statistics (Admin only)"""
    try:
        from sqlalchemy import func
        
        now = datetime.utcnow()
        
        # Total subscriptions
        total_subscriptions = db.query(Subscription).count()
        
        # Active subscriptions
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.end_date > now
        ).count()
        
        # Expired subscriptions
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.status == "expired"
        ).count()
        
        # Cancelled subscriptions
        cancelled_subscriptions = db.query(Subscription).filter(
            Subscription.status == "cancelled"
        ).count()
        
        # Total revenue
        total_revenue = db.query(func.sum(Subscription.amount_paid)).filter(
            Subscription.status == "active"
        ).scalar() or 0
        
        # Monthly recurring revenue (MRR)
        mrr = db.query(func.sum(Subscription.amount_paid)).filter(
            Subscription.status == "active",
            Subscription.end_date > now,
            Subscription.plan.has(type="monthly")
        ).scalar() or 0
        
        # Subscriptions by plan
        plans_stats = db.query(
            Plan.name,
            Plan.type,
            func.count(Subscription.id).label('count')
        ).outerjoin(Subscription, Plan.id == Subscription.plan_id).filter(
            Subscription.status == "active",
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
                {"name": p.name, "type": p.type, "count": p.count}
                for p in plans_stats
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
@admin_route("subscriptions_view")
def admin_get_subscription(
    request: Request,
    subscription_id: int,
    admin: Admin = Depends(require_permission("subscriptions_view")),
    db: Session = Depends(get_db),
):
    """Get a specific subscription by ID (Admin only)"""
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/subscriptions/{subscription_id}/cancel", response_model=MessageResponse)
@admin_route("subscriptions_update")
def admin_cancel_subscription(
    request: Request,
    subscription_id: int,
    admin: Admin = Depends(require_permission("subscriptions_update")),
    db: Session = Depends(get_db),
):
    """Cancel a user's subscription (Admin only)"""
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
        
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        db.commit()
        
        return MessageResponse(message=f"Subscription {subscription.subscription_id} cancelled successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== USER SUBSCRIPTION MANAGEMENT (Admin) ====================
@router.get("/users/{user_id}/subscriptions", response_model=List[SubscriptionResponse])
@admin_route("users_view_subscriptions")
def admin_get_user_subscriptions(
    request: Request,
    user_id: int,
    admin: Admin = Depends(require_permission("users_view_subscriptions")),
    db: Session = Depends(get_db),
):
    """Get all subscriptions for a specific user (Admin only)"""
    try:
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
        
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== COURSE MANAGEMENT ====================

@router.post("/courses", response_model=CourseResponse)
@admin_route("courses_create")
async def create_course(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    price: int = Form(0),
    image: UploadFile = File(None),
    instructor: str = Form(None),
    duration_months: int = Form(None),
    admin: Admin = Depends(require_permission("courses_create")),
    db: Session = Depends(get_db),
):
    """Create a new course with image upload"""
    try:
        course_data = {
            "title": title,
            "description": description,
            "price": price,
            "instructor": instructor,
            "duration_months": duration_months
        }
        course = CourseService.create_course(db, course_data, image)
        return course
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses", response_model=List[CourseResponse])
@admin_route("courses")
def get_all_courses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    admin: Admin = Depends(require_permission("courses")),
    db: Session = Depends(get_db),
):
    """Get all courses"""
    try:
        courses = CourseService.get_courses(db, skip, limit, status)
        
        # Add stats to each course
        result = []
        for course in courses:
            stats = CourseService.get_course_stats(db, course.id)
            result.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "price": course.price,
                "status": course.status,
                "image": course.image,
                "instructor": course.instructor,
                "duration_months": course.duration_months,
                "total_topics": len(course.topics),
                "total_enrolled": stats["total_enrolled"],
                "created_at": course.created_at,
                "updated_at": course.updated_at
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
@admin_route("courses_view")
def get_course(
    request: Request,
    course_id: int,
    admin: Admin = Depends(require_permission("courses_view")),
    db: Session = Depends(get_db),
):
    """Get course details with topics"""
    try:
        course = CourseService.get_course(db, course_id)
        topics = CourseService.get_topics(db, course_id)
        stats = CourseService.get_course_stats(db, course_id)
        
        return {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "price": course.price,
            "status": course.status,
            "image": course.image,
            "instructor": course.instructor,
            "duration_months": course.duration_months,
            "total_topics": len(topics),
            "total_enrolled": stats["total_enrolled"],
            "created_at": course.created_at,
            "updated_at": course.updated_at,
            "topics": topics
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/courses/{course_id}", response_model=CourseResponse)
@admin_route("courses_update")
async def update_course(
    request: Request,
    course_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    status: Optional[CourseStatus] = Form(None),
    image: UploadFile = File(None),
    instructor: Optional[str] = Form(None),
    duration_months: Optional[int] = Form(None),
    admin: Admin = Depends(require_permission("courses_update")),
    db: Session = Depends(get_db),
):
    """Update a course with optional image upload"""
    try:
        course_data = {}
        if title is not None:
            course_data["title"] = title
        if description is not None:
            course_data["description"] = description
        if price is not None:
            course_data["price"] = price
        if status is not None:
            course_data["status"] = status
        if instructor is not None:
            course_data["instructor"] = instructor
        if duration_months is not None:
            course_data["duration_months"] = duration_months
        
        course = CourseService.update_course(db, course_id, course_data, image)
        return course
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/courses/{course_id}", response_model=MessageResponse)
@admin_route("courses_delete")
def delete_course(
    request: Request,
    course_id: int,
    admin: Admin = Depends(require_permission("courses_delete")),
    db: Session = Depends(get_db),
):
    """Delete a course"""
    try:
        result = CourseService.delete_course(db, course_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== TOPIC MANAGEMENT ====================

@router.post("/courses/{course_id}/topics", response_model=TopicResponse)
@admin_route("topics_create")
def create_topic(
    request: Request,
    course_id: int,
    data: TopicCreate,
    admin: Admin = Depends(require_permission("topics_create")),
    db: Session = Depends(get_db),
):
    """Create a new topic for a course"""
    try:
        topic = CourseService.create_topic(db, course_id, data.title)
        return topic
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses/{course_id}/topics", response_model=List[TopicResponse])
@admin_route("course_topics")
def get_course_topics(
    request: Request,
    course_id: int,
    admin: Admin = Depends(require_permission("course_topics")),
    db: Session = Depends(get_db),
):
    """Get all topics for a course"""
    try:
        topics = CourseService.get_topics(db, course_id)
        return topics
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/topics/{topic_id}", response_model=TopicResponse)
@admin_route("topics_update")
def update_topic(
    request: Request,
    topic_id: int,
    data: TopicUpdate,
    admin: Admin = Depends(require_permission("topics_update")),
    db: Session = Depends(get_db),
):
    """Update a topic"""
    try:
        topic = CourseService.update_topic(db, topic_id, data.title, data.order)
        return topic
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/topics/{topic_id}", response_model=MessageResponse)
@admin_route("topics_delete")
def delete_topic(
    request: Request,
    topic_id: int,
    admin: Admin = Depends(require_permission("topics_delete")),
    db: Session = Depends(get_db),
):
    """Delete a topic"""
    try:
        result = CourseService.delete_topic(db, topic_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== CLASS MANAGEMENT ====================

@router.post("/topics/{topic_id}/classes", response_model=ClassResponse)
@admin_route("classes_create")
def create_class(
    request: Request,
    topic_id: int,
    data: ClassCreate,
    admin: Admin = Depends(require_permission("classes_create")),
    db: Session = Depends(get_db),
):
    """Create a new class for a topic"""
    try:
        class_obj = CourseService.create_class(db, topic_id, data.model_dump())
        return class_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/topics/{topic_id}/classes", response_model=List[ClassResponse])
@admin_route("classes_view")
def get_topic_classes(
    request: Request,
    topic_id: int,
    admin: Admin = Depends(require_permission("classes_view")),
    db: Session = Depends(get_db),
):
    """Get all classes for a topic"""
    try:
        classes = CourseService.get_classes(db, topic_id)
        return classes
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/classes/{class_id}", response_model=ClassResponse)
@admin_route("classes_update")
def update_class(
    request: Request,
    class_id: int,
    data: ClassUpdate,
    admin: Admin = Depends(require_permission("classes_update")),
    db: Session = Depends(get_db),
):
    """Update a class"""
    try:
        class_obj = CourseService.update_class(db, class_id, data.model_dump(exclude_unset=True))
        return class_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/classes/{class_id}", response_model=MessageResponse)
@admin_route("classes_delete")
def delete_class(
    request: Request,
    class_id: int,
    admin: Admin = Depends(require_permission("classes_delete")),
    db: Session = Depends(get_db),
):
    """Delete a class"""
    try:
        result = CourseService.delete_class(db, class_id)
        return MessageResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== ENROLLMENT MANAGEMENT ====================

@router.get("/enrollments", response_model=EnrollmentListResponse)
@admin_route("enrollments")
def get_all_enrollments(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    course_id: int = None,
    user_id: int = None,
    search: str = None,
    admin: Admin = Depends(require_permission("enrollments")),
    db: Session = Depends(get_db),
):
    """
    Get all enrollments with user and course information
    """
    try:
        result = CourseService.get_all_enrollments_with_details(
            db, skip, limit, status, course_id, user_id, search
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/enrollments/{enrollment_id}", response_model=EnrollmentDetailResponse)
@admin_route("enrollments_view")
def get_enrollment_details(
    request: Request,
    enrollment_id: int,
    admin: Admin = Depends(require_permission("enrollments_view")),
    db: Session = Depends(get_db),
):
    """
    Get detailed enrollment information
    """
    try:
        enrollment = CourseService.get_enrollment_by_id_with_details(db, enrollment_id)
        return enrollment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/enrollments/stats/summary")
@admin_route("enrollments_stats")
def get_enrollment_summary(
    request: Request,
    admin: Admin = Depends(require_permission("enrollments_stats")),
    db: Session = Depends(get_db),
):
    """
    Get enrollment summary statistics
    """
    try:
        from sqlalchemy import func
        
        total_enrollments = db.query(Enrollment).count()
        active_enrollments = db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.ACTIVE
        ).count()
        completed_enrollments = db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.COMPLETED
        ).count()
        dropped_enrollments = db.query(Enrollment).filter(
            Enrollment.status == EnrollmentStatus.DROPPED
        ).count()
        
        total_users_enrolled = db.query(Enrollment.user_id).distinct().count()
        total_courses_with_enrollments = db.query(Enrollment.course_id).distinct().count()
        
        avg_progress = db.query(func.avg(Enrollment.progress)).scalar() or 0
        
        recent_enrollments = CourseService.get_recent_enrollments(db, 5)
        
        return {
            "total_enrollments": total_enrollments,
            "active_enrollments": active_enrollments,
            "completed_enrollments": completed_enrollments,
            "dropped_enrollments": dropped_enrollments,
            "total_users_enrolled": total_users_enrolled,
            "total_courses_with_enrollments": total_courses_with_enrollments,
            "average_progress": round(avg_progress, 2),
            "recent_enrollments": recent_enrollments
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/enrollments/stats/by-course", response_model=List[dict])
@admin_route("enrollments_stats_course")
def get_enrollment_stats_by_course(
    request: Request,
    course_id: int = None,
    admin: Admin = Depends(require_permission("enrollments_stats_course")),
    db: Session = Depends(get_db),
):
    """
    Get enrollment statistics grouped by course
    """
    try:
        stats = CourseService.get_enrollment_stats_by_course(db, course_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses/{course_id}/enrollments", response_model=EnrollmentListResponse)
@admin_route("courses_enrollments")
def get_course_enrollments(
    request: Request,
    course_id: int,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    admin: Admin = Depends(require_permission("courses_enrollments")),
    db: Session = Depends(get_db),
):
    """
    Get enrollments for a specific course with user information
    """
    try:
        result = CourseService.get_all_enrollments_with_details(
            db, skip, limit, status, course_id=course_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/users/{user_id}/enrollments", response_model=EnrollmentListResponse)
@admin_route("users_view_enrollments")
def get_user_enrollments(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    admin: Admin = Depends(require_permission("users_view_enrollments")),
    db: Session = Depends(get_db),
):
    """
    Get enrollments for a specific user with course information
    """
    try:
        result = CourseService.get_all_enrollments_with_details(
            db, skip, limit, status, user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# ==================== CERTIFICATE MANAGEMENT ====================

@router.post("/certificates/refresh-all", response_model=dict)
@admin_route("certificates_create")
def refresh_all_certificates(
    request: Request,
    admin: Admin = Depends(require_permission("certificates_create")),
    db: Session = Depends(get_db),
):
    """Refresh all certificates based on current enrollments"""
    try:
        result = CertificateService.refresh_all_certificates(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates", response_model=dict)
@admin_route("certificates")
def get_all_certificates(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    search: str = None,
    course_id: int = None,
    user_id: int = None,
    admin: Admin = Depends(require_permission("certificates")),
    db: Session = Depends(get_db),
):
    """Get all certificates with filters"""
    try:
        result = CertificateService.get_all_certificates(
            db, skip, limit, status, search, course_id, user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/stats", response_model=CertificateStatsResponse)
@admin_route("certificates_stats")
def get_certificate_stats(
    request: Request,
    admin: Admin = Depends(require_permission("certificates_stats")),
    db: Session = Depends(get_db),
):
    """Get certificate statistics for dashboard"""
    try:
        stats = CertificateService.get_certificate_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/pending", response_model=dict)
@admin_route("certificates_pending")
def get_pending_certificates(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    admin: Admin = Depends(require_permission("certificates_pending")),
    db: Session = Depends(get_db),
):
    """Get all pending certificates (ready for approval)"""
    try:
        result = CertificateService.get_all_certificates(db, skip, limit, status="pending")
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/issued", response_model=dict)
@admin_route("certificates_issued")
def get_issued_certificates(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    admin: Admin = Depends(require_permission("certificates_issued")),
    db: Session = Depends(get_db),
):
    """Get all issued certificates"""
    try:
        result = CertificateService.get_all_certificates(db, skip, limit, status="issued")
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/revoked", response_model=dict)
@admin_route("certificates_revoked")
def get_revoked_certificates(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    admin: Admin = Depends(require_permission("certificates_revoked")),
    db: Session = Depends(get_db),
):
    """Get all revoked certificates"""
    try:
        result = CertificateService.get_all_certificates(db, skip, limit, status="revoked")
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/{certificate_id}", response_model=CertificateResponse)
@admin_route("certificates_view")
def get_certificate_details(
    request: Request,
    certificate_id: int,
    admin: Admin = Depends(require_permission("certificates_view")),
    db: Session = Depends(get_db),
):
    """Get certificate details by ID"""
    try:
        certificate = CertificateService.get_certificate_by_id(db, certificate_id)
        # Get enrollment progress
        progress = certificate.enrollment.progress if certificate.enrollment else 0
        
        return {
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "certificate_number": certificate.certificate_number,
            "user_id": certificate.user_id,
            "user_name": certificate.user.get_full_name(),
            "user_email": certificate.user.email,
            "user_student_id": certificate.user.student_id,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "course_image": certificate.course.image,
            "full_name": certificate.full_name,
            "grade": certificate.grade,
            "duration": certificate.duration,
            "progress": progress,
            "status": certificate.status,
            "issue_date": certificate.issue_date,
            "created_at": certificate.created_at,
            "updated_at": certificate.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/certificates/{certificate_id}/issue", response_model=CertificateResponse)
@admin_route("certificates_update_issue")
def issue_certificate(
    request: Request,
    certificate_id: int,
    admin: Admin = Depends(require_permission("certificates_update_issue")),
    db: Session = Depends(get_db),
):
    """Issue a pending certificate"""
    try:
        certificate = CertificateService.issue_certificate(db, certificate_id)
        return {
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "certificate_number": certificate.certificate_number,
            "user_id": certificate.user_id,
            "user_name": certificate.user.get_full_name(),
            "user_email": certificate.user.email,
            "user_student_id": certificate.user.student_id,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "course_image": certificate.course.image,
            "full_name": certificate.full_name,
            "grade": certificate.grade,
            "duration": certificate.duration,
            "status": certificate.status,
            "issue_date": certificate.issue_date,
            "created_at": certificate.created_at,
            "updated_at": certificate.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/certificates/{certificate_id}/revoke", response_model=CertificateResponse)
@admin_route("certificates_update_revoke")
def revoke_certificate(
    request: Request,
    certificate_id: int,
    admin: Admin = Depends(require_permission("certificates_update_revoke")),
    db: Session = Depends(get_db),
):
    """Revoke an issued certificate"""
    try:
        certificate = CertificateService.revoke_certificate(db, certificate_id)
        return {
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "certificate_number": certificate.certificate_number,
            "user_id": certificate.user_id,
            "user_name": certificate.user.get_full_name(),
            "user_email": certificate.user.email,
            "user_student_id": certificate.user.student_id,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "course_image": certificate.course.image,
            "full_name": certificate.full_name,
            "grade": certificate.grade,
            "duration": certificate.duration,
            "status": certificate.status,
            "issue_date": certificate.issue_date,
            "created_at": certificate.created_at,
            "updated_at": certificate.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/certificates/bulk-issue", response_model=MessageResponse)
@admin_route("certificates_bulk_issue")
def bulk_issue_certificates(
    request: Request,
    certificate_ids: List[int],
    admin: Admin = Depends(require_permission("certificates_bulk_issue")),
    db: Session = Depends(get_db),
):
    """Bulk issue multiple certificates"""
    try:
        issued_count = 0
        failed_ids = []
        
        for cert_id in certificate_ids:
            try:
                CertificateService.issue_certificate(db, cert_id)
                issued_count += 1
            except Exception as e:
                failed_ids.append({"id": cert_id, "error": str(e)})
        
        return MessageResponse(
            message=f"Issued {issued_count} certificates. Failed: {len(failed_ids)}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/certificates/bulk-revoke", response_model=MessageResponse)
@admin_route("certificates_bulk_revoke")
def bulk_revoke_certificates(
    request: Request,
    certificate_ids: List[int],
    admin: Admin = Depends(require_permission("certificates_bulk_revoke")),
    db: Session = Depends(get_db),
):
    """Bulk revoke multiple certificates"""
    try:
        revoked_count = 0
        failed_ids = []
        
        for cert_id in certificate_ids:
            try:
                CertificateService.revoke_certificate(db, cert_id)
                revoked_count += 1
            except Exception as e:
                failed_ids.append({"id": cert_id, "error": str(e)})
        
        return MessageResponse(
            message=f"Revoked {revoked_count} certificates. Failed: {len(failed_ids)}"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/certificates/{certificate_id}", response_model=MessageResponse)
@admin_route("certificates_delete")
def delete_certificate(
    request: Request,
    certificate_id: int,
    admin: Admin = Depends(require_permission("certificates_delete")),
    db: Session = Depends(get_db),
):
    """Delete a certificate (permanent)"""
    try:
        CertificateService.delete_certificate(db, certificate_id)
        return MessageResponse(message="Certificate deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/courses/{course_id}/certificates", response_model=dict)
@admin_route("certificates_course_view")
def get_course_certificates(
    request: Request,
    course_id: int,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    admin: Admin = Depends(require_permission("certificates_course_view")),
    db: Session = Depends(get_db),
):
    """Get all certificates for a specific course"""
    try:
        result = CertificateService.get_all_certificates(
            db, skip, limit, status, course_id=course_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/users/{user_id}/certificates", response_model=dict)
@admin_route("users_certificates_view")
def get_user_certificates_admin(
    request: Request,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    admin: Admin = Depends(require_permission("users_certificates_view")),
    db: Session = Depends(get_db),
):
    """Get all certificates for a specific user"""
    try:
        result = CertificateService.get_all_certificates(
            db, skip, limit, status, user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/certificates/export/csv")
@admin_route("certificates_export")
def export_certificates_csv(
    request: Request,
    status: str = None,
    course_id: int = None,
    admin: Admin = Depends(require_permission("certificates_export")),
    db: Session = Depends(get_db),
):
    """Export certificates to CSV"""
    try:
        import csv
        from fastapi.responses import StreamingResponse
        import io
        
        # Get certificates
        result = CertificateService.get_all_certificates(
            db, skip=0, limit=10000, status=status, course_id=course_id
        )
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Certificate Number", "Student Name", "Student Email", 
            "Student ID", "Course Title", "Grade", "Progress", "Status", 
            "Issue Date", "Created At"
        ])
        
        # Write data
        for cert in result["certificates"]:
            writer.writerow([
                cert["certificate_number"],
                cert["user_name"],
                cert["user_email"],
                cert.get("user_student_id", ""),
                cert["course_title"],
                cert.get("grade", ""),
                cert.get("progress", 0),
                cert["status"],
                cert.get("issue_date", ""),
                cert["created_at"]
            ])
        
        # Return CSV file
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=certificates_export.csv"
        return response
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))