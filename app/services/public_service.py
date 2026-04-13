from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.private_tutor import PrivateTutorRequest, RequestStatus
from app.services.email_service import send_tutor_request_admin_notification, send_tutor_request_confirmation
from app.config.settings import settings
from app.models.contact import ContactMessage, ContactStatus

class PublicService:
    
    @staticmethod
    def create_request(db: Session, request_data: dict) -> PrivateTutorRequest:
        """Create a public tutor request (no login required)"""
        tutor_request = PrivateTutorRequest(
            full_name=request_data['full_name'],
            email=request_data['email'],
            phone=request_data.get('phone'),
            subject=request_data['subject'],
            message=request_data.get('message'),
            student_level=request_data.get('student_level'),
            preferred_schedule=request_data.get('preferred_schedule'),
            status=RequestStatus.PENDING
        )
        
        db.add(tutor_request)
        db.commit()
        db.refresh(tutor_request)
        
        return tutor_request
    
    @staticmethod
    def get_all_requests(db: Session, skip: int = 0, limit: int = 50, 
                         status: str = None, search: str = None) -> Dict:
        """Get all requests (admin)"""
        query = db.query(PrivateTutorRequest)
        
        if status:
            query = query.filter(PrivateTutorRequest.status == status)
        
        if search:
            query = query.filter(
                or_(
                    PrivateTutorRequest.full_name.ilike(f"%{search}%"),
                    PrivateTutorRequest.email.ilike(f"%{search}%"),
                    PrivateTutorRequest.subject.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        requests = query.order_by(PrivateTutorRequest.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "requests": requests
        }

    @staticmethod
    def get_request_by_id(db: Session, request_id: int) -> Optional[PrivateTutorRequest]:
        """Get single request by ID"""
        return db.query(PrivateTutorRequest).filter(PrivateTutorRequest.id == request_id).first()
    
    @staticmethod
    def update_status(db: Session, request_id: int, status: str) -> PrivateTutorRequest:
        """Update request status (admin)"""
        request = db.query(PrivateTutorRequest).filter(PrivateTutorRequest.id == request_id).first()
        if not request:
            raise ValueError("Request not found")
        
        request.status = status
        db.commit()
        db.refresh(request)
        
        return request
    
    @staticmethod
    def delete_request(db: Session, request_id: int) -> Dict:
        """Delete a request (admin)"""
        request = db.query(PrivateTutorRequest).filter(PrivateTutorRequest.id == request_id).first()
        if not request:
            raise ValueError("Request not found")
        
        db.delete(request)
        db.commit()
        return {"message": "Request deleted successfully"}
    
    @staticmethod
    def get_stats(db: Session) -> Dict:
        """Get request statistics"""
        total = db.query(PrivateTutorRequest).count()
        pending = db.query(PrivateTutorRequest).filter(PrivateTutorRequest.status == RequestStatus.PENDING).count()
        contacted = db.query(PrivateTutorRequest).filter(PrivateTutorRequest.status == RequestStatus.CONTACTED).count()
        completed = db.query(PrivateTutorRequest).filter(PrivateTutorRequest.status == RequestStatus.COMPLETED).count()
        
        return {
            "total": total,
            "pending": pending,
            "contacted": contacted,
            "completed": completed
        }
    
    @staticmethod
    def create_message(db: Session, message_data: dict) -> ContactMessage:
        """Create a contact message (public)"""
        contact = ContactMessage(
            full_name=message_data['full_name'],
            email=message_data['email'],
            phone=message_data.get('phone'),
            subject=message_data['subject'],
            message=message_data['message'],
            status=ContactStatus.UNREAD
        )
        
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        return contact
    
    @staticmethod
    def get_message_by_id(db: Session, message_id: int) -> Optional[ContactMessage]:
        """Get single message by ID"""
        return db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    
    @staticmethod
    def get_all_messages(db: Session, skip: int = 0, limit: int = 50, 
                         status: str = None, search: str = None) -> Dict:
        """Get all messages (admin)"""
        query = db.query(ContactMessage)
        
        if status:
            query = query.filter(ContactMessage.status == status)
        
        if search:
            query = query.filter(
                or_(
                    ContactMessage.full_name.ilike(f"%{search}%"),
                    ContactMessage.email.ilike(f"%{search}%"),
                    ContactMessage.subject.ilike(f"%{search}%"),
                    ContactMessage.message.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        messages = query.order_by(ContactMessage.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "messages": messages
        }
    
    @staticmethod
    def update_status(db: Session, message_id: int, status: str) -> ContactMessage:
        """Update message status (admin)"""
        message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        if not message:
            raise ValueError("Message not found")
        
        message.status = status
        if status == ContactStatus.READ and not message.read_at:
            message.read_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return message
    
    @staticmethod
    def delete_message(db: Session, message_id: int) -> Dict:
        """Delete a message (admin)"""
        message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        if not message:
            raise ValueError("Message not found")
        
        db.delete(message)
        db.commit()
        return {"message": "Message deleted successfully"}
    
    @staticmethod
    def get_stats(db: Session) -> Dict:
        """Get message statistics"""
        total = db.query(ContactMessage).count()
        unread = db.query(ContactMessage).filter(ContactMessage.status == ContactStatus.UNREAD).count()
        read = db.query(ContactMessage).filter(ContactMessage.status == ContactStatus.READ).count()
        replied = db.query(ContactMessage).filter(ContactMessage.status == ContactStatus.REPLIED).count()
        
        return {
            "total": total,
            "unread": unread,
            "read": read,
            "replied": replied
        }