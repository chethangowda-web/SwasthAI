from fastapi import FastAPI
from app.api.endpoints import attendance, supervisor, scheduling, analytics, health_assistant, face_auth, maps, notifications
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME, 
    description="AI-powered Rural Health Worker Attendance Management System"
)

# Register endpoints
app.include_router(attendance.router, prefix=f"{settings.API_V1_STR}/attendance", tags=["attendance"])
app.include_router(supervisor.router, prefix=f"{settings.API_V1_STR}/supervisor", tags=["supervisor"])
app.include_router(scheduling.router, prefix=f"{settings.API_V1_STR}/scheduling", tags=["scheduling"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(health_assistant.router, prefix=f"{settings.API_V1_STR}/health-assistant", tags=["health-assistant"])
app.include_router(face_auth.router, prefix=f"{settings.API_V1_STR}/face-auth", tags=["face-auth"])
app.include_router(maps.router, prefix=f"{settings.API_V1_STR}/maps", tags=["maps"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])

@app.get("/")
def read_root():
    return {"message": "Welcome to SwasthAI API"}

