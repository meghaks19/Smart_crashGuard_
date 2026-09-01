"""YOLO-backed accident inference. No result is simulated."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import numpy as np

@dataclass(frozen=True)
class Detection:
    confidence: float
    class_name: str
    box: tuple[int, int, int, int]

class YOLOAccidentDetector:
    def __init__(self, model_path: str, accident_class_names: Iterable[str], confidence_threshold: float):
        if not Path(model_path).is_file():
            raise FileNotFoundError(f"YOLO weights not found: {model_path}. Add trained weights or update model_path.")
        from ultralytics import YOLO
        self.model = YOLO(model_path)
        self.accident_names = {x.lower() for x in accident_class_names}
        self.threshold = confidence_threshold

    def detect(self, frame: np.ndarray) -> list[Detection]:
        result = self.model.predict(frame, conf=self.threshold, verbose=False)[0]
        hits = []
        for box in result.boxes:
            class_name = str(result.names[int(box.cls.item())]).lower()
            if class_name not in self.accident_names: continue
            hits.append(Detection(float(box.conf.item()), class_name,
                tuple(int(v) for v in box.xyxy[0].tolist())))
        return hits

class DetectionGate:
    """Requires consecutive positive frames before a single incident triggers."""
    def __init__(self, required_positive_frames: int):
        if required_positive_frames < 1: raise ValueError("required_positive_frames must be >= 1")
        self.required, self.count, self.triggered = required_positive_frames, 0, False
    def update(self, detections: list[Detection]) -> bool:
        self.count = self.count + 1 if detections else 0
        if not self.triggered and self.count >= self.required:
            self.triggered = True
            return True
        return False
