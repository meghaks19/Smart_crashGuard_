# clip_extractor.py
"""
Extract video clips around accident events.
Saves 10 minutes before + 10 minutes after accident detection.
"""

import cv2
import os
from datetime import timedelta
from pathlib import Path


class ClipExtractor:
    """
    Extracts and saves video clips centered around accident events.
    """
    
    def __init__(self, buffer_frames=None, fps=30):
        """
        Args:
            buffer_frames: Number of frames to save before/after accident
                          If None, defaults to 10 minutes at given FPS
            fps: Frames per second of video
        """
        self.fps = fps
        # Default: 10 minutes = 10*60*fps frames
        self.buffer_frames = buffer_frames or int(10 * 60 * fps)
        
    def extract_clip(self, video_path, accident_frame, output_dir="outputs"):
        """
        Extract and save video clip around accident frame.
        
        Args:
            video_path: Path to original video
            accident_frame: Frame number where accident occurred
            output_dir: Directory to save clips
        
        Returns:
            {
                'clip_path': str (path to saved clip),
                'start_frame': int,
                'end_frame': int,
                'duration': str (human readable)
            }
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Calculate frame range
        start_frame = max(0, accident_frame - self.buffer_frames)
        end_frame = accident_frame + self.buffer_frames
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Adjust end frame if exceeds total
        if end_frame > total_frames:
            end_frame = total_frames
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create output filename
        accident_time = timedelta(seconds=accident_frame / self.fps)
        clip_name = f"accident_{int(accident_time.total_seconds())}s.mp4"
        clip_path = os.path.join(output_dir, clip_name)
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(clip_path, fourcc, self.fps, (width, height))
        
        # Extract frames
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_count = start_frame
        
        while frame_count < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            writer.write(frame)
            frame_count += 1
        
        cap.release()
        writer.release()
        
        # Calculate duration
        duration_frames = end_frame - start_frame
        duration_seconds = duration_frames / self.fps
        duration_str = self._format_duration(duration_seconds)
        
        return {
            "clip_path": clip_path,
            "start_frame": start_frame,
            "end_frame": end_frame,
            "duration": duration_str,
            "duration_seconds": duration_seconds,
            "accident_frame_offset": accident_frame - start_frame
        }
    
    def extract_multiple_clips(self, video_path, accident_frames, output_dir="outputs"):
        """
        Extract clips for multiple accident events.
        
        Args:
            video_path: Path to video
            accident_frames: List of frame numbers with accidents
            output_dir: Output directory
        
        Returns:
            List of clip metadata dicts
        """
        clips = []
        for i, frame_num in enumerate(accident_frames, 1):
            print(f"Extracting clip {i}/{len(accident_frames)} for frame {frame_num}...")
            clip_info = self.extract_clip(video_path, frame_num, output_dir)
            clips.append(clip_info)
            print(f"  ✓ Saved: {clip_info['clip_path']}")
        
        return clips
    
    @staticmethod
    def _format_duration(seconds):
        """Convert seconds to HH:MM:SS format."""
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"


class VideoBuffer:
    """
    Circular buffer for frame history.
    Keeps last N frames in memory for quick clip extraction.
    """
    
    def __init__(self, buffer_size=18000):  # 10 minutes at 30 fps
        """
        Args:
            buffer_size: Number of frames to keep in memory
        """
        self.buffer_size = buffer_size
        self.frames = []
        self.frame_indices = []
        self.current_idx = 0
        
    def add_frame(self, frame, frame_idx):
        """Add frame to circular buffer."""
        if len(self.frames) < self.buffer_size:
            self.frames.append(frame.copy())
            self.frame_indices.append(frame_idx)
        else:
            self.frames[self.current_idx] = frame.copy()
            self.frame_indices[self.current_idx] = frame_idx
            self.current_idx = (self.current_idx + 1) % self.buffer_size
    
    def get_buffered_frames(self):
        """Get all buffered frames in chronological order."""
        if len(self.frames) < self.buffer_size:
            # Not yet full, return in order
            return self.frames, self.frame_indices
        else:
            # Full buffer, reorder starting from current index
            frames = self.frames[self.current_idx:] + self.frames[:self.current_idx]
            indices = self.frame_indices[self.current_idx:] + self.frame_indices[:self.current_idx]
            return frames, indices
    
    def save_to_video(self, output_path, fps=30):
        """Save buffered frames to video file."""
        if not self.frames:
            return None
        
        frames, indices = self.get_buffered_frames()
        height, width = frames[0].shape[:2]
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            writer.write(frame)
        
        writer.release()
        
        return {
            "video_path": output_path,
            "frame_count": len(frames),
            "frame_indices": indices
        }
