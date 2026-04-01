from functools import wraps

def admin_route(permission_name: str = None):
    """
    Mark a route as requiring admin permission.
    If permission_name is provided, use it; otherwise auto-generate from route.
    """
    def decorator(func):
        # Store permission info in function metadata
        if permission_name:
            func._admin_permission = permission_name
        else:
            func._admin_route = True  # Auto-generate flag
        return func
    return decorator