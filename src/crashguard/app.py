"""Live CrashGuard pipeline used by both the CLI and Streamlit dashboard."""
from __future__ import annotations
from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path
import cv2
from .alerts import TwilioSMS, build_alert
from .config import Settings
from .detection import DetectionGate, YOLOAccidentDetector
from .gps import SerialGPS
from .rag import EmergencyRAG
from .video_buffer import RollingVideoBuffer

FrameCallback = Callable[[object, list, int], None]
StopCheck = Callable[[], bool]

class CrashGuardApp:
    def __init__(self, settings: Settings):
        self.settings = settings

    def run(self, on_frame: FrameCallback | None = None, should_stop: StopCheck | None = None) -> list[str]:
        """Process the configured source and return saved incident folders.

        `on_frame` makes the same pipeline usable from Streamlit without OpenCV windows.
        """
        s = self.settings
        cap = cv2.VideoCapture(s.source)
        if not cap.isOpened(): raise RuntimeError(f"Cannot open video source: {s.source}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0: raise RuntimeError("Video source did not provide valid frame dimensions.")
        detector = YOLOAccidentDetector(s.model_path, s.accident_class_names, s.confidence_threshold)
        gate = DetectionGate(s.required_positive_frames)
        buffer = RollingVideoBuffer(s.output_dir, fps, width, height, s.pre_event_minutes, s.segment_seconds)
        gps = SerialGPS(s.gps.serial_port, s.gps.baudrate) if s.gps.enabled else None
        if gps: gps.start()
        rag = EmergencyRAG(s.rag.knowledge_dir, s.rag.index_path, s.rag.metadata_path, s.rag.embedding_model, s.rag.top_k)
        incident_dir = post_writer = None
        post_remaining = frame_number = 0
        incident_paths: list[str] = []
        try:
            while True:
                if should_stop and should_stop(): break
                ok, frame = cap.read()
                if not ok: break
                buffer.write(frame); frame_number += 1
                detections = detector.detect(frame) if frame_number % s.detector_frame_stride == 0 else []
                for item in detections:
                    x1, y1, x2, y2 = item.box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, f"{item.class_name}: {item.confidence:.2f}", (x1, max(25, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 0, 255), 2)
                if gate.update(detections):
                    happened = datetime.now(timezone.utc); stamp = happened.strftime("%Y%m%dT%H%M%SZ")
                    incident_dir = Path(s.output_dir) / "incidents" / stamp; incident_dir.mkdir(parents=True, exist_ok=True)
                    incident_paths.append(str(incident_dir)); buffer.freeze_pre_event(incident_dir)
                    post_writer = cv2.VideoWriter(str(incident_dir / "post_event.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
                    if not post_writer.isOpened(): raise RuntimeError("Cannot create post-event video file.")
                    post_remaining = int(s.post_event_minutes * 60 * fps)
                    fix = gps.latest_fix() if gps else None
                    guidance = rag.answer("What are safe general actions after a road crash?", s.rag.use_openai)
                    message = build_alert(s.vehicle_id, happened, fix, guidance[:500])
                    deliveries = [d.__dict__ for d in TwilioSMS().send_all(s.contacts, message)]
                    metadata = {"vehicle_id": s.vehicle_id, "detected_at": happened.isoformat(), "gps": fix.__dict__ if fix else None,
                                "detections": [d.__dict__ for d in detections], "alert": message, "deliveries": deliveries,
                                "status": "recording_post_event"}
                    (incident_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                if post_writer:
                    post_writer.write(frame); post_remaining -= 1
                    if post_remaining <= 0:
                        post_writer.release(); post_writer = None
                        metadata_path = incident_dir / "metadata.json"; metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                        metadata["status"] = "complete"; metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
                if on_frame: on_frame(frame, detections, frame_number)
                if s.show_preview:
                    cv2.imshow("Smart CrashGuard (press q to stop)", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"): break
        finally:
            if post_writer: post_writer.release()
            buffer.close(); cap.release(); cv2.destroyAllWindows()
            if gps: gps.stop()
        return incident_paths
