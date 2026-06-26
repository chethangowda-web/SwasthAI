from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.core.auth import get_current_user
from app.services.face_verifier import FaceVerifierService
from app.models.models import User, HealthWorker

router = APIRouter()

class RegisterFaceRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded string of the registration profile selfie")

class VerifyFaceRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded string of the check-in selfie to verify")

@router.post("/register-face", response_model=dict)
def register_worker_face(
    req: RegisterFaceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Extracts and stores facial biometric embeddings for the authenticated health worker.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user or user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only health workers can register biometrics"
        )
        
    worker = db.query(HealthWorker).filter(HealthWorker.user_id == user.id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health worker profile not found"
        )

    verifier = FaceVerifierService()
    embedding, err = verifier.extract_embedding(req.image_base64)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Face registration failed: {err}"
        )

    # Save embedding securely to worker record
    worker.face_embedding = embedding
    db.commit()

    return {
        "status": "success",
        "message": "Face biometrics registered successfully",
        "embedding_dimensions": len(embedding)
    }

@router.post("/verify-face", response_model=dict)
def verify_worker_face(
    req: VerifyFaceRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Compares a test check-in selfie against the worker's registered facial profile.
    Checks similarity scores and runs texture-based liveness/spoofing checks.
    """
    clerk_id = current_user.get("sub")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if not user or user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )

    worker = db.query(HealthWorker).filter(HealthWorker.user_id == user.id).first()
    if not worker or not worker.face_embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker has not registered biometrics yet"
        )

    verifier = FaceVerifierService()
    
    # 1. Check Spoofing / Liveness
    is_spoof, spoof_score = verifier.detect_spoofing(req.image_base64)
    if is_spoof:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Face verification rejected: Liveness/Spoofing check failed (confidence: {round(spoof_score*100, 1)}%)"
        )

    # 2. Extract Embedding from selfie
    selfie_embedding, err = verifier.extract_embedding(req.image_base64)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process selfie biometrics: {err}"
        )

    # 3. Calculate Cosine Similarity
    similarity = verifier.verify_similarity(worker.face_embedding, selfie_embedding)
    
    # Standard threshold for ArcFace matching is typically 0.50 - 0.60
    threshold = 0.55
    is_match = similarity >= threshold

    return {
        "status": "success",
        "verified": is_match,
        "similarity_score": round(similarity, 3),
        "threshold": threshold,
        "liveness_check": "passed",
        "spoof_probability": round(spoof_score, 3)
    }
