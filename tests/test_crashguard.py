from datetime import datetime, timezone
from crashguard.alerts import build_alert
from crashguard.config import Contact
from crashguard.gps import GPSFix

def test_alert_contains_google_maps_location():
    fix = GPSFix(12.9716, 77.5946, "2026-01-01T00:00:00+00:00")
    text = build_alert("KA-01-1234", datetime.now(timezone.utc), fix)
    assert "maps.google.com" in text
    assert "KA-01-1234" in text

def test_contact_is_a_configuration_value():
    assert Contact("Priya", "+919876543210").relation == "Family"
