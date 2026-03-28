from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from app.config.settings import settings

security = HTTPBearer()


def get_current_user(token=Depends(security)):
    try:
        payload = jwt.decode(
            token.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, message="Invalid token")
