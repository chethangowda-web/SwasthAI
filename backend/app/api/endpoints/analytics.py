from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.analytics_agent import AnalyticsAgent
from app.models.models import User

router = APIRouter()

@router.get("/dashboard-metrics", response_model=dict)
def get_analytics_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves all dashboard analytics metrics including:
    - Attendance trends (over 30 days)
    - Village coverage metrics
    - Health worker efficiency scores
    - Geographical check-in heatmap coordinates
    - Gemini-powered staffing shortage predictions
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user or user.role not in ["supervisor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only supervisors and admins can access dashboard analytics"
        )
        
    agent = AnalyticsAgent(db)
    metrics = agent.get_full_analytics_dashboard()
    
    return {
        "status": "success",
        "data": metrics
    }
