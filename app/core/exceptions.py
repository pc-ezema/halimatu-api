from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions"""
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail}
        )
    
    # Log the error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return generic error response
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred"}
    )
