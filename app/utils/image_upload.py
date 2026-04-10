import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config.settings import settings

class ImageUpload:
    
    @staticmethod
    def save_course_image(file: UploadFile, course_id: int) -> Optional[str]:
        """Save course image and return full URL"""
        try:
            # Validate file type
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in settings.allowed_image_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_image_extensions)}"
                )
            
            # Read file content
            contents = file.file.read()
            
            # Validate file size
            if len(contents) > settings.max_upload_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max size: {settings.max_upload_size // (1024*1024)}MB"
                )
            
            # Create directory if not exists (use same storage_path as profile pictures)
            upload_dir = os.path.join(settings.storage_path, "course_images")
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"course_{course_id}_{timestamp}.{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
            
            # Return the URL path (relative to /uploads mount)
            return f"/uploads/course_images/{filename}"
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    
    @staticmethod
    def delete_course_image(image_url: str) -> bool:
        """Delete course image file"""
        try:
            if not image_url:
                return True
            
            # Extract filename from URL
            filename = image_url.split('/')[-1]
            file_path = os.path.join(settings.storage_path, "course_images", filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False