from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from jose import jwt
from app.config.settings import settings
from app.database.database import SessionLocal
from app.models.admin import Admin
from app.services.admin_auth_service import check_permission
from app.utils.permission_generator import PermissionGenerator
import re

class AdminPermissionMiddleware(BaseHTTPMiddleware):
    """Middleware to check admin permissions for admin routes"""
    
    ADMIN_PREFIX = "/admin"
    PUBLIC_ROUTES = [
        r'/admin/login',
        r'/admin/docs',
        r'/admin/redoc',
        r'/admin/openapi.json',
        r'/admin/me',
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is an admin route
        if not request.url.path.startswith(self.ADMIN_PREFIX):
            return await call_next(request)
        
        # Check if route is public
        for public_route in self.PUBLIC_ROUTES:
            if re.match(public_route, request.url.path):
                return await call_next(request)
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authentication token"
            )
        
        token = auth_header.replace('Bearer ', '')
        
        # Verify token and get admin
        db = SessionLocal()
        try:
            # Decode token
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
                if payload.get("type") != "admin":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token type"
                    )
                admin_id = int(payload.get("sub"))
            except jwt.JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            # Get admin from database
            admin = db.query(Admin).filter(
                Admin.id == admin_id,
                Admin.status == "active"
            ).first()
            
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Admin not found or inactive"
                )
            
            # Check if this route requires permission (has @admin_route decorator)
            # We need to check if the route endpoint has the admin_route attribute
            from fastapi import FastAPI
            from app.main import app
            
            for route in app.routes:
                if route.path == request.url.path and request.method in route.methods:
                    if hasattr(route, 'endpoint'):
                        endpoint = route.endpoint
                        if hasattr(endpoint, '_admin_route') or hasattr(endpoint, '_admin_permission'):
                            # This route requires permission
                            required_permission = None
                            
                            if hasattr(endpoint, '_admin_permission'):
                                required_permission = endpoint._admin_permission
                            else:
                                # Auto-generate permission
                                required_permission = PermissionGenerator.generate_permission_name(
                                    request.method, 
                                    request.url.path
                                )
                            
                            # Check permission (superadmin bypass)
                            if admin.role and admin.role.name == "superadmin":
                                pass  # Superadmin can access everything
                            elif not check_permission(admin, required_permission):
                                raise HTTPException(
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Permission denied. Required: {required_permission}"
                                )
                    break
            
            # Add admin to request state
            request.state.admin = admin
            
        finally:
            db.close()
        
        return await call_next(request)