import os
import cv2
import streamlit as st
from datetime import datetime
from twilio.rest import Client

from damage_detector import DamageDetector


# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Smart CrashGuard",
    page_icon="🚗",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "accident_detected" not in st.session_state:
    st.session_state.accident_detected = False

if "accident_date" not in st.session_state:
    st.session_state.accident_date = ""

if "accident_time" not in st.session_state:
    st.session_state.accident_time = ""

if "gps_location" not in st.session_state:
    st.session_state.gps_location = ""

if "accident_clip" not in st.session_state:
    st.session_state.accident_clip = None


# ============================================================
# TITLE
# ============================================================

st.title("🚗 Smart CrashGuard")

st.write(
    "AI-based vehicle accident detection and emergency alert system"
)


# ============================================================
# GPS LOCATION
# ============================================================

GPS_LATITUDE = 12.9716
GPS_LONGITUDE = 77.5946

GPS_LOCATION = (
    f"{GPS_LATITUDE}° N, "
    f"{GPS_LONGITUDE}° E"
)

st.write(f"📍 GPS Location: {GPS_LOCATION}")

# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "yolov8n.pt"
)


# ============================================================
# LOAD YOLO MODEL
# ============================================================

try:
    detector = DamageDetector(
        model_path=MODEL_PATH,
        conf=0.45
    )

except Exception as error:
    st.error("❌ Failed to load YOLO model.")
    st.exception(error)
    st.stop()


if not detector.available:
    st.error("❌ YOLO model is not available.")

    st.info(
        f"Check model file: {MODEL_PATH}"
    )

    st.stop()


# ============================================================
# TWILIO SMS FUNCTION
# ============================================================

def send_sms(phone_number, message):
    account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
    auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
    twilio_phone = st.secrets["TWILIO_PHONE_NUMBER"]

    client = Client(
        account_sid,
        auth_token
    )

    message_response = client.messages.create(
        body=message,
        from_=twilio_phone,
        to=phone_number
    )

    return message_response.sid


# ============================================================
# EXTRACT ACCIDENT CLIP
# ============================================================

def extract_accident_clip(
    video_path,
    output_path,
    accident_time_seconds,
    before_seconds=600,
    after_seconds=600
):
    """
    Extract a video clip containing:

    10 minutes BEFORE accident
    +
    accident
    +
    10 minutes AFTER accident

    600 seconds = 10 minutes.
    """

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return False, 0, 0

    fps = cap.get(cv2.CAP_PROP_FPS)

    total_frames = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    if fps <= 0:
        cap.release()
        return False, 0, 0

    duration = total_frames / fps

    # --------------------------------------------------------
    # Calculate available clip range
    # --------------------------------------------------------

    start_time = max(
        0,
        accident_time_seconds - before_seconds
    )

    end_time = min(
        duration,
        accident_time_seconds + after_seconds
    )

    if end_time <= start_time:
        cap.release()
        return False, 0, 0

    # --------------------------------------------------------
    # Move to beginning of clip
    # --------------------------------------------------------

    start_frame = int(
        start_time * fps
    )

    end_frame = int(
        end_time * fps
    )

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        start_frame
    )

    # --------------------------------------------------------
    # Video dimensions
    # --------------------------------------------------------

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    if width <= 0 or height <= 0:
        cap.release()
        return False, 0, 0

    # --------------------------------------------------------
    # Create video writer
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height)
    )

    if not writer.isOpened():
        cap.release()
        return False, 0, 0

    # --------------------------------------------------------
    # Extract frames
    # --------------------------------------------------------

    current_frame = start_frame

    while current_frame <= end_frame:

        success, frame = cap.read()

        if not success:
            break

        writer.write(frame)

        current_frame += 1

    writer.release()
    cap.release()

    extracted_duration = (
        end_time - start_time
    )

    return True, start_time, extracted_duration


# ============================================================
# VIDEO UPLOAD
# ============================================================

uploaded_video = st.file_uploader(
    "Upload Accident Video",
    type=[
        "mp4",
        "avi",
        "mov",
        "mkv"
    ]
)


# ============================================================
# DISPLAY VIDEO
# ============================================================

if uploaded_video is not None:

    st.subheader("🎥 Uploaded Video")

    st.video(uploaded_video)


# ============================================================
# PROCESS VIDEO BUTTON
# ============================================================

if st.button(
    "🔍 Process Video",
    type="primary"
):

    # --------------------------------------------------------
    # Check video
    # --------------------------------------------------------

    if uploaded_video is None:

        st.warning(
            "⚠️ Please upload a video first."
        )

        st.stop()


    # --------------------------------------------------------
    # Create output folder
    # --------------------------------------------------------

    output_dir = os.path.join(
        os.path.dirname(__file__),
        "outputs"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Save uploaded video
    # --------------------------------------------------------

    video_path = os.path.join(
        output_dir,
        "uploaded_video.mp4"
    )

    with open(
        video_path,
        "wb"
    ) as video_file:

        video_file.write(
            uploaded_video.getbuffer()
        )


    st.success(
        "✅ Video uploaded successfully."
    )


    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        video_path
    )

    if not cap.isOpened():

        st.error(
            "❌ Cannot open uploaded video."
        )

        st.stop()


    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30.0


    duration_seconds = (
        total_frames / fps
        if total_frames > 0
        else 0
    )


    # ========================================================
    # DETECTION VARIABLES
    # ========================================================

    frame_number = 0
    frames_checked = 0
    positive_frames = 0

    consecutive_positive = 0
    max_consecutive_positive = 0

    max_confidence = 0.0
    detected_label = None

    accident_found = False
    accident_frame = None
    accident_video_time = None


    # ========================================================
    # PROGRESS BAR
    # ========================================================

    progress = st.progress(0)


    # ========================================================
    # READ VIDEO FRAME BY FRAME
    # ========================================================

    while True:

        success, frame = cap.read()

        if not success:
            break


        frame_number += 1


        # ----------------------------------------------------
        # Process every 5th frame
        # ----------------------------------------------------

        if frame_number % 5 != 0:
            continue


        frames_checked += 1


        # ----------------------------------------------------
        # YOLO DETECTION
        # ----------------------------------------------------

        detections = detector.detect(
            frame
        )


        if len(detections) > 0:

            positive_frames += 1

            consecutive_positive += 1


            if (
                consecutive_positive
                > max_consecutive_positive
            ):

                max_consecutive_positive = (
                    consecutive_positive
                )


            # ------------------------------------------------
            # Find highest confidence detection
            # ------------------------------------------------

            for detection in detections:

                confidence = float(
                    detection.get(
                        "conf",
                        0
                    )
                )

                label = detection.get(
                    "label",
                    "object"
                )


                if confidence > max_confidence:

                    max_confidence = (
                        confidence
                    )

                    detected_label = (
                        label
                    )


        else:

            consecutive_positive = 0


        # ====================================================
        # CONFIRM ACCIDENT
        # ====================================================

        if (
            max_consecutive_positive
            >= 5
            and not accident_found
        ):

            accident_found = True

            accident_frame = frame_number

            accident_video_time = (
                frame_number / fps
            )

            # IMPORTANT:
            # Do NOT break here.
            #
            # We continue processing the video so that
            # the 10-minute-after section is available.


        # ====================================================
        # UPDATE PROGRESS
        # ====================================================

        if total_frames > 0:

            progress_value = (
                frame_number / total_frames
            )

            progress.progress(
                min(
                    progress_value,
                    1.0
                )
            )


    # ========================================================
    # RELEASE VIDEO
    # ========================================================

    cap.release()

    progress.progress(1.0)


    # ========================================================
    # ACCIDENT DETECTED
    # ========================================================

    if accident_found:

        now = datetime.now()


        accident_date = now.strftime(
            "%d-%m-%Y"
        )


        # Time inside the uploaded video
        video_minutes = int(
            accident_video_time // 60
        )

        video_seconds = int(
            accident_video_time % 60
        )


        accident_time = (
            f"{video_minutes:02d}:"
            f"{video_seconds:02d}"
        )


        # ----------------------------------------------------
        # Save session data
        # ----------------------------------------------------

        st.session_state.accident_detected = True

        st.session_state.accident_date = (
            accident_date
        )

        st.session_state.accident_time = (
            accident_time
        )

        st.session_state.gps_location = (
            GPS_LOCATION
        )


        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        st.error(
            "🚨 ACCIDENT DETECTED!"
        )


        st.subheader(
            "🚨 Accident Details"
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "Date",
                accident_date
            )


        with col2:

            st.metric(
                "Video Time",
                accident_time
            )


        with col3:

            st.metric(
                "Confidence",
                f"{max_confidence * 100:.1f}%"
            )


        st.write(
            f"📍 GPS Location: {GPS_LOCATION}"
        )

        
        st.write(
            f"🔁 Consecutive detections: "
            f"{max_consecutive_positive}"
        )


        # ====================================================
        # EXTRACT 10 MINUTES BEFORE + AFTER
        # ====================================================

        st.subheader(
            "🎬 Accident Video Extraction"
        )


        st.write(
            "Extracting 10 minutes before "
            "and 10 minutes after the detected accident..."
        )


        accident_clip_path = os.path.join(
            output_dir,
            "accident_clip.mp4"
        )


        success, clip_start, clip_duration = (
            extract_accident_clip(
                video_path=video_path,
                output_path=accident_clip_path,
                accident_time_seconds=(
                    accident_video_time
                ),
                before_seconds=600,
                after_seconds=600
            )
        )


        if success:

            st.session_state.accident_clip = (
                accident_clip_path
            )


            st.success(
                "✅ Accident clip created successfully!"
            )


            # ------------------------------------------------
            # Show extraction information
            # ------------------------------------------------

            actual_before = min(
                600,
                accident_video_time
            )

            actual_after = min(
                600,
                max(
                    0,
                    duration_seconds
                    - accident_video_time
                )
            )


            col1, col2, col3 = st.columns(3)


            with col1:

                st.metric(
                    "Before Accident",
                    f"{actual_before / 60:.1f} min"
                )


            with col2:

                st.metric(
                    "Accident",
                    accident_time
                )


            with col3:

                st.metric(
                    "After Accident",
                    f"{actual_after / 60:.1f} min"
                )


            # ------------------------------------------------
            # Display extracted video
            # ------------------------------------------------

            st.subheader(
                "🎥 Accident Clip"
            )


            with open(
                accident_clip_path,
                "rb"
            ) as clip_file:

                clip_bytes = clip_file.read()


            st.video(
                clip_bytes
            )


            # ------------------------------------------------
            # Download button
            # ------------------------------------------------

            st.download_button(
                label="⬇️ Download Accident Clip",
                data=clip_bytes,
                file_name="accident_clip.mp4",
                mime="video/mp4"
            )


        else:

            st.warning(
                "⚠️ Accident detected, but the "
                "surrounding video clip could not be created."
            )


    # ========================================================
    # NO ACCIDENT
    # ========================================================

    else:

        st.session_state.accident_detected = False

        st.success(
            "✅ No Accident / Damage Detected"
        )


        st.write(
            f"🎞️ Frames checked: "
            f"{frames_checked}"
        )


        st.write(
            f"Positive frames: "
            f"{positive_frames}"
        )


# ============================================================
# FAMILY ALERT SECTION
# ============================================================

if st.session_state.accident_detected:

    st.divider()

    st.subheader(
        "📱 Emergency Family Alert"
    )


    family_name = st.text_input(
        "Family Member Name"
    )


    family_phone = st.text_input(
        "Family Member Phone Number",
        placeholder="+91XXXXXXXXXX"
    )


    # --------------------------------------------------------
    # SEND ALERT
    # --------------------------------------------------------

    if st.button(
        "📨 Send Alert to Family"
    ):

        if family_name == "":

            st.warning(
                "Please enter family member name."
            )


        elif family_phone == "":

            st.warning(
                "Please enter family phone number."
            )


        else:

            # ------------------------------------------------
            # Emergency message
            # ------------------------------------------------

            emergency_message = (
                "🚨 SMART CRASHGUARD ALERT 🚨\n\n"
                "Possible accident detected.\n\n"
                f"Date: "
                f"{st.session_state.accident_date}\n"
                f"Video Time: "
                f"{st.session_state.accident_time}\n"
                f"GPS Location: "
                f"{st.session_state.gps_location}\n\n"
                "Please check immediately."
            )


            # ------------------------------------------------
            # Send SMS
            # ------------------------------------------------

            try:

                sms_sid = send_sms(
                    family_phone,
                    emergency_message
                )


                st.success(
                    "✅ Emergency message sent "
                    "to family member!"
                )


                st.write(
                    f"👤 Family Member: "
                    f"{family_name}"
                )


                st.write(
                    f"📱 Phone: "
                    f"{family_phone}"
                )


                st.write(
                    f"📨 Message ID: "
                    f"{sms_sid}"
                )


            except Exception as error:

                st.error(
                    "❌ Unable to send SMS."
                )


                st.write(
                    f"Error: {error}"
                )

        


