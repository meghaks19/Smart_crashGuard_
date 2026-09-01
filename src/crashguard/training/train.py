"""Train a YOLO model from an annotated YOLO-format dataset."""
from __future__ import annotations
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/dataset.yaml")
    parser.add_argument("--base-model", default="yolo11n.pt", help="Pretrained starting weights")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default=None, help="e.g. 0 for CUDA GPU, cpu for CPU")
    args = parser.parse_args()
    if not Path(args.data).is_file(): raise FileNotFoundError(f"Dataset YAML not found: {args.data}")
    from ultralytics import YOLO
    model = YOLO(args.base_model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, device=args.device, project="artifacts/training", name="accident_detector")
    print("Validate on held-out crash and non-crash footage before deploying. Weights are under artifacts/training/accident_detector/weights/.")
if __name__ == "__main__": main()
