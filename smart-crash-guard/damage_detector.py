from pathlib import Path
from ultralytics import YOLO
import cv2


class DamageDetector:
    """Detect vehicle damage across a complete video."""

    DAMAGE_TERMS = (
        "damage", "damaged", "dent", "scratch",
        "crack", "broken", "shatter", "wreck"
    )

    def __init__(self, model_path="yolov8n.pt", conf=0.45):
    self.model_path = Path(model_path)
    self.conf = conf
    self.damage_ids = []
    self.model = None

    if not self.model_path.exists():
        return

    self.model = YOLO(str(self.model_path))
    self.damage_ids = list(self.model.names.keys())

        if not self.model_path.exists():
            return

        self.model = YOLO(str(self.model_path))

        self.damage_ids = list(self.model.names.keys())

    @property
    def available(self):
        return self.model is not None and bool(self.damage_ids)

    def detect(self, frame):
        """Detect damage in ONE frame."""
        if not self.available:
            return []

        result = self.model(
            frame,
            classes=self.damage_ids,
            conf=self.conf,
            verbose=False
        )[0]

        detections = []

        for box, confidence, class_id in zip(
            result.boxes.xyxy,
            result.boxes.conf,
            result.boxes.cls
        ):
            detections.append({
                "bbox": tuple(box.tolist()),
                "conf": float(confidence),
                "label": str(self.model.names[int(class_id)])
            })

        return detections

    def detect_video(self, video_path, frame_skip=5):
        """
        Process the complete video.

        frame_skip=5 means every 5th frame is checked.
        Returns accident/damage result and detection details.
        """

        if not self.available:
            return {
                "accident_found": False,
                "detections": [],
                "frames_checked": 0
            }

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            return {
                "accident_found": False,
                "detections": [],
                "frames_checked": 0
            }

        frame_number = 0
        frames_checked = 0
        all_detections = []

        while True:
            success, frame = cap.read()

            if not success:
                break

            frame_number += 1

            # Process only every nth frame
            if frame_number % frame_skip != 0:
                continue

            frames_checked += 1

            detections = self.detect(frame)

            if detections:
                all_detections.extend([
                    {
                        "frame": frame_number,
                        **detection
                    }
                    for detection in detections
                ])

        cap.release()

        return {
            "accident_found": len(all_detections) > 0,
            "detections": all_detections,
            "frames_checked": frames_checked
        }
    
