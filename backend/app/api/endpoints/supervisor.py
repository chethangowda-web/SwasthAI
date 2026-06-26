from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.supervisor_agent import AISupervisorAgent
from app.models.models import User, Supervisor

router = APIRouter()

@router.post("/generate-report", response_model=dict)
def generate_report(
    timeframe: str = "daily",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers the AI Supervisor Agent (LangGraph Workflow) to analyze attendance anomalies
    and generate a report with recommendations and risk scores.
    """
    if timeframe not in ["daily", "weekly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeframe must be 'daily' or 'weekly'"
        )

    # Resolve Clerk Identity to internal Supervisor profile
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    # Simple auto-provision or validation for supervisor in testing
    if not user or user.role != "supervisor":
        # Check if we should provision a test supervisor
        if not user:
            user = User(
                clerk_id=clerk_id,
                full_name=current_user.get("name", "Test Supervisor"),
                role="supervisor"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Setup supervisor profile
            supervisor = Supervisor(user_id=user.id, region="Bengaluru Rural")
            db.add(supervisor)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only supervisors can generate reports"
            )
    
    # Run the AI Supervisor agent
    agent = AISupervisorAgent(db)
    report = agent.run(user.id, timeframe=timeframe)
    
    return {
        "message": f"AI {timeframe.capitalize()} Report generated successfully",
        "insight_id": report["insight_id"],
        "executive_summary": report["executive_summary"],
        "risk_score": report["risk_score"],
        "recommendations": report["recommendations"],
        "metrics": report["metrics"]
    }
