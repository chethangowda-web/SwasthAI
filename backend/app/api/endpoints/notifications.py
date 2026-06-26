from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import List, Any
from app.db.session import get_db
from app.core.auth import get_current_user
from app.models.models import User, Notification
from app.services.notification_service import NotificationDispatcher

router = APIRouter()

class NotificationResponse(BaseModel):
    id: UUID
    title: str
    message: str
    is_read: bool
    created_at: Any # Custom serializer handling for datetime in production

    class Config:
        from_attributes = True

class TestAlertRequest(BaseModel):
    alert_type: str # 'emergency_alert', 'missed_attendance', 'late_attendance', 'new_schedule', 'ai_recommendation'
    message: str

@router.get("/my-alerts", response_model=List[dict])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves all notification alerts for the logged-in user.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    notifications = db.query(Notification).filter(
        Notification.user_id == user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "is_read": n.is_read,
            "created_at": n.created_at
        } for n in notifications
    ]

@router.post("/{notification_id}/read", response_model=dict)
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Marks a notification alert as read.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
        
    if notification.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to mark this notification"
        )
        
    notification.is_read = True
    db.commit()
    
    return {"status": "success", "message": "Notification marked as read"}

@router.post("/trigger-test-alert", response_model=dict)
def trigger_test_alert(
    req: TestAlertRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers a multi-channel alert dispatch to verify integrations (Twilio, SendGrid, FCM).
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
        
    dispatcher = NotificationDispatcher()
    dispatcher.dispatch_alert(
        user_id=user.id,
        phone_number=user.phone_number,
        email=user.email,
        alert_type=req.alert_type,
        message=req.message
    )
    
    # Save log to DB
    notif = Notification(
        user_id=user.id,
        title=f"Test Alert: {req.alert_type.replace('_', ' ').title()}",
        message=req.message,
        is_read=False
    )
    db.add(notif)
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Multi-channel {req.alert_type} test dispatch complete.",
        "sent_to": {
            "email": user.email,
            "phone": user.phone_number
        }
    }
