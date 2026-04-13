from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.public import ContactCreate, TutorRequestCreate, MessageResponse
from app.services.public_service import PublicService
from app.config.limiter import limiter
from app.services.email_service import send_contact_admin_notification, send_contact_confirmation, send_tutor_request_admin_notification, send_tutor_request_confirmation
from app.config.settings import settings

router = APIRouter(prefix="/api/public", tags=["Public"])

@router.post("/tutor-request", response_model=MessageResponse)
@limiter.limit("5/minute")
def request_private_tutor(
    request: Request,
    data: TutorRequestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request a private tutor (public form - no login required)"""
    try:
        # Save to database
        tutor_request = PublicService.create_request(db, data.model_dump())
        
        # Send emails in background
        background_tasks.add_task(
            send_tutor_request_confirmation,
            email=data.email,
            user_name=data.full_name,
            subject=data.subject
        )
        
        background_tasks.add_task(
            send_tutor_request_admin_notification,
            admin_email=settings.admin_email,
            request_data=data.model_dump()
        )
        
        return MessageResponse(
            message="Thank you! Your tutor request has been submitted. We will contact you within 24 hours."
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# ==================== CONTACT US ====================

@router.post("/contact", response_model=MessageResponse)
@limiter.limit("5/minute")
def submit_contact_form(
    request: Request,
    data: ContactCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Submit contact form (public - no login required)"""
    try:
        # Save to database
        contact = PublicService.create_message(db, data.model_dump())
        
        # Send confirmation email to user
        background_tasks.add_task(
            send_contact_confirmation,
            email=data.email,
            user_name=data.full_name,
            subject=data.subject
        )
        
        # Send notification email to admin
        background_tasks.add_task(
            send_contact_admin_notification,
            admin_email=settings.admin_email,
            contact_data={
                "full_name": data.full_name,
                "email": data.email,
                "phone": data.phone,
                "subject": data.subject,
                "message": data.message
            }
        )
        
        return MessageResponse(
            success=True,
            message="Thank you for contacting us! We will get back to you within 24-48 hours."
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))