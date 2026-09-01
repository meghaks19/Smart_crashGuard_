from crashguard.detection import Detection, DetectionGate
from crashguard.gps import SerialGPS

def test_gate_requires_consecutive_positive_detections():
    gate = DetectionGate(2)
    assert not gate.update([Detection(.9, "accident", (0, 0, 1, 1))])
    assert gate.update([Detection(.9, "accident", (0, 0, 1, 1))])
    assert not gate.update([Detection(.9, "accident", (0, 0, 1, 1))])

def test_gga_parser_returns_real_coordinates():
    fix = SerialGPS._parse_gga("$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47")
    assert round(fix.latitude, 4) == 48.1173
    assert round(fix.longitude, 4) == 11.5167
