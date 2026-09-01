#!/usr/bin/env python3
"""
Test script to run crash detection on sample video
with full emergency response system
"""
from app import CrashGuardPipeline
import os

def test_crash_detection():
    # Path to your own video file
    # Put your video in the data folder and name it my_video.mp4
    test_video = "data/my_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Video not found: {test_video}")
        print("Place your video in the data folder and rename it to my_video.mp4")
        return
    
    print("="*60)
    print("🚗 CRASHGUARD - ACCIDENT DETECTION SYSTEM")
    print("Complete Emergency Response Pipeline")
    print("="*60)
    print(f"\n📹 Processing video: {test_video}")
    
    try:
        # Initialize pipeline in fast mode for quicker processing
        pipeline = CrashGuardPipeline(
            test_video,
            conf=0.4,
            fast_mode=True,
            frame_skip=2,
            resize_scale=0.8
        )
        
        # Add emergency contacts
        print("\n📱 Adding emergency contacts...")
        pipeline.add_emergency_contact("Emergency Services", phone="911", email="dispatch@police.gov")
        pipeline.add_emergency_contact("Family", phone="555-1234", email="family@email.com")
        pipeline.add_emergency_contact("Insurance", phone="1-800-INS-HELP", email="claims@insurance.com")
        
        # Process video and detect accidents
        print("\n⏳ Running detection pipeline...\n")
        clips = pipeline.process_video(
            output_path="outputs/crash_detected.mp4",
            visualize=False  # Set to True to see live video window
        )
        
        # Print results
        pipeline.print_summary()
        
        # Generate emergency reports for detected accidents
        if pipeline.accident_frames:
            print(f"\n⚠️  ACCIDENTS DETECTED IN {len(pipeline.accident_frames)} FRAMES!")
            print("\nGenerating emergency reports...")
            
            for i, frame_num in enumerate(pipeline.accident_frames[:3], 1):  # First 3 accidents
                gps_coords = (37.7749, -122.4194)  # Example GPS (SF coordinates)
                report_path = pipeline.generate_emergency_report(frame_num, gps_coords)
                print(f"  ✓ Report {i} saved: {report_path}")
            
            # Print guidance for first accident
            first_accident_frame = pipeline.accident_frames[0]
            guidance = pipeline.get_emergency_guidance(
                first_accident_frame,
                gps_coords=(37.7749, -122.4194)
            )
            print(f"Alert Type: {guidance['accident_type'].upper()}")
            print(f"Immediate Steps:")
            for step in guidance['immediate_steps']:
                print(f"  • {step}")
            print(f"\nEmergency Number: {guidance['emergency_number']}")
            
        else:
            print("\n✅ No accidents detected in this video.")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_crash_detection()
