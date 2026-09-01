"""Optional NMEA GPS reader; it never creates a fictional location."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import threading

@dataclass(frozen=True)
class GPSFix:
    latitude: float
    longitude: float
    captured_at: str

class SerialGPS:
    def __init__(self, port: str, baudrate: int = 9600):
        self.port, self.baudrate, self._latest = port, baudrate, None
        self._stop, self._thread = threading.Event(), None
    def start(self):
        self._thread = threading.Thread(target=self._read_loop, daemon=True); self._thread.start()
    def stop(self):
        self._stop.set()
        if self._thread: self._thread.join(timeout=2)
    def latest_fix(self) -> GPSFix | None: return self._latest
    def _read_loop(self):
        import serial
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as stream:
                while not self._stop.is_set():
                    fix = self._parse_gga(stream.readline().decode("ascii", errors="ignore").strip())
                    if fix: self._latest = fix
        except serial.SerialException as error:
            print(f"GPS unavailable ({error}); GPS metadata will be null.")
    @staticmethod
    def _parse_gga(sentence: str) -> GPSFix | None:
        p = sentence.split(",")
        if len(p) < 7 or not p[0].endswith("GGA") or p[6] == "0": return None
        try:
            def decimal(value, direction):
                n = 2 if direction in ("N", "S") else 3
                result = float(value[:n]) + float(value[n:]) / 60
                return -result if direction in ("S", "W") else result
            return GPSFix(decimal(p[2], p[3]), decimal(p[4], p[5]), datetime.now(timezone.utc).isoformat())
        except (ValueError, IndexError): return None
