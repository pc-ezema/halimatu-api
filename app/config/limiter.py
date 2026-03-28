from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Optional: Custom error response for rate limit
def rate_limit_exceeded_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=429,
        content={"message": "Rate limit exceeded. Try again later."}
    )