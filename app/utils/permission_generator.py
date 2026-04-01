import re
from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
from app.models.permission import Permission
from app.models.role import Role

class PermissionGenerator:
    """Automatically generate permissions from admin routes"""
    
    @classmethod
    def generate_permission_name(cls, method: str, path: str, endpoint=None) -> Optional[str]:
        """Generate permission name from HTTP method and path or from decorator"""
        
        # Check if endpoint has custom permission from decorator
        if endpoint:
            # Check for custom permission from @admin_route("permission_name")
            if hasattr(endpoint, '_admin_permission'):
                return endpoint._admin_permission
            
            # Check for auto-generated flag
            if hasattr(endpoint, '_admin_route'):
                # Auto-generate from path
                pass  # Continue to path-based generation
        
        # Remove trailing slash
        path = path.rstrip('/')
        
        # Skip login endpoint
        if path.endswith('/login'):
            return None
        
        # Get the resource from path
        parts = path.strip('/').split('/')
        
        # Map HTTP methods to actions
        action_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        
        # For admin routes, the pattern is /api/admin/{resource}
        if len(parts) >= 3:
            resource = parts[2]  # Get the main resource (skip 'api' and 'admin')
            action = action_map.get(method, 'manage')
            
            # Check if there's a specific action in the path
            if len(parts) > 3:
                specific_action = parts[3]
                # Skip IDs (numbers) and 'me'
                if not specific_action.isdigit() and specific_action not in ['me']:
                    return f"{resource}_{specific_action}"
            
            return f"{resource}_{action}"
        
        return None
    
    @classmethod
    def get_admin_routes_with_permissions(cls, app) -> List[Dict]:
        """Get all admin routes that need permissions"""
        routes_with_permissions = []
        
        for route in app.routes:
            # Check if it's an admin route
            if hasattr(route, 'path') and '/api/admin' in route.path:
                # Skip login and docs routes
                if route.path.endswith('/login') or route.path in ['/api/admin/docs', '/api/admin/redoc', '/api/admin/openapi.json']:
                    continue
                
                methods = []
                if hasattr(route, 'methods'):
                    methods = list(route.methods) if route.methods else []
                
                endpoint = getattr(route, 'endpoint', None)
                
                for method in methods:
                    # Check if endpoint has permission info from decorator
                    perm_name = None
                    
                    if endpoint:
                        # Check for custom permission
                        if hasattr(endpoint, '_admin_permission'):
                            perm_name = endpoint._admin_permission
                        # Check for auto-generated flag
                        elif hasattr(endpoint, '_admin_route'):
                            perm_name = cls.generate_permission_name(method, route.path, endpoint)
                    
                    # If no decorator, skip (don't create permission)
                    if perm_name:
                        routes_with_permissions.append({
                            'path': route.path,
                            'method': method,
                            'permission': perm_name,
                            'endpoint': endpoint
                        })
        
        return routes_with_permissions
    
    @classmethod
    def sync_permissions(cls, db: Session, app) -> Dict:
        """Synchronize database permissions with route definitions"""
        created = []
        existing = []
        
        # Get all admin routes that need permissions
        routes = cls.get_admin_routes_with_permissions(app)
        
        # Get all unique permission names from routes
        required_permissions = {route['permission'] for route in routes}
        
        # Sync with database
        for perm_name in required_permissions:
            existing_perm = db.query(Permission).filter(Permission.name == perm_name).first()
            if not existing_perm:
                # Parse resource and action from permission name
                parts = perm_name.split('_')
                resource = parts[0] if len(parts) > 0 else None
                action = parts[1] if len(parts) > 1 else None
                
                permission = Permission(
                    name=perm_name,
                    resource=resource,
                    action=action,
                    description=f"Can {action} {resource}" if resource and action else perm_name
                )
                db.add(permission)
                created.append(perm_name)
            else:
                existing.append(perm_name)
        
        db.commit()
        
        return {
            'created': created,
            'existing': existing,
            'total': len(required_permissions),
            'routes': routes
        }