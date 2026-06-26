from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping=True is useful for detecting disconnected/stale connections
    pool_pre_ping=True,
    # Supabase/PostgreSQL connections can be pooled
)

# SessionLocal class for instantiating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Dependency to get db session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
