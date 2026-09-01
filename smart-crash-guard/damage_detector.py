"""Visible vehicle-damage detection using a custom YOLO model."""
from pathlib import Path

from ultralytics import YOLO


class DamageDetector:
    """Detect dents, cracks, scratches, or damaged vehicles in a frame."""

    DAMAGE_TERMS = ("damage", "damaged", "dent", "scratch", "crack", "broken", "shatter", "wreck")

    def __init__(self, model_path="models/vehicle_damage.pt", conf=0.45):
        self.model_path = Path(model_path)
        self.conf = conf
        self.model = None
        self.damage_ids = []
        if not self.model_path.exists():
            return
        self.model = YOLO(str(self.model_path))
        self.damage_ids = [
            class_id for class_id, label in self.model.names.items()
            if any(term in str(label).lower() for term in self.DAMAGE_TERMS)
        ]

    @property
    def available(self):
        return self.model is not None and bool(self.damage_ids)

    def detect(self, frame):
        if not self.available:
            return []
        result = self.model(frame, classes=self.damage_ids, conf=self.conf, verbose=False)[0]
        return [
            {"bbox": tuple(box.tolist()), "conf": float(confidence),
             "label": str(self.model.names[int(class_id)])}
            for box, confidence, class_id in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls)
        ]
