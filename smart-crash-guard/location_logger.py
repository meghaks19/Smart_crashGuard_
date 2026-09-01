# location_logger.py
"""
GPS location and accident event logging.
Records timestamp, coordinates, and accident details.
"""

import json
import csv
from datetime import datetime
from pathlib import Path


class LocationLogger:
    """
    Logs accident events with GPS coordinates and timestamps.
    """
    
    def __init__(self, output_dir="outputs"):
        """Initialize logger."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.events = []
        
    def log_event(self, accident_info, gps_coords=None, vehicle_info=None):
        """
        Log an accident event.
        
        Args:
            accident_info: Dict with frame, alert_level, collisions
            gps_coords: Tuple (latitude, longitude) or None
            vehicle_info: Dict with vehicle details
        
        Returns:
            Event dict logged
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "frame_number": accident_info.get("frame", -1),
            "alert_level": accident_info.get("alert_level", "UNKNOWN"),
            "collisions": accident_info.get("collisions", []),
            "near_miss": accident_info.get("near_miss", []),
            "high_velocity_vehicles": accident_info.get("high_velocity", []),
            "gps": {
                "latitude": gps_coords[0] if gps_coords else None,
                "longitude": gps_coords[1] if gps_coords else None
            },
            "vehicle_info": vehicle_info or {}
        }
        
        self.events.append(event)
        return event
    
    def save_json(self, filename="accident_log.json"):
        """Save all logged events as JSON."""
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, indent=2)
        
        return str(output_path)
    
    def save_csv(self, filename="accident_log.csv"):
        """Save events as CSV for spreadsheet compatibility."""
        if not self.events:
            return None
        
        output_path = self.output_dir / filename
        
        # Flatten nested dicts for CSV
        flat_events = []
        for event in self.events:
            flat = {
                "timestamp": event["timestamp"],
                "frame": event["frame_number"],
                "alert_level": event["alert_level"],
                "collision_count": len(event["collisions"]),
                "collisions": str(event["collisions"]),
                "near_miss_count": len(event["near_miss"]),
                "near_misses": str(event["near_miss"]),
                "high_velocity_count": len(event["high_velocity_vehicles"]),
                "high_velocity_ids": str(event["high_velocity_vehicles"]),
                "latitude": event["gps"]["latitude"],
                "longitude": event["gps"]["longitude"]
            }
            flat_events.append(flat)
        
        # Write CSV
        fieldnames = [
            "timestamp", "frame", "alert_level", "collision_count",
            "collisions", "near_miss_count", "near_misses",
            "high_velocity_count", "high_velocity_ids", "latitude", "longitude"
        ]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_events)
        
        return str(output_path)
    
    def get_summary(self):
        """Get summary statistics."""
        critical_count = sum(1 for e in self.events if e["alert_level"] == "CRITICAL")
        warning_count = sum(1 for e in self.events if e["alert_level"] == "WARNING")
        total_collisions = sum(len(e["collisions"]) for e in self.events)
        total_near_miss = sum(len(e["near_miss"]) for e in self.events)
        
        return {
            "total_events": len(self.events),
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "total_collisions": total_collisions,
            "total_near_misses": total_near_miss,
            "events_with_gps": sum(1 for e in self.events if e["gps"]["latitude"])
        }


class VehicleMetadata:
    """Store vehicle information for reporting."""
    
    def __init__(self):
        self.data = {
            "vehicle_type": "Dashcam",
            "make": None,
            "model": None,
            "year": None,
            "vin": None,
            "license_plate": None,
            "driver_name": None,
            "contact": None
        }
    
    def set_vehicle_info(self, **kwargs):
        """Set vehicle metadata."""
        for key, value in kwargs.items():
            if key in self.data:
                self.data[key] = value
    
    def get_vehicle_info(self):
        """Get vehicle metadata."""
        return self.data
    
    def save(self, output_path="outputs/vehicle_info.json"):
        """Save vehicle metadata."""
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2)
        return output_path
