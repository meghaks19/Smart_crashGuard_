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

# DEMO GPS LOCATION
# Replace this with your actual GPS module/location later.

GPS_LOCATION = "12.9716° N, 77.5946° E"


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
# VIDEO UPLOAD
# ============================================================

uploaded_video = st.file_uploader(
    "Upload Accident Video",
    type=["mp4", "avi", "mov"]
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

    if uploaded_video is None:

        st.warning(
            "⚠️ Please upload a video first."
        )

    else:

        # ----------------------------------------------------
        # Create output folder
        # ----------------------------------------------------

        os.makedirs(
            "outputs",
            exist_ok=True
        )


        # ----------------------------------------------------
        # Save uploaded video
        # ----------------------------------------------------

        video_path = (
            "outputs/uploaded_video.mp4"
        )

        with open(
            video_path,
            "wb"
        ) as video_file:

            video_file.write(
                uploaded_video.getbuffer()
            )

# ----------------------------------------------------
# Load YOLO damage detector
# ----------------------------------------------------

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "yolov8n.pt"
)

detector = DamageDetector(
    model_path=MODEL_PATH,
    conf=0.45
)

# ----------------------------------------------------
# Check model
# ----------------------------------------------------

if not detector.available:

    st.error(
        "❌ YOLO model is not available."
    )

    st.info(
        f"Check model file: {MODEL_PATH}"
    )

else:

    st.info(
        "🤖 Analyzing video..."
    )

    # ------------------------------------------------
    # Open video with OpenCV
    # ------------------------------------------------

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():

        st.error(
            "❌ Cannot open uploaded video."
        )

    else:
        # Continue with your existing video-processing code here
        
                # --------------------------------------------
                # Video information
                # --------------------------------------------

                total_frames = int(
                    cap.get(
                        cv2.CAP_PROP_FRAME_COUNT
                    )
                )


                frame_number = 0
                frames_checked = 0
                positive_frames = 0

                consecutive_positive = 0
                max_consecutive_positive = 0

                max_confidence = 0.0
                detected_label = None

                accident_found = False


                # --------------------------------------------
                # Progress bar
                # --------------------------------------------

                progress = st.progress(0)


                # --------------------------------------------
                # Read video frame-by-frame
                # --------------------------------------------

                while True:

                    success, frame = cap.read()


                    if not success:
                        break


                    frame_number += 1


                    # Process every 5th frame
                    if frame_number % 5 != 0:
                        continue


                    frames_checked += 1


                    # ----------------------------------------
                    # YOLO detection
                    # ----------------------------------------

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


                        # Find highest confidence
                        for detection in detections:

                            confidence = float(
                                detection.get(
                                    "conf",
                                    0
                                )
                            )

                            label = detection.get(
                                "label",
                                "damage"
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


                    # ----------------------------------------
                    # Confirm accident
                    # ----------------------------------------

                    if (
                        max_consecutive_positive
                        >= 5
                    ):

                        accident_found = True

                        break


                    # ----------------------------------------
                    # Update progress
                    # ----------------------------------------

                    if total_frames > 0:

                        progress_value = (
                            frame_number
                            / total_frames
                        )

                        progress.progress(
                            min(
                                progress_value,
                                1.0
                            )
                        )


                # --------------------------------------------
                # Release video
                # --------------------------------------------

                cap.release()

                progress.progress(1.0)


                # =================================================
                # ACCIDENT DETECTED
                # =================================================

                if accident_found:

                    now = datetime.now()


                    accident_date = (
                        now.strftime(
                            "%d-%m-%Y"
                        )
                    )


                    accident_time = (
                        now.strftime(
                            "%H:%M:%S"
                        )
                    )


                    # Save session data
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


                    # ---------------------------------------------
                    # Display result
                    # ---------------------------------------------

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
                            "Time",
                            accident_time
                        )


                    with col3:

                        st.metric(
                            "Confidence",
                            f"{max_confidence * 100:.1f}%"
                        )


                    st.write(
                        f"📍 GPS Location: "
                        f"{GPS_LOCATION}"
                    )


                    if detected_label:

                        st.write(
                            f"🔎 Detected: "
                            f"{detected_label}"
                        )


                    st.write(
                        f"🎞️ Frames checked: "
                        f"{frames_checked}"
                    )


                    st.write(
                        f"✅ Positive frames: "
                        f"{positive_frames}"
                    )


                    st.write(
                        f"🔁 Consecutive detections: "
                        f"{max_consecutive_positive}"
                    )


                # =================================================
                # NO ACCIDENT
                # =================================================

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
            # Create emergency message
            # ------------------------------------------------

            emergency_message = (
                "🚨 SMART CRASHGUARD ALERT 🚨\n\n"
                "Possible accident detected.\n\n"
                f"Date: "
                f"{st.session_state.accident_date}\n"
                f"Time: "
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
