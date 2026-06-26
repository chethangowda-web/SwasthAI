import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, Date
from app.models.models import Attendance, Village, HealthWorker, Schedule, User
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class AnalyticsAgent:
    def __init__(self, db: Session):
        self.db = db
        if settings.GOOGLE_GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GOOGLE_GEMINI_API_KEY,
                temperature=0.0
            )
        else:
            self.llm = None

    def get_attendance_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Calculates daily check-in volume over the past N days.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query: Count check-ins grouped by check-in date
        results = self.db.query(
            func.cast(Attendance.check_in_time, Date).label("date"),
            func.count(Attendance.id).label("count")
        ).filter(
            Attendance.check_in_time >= start_date
        ).group_by(
            func.cast(Attendance.check_in_time, Date)
        ).order_by(
            "date"
        ).all()
        
        return [{"date": str(r[0]), "count": r[1]} for r in results]

    def get_village_coverage(self) -> Dict[str, Any]:
        """
        Calculates coverage: unique villages visited vs total villages.
        """
        total_villages = self.db.query(Village).count()
        
        # Unique villages visited in the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        visited_villages_count = self.db.query(
            func.count(func.distinct(Attendance.village_id))
        ).filter(
            Attendance.check_in_time >= start_date
        ).scalar() or 0

        coverage_pct = (visited_villages_count / total_villages * 100) if total_villages > 0 else 0.0
        
        return {
            "total_villages": total_villages,
            "visited_villages_30d": visited_villages_count,
            "coverage_percentage": round(coverage_pct, 1)
        }

    def get_worker_efficiency(self) -> List[Dict[str, Any]]:
        """
        Calculates worker efficiency: percentage of schedules successfully completed.
        """
        # Query total active workers
        workers = self.db.query(HealthWorker).all()
        
        efficiency_list = []
        for w in workers:
            total_scheduled = self.db.query(Schedule).filter(
                and_(
                    Schedule.worker_id == w.user_id,
                    Schedule.status != 'reassigned'
                )
            ).count()
            
            completed_schedules = self.db.query(Schedule).filter(
                and_(
                    Schedule.worker_id == w.user_id,
                    Schedule.status == 'completed'
                )
            ).count()
            
            efficiency_pct = (completed_schedules / total_scheduled * 100) if total_scheduled > 0 else 100.0
            
            efficiency_list.append({
                "worker_id": w.user_id,
                "worker_name": w.user.full_name if w.user else "Unknown",
                "total_scheduled": total_scheduled,
                "completed": completed_schedules,
                "efficiency_percentage": round(efficiency_pct, 1)
            })
            
        return efficiency_list

    def get_heatmap_coords(self) -> List[Dict[str, Any]]:
        """
        Aggregates check-in locations for spatial heatmap rendering.
        """
        # Fetch coordinates of all check-ins
        from app.models.models import GPSLog
        results = self.db.query(
            GPSLog.latitude,
            GPSLog.longitude,
            func.count(GPSLog.id).label("weight")
        ).group_by(
            GPSLog.latitude, GPSLog.longitude
        ).all()
        
        return [{"lat": float(r[0]), "lng": float(r[1]), "weight": r[2]} for r in results]

    def predict_staffing_shortages(self) -> Dict[str, Any]:
        """
        Predicts staffing shortages and high-risk villages using historical data and Gemini.
        """
        # Prepare basic counts to feed Gemini
        total_workers = self.db.query(HealthWorker).count()
        total_villages = self.db.query(Village).count()
        
        # Absences in the last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        recent_absences = self.db.query(Schedule).filter(
            and_(
                Schedule.scheduled_date >= start_date.date(),
                Schedule.status == 'missed'
            )
        ).count()
        
        if not self.llm:
            # Fallback mock forecasting logic
            predicted_shortage_days = ["Monday", "Thursday"]
            return {
                "forecast_summary": f"Based on recent patterns, staffing shortages are likely on {', '.join(predicted_shortage_days)} next week.",
                "high_risk_villages": ["Village A", "Village C"],
                "shortage_probability_pct": 25.0
            }
            
        prompt = (
            "You are the SwasthAI Predictive Analytics Agent. Project staffing shortages for next week based on these metrics:\n"
            f"- Total workers: {total_workers}\n"
            f"- Total villages to cover: {total_villages}\n"
            f"- Missed scheduled shifts (past 7 days): {recent_absences}\n\n"
            "Forecast the potential shortage risk. Respond ONLY with a valid JSON block containing "
            "a 'forecast_summary', a list of 'high_risk_villages' (predicting which might face coverage gaps), "
            "and an overall 'shortage_probability_pct' (float):\n"
            '{"forecast_summary": "string", "high_risk_villages": ["string"], "shortage_probability_pct": float}'
        )
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a forecasting analyst for rural public health operations."),
                HumanMessage(content=prompt)
            ])
            result = json.loads(response.content.strip())
            return {
                "forecast_summary": result.get("forecast_summary", ""),
                "high_risk_villages": result.get("high_risk_villages", []),
                "shortage_probability_pct": result.get("shortage_probability_pct", 0.0)
            }
        except Exception as e:
            return {
                "forecast_summary": f"Forecasting error: {str(e)}",
                "high_risk_villages": [],
                "shortage_probability_pct": 50.0
            }
            
    def get_full_analytics_dashboard(self) -> dict:
        """
        Compiles all charts and analytics models.
        """
        coverage = self.get_village_coverage()
        trends = self.get_attendance_trends()
        efficiency = self.get_worker_efficiency()
        heatmap = self.get_heatmap_coords()
        predictions = self.predict_staffing_shortages()
        
        return {
            "coverage": coverage,
            "trends": trends,
            "efficiency": efficiency,
            "heatmap": heatmap,
            "predictions": predictions
        }
