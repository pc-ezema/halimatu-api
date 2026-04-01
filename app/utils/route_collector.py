from typing import List, Dict
from fastapi import FastAPI
import re

class RouteCollector:
    """Collect and analyze admin routes"""
    
    @staticmethod
    def get_admin_routes(app: FastAPI) -> List[Dict]:
        """Extract all admin routes from the FastAPI app"""
        admin_routes = []
        
        for route in app.routes:
            # Check if route is admin route
            if hasattr(route, 'path') and route.path.startswith('/api/admin'):
                # Skip docs and static routes
                if route.path in ['/api/admin/docs', '/api/admin/redoc', '/api/admin/openapi.json']:
                    continue
                
                # Get route methods
                methods = []
                if hasattr(route, 'methods'):
                    methods = list(route.methods) if route.methods else []
                
                # Get endpoint if available
                endpoint = None
                if hasattr(route, 'endpoint'):
                    endpoint = route.endpoint
                
                admin_routes.append({
                    'path': route.path,
                    'methods': methods,
                    'name': getattr(route, 'name', None),
                    'endpoint': endpoint
                })
        
        return admin_routes
    
    @staticmethod
    def print_route_permissions(app: FastAPI):
        """Print all admin routes and their required permissions"""
        from app.utils.permission_generator import PermissionGenerator
        
        routes = RouteCollector.get_admin_routes(app)
        
        print("\n" + "="*80)
        print("ADMIN ROUTES & PERMISSIONS")
        print("="*80)
        
        for route in routes:
            for method in route['methods']:
                # Pass the endpoint to the permission generator
                permission = PermissionGenerator.generate_permission_name(
                    method, 
                    route['path'], 
                    route['endpoint']  # Pass the endpoint to check decorator metadata
                )
                if permission:
                    print(f"{method:6} {route['path']:50} -> {permission}")
        
        print("="*80 + "\n")