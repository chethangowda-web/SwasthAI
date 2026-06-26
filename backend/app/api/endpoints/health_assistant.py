from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Optional
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.health_assistant import AIHealthAssistant
from app.models.models import User, HealthWorker

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: Optional[UUID] = Field(None, description="Active chat session ID. Omit to start a new chat.")
    message_text: str = Field(..., min_length=1, description="Message query from the health worker")
    language: str = Field("en", pattern="^(en|hi|kn)$", description="Language setting: 'en' (English), 'hi' (Hindi), or 'kn' (Kannada)")

class ChatResponse(BaseModel):
    session_id: UUID
    response_text: str
    language: str
    audio_base64: str

@router.post("/chat", response_model=ChatResponse)
def health_worker_chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submits a message query to the AI Health Assistant.
    Retrieves session context memory, processes translation and protocols via Gemini,
    stores logs, and synthesizes speech output.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    # Auto-provision or validate health worker profile
    if not user or user.role != "worker":
        if not user:
            user = User(
                clerk_id=clerk_id,
                full_name=current_user.get("name", "Test Health Worker"),
                role="worker"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            worker = HealthWorker(user_id=user.id)
            db.add(worker)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only field health workers can access the health assistant"
            )
            
    session_id = req.session_id or uuid4()
    
    assistant = AIHealthAssistant(db)
    result = assistant.process_message(
        worker_id=user.id,
        session_id=session_id,
        text_content=req.message_text,
        language=req.language
    )
    
    return {
        "session_id": result["session_id"],
        "response_text": result["response_text"],
        "language": result["language"],
        "audio_base64": result["audio_base64"]
    }
