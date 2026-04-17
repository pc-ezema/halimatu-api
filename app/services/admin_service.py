from datetime import datetime
from operator import or_
from typing import List, Optional, Dict
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.models.role import Role
from app.models.permission import Permission
from app.services.admin_auth_service import hash_password, verify_password
from app.models.user import User
from app.utils.password_generator import PasswordGenerator
from app.services.email_service import send_new_password_email

class AdminService:
    """Service for admin-related operations"""
    
    @staticmethod
    def update_admin_profile(db: Session, admin_id: int, profile_data: dict) -> Admin:
        """Update admin profile"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        # Check if email already exists for another admin
        if 'email' in profile_data and profile_data['email'] != admin.email:
            existing = db.query(Admin).filter(
                Admin.email == profile_data['email'],
                Admin.id != admin_id
            ).first()
            if existing:
                raise ValueError("Email already in use by another admin")
        
        for key, value in profile_data.items():
            if value is not None:
                setattr(admin, key, value)
        
        admin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admin)
        return admin

    @staticmethod
    def change_admin_password(db: Session, admin_id: int, current_password: str, new_password: str) -> Dict:
        """Change admin password"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        # Verify current password
        if not verify_password(current_password, admin.password):
            raise ValueError("Current password is incorrect")
        
        # Check if new password is same as old
        if verify_password(new_password, admin.password):
            raise ValueError("New password cannot be the same as current password")
        
        # Update password
        admin.password = hash_password(new_password)
        admin.updated_at = datetime.utcnow()
        
        # Revoke all refresh tokens for this admin (optional, for security)
        from app.models.refresh_token import RefreshToken
        # Note: You may need a separate refresh token table for admins
        # or use the same table with a type filter
        
        db.commit()
        
        return {"message": "Password changed successfully"}

    @staticmethod
    def logout_admin(db: Session, admin_id: int, token: str) -> Dict:
        """Logout admin by revoking token"""
        # If you have a token blacklist or refresh token system
        # You can revoke the specific token
        from app.models.refresh_token import RefreshToken
        
        # Revoke the specific refresh token
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.user_id == admin_id,
            RefreshToken.is_revoked == False
        ).first()
        
        if token_record:
            token_record.is_revoked = True
            db.commit()
            return {"message": "Logged out successfully"}
        
        return {"message": "Session already expired"}

    @staticmethod
    def logout_all_admin_sessions(db: Session, admin_id: int) -> Dict:
        """Logout admin from all devices"""
        from app.models.refresh_token import RefreshToken
        
        # Revoke all refresh tokens for this admin
        db.query(RefreshToken).filter(
            RefreshToken.user_id == admin_id,
            RefreshToken.is_revoked == False
        ).update({"is_revoked": True})
        
        db.commit()
        return {"message": "Logged out from all devices successfully"}

class RoleService:
    """Service for role management"""
    
    @staticmethod
    def create_role(db: Session, name: str) -> Role:
        """Create a new role"""
        existing = db.query(Role).filter(Role.name == name).first()
        if existing:
            raise ValueError("Role already exists")
        
        role = Role(name=name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        """Get all roles"""
        return db.query(Role).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_role(db: Session, role_id: int) -> Role:
        """Get role by ID"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        return role
    
    @staticmethod
    def update_role(db: Session, role_id: int, name: str = None) -> Role:
        """Update role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        
        if name:
            # Check if name already exists
            existing = db.query(Role).filter(Role.name == name, Role.id != role_id).first()
            if existing:
                raise ValueError("Role name already exists")
            role.name = name
        
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        return role
    
    @staticmethod
    def delete_role(db: Session, role_id: int) -> Dict:
        """Delete role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        
        # Don't delete superadmin role
        if role.name == "superadmin":
            raise ValueError("Cannot delete superadmin role")
        
        # Check if role has admins assigned
        if role.admins:
            raise ValueError(f"Cannot delete role with {len(role.admins)} admins assigned")
        
        db.delete(role)
        db.commit()
        return {"message": "Role deleted successfully"}

class PermissionService:
    """Service for permission management"""
    
    @staticmethod
    def create_permission(db: Session, name: str, resource: str = None, action: str = None, description: str = None) -> Permission:
        """Create a new permission"""
        existing = db.query(Permission).filter(Permission.name == name).first()
        if existing:
            raise ValueError("Permission already exists")
        
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Get all permissions"""
        return db.query(Permission).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_permission(db: Session, permission_id: int) -> Permission:
        """Get permission by ID"""
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            raise ValueError("Permission not found")
        return permission
    
    @staticmethod
    def assign_permissions_to_role(db: Session, role_id: int, permission_ids: List[int]) -> Dict:
        """Assign permissions to a role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        
        permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
        role.permissions = permissions
        db.commit()
        
        return {"message": f"Assigned {len(permissions)} permissions to role {role.name}"}
    
    @staticmethod
    def get_role_permissions(db: Session, role_id: int) -> List[Permission]:
        """Get permissions for a role"""
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError("Role not found")
        return role.permissions

class AdminUserService:
    """Service for admin user management"""
    
    @staticmethod
    def create_admin(db: Session, name: str, email: str, password: str, role_id: int = None) -> Admin:
        """Create a new admin"""
        # Check if email exists
        existing = db.query(Admin).filter(Admin.email == email).first()
        if existing:
            raise ValueError("Admin with this email already exists")
        
        # Check if role exists
        if role_id:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ValueError("Role not found")
        
        admin = Admin(
            name=name,
            email=email,
            password=hash_password(password),
            role_id=role_id,
            status="active"
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    @staticmethod
    def get_admins(db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
        """Get all admins"""
        return db.query(Admin).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_admin(db: Session, admin_id: int) -> Admin:
        """Get admin by ID"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        return admin
    
    @staticmethod
    def get_admin_by_email(db: Session, email: str) -> Admin:
        """Get admin by email"""
        admin = db.query(Admin).filter(Admin.email == email).first()
        if not admin:
            raise ValueError("Admin not found")
        return admin
    
    @staticmethod
    def update_admin(db: Session, admin_id: int, **kwargs) -> Admin:
        """Update admin"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        # Don't allow updating email to existing one
        if 'email' in kwargs:
            existing = db.query(Admin).filter(Admin.email == kwargs['email'], Admin.id != admin_id).first()
            if existing:
                raise ValueError("Email already in use")
        
        for key, value in kwargs.items():
            if value is not None and key != 'password':
                setattr(admin, key, value)
        
        admin.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(admin)
        return admin
    
    @staticmethod
    def update_admin_password(db: Session, admin_id: int, new_password: str) -> Dict:
        """Update admin password"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        admin.password = hash_password(new_password)
        admin.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Password updated successfully"}
    
    @staticmethod
    def delete_admin(db: Session, admin_id: int) -> Dict:
        """Delete admin"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        # Don't delete the last superadmin
        if admin.role and admin.role.name == "superadmin":
            superadmin_count = db.query(Admin).filter(Admin.role.has(name="superadmin")).count()
            if superadmin_count <= 1:
                raise ValueError("Cannot delete the last superadmin")
        
        db.delete(admin)
        db.commit()
        return {"message": "Admin deleted successfully"}
    
    @staticmethod
    def toggle_admin_status(db: Session, admin_id: int) -> Dict:
        """Toggle admin active status"""
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin:
            raise ValueError("Admin not found")
        
        admin.status = "active" if admin.status == "inactive" else "inactive"
        admin.updated_at = datetime.utcnow()
        db.commit()
        
        status = "activated" if admin.status == "active" else "deactivated"
        return {"message": f"Admin {status} successfully"}

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100, search: str = None) -> List[User]:
        """Get all regular users with optional search"""
        query = db.query(User).filter(User.deleted_at.is_(None))
        
        if search:
            query = query.filter(
                or_(
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.student_id.ilike(f"%{search}%")
                )
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Get user by ID"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        return user
    
    @staticmethod
    def resend_user_password(db: Session, user_id: int, new_password: str) -> Dict:
        """Reset user password and send email"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Generate a random password
        new_password = PasswordGenerator.generate_random_password()
        
        # Update password
        user.hashed_password = hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        
        # Revoke all refresh tokens
        from app.models.refresh_token import RefreshToken
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).update({"is_revoked": True})
        
        db.commit()
        
        # Send email with new password
        BackgroundTasks.add_task(send_new_password_email, user.email, new_password, user.get_full_name())

        return {
            "message": f"Password reset successfully for {user.email}",
            "new_password": new_password  # Remove this in production
        }
    
    @staticmethod
    def toggle_user_status(db: Session, user_id: int) -> Dict:
        """Toggle user active status"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        user.status = "active" if user.status == "inactive" else "inactive"
        user.updated_at = datetime.utcnow()
        db.commit()
        
        status = "activated" if user.status == "active" else "deactivated"
        return {"message": f"User {status} successfully"}
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> Dict:
        """Soft delete a user"""
        user = db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        # Soft delete
        user.deleted_at = datetime.utcnow()
        user.status = "inactive"
        db.commit()
        
        return {"message": f"User {user.email} deleted successfully"}
    
    @staticmethod
    def get_user_stats(db: Session) -> Dict:
        """Get user statistics"""
        total_users = db.query(User).filter(User.deleted_at.is_(None)).count()
        active_users = db.query(User).filter(
            User.status == "active",
            User.deleted_at.is_(None)
        ).count()
        inactive_users = db.query(User).filter(
            User.status == "inactive",
            User.deleted_at.is_(None)
        ).count()
        verified_users = db.query(User).filter(
            User.email_verified_at.isnot(None),
            User.deleted_at.is_(None)
        ).count()
        
        return {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
            "verified": verified_users
        }