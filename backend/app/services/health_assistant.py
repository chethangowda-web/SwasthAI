import base64
import io
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import ChatHistory, HealthWorker
from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from gtts import gTTS

class AIHealthAssistant:
    def __init__(self, db: Session):
        self.db = db
        if settings.GOOGLE_GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GOOGLE_GEMINI_API_KEY,
                temperature=0.3
            )
        else:
            self.llm = None

    def get_conversation_history(self, worker_id: uuid.UUID, session_id: uuid.UUID) -> List[ChatHistory]:
        """
        Retrieves historical messages for a given session.
        """
        return self.db.query(ChatHistory).filter(
            ChatHistory.worker_id == worker_id,
            ChatHistory.session_id == session_id
        ).order_by(ChatHistory.created_at.asc()).all()

    def process_message(
        self, 
        worker_id: uuid.UUID, 
        session_id: uuid.UUID, 
        text_content: str, 
        language: str = "en"
    ) -> dict:
        """
        Processes a text/audio query, generates a response via Gemini with memory context,
        stores the conversation in the database, and returns the response with base64 TTS audio.
        """
        # 1. Fetch conversation history
        history = self.get_conversation_history(worker_id, session_id)
        
        # 2. Build message context for LLM
        messages = [
            SystemMessage(content=(
                "You are the SwasthAI Health Assistant, an empathetic and highly knowledgeable public health AI companion. "
                "Your role is to support rural health workers with screening guidelines, sanitation protocols, and basic "
                "healthcare advice based on government guidelines. "
                "IMPORTANT: Keep your answers simple, clear, and tailored to rural healthcare workers. "
                "Always communicate in the requested language (English, Hindi, or Kannada). "
                "If a query is outside public health (e.g. general chit-chat), gently redirect them back to health protocols. "
                "Clearly state when a referral to a secondary hospital is required."
            ))
        ]
        
        # Append historical messages
        for msg in history:
            if msg.sender == "worker":
                messages.append(HumanMessage(content=msg.message))
            else:
                messages.append(AIMessage(content=msg.message))
                
        # Append current user message
        messages.append(HumanMessage(content=text_content))

        # 3. Call Gemini API
        ai_response_text = ""
        if self.llm:
            try:
                response = self.llm.invoke(messages)
                ai_response_text = response.content
            except Exception as e:
                ai_response_text = f"Error generating response: {str(e)}"
        else:
            # Fallback mock responses
            if language == "kn":
                ai_response_text = "ನಮಸ್ಕಾರ, ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ? (Mock Kannada Response)"
            elif language == "hi":
                ai_response_text = "नमस्ते, मैं आपकी क्या सहायता कर सकता हूँ? (Mock Hindi Response)"
            else:
                ai_response_text = "Hello, I am the SwasthAI Health Assistant. How can I help you today? (Mock English Response)"

        # 4. Save conversation to database
        user_msg = ChatHistory(
            worker_id=worker_id,
            session_id=session_id,
            sender="worker",
            message=text_content
        )
        ai_msg = ChatHistory(
            worker_id=worker_id,
            session_id=session_id,
            sender="ai_assistant",
            message=ai_response_text
        )
        
        self.db.add(user_msg)
        self.db.add(ai_msg)
        self.db.commit()

        # 5. Generate TTS (Text-to-Speech) Audio
        # Mapping language strings to gTTS supported codes
        lang_code = "en"
        if language == "hi":
            lang_code = "hi"
        elif language == "kn":
            lang_code = "kn"

        audio_base64 = ""
        try:
            tts = gTTS(text=ai_response_text, lang=lang_code)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_base64 = base64.b64encode(fp.read()).decode("utf-8")
        except Exception as e:
            # In case TTS fails (e.g. network issue), return empty audio gracefully
            print(f"TTS Generation failed: {str(e)}")

        return {
            "session_id": session_id,
            "response_text": ai_response_text,
            "language": language,
            "audio_base64": audio_base64
        }
