# alert_system.py
"""
Multi-channel alert system for accident notifications.
Supports email, SMS, in-app alerts, and emergency contacts.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class AlertMessage:
    """Create formatted alert messages."""
    
    @staticmethod
    def create_critical_alert(event_info):
        """Create CRITICAL accident alert message."""
        return f"""
🚨 CRITICAL ACCIDENT DETECTED 🚨

Time: {event_info.get('timestamp', 'Unknown')}
Frame: {event_info.get('frame_number', 'N/A')}
Vehicles Involved: {len(event_info.get('collisions', []))}

Location: 
  Latitude: {event_info.get('gps', {}).get('latitude', 'N/A')}
  Longitude: {event_info.get('gps', {}).get('longitude', 'N/A')}

⚠️ IMMEDIATE ACTION REQUIRED
- Video evidence saved
- Emergency services may be needed
- Check vehicle and occupants immediately
        """
    
    @staticmethod
    def create_warning_alert(event_info):
        """Create WARNING near-miss alert message."""
        return f"""
⚠️ NEAR-MISS DETECTED ⚠️

Time: {event_info.get('timestamp', 'Unknown')}
Frame: {event_info.get('frame_number', 'N/A')}
Vehicles in Close Proximity: {len(event_info.get('near_miss', []))}

Location:
  Latitude: {event_info.get('gps', {}).get('latitude', 'N/A')}
  Longitude: {event_info.get('gps', {}).get('longitude', 'N/A')}

ℹ️ Review clip for safety assessment
        """
    
    @staticmethod
    def create_summary_report(summary, log_path=None):
        """Create summary report."""
        report = f"""
📊 CRASHGUARD INCIDENT REPORT

Total Events: {summary.get('total_events', 0)}
  ├─ Critical Alerts: {summary.get('critical_alerts', 0)}
  ├─ Warning Alerts: {summary.get('warning_alerts', 0)}
  ├─ Collisions Detected: {summary.get('total_collisions', 0)}
  ├─ Near-Misses: {summary.get('total_near_misses', 0)}
  └─ Events with GPS: {summary.get('events_with_gps', 0)}

Generated: {datetime.now().isoformat()}
"""
        if log_path:
            report += f"Log File: {log_path}\n"
        
        return report


class AlertChannel:
    """Base class for alert channels."""
    
    def send(self, message: str, recipient: str):
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """Email alert channel (stub for integration)."""
    
    def send(self, message: str, recipient: str):
        """
        Send email alert.
        Note: Requires SMTP configuration (not implemented).
        """
        log_entry = {
            "channel": "EMAIL",
            "recipient": recipient,
            "timestamp": datetime.now().isoformat(),
            "message": message[:100] + "..." if len(message) > 100 else message,
            "status": "QUEUED"
        }
        return log_entry


class SMSAlertChannel(AlertChannel):
    """SMS alert channel (stub for integration)."""
    
    def send(self, message: str, recipient: str):
        """
        Send SMS alert.
        Note: Requires Twilio/carrier API (not implemented).
        """
        log_entry = {
            "channel": "SMS",
            "recipient": recipient,
            "timestamp": datetime.now().isoformat(),
            "message": message[:160],  # SMS limit
            "status": "QUEUED"
        }
        return log_entry


class AppAlertChannel(AlertChannel):
    """In-app notification channel."""
    
    def __init__(self, output_dir="outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.notifications = []
    
    def send(self, message: str, recipient: str = "USER"):
        """Save in-app notification."""
        notification = {
            "channel": "APP",
            "recipient": recipient,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "status": "DELIVERED"
        }
        self.notifications.append(notification)
        return notification
    
    def save_notifications(self, filename="notifications.json"):
        """Save notifications to file."""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.notifications, f, indent=2)
        return str(output_path)


class AlertSystem:
    """
    Integrated alert system managing multiple channels.
    """
    
    def __init__(self, output_dir="outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.channels = {
            "email": EmailAlertChannel(),
            "sms": SMSAlertChannel(),
            "app": AppAlertChannel(output_dir)
        }
        
        self.emergency_contacts = []
        self.alert_history = []
    
    def add_emergency_contact(self, name: str, phone: str = None, email: str = None):
        """Add emergency contact."""
        contact = {
            "name": name,
            "phone": phone,
            "email": email
        }
        self.emergency_contacts.append(contact)
        return contact
    
    def alert_accident(self, event_info: Dict, alert_level: str = "CRITICAL"):
        """
        Send alerts for accident event to all channels and contacts.
        
        Args:
            event_info: Accident event details
            alert_level: "CRITICAL" or "WARNING"
        """
        # Create message
        if alert_level == "CRITICAL":
            message = AlertMessage.create_critical_alert(event_info)
        else:
            message = AlertMessage.create_warning_alert(event_info)
        
        # Send to all channels
        sent_alerts = []
        
        # In-app notification
        app_result = self.channels["app"].send(message)
        sent_alerts.append(app_result)
        
        # Send to emergency contacts
        for contact in self.emergency_contacts:
            if contact.get("email"):
                email_result = self.channels["email"].send(message, contact["email"])
                sent_alerts.append(email_result)
            
            if contact.get("phone"):
                sms_result = self.channels["sms"].send(message, contact["phone"])
                sent_alerts.append(sms_result)
        
        # Log alert
        alert_log = {
            "timestamp": datetime.now().isoformat(),
            "event_frame": event_info.get("frame_number"),
            "alert_level": alert_level,
            "channels_used": len(sent_alerts),
            "contacts_notified": len(self.emergency_contacts),
            "status": "SENT"
        }
        
        self.alert_history.append(alert_log)
        
        return {
            "message": message,
            "sent_alerts": sent_alerts,
            "alert_log": alert_log
        }
    
    def get_contact_list(self):
        """Get all emergency contacts."""
        return self.emergency_contacts
    
    def save_alert_history(self, filename="alert_history.json"):
        """Save alert history."""
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.alert_history, f, indent=2)
        return str(output_path)
    
    def print_summary(self):
        """Print alert system summary."""
        print(f"\n📢 Alert System Summary")
        print(f"{'='*50}")
        print(f"Emergency Contacts: {len(self.emergency_contacts)}")
        for contact in self.emergency_contacts:
            print(f"  • {contact['name']}")
            if contact.get('email'):
                print(f"    Email: {contact['email']}")
            if contact.get('phone'):
                print(f"    Phone: {contact['phone']}")
        print(f"\nAlerts Sent: {len(self.alert_history)}")
        print(f"Critical Alerts: {sum(1 for a in self.alert_history if a['alert_level'] == 'CRITICAL')}")
        print(f"Warning Alerts: {sum(1 for a in self.alert_history if a['alert_level'] == 'WARNING')}")


class NotificationQueue:
    """Queue for managing notifications when offline."""
    
    def __init__(self, output_dir="outputs"):
        self.output_dir = Path(output_dir)
        self.queue = []
    
    def enqueue(self, alert_message: str, recipient: str, channel: str):
        """Add alert to queue."""
        item = {
            "timestamp": datetime.now().isoformat(),
            "message": alert_message,
            "recipient": recipient,
            "channel": channel,
            "status": "QUEUED"
        }
        self.queue.append(item)
        return item
    
    def save_queue(self, filename="notification_queue.json"):
        """Save queue to file for retry later."""
        output_path = self.output_dir / filename
        with open(output_path, 'w') as f:
            json.dump(self.queue, f, indent=2)
        return str(output_path)
    
    def clear_queue(self):
        """Clear sent notifications from queue."""
        self.queue = [item for item in self.queue if item['status'] != 'SENT']
