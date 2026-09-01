"""Stage a small balanced Traffic-Net subset for manual YOLO annotation.

Traffic-Net has image-level classes only. This script never creates fake
bounding boxes or YOLO labels; annotate staged images before training.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/external/Traffic-Net/raw/trafficnet_dataset_v1")
    parser.add_argument("--destination", default="data/to_annotate/traffic_net")
    parser.add_argument("--per-class", type=int, default=300)
    args = parser.parse_args()
    source, destination = Path(args.source), Path(args.destination)
    if not source.is_dir():
        raise FileNotFoundError(f"Traffic-Net source folder not found: {source}")
    selected_classes = ("accident", "dense_traffic", "sparse_traffic")
    manifest = ["# Traffic-Net staging manifest", "# Image-level source classes only: annotate YOLO boxes manually before training."]
    staged = 0
    for split in ("train", "test"):
        output_split = "train" if split == "train" else "val"
        for class_name in selected_classes:
            class_dir = source / split / class_name
            if not class_dir.is_dir():
                print(f"Skipping missing class folder: {class_dir}")
                continue
            files = sorted(p for p in class_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)[:args.per_class]
            for number, image in enumerate(files):
                target = destination / output_split / class_name / f"trafficnet_{split}_{class_name}_{number:04d}{image.suffix.lower()}"
                link_or_copy(image, target)
                manifest.append(f"{target.as_posix()},source_class={class_name}")
                staged += 1
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "README.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"Staged {staged} images under {destination}.")
    print("Next: annotate accident boxes with CVAT/Label Studio/Roboflow, then export YOLO labels into data/yolo.")

if __name__ == "__main__":
    main()
