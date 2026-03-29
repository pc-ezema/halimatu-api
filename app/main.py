from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from app.config.limiter import limiter
from app.core.logger import setup_logger
from app.database.database import engine, Base
import logging
# Serve static files for profile pictures
from fastapi.staticfiles import StaticFiles
import os
from app.config.settings import settings

# Setup logger
logger = setup_logger()

# Create database tables
try:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="Halimatu",
    version="1.0.0",
    description="Learning Management System"
)

# Attach limiter to app and add middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Include routers
from app.routes import auth, user  # Fix: import user from routes, not models
app.include_router(auth.router)
app.include_router(user.router)  # Now this will work

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

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")