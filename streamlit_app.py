"""Start with: streamlit run streamlit_app.py"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import shutil
import time
import cv2
import streamlit as st
from crashguard.app import CrashGuardApp
from crashguard.config import load_settings

st.set_page_config(page_title="Smart CrashGuard", page_icon="🚗", layout="wide")
st.title("🚗 Smart CrashGuard")
st.caption("YOLO-based dashcam review and incident capture. Validate your model before relying on it.")

with st.sidebar:
    st.header("Configuration")
    config_path = st.text_input("Settings file", "config/settings.yaml")
    mode = st.radio("Video source", ("Upload test video", "Use source from settings"))
    st.warning("SMS is dry-run unless TWILIO_SEND_ENABLED=true in .env.")

try:
    settings = load_settings(config_path)
    model_ok = Path(settings.model_path).is_file()
    st.sidebar.success(f"Vehicle: {settings.vehicle_id}")
    st.sidebar.write(f"YOLO weights: {'ready' if model_ok else 'missing'}")
except Exception as error:
    settings, model_ok = None, False
    st.error(f"Configuration error: {error}")
    st.info("Copy config/settings.example.yaml to config/settings.yaml, then add your vehicle ID and model path.")

uploaded = None
if mode == "Upload test video":
    uploaded = st.file_uploader("Upload a dashcam video for safe testing", type=["mp4", "avi", "mov", "mkv"])
    st.caption("The upload is saved under storage/_uploads during processing.")

left, right = st.columns([3, 1])
preview, status, metrics = left.empty(), right.empty(), right.empty()

can_start = settings is not None and model_ok and (mode != "Upload test video" or uploaded is not None)
if st.button("Start analysis", type="primary", disabled=not can_start):
    run_settings = settings
    if uploaded:
        upload_dir = Path(settings.output_dir) / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploaded_path = upload_dir / f"{int(time.time())}_{uploaded.name}"
        with uploaded_path.open("wb") as target:
            shutil.copyfileobj(uploaded, target)
        run_settings = replace(settings, source=str(uploaded_path))
    run_settings = replace(run_settings, show_preview=False)
    progress = {"frames": 0}
    started = time.time()

    def update_frame(frame, detections, number):
        progress["frames"] = number
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        preview.image(rgb_frame, channels="RGB", caption="Analysed frame", use_container_width=True)
        status.info(f"Accident-class detections in this frame: {len(detections)}")
        metrics.metric("Frames processed", number)

    try:
        with st.spinner("Loading YOLO and processing video..."):
            incidents = CrashGuardApp(run_settings).run(on_frame=update_frame)
        elapsed = max(time.time() - started, 0.1)
        if incidents:
            st.error("Potential incident triggered. Video and metadata were saved.")
            for incident in incidents:
                st.code(incident)
        else:
            st.success(f"Analysis completed: {progress['frames']} frames in {elapsed:.1f} seconds. No trigger met the configured threshold.")
    except Exception as error:
        st.exception(error)

st.divider()
st.subheader("Before a real drive")
st.markdown("""
- Put your trained weights at the configured `model_path`; this app will not run without them.
- Test on held-out crash and normal-driving videos, then tune the confidence and consecutive-frame settings.
- Configure GPS only with a real receiver and enable live SMS only after recipient testing and consent.
- Incident folders are saved below `storage/incidents`.
""")
