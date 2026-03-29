from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Extra arguments to prevent hanging on cPanel/Shared Hosting
connect_args = {
    "connect_timeout": 10,  # If it can't connect in 10s, stop trying
}

try:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,    # Checks if connection is alive before using it
        pool_recycle=300,      # Recycle connections every 5 mins (cPanel kills long idle ones)
        pool_size=5,           # Keep pool small for shared hosting
        max_overflow=10,
        connect_args=connect_args,
        echo=False
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # We don't raise here so the app can at least start and show an error 
    # instead of hanging the whole server.
    engine = None 

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    if engine is None:
        raise Exception("Database engine was not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()