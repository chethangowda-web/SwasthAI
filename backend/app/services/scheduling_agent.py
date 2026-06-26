import json
import requests
from datetime import date, datetime
from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.models import HealthWorker, Village, Schedule, Notification, User
from app.core.config import settings

# LangGraph & LangChain imports
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Define State
class SchedulingState(TypedDict):
    absent_worker_id: UUID
    target_village_id: UUID
    scheduled_date: date
    db_session: Session
    candidates: List[Dict[str, Any]]
    best_candidate_id: Optional[UUID]
    recommendation_reason: str
    assigned_schedule_id: Optional[UUID]

# 1. Node: Fetch Candidate Workers
def fetch_candidates_node(state: SchedulingState) -> Dict[str, Any]:
    db = state["db_session"]
    absent_worker_id = state["absent_worker_id"]
    target_village_id = state["target_village_id"]
    scheduled_date = state["scheduled_date"]
    
    # Target village coordinates
    target_village = db.query(Village).filter(Village.id == target_village_id).first()
    if not target_village:
        return {"candidates": []}

    # Fetch all other active health workers who are marked 'available'
    workers = db.query(HealthWorker).filter(
        and_(
            HealthWorker.user_id != absent_worker_id,
            HealthWorker.availability_status == 'available'
        )
    ).all()
    
    candidates_list = []
    for w in workers:
        primary_village = db.query(Village).filter(Village.id == w.primary_village_id).first()
        
        # Calculate current workload for that date (count of scheduled visits)
        workload_count = db.query(Schedule).filter(
            and_(
                Schedule.worker_id == w.user_id,
                Schedule.scheduled_date == scheduled_date,
                Schedule.status != 'reassigned'
            )
        ).count()
        
        candidates_list.append({
            "worker_id": w.user_id,
            "worker_name": w.user.full_name if w.user else "Unknown",
            "primary_village_name": primary_village.name if primary_village else "Unknown",
            "origin_lat": float(primary_village.latitude) if primary_village else float(target_village.latitude),
            "origin_lng": float(primary_village.longitude) if primary_village else float(target_village.longitude),
            "current_workload": workload_count
        })
        
    return {
        "candidates": candidates_list
    }

# 2. Node: Calculate Transit Times & Distances (Maps / Distance Matrix)
def calculate_distances_node(state: SchedulingState) -> Dict[str, Any]:
    db = state["db_session"]
    target_village_id = state["target_village_id"]
    candidates = state["candidates"]
    
    target_village = db.query(Village).filter(Village.id == target_village_id).first()
    if not target_village or not candidates:
        return {"candidates": candidates}
        
    dest_coords = f"{target_village.latitude},{target_village.longitude}"
    
    # We query Google Distance Matrix API if key is available, else mock
    if settings.GOOGLE_MAPS_API_KEY:
        origins = "|".join([f"{c['origin_lat']},{c['origin_lng']}" for c in candidates])
        url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origins}&destinations={dest_coords}&key={settings.GOOGLE_MAPS_API_KEY}"
        )
        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()
            
            # Populate distances in candidates
            if data.get("status") == "OK":
                elements = data["rows"][0]["elements"]
                for idx, element in enumerate(elements):
                    if element.get("status") == "OK":
                        candidates[idx]["distance_meters"] = element["distance"]["value"]
                        candidates[idx]["duration_seconds"] = element["duration"]["value"]
                    else:
                        candidates[idx]["distance_meters"] = 999999
                        candidates[idx]["duration_seconds"] = 99999
        except Exception:
            # Fallback to straight-line estimation if API call fails
            pass
            
    # Fallback / mock calculation (straight line distance in meters)
    for c in candidates:
        if "distance_meters" not in c:
            # Simple Euclidean approximation in degrees * 111,000 meters
            lat_diff = c["origin_lat"] - float(target_village.latitude)
            lng_diff = c["origin_lng"] - float(target_village.longitude)
            approx_dist = int((lat_diff**2 + lng_diff**2)**0.5 * 111000)
            c["distance_meters"] = approx_dist
            c["duration_seconds"] = int(approx_dist / 10)  # assume average 10 m/s (~36km/h) transit speed
            
    return {"candidates": candidates}

# 3. Node: Select Best Replacement via Gemini (Workload balancing check)
def select_candidate_gemini_node(state: SchedulingState) -> Dict[str, Any]:
    candidates = state["candidates"]
    
    if not candidates:
        return {
            "best_candidate_id": None,
            "recommendation_reason": "No available candidates found."
        }
        
    if not settings.GOOGLE_GEMINI_API_KEY:
        # Fallback Mock Selector: choose the candidate with lowest workload, breaking ties by distance
        sorted_candidates = sorted(candidates, key=lambda x: (x["current_workload"], x["distance_meters"]))
        best = sorted_candidates[0]
        return {
            "best_candidate_id": best["worker_id"],
            "recommendation_reason": f"Fallback Mock: Selected {best['worker_name']} due to lowest current workload ({best['current_workload']}) and proximity ({round(best['distance_meters']/1000, 1)}km away)."
        }
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GOOGLE_GEMINI_API_KEY,
        temperature=0.0
    )
    
    prompt = (
        "You are the SwasthAI Smart Scheduling Agent. Select the optimal replacement worker to cover an absence at the target village.\n"
        "Balance two key criteria:\n"
        "1. Transit Proximity (closer is better to minimize travel times).\n"
        "2. Workload Balance (avoid assigning to workers who already have a high current workload to prevent burnout).\n\n"
        f"Candidates Details:\n{json.dumps([{ 'id': str(c['worker_id']), 'name': c['worker_name'], 'distance_km': round(c['distance_meters']/1000, 2), 'current_workload': c['current_workload'] } for c in candidates], indent=2)}\n\n"
        "Respond ONLY with a valid JSON block containing the 'selected_worker_id' (must match one of the candidate IDs) and a short 'reason' outlining your decision logic:\n"
        '{"selected_worker_id": "string", "reason": "string"}'
    )
    
    try:
        response = llm.invoke([
            SystemMessage(content="You are a routing and workload balancing assistant."),
            HumanMessage(content=prompt)
        ])
        result = json.loads(response.content.strip())
        return {
            "best_candidate_id": UUID(result.get("selected_worker_id")),
            "recommendation_reason": result.get("reason", "Selected by AI logic.")
        }
    except Exception as e:
        # Fallback selector
        best = sorted(candidates, key=lambda x: (x["current_workload"], x["distance_meters"]))[0]
        return {
            "best_candidate_id": best["worker_id"],
            "recommendation_reason": f"AI error fallback selection: {best['worker_name']}. Details: {str(e)}"
        }

# 4. Node: Assign & Create Notification
def assign_and_notify_node(state: SchedulingState) -> Dict[str, Any]:
    db = state["db_session"]
    best_candidate_id = state["best_candidate_id"]
    target_village_id = state["target_village_id"]
    scheduled_date = state["scheduled_date"]
    reason = state["recommendation_reason"]
    
    if not best_candidate_id:
        return {"assigned_schedule_id": None}
        
    # Create new schedule entry
    schedule = Schedule(
        worker_id=best_candidate_id,
        village_id=target_village_id,
        scheduled_date=scheduled_date,
        status="scheduled"
    )
    db.add(schedule)
    db.flush()
    
    # Notify the replacement worker
    notification = Notification(
        user_id=best_candidate_id,
        title="Emergency Reassignment Alert",
        message=f"You have been reassigned to visit the target village on {scheduled_date}. AI Reason: {reason}",
        is_read=False
    )
    db.add(notification)
    db.commit()
    
    return {"assigned_schedule_id": schedule.id}


class AISchedulingAgent:
    def __init__(self, db: Session):
        self.db = db
        builder = StateGraph(SchedulingState)
        
        builder.add_node("fetch_candidates", fetch_candidates_node)
        builder.add_node("calculate_distances", calculate_distances_node)
        builder.add_node("select_candidate", select_candidate_gemini_node)
        builder.add_node("assign_and_notify", assign_and_notify_node)
        
        builder.set_entry_point("fetch_candidates")
        builder.add_edge("fetch_candidates", "calculate_distances")
        builder.add_edge("calculate_distances", "select_candidate")
        builder.add_edge("select_candidate", "assign_and_notify")
        builder.add_edge("assign_and_notify", END)
        
        self.graph = builder.compile()

    def run(self, absent_worker_id: UUID, target_village_id: UUID, scheduled_date: date) -> dict:
        initial_state = {
            "absent_worker_id": absent_worker_id,
            "target_village_id": target_village_id,
            "scheduled_date": scheduled_date,
            "db_session": self.db,
            "candidates": [],
            "best_candidate_id": None,
            "recommendation_reason": "",
            "assigned_schedule_id": None
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "assigned_schedule_id": result["assigned_schedule_id"],
            "replacement_worker_id": result["best_candidate_id"],
            "reason": result["recommendation_reason"]
        }
