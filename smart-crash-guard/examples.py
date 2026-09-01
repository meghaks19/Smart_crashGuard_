#!/usr/bin/env python3
"""
CRASHGUARD - Vehicle Accident Detection System
Example usage and testing
"""

def example_1_basic_detection():
    """Basic example: detect accidents in a video"""
    from app import CrashGuardPipeline
    
    # Create pipeline instance
    pipeline = CrashGuardPipeline('data/test_output.mp4')
    
    # Process video and save output
    accidents = pipeline.process_video(
        output_path='outputs/crash_detected.mp4',
        visualize=False
    )
    
    # Show results
    pipeline.print_summary()


def example_2_real_time_detection():
    """Real-time detection with live visualization"""
    from app import CrashGuardPipeline
    
    pipeline = CrashGuardPipeline('data/test_output.mp4')
    
    # Process with real-time display (press 'q' to quit)
    accidents = pipeline.process_video(
        output_path=None,  # Don't save
        visualize=True  # Show live window
    )
    
    print(f"\nDetected {len(accidents)} accident frames")


def example_3_custom_thresholds():
    """Use custom detection thresholds"""
    from accident_detector import AccidentDetector
    from detector import VehicleDetector
    from tracker import GatedTracker
    from kinematics import VelocityTracker
    import cv2
    
    # Custom parameters
    detector = VehicleDetector(conf=0.5)  # Higher confidence
    tracker = GatedTracker(max_distance=100, max_missed_frames=5)
    vel_tracker = VelocityTracker()
    accident_detector = AccidentDetector(
        iou_threshold=0.15,  # 15% overlap = collision
        proximity_threshold=50,  # Closer = danger
        velocity_threshold=150  # Higher velocity = more risk
    )
    
    cap = cv2.VideoCapture('data/test_output.mp4')
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_idx += 1
        
        # Run pipeline
        detections = detector.detect(frame)
        tracked = tracker.update(detections)
        
        tracked_objects = []
        for tid, bbox in tracked.items():
            x1, y1, x2, y2 = bbox
            tracked_objects.append({
                "id": tid,
                "bbox": bbox,
                "centroid": ((x1+x2)/2, (y1+y2)/2)
            })
        
        velocities = vel_tracker.update(tracked_objects, fps)
        result = accident_detector.detect(tracked_objects, velocities)
        
        if result["risky"]:
            print(f"Frame {frame_idx}: Alert = {accident_detector.get_alert_level(result)}")
            if result["collisions"]:
                print(f"  Collisions: {result['collisions']}")
    
    cap.release()


def example_4_integrate_with_existing_code():
    """Show how to integrate CrashGuard into existing Python code"""
    
    # Import what you need
    from accident_detector import AccidentDetector, iou, bbox_distance
    
    # Your existing vehicle detection code
    detected_vehicles = [
        {"bbox": (100, 100, 150, 200), "conf": 0.95},
        {"bbox": (120, 110, 170, 210), "conf": 0.92}
    ]
    
    # Your existing tracking code
    tracked = {
        1: (100, 100, 150, 200),
        2: (120, 110, 170, 210)
    }
    
    # Your existing velocity data
    velocities = {
        1: 75.5,  # pixels/second
        2: 95.2
    }
    
    # Create tracked_objects format
    tracked_objects = [
        {"id": 1, "bbox": (100, 100, 150, 200), "centroid": (125, 150)},
        {"id": 2, "bbox": (120, 110, 170, 210), "centroid": (145, 160)}
    ]
    
    # Initialize accident detector
    accident_detector = AccidentDetector(
        iou_threshold=0.1,
        proximity_threshold=30,
        velocity_threshold=100
    )
    
    # Detect accidents
    result = accident_detector.detect(tracked_objects, velocities)
    alert = accident_detector.get_alert_level(result)
    
    print(f"Alert Level: {alert}")
    print(f"Result: {result}")
    
    # Check individual metrics
    bbox1 = tracked[1]
    bbox2 = tracked[2]
    overlap = iou(bbox1, bbox2)
    distance = bbox_distance(bbox1, bbox2)
    
    print(f"IoU (overlap): {overlap:.3f}")
    print(f"Distance: {distance:.1f} pixels")


def print_help():
    """Print usage instructions"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           CRASHGUARD - Accident Detection System               ║
╚════════════════════════════════════════════════════════════════╝

Available Examples:
  1. example_1_basic_detection()      - Process video file
  2. example_2_real_time_detection()  - Live visualization
  3. example_3_custom_thresholds()    - Custom parameters
  4. example_4_integrate_with_existing_code() - Integration guide

Quick Start:
  >>> from examples import example_1_basic_detection
  >>> example_1_basic_detection()

Component Classes:
  - VehicleDetector       - YOLO vehicle detection
  - GatedTracker          - Multi-object tracking
  - VelocityTracker       - Velocity computation
  - AccidentDetector      - Collision detection

Python Usage:
  from app import CrashGuardPipeline
  
  pipeline = CrashGuardPipeline('video.mp4')
  accidents = pipeline.process_video(output_path='out.mp4')
  pipeline.print_summary()
    """)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        if example_name == "1":
            print("Running: Basic Detection")
            example_1_basic_detection()
        elif example_name == "2":
            print("Running: Real-time Detection")
            example_2_real_time_detection()
        elif example_name == "3":
            print("Running: Custom Thresholds")
            example_3_custom_thresholds()
        elif example_name == "4":
            print("Running: Integration Example")
            example_4_integrate_with_existing_code()
        else:
            print(f"Unknown example: {example_name}")
            print_help()
    else:
        print_help()
