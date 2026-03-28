import logging
import sys
import os
from datetime import datetime

def setup_logger():
    """Setup application logger"""
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"Created logs directory: {logs_dir}")
    
    # Create logger
    logger = logging.getLogger("halimatu_api")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create file handler for all logs
    log_file = os.path.join(logs_dir, f"halimatu_{datetime.now().strftime('%Y%m%d')}.log")
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")
        file_handler = None
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler.setFormatter(formatter)
    if file_handler:
        file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    if file_handler:
        logger.addHandler(file_handler)
    
    return logger