from pathlib import Path
from ultralytics import YOLO
import cv2


class DamageDetector:

    DAMAGE_TERMS = (
        "damage",
        "damaged",
        "dent",
        "scratch",
        "crack",
        "broken",
        "shatter",
        "wreck",
        "accident",
        "collision",
        "crash"
    )

    def __init__(self, model_path="best.pt", conf=0.45):
        self.model_path = Path(model_path)
        self.conf = conf
        self.model = None
        self.damage_ids = []

        # Check model file
        if not self.model_path.exists():
            print(f"Model not found: {self.model_path}")
            return

        try:
            self.model = YOLO(str(self.model_path))

            # Find classes related to accident/damage
            for class_id, class_name in self.model.names.items():

                class_name = str(class_name).lower()

                if any(term in class_name for term in self.DAMAGE_TERMS):
                    self.damage_ids.append(class_id)

            print("Model loaded successfully.")
            print("Model classes:", self.model.names)
            print("Damage classes:", self.damage_ids)

        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None

    @property
    def available(self):
        return (
            self.model is not None
            and len(self.damage_ids) > 0
        )

    def detect(self, frame):
        """
        Detect accident/damage in one frame.
        """

        if not self.available:
            return []

        try:
            result = self.model(
                frame,
                classes=self.damage_ids,
                conf=self.conf,
                verbose=False
            )[0]

            detections = []

            if result.boxes is None:
                return detections

            for box, confidence, class_id in zip(
                result.boxes.xyxy,
                result.boxes.conf,
                result.boxes.cls
            ):

                class_id = int(class_id)

                detections.append({
                    "bbox": tuple(
                        round(float(value), 2)
                        for value in box.tolist()
                    ),
                    "conf": round(float(confidence), 3),
                    "label": str(
                        self.model.names[class_id]
                    )
                })

            return detections

        except Exception as e:
            print(f"Detection error: {e}")
            return []

    def detect_video(self, video_path, frame_skip=5):
        """
        Process the complete video.

        frame_skip=5:
        Checks every 5th frame.

        Returns:
            accident_found
            detections
            frames_checked
        """

        if not self.available:
            return {
                "accident_found": False,
                "detections": [],
                "frames_checked": 0
            }

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            print(f"Unable to open video: {video_path}")

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

            # Skip frames
            if frame_number % frame_skip != 0:
                continue

            frames_checked += 1

            detections = self.detect(frame)

            if detections:

                for detection in detections:

                    all_detections.append({
                        "frame": frame_number,
                        **detection
                    })

        cap.release()

        return {
            "accident_found": len(all_detections) > 0,
            "detections": all_detections,
            "frames_checked": frames_checked
        }
