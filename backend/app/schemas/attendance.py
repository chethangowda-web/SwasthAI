from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class AttendanceCreate(BaseModel):
    village_id: UUID = Field(..., description="ID of the village the worker is checking into")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Captured check-in latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Captured check-in longitude")
    selfie_url: str = Field(..., description="Uploaded selfie URL on Supabase storage")

class AttendanceResponse(BaseModel):
    id: UUID
    worker_id: UUID
    village_id: UUID
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FaceVerificationResponse(BaseModel):
    id: UUID
    attendance_id: UUID
    selfie_url: str
    confidence_score: float
    is_match: bool
    ai_analysis_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
