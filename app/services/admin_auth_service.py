from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.admin import Admin
from app.models.role import Role
from app.models.permission import Permission
from app.config.settings import settings

# Configure Argon2 - Most secure password hashing
pwd_context = CryptContext(
    schemes=["argon2"],  # Use Argon2 as the primary scheme
    deprecated="auto",
    # Argon2 configuration for optimal security vs performance
    argon2__rounds=2,           # Number of iterations (adjust based on your server)
    argon2__memory_cost=1024,   # Memory cost in KB (1024 = 1GB)
    argon2__parallelism=2,      # Number of parallel threads
    argon2__hash_len=32,        # Length of the hash in bytes
    argon2__salt_len=16         # Length of the salt in bytes
)

def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return pwd_context.verify(plain_password, hashed_password)

def create_admin_token(admin_id: int) -> str:
    """Create JWT token for admin"""
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": str(admin_id),
        "exp": expire,
        "type": "admin"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def authenticate_admin(db: Session, email: str, password: str) -> Optional[Admin]:
    """Authenticate admin user"""
    admin = db.query(Admin).filter(
        Admin.email == email,
        Admin.status == "active"
    ).first()
    
    if not admin:
        return None
    
    if not verify_password(password, admin.password):
        return None
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    return admin

def get_current_admin(db: Session, token: str) -> Admin:
    """Get current admin from token"""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        if payload.get("type") != "admin":
            raise ValueError("Invalid token type")
        
        admin_id = int(payload.get("sub"))
        admin = db.query(Admin).filter(
            Admin.id == admin_id,
            Admin.status == "active"
        ).first()
        
        if not admin:
            raise ValueError("Admin not found")
        
        return admin
        
    except jwt.JWTError:
        raise ValueError("Invalid token")

def check_permission(admin: Admin, permission_name: str) -> bool:
    """Check if admin has a specific permission"""
    if not admin.role:
        return False
    
    for permission in admin.role.permissions:
        if permission.name == permission_name:
            return True
    
    return False