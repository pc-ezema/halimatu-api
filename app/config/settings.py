from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import os

# 1. Define the base directory (the 'halimatu' folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    # Application
    app_name: str = "Halimatu"
    debug: bool = False
    base_url: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 1
    max_login_attempts: int = 5 
    lockout_duration_minutes: int = 30

    # Database
    db_user: str
    db_password: Optional[str]
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str

    # SMTP
    smtp_mailer: str = "smtp"
    smtp_username: str
    smtp_password: str
    mail_from: str
    smtp_port: int
    smtp_host: str
    smtp_encryption: str

    # Storage - Use BASE_DIR here too for consistency
    storage_path: str = str(BASE_DIR / "storage")
    max_upload_size: int = 5 * 1024 * 1024  # 5MB
    allowed_image_extensions: list = ["jpg", "jpeg", "png"]

    # Add to Settings class
    flutterwave_public_key: str
    flutterwave_secret_key: str
    flutterwave_encryption_key: str
    flutterwave_webhook_secret: str
    flutterwave_production: bool = False  # False for sandbox, True for production
    frontend_url: str = "https://halimatu-sadiyyah.com.ng"

    admin_email: str

    # 2. Modern Pydantic V2 Configuration
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Generate database URL from components"""
        password = f":{self.db_password}" if self.db_password else ""
        return (
            f"mysql+pymysql://{self.db_user}"
            f"{password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

@lru_cache
def get_settings():
    """Cache settings for performance"""
    return Settings()

settings = get_settings()