import json
from datetime import datetime, timedelta
from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.models import Attendance, GPSLog, FaceVerification, HealthWorker, Village, User, AIInsight, Schedule
from app.core.config import settings

# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Define state structure for LangGraph
class AgentState(TypedDict):
    supervisor_id: UUID
    timeframe: str  # "daily" or "weekly"
    db_session: Session
    raw_records: List[Dict[str, Any]]
    anomalies: Dict[str, Any]
    report_text: str
    risk_score: int
    recommendations: List[str]
    saved_insight_id: Optional[UUID]

# 1. Node: Fetch Data
def fetch_data_node(state: AgentState) -> Dict[str, Any]:
    db = state["db_session"]
    supervisor_id = state["supervisor_id"]
    timeframe = state["timeframe"]
    
    # Calculate starting range
    days_back = 1 if timeframe == "daily" else 7
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Fetch villages managed by this supervisor
    villages = db.query(Village).filter(Village.supervisor_id == supervisor_id).all()
    village_ids = [v.id for v in villages]
    
    if not village_ids:
        return {"raw_records": []}

    # Fetch attendance logs
    attendance_records = db.query(Attendance).filter(
        and_(
            Attendance.village_id.in_(village_ids),
            Attendance.check_in_time >= start_date
        )
    ).all()

    # Fetch scheduled assignments to compute absenteeism
    schedules = db.query(Schedule).filter(
        and_(
            Schedule.village_id.in_(village_ids),
            Schedule.scheduled_date >= start_date.date()
        )
    ).all()

    # Format records for analysis
    records_data = []
    for att in attendance_records:
        # Get face verification result
        face_ver = db.query(FaceVerification).filter(FaceVerification.attendance_id == att.id).first()
        gps = db.query(GPSLog).filter(GPSLog.attendance_id == att.id).first()
        
        records_data.append({
            "attendance_id": att.id,
            "worker_name": att.worker.user.full_name if att.worker and att.worker.user else "Unknown",
            "village_name": att.village.name,
            "check_in": att.check_in_time,
            "status": att.status,
            "gps_lat": float(gps.latitude) if gps else None,
            "gps_lng": float(gps.longitude) if gps else None,
            "confidence": float(face_ver.confidence_score) if face_ver else 1.0,
            "ai_notes": face_ver.ai_analysis_notes if face_ver else ""
        })

    formatted_schedules = [{
        "worker_id": sch.worker_id,
        "village_id": sch.village_id,
        "date": sch.scheduled_date,
        "status": sch.status
    } for sch in schedules]

    return {
        "raw_records": records_data,
        "anomalies": {
            "schedules": formatted_schedules
        }
    }

# 2. Node: Analyze Anomalies (Rule Engine Node)
def analyze_anomalies_node(state: AgentState) -> Dict[str, Any]:
    raw_records = state["raw_records"]
    schedules = state["anomalies"].get("schedules", [])
    
    late_arrivals = []
    suspicious = []
    gps_anomalies = []
    absentees = 0
    
    # 1. Analyze late arrivals (arbitrary threshold: checked in after 9:30 AM local time)
    for rec in raw_records:
        check_in_time = rec["check_in"]
        # Convert to local time approximation or use Hour checking
        if check_in_time.hour >= 4: # 4 UTC is 9:30 AM IST (UTC+5:30)
            late_arrivals.append(rec)
        
        # 2. GPS anomalies and Suspicious Face verification
        if rec["status"] == "flagged":
            if "GEO-FENCE" in rec["ai_notes"]:
                gps_anomalies.append(rec)
            else:
                suspicious.append(rec)

    # 3. Absenteeism check (comparing schedule status)
    for sch in schedules:
        if sch["status"] == "missed":
            absentees += 1

    return {
        "anomalies": {
            "late_count": len(late_arrivals),
            "late_details": [r["worker_name"] for r in late_arrivals],
            "suspicious_count": len(suspicious),
            "suspicious_details": [r["worker_name"] for r in suspicious],
            "gps_anomaly_count": len(gps_anomalies),
            "gps_anomaly_details": [f"{r['worker_name']} in {r['village_name']}" for r in gps_anomalies],
            "absentee_count": absentees
        }
    }

# 3. Node: LLM Summarize and Recommendation (Gemini Node)
def summarize_with_gemini_node(state: AgentState) -> Dict[str, Any]:
    anomalies = state["anomalies"]
    timeframe = state["timeframe"]
    
    # Check if Gemini API key exists
    if not settings.GOOGLE_GEMINI_API_KEY:
        # Fallback Mock Report
        return {
            "report_text": f"Mock {timeframe} summary: All systems operational. Detected {anomalies['late_count']} late arrivals.",
            "risk_score": 15,
            "recommendations": ["Ensure workers activate GPS before check-in."]
        }
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GOOGLE_GEMINI_API_KEY,
        temperature=0.2
    )
    
    prompt = (
        f"You are the SwasthAI Intelligent Supervisor Agent. Analyze the following workforce metrics for a {timeframe} cycle:\n"
        f"- Late Arrivals: {anomalies['late_count']} (Workers: {', '.join(anomalies['late_details'])})\n"
        f"- GPS Geo-fence Violations: {anomalies['gps_anomaly_count']} (Details: {', '.join(anomalies['gps_anomaly_details'])})\n"
        f"- Face Spoof/Verification Flags: {anomalies['suspicious_count']} (Workers: {', '.join(anomalies['suspicious_details'])})\n"
        f"- Absentees: {anomalies['absentee_count']}\n\n"
        "Provide a concise, professional report structured EXACTLY as follows:\n"
        "1. Executive Summary\n"
        "2. Risk Assessment (Rate risk score from 0 to 100 based on counts)\n"
        "3. Concrete Actionable Recommendations for the supervisor.\n"
        "Respond ONLY with a valid JSON block matching this structure:\n"
        '{"executive_summary": "string", "risk_score": int, "recommendations": ["string"]}'
    )
    
    try:
        response = llm.invoke([
            SystemMessage(content="You are a clinical supervisor assistant."),
            HumanMessage(content=prompt)
        ])
        
        result = json.loads(response.content.strip())
        return {
            "report_text": result.get("executive_summary", ""),
            "risk_score": result.get("risk_score", 0),
            "recommendations": result.get("recommendations", [])
        }
    except Exception as e:
        return {
            "report_text": f"Error running Gemini summary: {str(e)}",
            "risk_score": 50,
            "recommendations": ["Review logs manually."]
        }

# 4. Node: Persist Insights
def save_insights_node(state: AgentState) -> Dict[str, Any]:
    db = state["db_session"]
    supervisor_id = state["supervisor_id"]
    report_text = state["report_text"]
    risk_score = state["risk_score"]
    recommendations = state["recommendations"]
    
    # Save a new AI Insight record
    insight = AIInsight(
        supervisor_id=supervisor_id,
        insight_text=f"Risk Score: {risk_score} | {report_text} | Recommendations: {'; '.join(recommendations)}",
        severity="critical" if risk_score >= 70 else ("warning" if risk_score >= 40 else "info")
    )
    
    db.add(insight)
    db.commit()
    db.refresh(insight)
    
    return {"saved_insight_id": insight.id}


class AISupervisorAgent:
    def __init__(self, db: Session):
        self.db = db
        # Build state graph
        builder = StateGraph(AgentState)
        
        # Add nodes
        builder.add_node("fetch_data", fetch_data_node)
        builder.add_node("analyze_anomalies", analyze_anomalies_node)
        builder.add_node("summarize_gemini", summarize_with_gemini_node)
        builder.add_node("save_insights", save_insights_node)
        
        # Define workflow sequence
        builder.set_entry_point("fetch_data")
        builder.add_edge("fetch_data", "analyze_anomalies")
        builder.add_edge("analyze_anomalies", "summarize_gemini")
        builder.add_edge("summarize_gemini", "save_insights")
        builder.add_edge("save_insights", END)
        
        self.graph = builder.compile()

    def run(self, supervisor_id: UUID, timeframe: str = "daily") -> dict:
        initial_state = {
            "supervisor_id": supervisor_id,
            "timeframe": timeframe,
            "db_session": self.db,
            "raw_records": [],
            "anomalies": {},
            "report_text": "",
            "risk_score": 0,
            "recommendations": [],
            "saved_insight_id": None
        }
        
        # Execute the Graph
        result = self.graph.invoke(initial_state)
        
        return {
            "insight_id": result["saved_insight_id"],
            "executive_summary": result["report_text"],
            "risk_score": result["risk_score"],
            "recommendations": result["recommendations"],
            "metrics": result["anomalies"]
        }
