import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SwasthAI API"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/swasthai")
    
    # Clerk Authentication
    CLERK_API_URL: str = os.getenv("CLERK_API_URL", "https://api.clerk.com/v1")
    CLERK_SECRET_KEY: Optional[str] = os.getenv("CLERK_SECRET_KEY")
    CLERK_JWT_ISSUER: Optional[str] = os.getenv("CLERK_JWT_ISSUER") # e.g. https://clerk.yourdomain.com or https://noble-mammoth-99.clerk.accounts.dev
    
    # Google API Keys
    GOOGLE_GEMINI_API_KEY: Optional[str] = os.getenv("GOOGLE_GEMINI_API_KEY")
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    
    # Supabase (Storage)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    SUPABASE_STORAGE_BUCKET: str = "swasthai-selfies"
    
    # Twilio (SMS & WhatsApp)
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    # SendGrid (Email)
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "alerts@swasthai.org")
    
    # Firebase (Push Notifications)
    FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_JSON")

    class Config:
        case_sensitive = True

settings = Settings()
