from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date
from pydantic import BaseModel
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.scheduling_agent import AISchedulingAgent
from app.models.models import User

router = APIRouter()

class ReassignmentRequest(BaseModel):
    absent_worker_id: UUID
    target_village_id: UUID
    scheduled_date: date

@router.post("/reassign", response_model=dict)
def trigger_reassignment(
    req: ReassignmentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually triggers the Smart Scheduling Agent to find a replacement worker,
    calculating distance matrix indices, balancing workloads, and assigning the replacement.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user or user.role not in ["supervisor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only supervisors or admins can trigger reassignments"
        )
        
    agent = AISchedulingAgent(db)
    result = agent.run(
        absent_worker_id=req.absent_worker_id,
        target_village_id=req.target_village_id,
        scheduled_date=req.scheduled_date
    )
    
    if not result["replacement_worker_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find any available replacement health worker."
        )
        
    return {
        "message": "Reassignment processed successfully",
        "assigned_schedule_id": result["assigned_schedule_id"],
        "replacement_worker_id": result["replacement_worker_id"],
        "reason": result["reason"]
    }
