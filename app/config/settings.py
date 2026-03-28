from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "Halimatu"
    debug: bool = False

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 1
    max_login_attempts: int = 5  # Add this field
    lockout_duration_minutes: int = 30

    # Database
    db_user: str = "root"
    db_password: Optional[str] = None
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "halimatu"

    # SMTP
    smtp_mailer: str = "smtp"
    smtp_username: str
    smtp_password: str
    mail_from: str
    smtp_port: int = 2525
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_encryption: str = "tls"

    # Storage
    storage_path: str = os.path.join(os.getcwd(), "storage")

    @property
    def database_url(self) -> str:
        """Generate database URL from components"""
        password = f":{self.db_password}" if self.db_password else ""
        return (
            f"mysql+pymysql://{self.db_user}"
            f"{password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # This allows case-insensitive matching


@lru_cache
def get_settings():
    """Cache settings for performance"""
    return Settings()


settings = get_settings()