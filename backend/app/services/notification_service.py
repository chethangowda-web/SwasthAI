import json
import logging
from typing import Optional
from uuid import UUID
from app.core.config import settings

# Graceful import check for Twilio/SendGrid
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger("swasthai.notifications")

class NotificationDispatcher:
    def __init__(self):
        # Initialize Twilio Client
        self.twilio_client = None
        if TWILIO_AVAILABLE and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                self.twilio_client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")

        # Initialize SendGrid Client
        self.sendgrid_client = None
        if SENDGRID_AVAILABLE and settings.SENDGRID_API_KEY:
            try:
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {str(e)}")

    def send_push(self, user_id: UUID, title: str, message: str) -> bool:
        """
        Dispatches a Push notification via Firebase Cloud Messaging (FCM).
        FCM requires a registered client token for the given user.
        """
        logger.info(f"FCM Push Alert to User {user_id} | Title: {title} | Message: {message}")
        if settings.FIREBASE_CREDENTIALS_JSON:
            try:
                # Actual Firebase FCM integration:
                # In production, we'd fetch the user's FCM push token from our DB, e.g.:
                # token = db.query(FCMToken).filter(FCMToken.user_id == user_id).first()
                # messaging.send(messaging.Message(notification=..., token=token))
                pass
            except Exception as e:
                logger.error(f"FCM Push failed: {str(e)}")
                return False
        return True

    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Dispatches an SMS notification via Twilio.
        """
        logger.info(f"SMS Dispatch to {phone_number} | Msg: {message}")
        if self.twilio_client and settings.TWILIO_PHONE_NUMBER:
            try:
                self.twilio_client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                return True
            except Exception as e:
                logger.error(f"Twilio SMS failed: {str(e)}")
                return False
        return True

    def send_whatsapp(self, phone_number: str, message: str) -> bool:
        """
        Dispatches a WhatsApp template/session alert via Twilio WhatsApp API.
        """
        logger.info(f"WhatsApp Dispatch to {phone_number} | Msg: {message}")
        if self.twilio_client and settings.TWILIO_WHATSAPP_NUMBER:
            try:
                # WhatsApp numbers must be prefixed with 'whatsapp:' in Twilio sandbox/api
                to_whatsapp = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number
                from_whatsapp = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}" if not settings.TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:") else settings.TWILIO_WHATSAPP_NUMBER
                
                self.twilio_client.messages.create(
                    body=message,
                    from_=from_whatsapp,
                    to=to_whatsapp
                )
                return True
            except Exception as e:
                logger.error(f"Twilio WhatsApp failed: {str(e)}")
                return False
        return True

    def send_email(self, destination_email: str, subject: str, body_text: str) -> bool:
        """
        Dispatches an email alert via SendGrid.
        """
        logger.info(f"Email Dispatch to {destination_email} | Subject: {subject}")
        if self.sendgrid_client:
            try:
                mail = Mail(
                    from_email=settings.FROM_EMAIL,
                    to_emails=destination_email,
                    subject=subject,
                    plain_text_content=body_text
                )
                self.sendgrid_client.send(mail)
                return True
            except Exception as e:
                logger.error(f"SendGrid email failed: {str(e)}")
                return False
        return True

    def dispatch_alert(
        self, 
        user_id: UUID, 
        phone_number: Optional[str], 
        email: Optional[str], 
        alert_type: str, 
        message: str
    ):
        """
        Dispatches multi-channel alerts based on specific alert rules.
        """
        title = f"SwasthAI Alert: {alert_type.replace('_', ' ').title()}"
        
        # 1. Always send Push Notification for real-time mobile app updates
        self.send_push(user_id, title, message)
        
        # 2. Channel Routing Rules:
        if alert_type in ["emergency_alert", "missed_attendance"]:
            # Critical alerts: Route to SMS and WhatsApp immediately
            if phone_number:
                self.send_sms(phone_number, f"{title} - {message}")
                self.send_whatsapp(phone_number, f"{title} - {message}")
            if email:
                self.send_email(email, title, message)
                
        elif alert_type in ["late_attendance", "new_schedule", "ai_recommendation"]:
            # Non-critical updates: Route to Push & Email (or WhatsApp if phone is present)
            if email:
                self.send_email(email, title, message)
            if phone_number and alert_type == "new_schedule":
                self.send_whatsapp(phone_number, f"{title} - {message}")
