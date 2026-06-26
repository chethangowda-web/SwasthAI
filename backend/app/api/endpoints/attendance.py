from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.core.auth import get_current_user
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.services.attendance_agent import AttendanceVerificationAgent

router = APIRouter()

@router.post("/check-in", response_model=dict, status_code=status.HTTP_201_CREATED)
def check_in(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submits a new check-in for the health worker.
    Runs the multi-agent AI verification for GPS location and selfie.
    """
    # Clerk user ID is mapped to local user in database
    # In production, we retrieve our internal UUID based on Clerk's 'sub' claim
    clerk_id = current_user.get("sub")
    
    # Simple mockup mapping or actual lookup
    # In a fully populated db, we would fetch the user:
    # user = db.query(User).filter(User.clerk_id == clerk_id).first()
    # For initial testing / fallback, we use a default UUID or lookup
    from app.models.models import User
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user:
        # Auto-provision user/worker for test purposes if they authenticate successfully via Clerk
        # but don't exist in our DB yet
        user = User(
            clerk_id=clerk_id,
            full_name=current_user.get("name", "Test Health Worker"),
            phone_number=current_user.get("phone_number"),
            email=current_user.get("email"),
            role="worker"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Provision worker sub-profile
        from app.models.models import HealthWorker
        worker = HealthWorker(user_id=user.id)
        db.add(worker)
        db.commit()

    agent = AttendanceVerificationAgent(db)
    result = agent.verify_attendance(user.id, data)
    
    return {
        "message": "Attendance processed successfully",
        "attendance_id": result["attendance"].id,
        "status": result["attendance"].status,
        "distance_meters": result["distance_meters"],
        "is_inside_fence": result["is_inside_fence"],
        "confidence_score": float(result["verification"].confidence_score),
        "ai_analysis_notes": result["verification"].ai_analysis_notes
    }
