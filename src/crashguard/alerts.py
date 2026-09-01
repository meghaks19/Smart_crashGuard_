"""Emergency alert generation. Sending is disabled unless explicitly enabled."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv
from .config import Contact
from .gps import GPSFix

@dataclass(frozen=True)
class AlertDelivery:
    recipient: str
    status: str
    detail: str

def build_alert(vehicle_id: str, occurred_at: datetime, location: GPSFix | None, guidance: str = "") -> str:
    where = (f"https://maps.google.com/?q={location.latitude},{location.longitude}" if location else "GPS unavailable")
    return (f"SMART CRASHGUARD ALERT: possible crash detected for vehicle {vehicle_id} at "
            f"{occurred_at.astimezone().isoformat(timespec='seconds')}. Location: {where}. "
            f"Please try contacting the driver and call local emergency services if needed. {guidance}".strip())

class TwilioSMS:
    def send_all(self, contacts: list[Contact], message: str) -> list[AlertDelivery]:
        load_dotenv()
        if os.getenv("TWILIO_SEND_ENABLED", "false").lower() != "true":
            return [AlertDelivery(c.phone, "dry_run", "Set TWILIO_SEND_ENABLED=true to send real SMS.") for c in contacts]
        sid, token, sender = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"), os.getenv("TWILIO_FROM_NUMBER"))
        if not all((sid, token, sender)): raise RuntimeError("Twilio credentials are missing from .env.")
        from twilio.rest import Client
        client, results = Client(sid, token), []
        for contact in contacts:
            sent = client.messages.create(body=message, from_=sender, to=contact.phone)
            results.append(AlertDelivery(contact.phone, "sent", sent.sid))
        return results
