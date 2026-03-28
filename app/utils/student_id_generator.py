import random
import string
from sqlalchemy.orm import Session
from app.models.user import User

class StudentIDGenerator:
    """Generate unique student IDs"""
    
    @staticmethod
    def generate_student_id() -> str:
        """
        Generate a unique student ID
        Format: STU + YEAR + 6-digit random number
        Example: STU2024001234
        """
        from datetime import datetime
        year = datetime.now().year
        random_num = random.randint(1000, 9999)
        return f"STU{year}{random_num:04d}"
    
    @staticmethod
    def generate_with_prefix(prefix: str = "STU") -> str:
        """
        Generate student ID with custom prefix
        Format: PREFIX + YEAR + 6-digit random number
        """
        from datetime import datetime
        year = datetime.now().year
        random_num = random.randint(1000, 9999)
        return f"{prefix}{year}{random_num:04d}"
    
    @staticmethod
    def generate_formatted(year: int = None, sequence: int = None) -> str:
        """
        Generate formatted student ID with optional parameters
        Format: STU-YYYY-XXXX
        """
        from datetime import datetime
        if not year:
            year = datetime.now().year
        if not sequence:
            sequence = random.randint(1000, 9999)
        return f"STU-{year}-{sequence:04d}"
    
    @staticmethod
    def generate_unique_student_id(db: Session, max_attempts: int = 5) -> str:
        """
        Generate a unique student ID that doesn't exist in the database
        """
        for attempt in range(max_attempts):
            # Generate a student ID
            student_id = StudentIDGenerator.generate_student_id()
            
            # Check if it exists
            existing = db.query(User).filter(User.student_id == student_id).first()
            if not existing:
                return student_id
            
            # If exists, try with a different random number
            if attempt == max_attempts - 1:
                # Last attempt - use timestamp for uniqueness
                import time
                timestamp = int(time.time() * 1000) % 1000000
                student_id = f"STU{timestamp}"
                
                # Final check
                existing = db.query(User).filter(User.student_id == student_id).first()
                if not existing:
                    return student_id
                
                raise Exception("Failed to generate unique student ID after multiple attempts")
        
        raise Exception("Failed to generate unique student ID")