"""Segmented disk recorder: practical rolling pre-event video without RAM exhaustion."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import cv2

@dataclass(frozen=True)
class ClipResult:
    incident_dir: str
    pre_event_segments: list[str]

class RollingVideoBuffer:
    def __init__(self, root: str, fps: float, width: int, height: int, pre_minutes: int = 10, segment_seconds: int = 60):
        if fps <= 0: raise ValueError("Input FPS is unknown; use a camera/video with valid FPS.")
        self.root, self.fps, self.size = Path(root), fps, (width, height)
        self.segment_frames = max(1, int(fps * segment_seconds))
        self.max_segments = max(1, (pre_minutes * 60 + segment_seconds - 1) // segment_seconds + 1)
        self.ring_dir = self.root / "rolling"; self.ring_dir.mkdir(parents=True, exist_ok=True)
        self.segments, self.writer, self.frames = deque(), None, 0
        self._open_segment()
    def _open_segment(self):
        if self.writer: self.writer.release(); self.segments.append(self.current_path); self._trim()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.current_path = self.ring_dir / f"segment_{stamp}_{len(self.segments):04d}.mp4"
        self.writer = cv2.VideoWriter(str(self.current_path), cv2.VideoWriter_fourcc(*"mp4v"), self.fps, self.size)
        if not self.writer.isOpened(): raise RuntimeError("Cannot create video. Check output directory and OpenCV codecs.")
        self.frames = 0
    def write(self, frame):
        self.writer.write(frame); self.frames += 1
        if self.frames >= self.segment_frames: self._open_segment()
    def _trim(self):
        while len(self.segments) > self.max_segments:
            old = self.segments.popleft(); old.unlink(missing_ok=True)
    def freeze_pre_event(self, incident_dir: str | Path) -> ClipResult:
        """Copy completed rolling segments; current segment remains recorded until rotated/closed."""
        # Finalize the currently open segment first, so the seconds immediately before detection are retained.`n        self._open_segment()`n        destination = Path(incident_dir) / "pre_event"; destination.mkdir(parents=True, exist_ok=True)
        copied = []
        for segment in self.segments:
            target = destination / segment.name; shutil.copy2(segment, target); copied.append(str(target))
        return ClipResult(str(Path(incident_dir)), copied)
    def close(self):
        if self.writer: self.writer.release(); self.writer = None

