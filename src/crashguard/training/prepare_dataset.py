"""Validate an existing YOLO dataset; annotation itself must be done by a human/tool."""
from __future__ import annotations
import argparse
from pathlib import Path

def validate_split(root: Path, split: str):
    images, labels = root / "images" / split, root / "labels" / split
    if not images.is_dir() or not labels.is_dir(): raise FileNotFoundError(f"Expected {images} and {labels}")
    image_files = [p for p in images.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    missing = [p.name for p in image_files if not (labels / f"{p.stem}.txt").is_file()]
    if missing: raise ValueError(f"{split}: labels missing for {len(missing)} images, e.g. {missing[:3]}")
    print(f"{split}: {len(image_files)} images, all have label files")
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", default="data/yolo")
    args = parser.parse_args(); root = Path(args.root)
    for split in ("train", "val"): validate_split(root, split)
if __name__ == "__main__": main()
