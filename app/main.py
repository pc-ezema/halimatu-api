from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.config.limiter import limiter
from app.core.logger import setup_logger
from app.database.database import engine, Base
from app.routes import auth, user, admin
# Serve static files for profile pictures
from fastapi.staticfiles import StaticFiles
import os
from app.config.settings import settings
from app.models.permission import Permission
from app.models.role import Role
# from app.schemas import admin
from app.utils.permission_generator import PermissionGenerator
from app.utils.route_collector import RouteCollector

# Setup logger
logger = setup_logger()

app = FastAPI(
    title="Halimatu",
    version="1.0.0",
    description="Learning Management System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach limiter to app and add middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Include routers
app.include_router(auth.router)
app.include_router(user.router) 
app.include_router(admin.router)

# Create storage directory if it doesn't exist
os.makedirs(settings.storage_path, exist_ok=True)

# Mount static files for profile pictures
app.mount("/uploads", StaticFiles(directory=settings.storage_path), name="uploads")

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to Halimatu API"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

# Custom validation error handler - makes validation errors readable
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and return clean messages"""
    errors = []
    
    for error in exc.errors():
        # Get the field name
        field = error["loc"][-1] if error["loc"] else "unknown"
        
        # Get the error message
        msg = error.get("msg", "Invalid value")
        
        # Clean up the message
        if "value_error" in msg:
            # Extract custom error message if it exists
            if "ctx" in error and "error" in error["ctx"]:
                msg = str(error["ctx"]["error"])
            else:
                msg = msg.replace("Value error, ", "")
        
        # Create user-friendly error message
        errors.append({
            "field": field,
            "message": msg
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "errors": errors
        }
    )

# Handle HTTPExceptions globally
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

# Handle rate limit errors
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    logger.warning(f"Rate limit exceeded: {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests. Please try again later."}
    )

# Handle general exceptions
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred. Please try again later."}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up...")
    # Create database tables
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    from app.database.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Step 1: Sync permissions from routes
        result = PermissionGenerator.sync_permissions(db, app)
        
        logger.info(f"Permissions synced: Created {len(result['created'])}, "
                   f"Existing {len(result['existing'])}, "
                   f"Total {result['total']}")
        
        # Step 2: Get superadmin role
        superadmin_role = db.query(Role).filter(Role.name == "superadmin").first()
        
        if superadmin_role:
            # Step 3: Get all permissions
            all_permissions = db.query(Permission).all()
            
            # Step 4: Assign ALL permissions to superadmin role
            if all_permissions:
                # Check if already assigned
                current_perms = set(p.id for p in superadmin_role.permissions)
                new_perms = [p for p in all_permissions if p.id not in current_perms]
                
                if new_perms:
                    superadmin_role.permissions.extend(new_perms)
                    db.commit()
                    logger.info(f"✅ Assigned {len(new_perms)} new permissions to superadmin role")
                else:
                    logger.info(f"✅ Superadmin already has all {len(all_permissions)} permissions")
            else:
                logger.warning("No permissions found to assign")
        else:
            logger.warning("Superadmin role not found. Please run seed_admin.py first.")
        
        # Print route permissions in debug mode
        if settings.debug:
            RouteCollector.print_route_permissions(app)
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    finally:
        db.close()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")