from datetime import datetime, timedelta
from jose import jwt
from app.config.settings import settings


def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode = {**data, "exp": expire}
    return jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )


def create_refresh_token(data: dict):
    expire = datetime.utcnow() + timedelta(
        days=settings.refresh_token_expire_days
    )
    to_encode = {**data, "exp": expire}
    return jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
