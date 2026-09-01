"""
CrashGuard Dashboard - Streamlit Web Interface
Real-time accident detection and emergency response visualization
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

from app import CrashGuardPipeline

# Page configuration
st.set_page_config(
    page_title="CrashGuard Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .critical {
        background-color: #ffcccc;
        padding: 1rem;
        border-left: 4px solid #ff0000;
        border-radius: 0.25rem;
    }
    .warning {
        background-color: #fff3cd;
        padding: 1rem;
        border-left: 4px solid #ffc107;
        border-radius: 0.25rem;
    }
    .success {
        background-color: #d4edda;
        padding: 1rem;
        border-left: 4px solid #28a745;
        border-radius: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🚗 CrashGuard Dashboard")
st.sidebar.markdown("---")

if "system_status" not in st.session_state:
    st.session_state["system_status"] = {
        "status": "Ready",
        "video": "No video loaded",
        "mode": "Fast mode",
        "last_run": "Never"
    }

# Load output data
output_dir = Path("outputs")
json_log = output_dir / "accident_log.json"
csv_log = output_dir / "accident_log.csv"
alert_history = output_dir / "alert_history.json"

st.title("SmartCrashGuard")

st.subheader("Upload Video")
center_col, _ = st.columns([2, 1])
with center_col:
    uploaded_video = st.file_uploader(
        "Choose a video file",
        type=["mp4", "avi", "mov"],
        help="Choose a dashcam or road video to detect accidents.",
        label_visibility="collapsed"
    )

    if uploaded_video is not None:
        upload_dir = Path("temp_uploads")
        upload_dir.mkdir(exist_ok=True)
        suffix = Path(uploaded_video.name).suffix or ".mp4"
        uploaded_path = upload_dir / f"uploaded_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        uploaded_path.write_bytes(uploaded_video.getvalue())
        st.session_state["uploaded_video_path"] = str(uploaded_path)
        st.session_state["system_status"]["video"] = uploaded_video.name
        st.session_state["system_status"]["status"] = "Video loaded"
        st.success(f"Ready to process: {uploaded_video.name}")

        if st.button("Process uploaded video"):
            st.session_state["system_status"]["status"] = "Processing"
            with st.spinner("Processing uploaded video in fast mode..."):
                pipeline = CrashGuardPipeline(
                    st.session_state["uploaded_video_path"],
                    conf=0.4,
                    fast_mode=True,
                    frame_skip=2,
                    resize_scale=0.8
                )
                pipeline.process_video(output_path="outputs/crash_detected.mp4", visualize=False)
            st.session_state["system_status"]["status"] = "Completed"
            st.session_state["system_status"]["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("Video processed successfully!")
            st.session_state["latest_video_output"] = "outputs/crash_detected.mp4"

if "uploaded_video_path" in st.session_state:
    st.caption(f"Uploaded file: {Path(st.session_state['uploaded_video_path']).name}")
    st.video(st.session_state["uploaded_video_path"])

output_video = output_dir / "crash_detected.mp4"

if output_video.exists():
    st.video(str(output_video))
else:
    st.warning("No annotated video found. Upload a video or run detection first.")
