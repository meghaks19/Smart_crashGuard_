"""Configuration loading for Smart CrashGuard."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml

@dataclass(frozen=True)
class Contact:
    name: str
    phone: str
    relation: str = "Family"

@dataclass(frozen=True)
class GPSConfig:
    enabled: bool = False
    serial_port: str = "COM3"
    baudrate: int = 9600

@dataclass(frozen=True)
class RAGConfig:
    knowledge_dir: str = "docs/emergency"
    index_path: str = "artifacts/emergency.faiss"
    metadata_path: str = "artifacts/emergency_chunks.json"
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 3
    use_openai: bool = False

@dataclass(frozen=True)
class Settings:
    vehicle_id: str
    source: int | str
    model_path: str
    accident_class_names: list[str] = field(default_factory=lambda: ["accident"])
    confidence_threshold: float = 0.75
    required_positive_frames: int = 5
    detector_frame_stride: int = 1
    pre_event_minutes: int = 10
    post_event_minutes: int = 10
    segment_seconds: int = 60
    output_dir: str = "storage"
    show_preview: bool = True
    gps: GPSConfig = field(default_factory=GPSConfig)
    contacts: list[Contact] = field(default_factory=list)
    rag: RAGConfig = field(default_factory=RAGConfig)

def load_settings(path: str | Path) -> Settings:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not raw.get("vehicle_id") or raw["vehicle_id"] == "YOUR-VEHICLE-ID":
        raise ValueError("Set vehicle_id in config/settings.yaml.")
    if not raw.get("model_path"):
        raise ValueError("Set model_path to trained YOLO weights.")
    source = raw.get("source", 0)
    if isinstance(source, str) and source.isdigit(): source = int(source)
    return Settings(**{**raw, "source": source, "gps": GPSConfig(**raw.get("gps", {})),
                       "contacts": [Contact(**c) for c in raw.get("contacts", [])],
                       "rag": RAGConfig(**raw.get("rag", {}))})
