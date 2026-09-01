# rag_emergency.py
"""
RAG (Retrieval-Augmented Generation) System
Retrieves emergency information relevant to accident location and type.
"""

import json
from pathlib import Path
from typing import List, Dict


class EmergencyKnowledgeBase:
    """
    Knowledge base containing emergency response procedures,
    medical guidelines, and location-specific resources.
    """
    
    def __init__(self):
        self.procedures = {
            "collision": [
                "Turn on hazard lights",
                "Check for injuries - call 911 if needed",
                "Move vehicles to safe location if possible",
                "Do not admit fault",
                "Exchange insurance information",
                "Take photos of damage and scene",
                "Get witness contact information",
                "File police report if required"
            ],
            "near_miss": [
                "Take deep breaths - stay calm",
                "Check mirrors and blind spots",
                "Reduce speed slightly",
                "Increase following distance",
                "Note other vehicle details if reckless driving",
                "Consider reporting dangerous driver if safe"
            ],
            "high_velocity": [
                "Reduce speed gradually",
                "Maintain safe following distance",
                "Avoid sudden maneuvers",
                "Check brake fluid and tire pressure",
                "Ensure vehicle is mechanically sound"
            ]
        }
        
        self.emergency_services = {
            "police": "911",
            "ambulance": "911",
            "fire": "911",
            "roadside_assistance": "1-800-AAA-HELP"
        }
        
        self.injury_first_aid = {
            "bleeding": [
                "Apply direct pressure with clean cloth",
                "Elevate injured area above heart if possible",
                "Do not remove embedded objects",
                "Call 911 if severe"
            ],
            "shock": [
                "Lay person flat with legs elevated",
                "Keep warm with blanket",
                "Do not give food or water",
                "Monitor breathing and pulse"
            ],
            "spinal_injury": [
                "Do NOT move the person",
                "Keep head and neck immobilized",
                "Call 911 immediately",
                "Wait for professional responders"
            ],
            "unconscious": [
                "Check for responsiveness and breathing",
                "Call 911 immediately",
                "Place in recovery position if breathing",
                "Perform CPR if trained and no pulse"
            ]
        }
        
        self.insurance_info = {
            "at_scene": [
                "Exchange policy numbers with other drivers",
                "Get claim adjuster contact info",
                "Document accident with photos",
                "Get police report number"
            ],
            "after_scene": [
                "File claim within 24 hours if possible",
                "Provide written statement to insurer",
                "Keep all accident documentation",
                "Get repair estimates from approved shops"
            ]
        }
    
    def get_accident_response(self, accident_type: str) -> List[str]:
        """Get emergency response steps for accident type."""
        return self.procedures.get(accident_type, self.procedures["collision"])
    
    def get_first_aid_steps(self, injury_type: str) -> List[str]:
        """Get first aid steps for injury type."""
        return self.injury_first_aid.get(injury_type, ["Call 911 for emergency assistance"])
    
    def get_emergency_number(self, service_type: str = "emergency") -> str:
        """Get emergency service number."""
        if service_type == "emergency":
            return "911"
        return self.emergency_services.get(service_type, "911")
    
    def get_all_procedures(self) -> Dict:
        """Get all emergency procedures."""
        return {
            "accident_procedures": self.procedures,
            "first_aid": self.injury_first_aid,
            "insurance": self.insurance_info,
            "emergency_services": self.emergency_services
        }


class LocationBasedResources:
    """
    Find location-specific emergency resources.
    """
    
    def __init__(self):
        # Sample database - in production would connect to real API
        self.resources_db = {
            "default": {
                "hospitals": ["Nearest Hospital - Call 911"],
                "police": ["Local Police - 911"],
                "fire": ["Fire Department - 911"],
                "towing": ["AAA Roadside Assistance - 1-800-AAA-HELP"]
            }
        }
    
    def get_nearby_hospitals(self, latitude: float, longitude: float, radius_km: int = 10) -> List[Dict]:
        """
        Retrieve nearby hospitals.
        Note: In production, integrate with Google Places API or similar.
        """
        return [
            {
                "name": "Nearest Hospital",
                "distance": f"~{radius_km}km",
                "emergency_room": True,
                "phone": "911"
            }
        ]
    
    def get_nearby_police(self, latitude: float, longitude: float) -> List[Dict]:
        """Get nearby police stations."""
        return [
            {
                "type": "Police",
                "emergency": "911",
                "non_emergency": "Contact your local precinct"
            }
        ]
    
    def get_towing_services(self, location: str = None) -> List[Dict]:
        """Get towing and roadside assistance."""
        return [
            {
                "service": "AAA Roadside Assistance",
                "phone": "1-800-AAA-HELP",
                "coverage": "AAA members"
            },
            {
                "service": "Insurance Roadside Assistance",
                "phone": "Check your policy card",
                "coverage": "Policy dependent"
            }
        ]


class RAGEmergencyAssistant:
    """
    RAG system that retrieves and provides relevant emergency information
    based on accident type and location.
    """
    
    def __init__(self, output_dir="outputs"):
        self.knowledge_base = EmergencyKnowledgeBase()
        self.location_resources = LocationBasedResources()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_emergency_guidance(self, accident_type: str, gps_coords: tuple = None) -> Dict:
        """
        Retrieve comprehensive emergency guidance for accident.
        
        Args:
            accident_type: "collision", "near_miss", or "high_velocity"
            gps_coords: (latitude, longitude) tuple or None
        
        Returns:
            Dict with emergency procedures, resources, and guidance
        """
        guidance = {
            "emergency_number": "911",
            "accident_type": accident_type,
            "immediate_steps": self.knowledge_base.get_accident_response(accident_type),
            "location": None,
            "nearby_resources": None,
            "first_aid": None,
            "insurance": self.knowledge_base.insurance_info
        }
        
        if gps_coords:
            guidance["location"] = {
                "latitude": gps_coords[0],
                "longitude": gps_coords[1],
                "coordinates_available": True
            }
            
            # Get location-based resources
            guidance["nearby_resources"] = {
                "hospitals": self.location_resources.get_nearby_hospitals(
                    gps_coords[0], gps_coords[1]
                ),
                "police": self.location_resources.get_nearby_police(gps_coords[0], gps_coords[1]),
                "towing": self.location_resources.get_towing_services()
            }
        
        # Add relevant first aid
        if accident_type == "collision":
            guidance["first_aid"] = {
                "check_for": ["Bleeding", "Loss of consciousness", "Spinal injuries"],
                "procedures": self.knowledge_base.injury_first_aid
            }
        
        return guidance
    
    def format_emergency_report(self, event_info: Dict, gps_coords: tuple = None) -> str:
        """
        Format complete emergency report with guidance.
        
        Args:
            event_info: Accident event details
            gps_coords: GPS coordinates if available
        
        Returns:
            Formatted emergency report string
        """
        accident_type = "collision" if event_info.get("collisions") else "near_miss"
        guidance = self.get_emergency_guidance(accident_type, gps_coords)
        
        report = f"""
╔════════════════════════════════════════════════════════════════════╗
║                  EMERGENCY RESPONSE GUIDANCE                       ║
║                     ACCIDENT ASSISTANCE REPORT                     ║
╚════════════════════════════════════════════════════════════════════╝

🚨 EMERGENCY: {event_info.get('alert_level', 'UNKNOWN')}
Type: {accident_type.upper()}
Time: {event_info.get('timestamp', 'Unknown')}

📍 LOCATION:
  Latitude: {gps_coords[0] if gps_coords else 'Unknown'}
  Longitude: {gps_coords[1] if gps_coords else 'Unknown'}

🆘 IMMEDIATE STEPS:
"""
        for i, step in enumerate(guidance["immediate_steps"], 1):
            report += f"  {i}. {step}\n"
        
        report += f"""
☎️  EMERGENCY NUMBER: {guidance['emergency_number']}

💊 FIRST AID INFORMATION:
"""
        if guidance.get("first_aid"):
            for condition, steps in guidance["first_aid"]["procedures"].items():
                report += f"  If {condition}:\n"
                for step in steps:
                    report += f"    • {step}\n"
        
        report += f"""
🏥 NEARBY RESOURCES:
"""
        if guidance.get("nearby_resources"):
            for hospital in guidance["nearby_resources"].get("hospitals", []):
                report += f"  Hospital: {hospital['name']} ({hospital['distance']})\n"
                report += f"    Emergency Room: Yes\n"
        
        report += f"""
🛞 ROADSIDE ASSISTANCE:
"""
        for service in guidance["nearby_resources"].get("towing", []) if guidance.get("nearby_resources") else []:
            report += f"  {service['service']}: {service['phone']}\n"
        
        report += f"""
📋 INSURANCE STEPS:
"""
        for step in guidance["insurance"].get("at_scene", []):
            report += f"  • {step}\n"
        
        report += f"""
⚠️  PRESERVE EVIDENCE:
  • Video footage from dashcam has been saved
  • Timestamp: {event_info.get('timestamp', 'Unknown')}
  • Frame: {event_info.get('frame_number', 'N/A')}
  • Location saved: {gps_coords if gps_coords else 'No GPS data'}
  
  Provide this information to:
    - Emergency responders
    - Insurance company
    - Police report

═════════════════════════════════════════════════════════════════════
Generated: {Path('').resolve()}
Report Type: Automated Emergency Assistance
═════════════════════════════════════════════════════════════════════
"""
        return report
    
    def save_emergency_report(self, event_info: Dict, gps_coords: tuple = None, 
                             filename: str = "emergency_report.txt"):
        """Save formatted emergency report to file."""
        report = self.format_emergency_report(event_info, gps_coords)
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return str(output_path)
    
    def get_json_guidance(self, accident_type: str, gps_coords: tuple = None) -> Dict:
        """Get guidance as JSON for programmatic use."""
        return self.get_emergency_guidance(accident_type, gps_coords)
