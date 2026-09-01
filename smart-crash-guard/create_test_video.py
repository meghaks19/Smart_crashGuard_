#!/usr/bin/env python3
"""
Create a video from the test images for crash detection testing
"""
import cv2
import os
import numpy as np
from pathlib import Path

def create_video_from_images():
    image_dir = "data/test_clips/video.mp4"
    output_video = "data/test_output.mp4"
    
    # Get all JPG images sorted
    images = sorted([f for f in os.listdir(image_dir) if f.endswith('.jpg')])
    
    if not images:
        print("❌ No JPG images found in data/test_clips/")
        return
    
    print(f"📸 Found {len(images)} images")
    print(f"Creating video from images...")
    
    # Read first image to get dimensions
    first_image = cv2.imread(os.path.join(image_dir, images[0]))
    if first_image is None:
        print(f"❌ Cannot read image: {images[0]}")
        return
    
    height, width = first_image.shape[:2]
    fps = 30
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    # Write each image to video
    for i, image_name in enumerate(images):
        image_path = os.path.join(image_dir, image_name)
        frame = cv2.imread(image_path)
        
        if frame is None:
            print(f"⚠️  Skipping {image_name}: cannot read")
            continue
        
        # Resize to match first image if needed
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))
        
        writer.write(frame)
        
        if (i + 1) % 10 == 0:
            print(f"  ✓ Processed {i+1}/{len(images)} images")
    
    writer.release()
    print(f"\n✅ Video created: {output_video}")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    print(f"   Duration: {len(images)/fps:.2f} seconds")
    
    return output_video

if __name__ == "__main__":
    create_video_from_images()
