from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(50), nullable=False, index=True) # 'worker', 'supervisor', 'admin'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    supervisor_profile = relationship("Supervisor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    worker_profile = relationship("HealthWorker", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Supervisor(Base):
    __tablename__ = "supervisors"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    region = Column(String(255), nullable=False)
    
    user = relationship("User", back_populates="supervisor_profile")
    villages = relationship("Village", back_populates="supervisor")
    ai_insights = relationship("AIInsight", back_populates="supervisor", cascade="all, delete-orphan")

class Village(Base):
    __tablename__ = "villages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("supervisors.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    supervisor = relationship("Supervisor", back_populates="villages")
    workers = relationship("HealthWorker", back_populates="primary_village")
    attendance_records = relationship("Attendance", back_populates="village", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="village", cascade="all, delete-orphan")
    health_reports = relationship("HealthReport", back_populates="village", cascade="all, delete-orphan")

class HealthWorker(Base):
    __tablename__ = "health_workers"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    primary_village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id", ondelete="SET NULL"), nullable=True)
    availability_status = Column(String(50), default="available") # 'available', 'on_leave', 'reassigned'
    face_embedding = Column(JSONB, nullable=True) # Serialized list of floats (512-D vector from InsightFace)
    
    user = relationship("User", back_populates="worker_profile")
    primary_village = relationship("Village", back_populates="workers")
    attendance_records = relationship("Attendance", back_populates="worker", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="worker", cascade="all, delete-orphan")
    health_reports = relationship("HealthReport", back_populates="worker")
    chat_history = relationship("ChatHistory", back_populates="worker", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("health_workers.user_id", ondelete="CASCADE"), nullable=False, index=True)
    village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False)
    check_in_time = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending", nullable=False) # 'pending', 'verified', 'flagged', 'rejected'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    worker = relationship("HealthWorker", back_populates="attendance_records")
    village = relationship("Village", back_populates="attendance_records")
    gps_logs = relationship("GPSLog", back_populates="attendance", cascade="all, delete-orphan")
    face_verification = relationship("FaceVerification", back_populates="attendance", uselist=False, cascade="all, delete-orphan")

class GPSLog(Base):
    __tablename__ = "gps_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_id = Column(UUID(as_uuid=True), ForeignKey("attendance.id", ondelete="CASCADE"), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    accuracy_meters = Column(Numeric(10, 2), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    attendance = relationship("Attendance", back_populates="gps_logs")

class FaceVerification(Base):
    __tablename__ = "face_verification"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_id = Column(UUID(as_uuid=True), ForeignKey("attendance.id", ondelete="CASCADE"), unique=True, nullable=False)
    selfie_url = Column(String, nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    is_match = Column(Boolean, nullable=False)
    ai_analysis_notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    attendance = relationship("Attendance", back_populates="face_verification")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("health_workers.user_id", ondelete="CASCADE"), nullable=False, index=True)
    village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    status = Column(String(50), default="scheduled") # 'scheduled', 'completed', 'missed', 'reassigned'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    worker = relationship("HealthWorker", back_populates="schedules")
    village = relationship("Village", back_populates="schedules")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("supervisors.user_id", ondelete="CASCADE"), nullable=False, index=True)
    insight_text = Column(String, nullable=False)
    severity = Column(String(50), default="info") # 'info', 'warning', 'critical'
    related_entity_type = Column(String(50), nullable=True) # 'worker', 'village'
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    supervisor = relationship("Supervisor", back_populates="ai_insights")

class HealthReport(Base):
    __tablename__ = "health_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("health_workers.user_id", ondelete="SET NULL"), nullable=True)
    village_id = Column(UUID(as_uuid=True), ForeignKey("villages.id", ondelete="CASCADE"), nullable=False)
    report_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    worker = relationship("HealthWorker", back_populates="health_reports")
    village = relationship("Village", back_populates="health_reports")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("health_workers.user_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sender = Column(String(50), nullable=False) # 'worker', 'ai_assistant'
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    worker = relationship("HealthWorker", back_populates="chat_history")
