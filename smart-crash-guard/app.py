import os
import cv2
import streamlit as st
from datetime import datetime
from twilio.rest import Client
from damage_detector import DamageDetector


# ==========================================================
# STREAMLIT CONFIG
# ==========================================================

st.set_page_config(
    page_title="Smart CrashGuard",
    page_icon="🚗",
    layout="wide"
)


# ==========================================================
# SESSION STATE
# ==========================================================

if "accident_detected" not in st.session_state:
    st.session_state.accident_detected = False

if "accident_date" not in st.session_state:
    st.session_state.accident_date = ""

if "accident_time" not in st.session_state:
    st.session_state.accident_time = ""

if "gps_location" not in st.session_state:
    st.session_state.gps_location = ""


# ==========================================================
# TITLE
# ==========================================================

st.title("🚗 Smart CrashGuard")

st.write(
    "AI-based accident detection and family alert system"
)


# ==========================================================
# GPS
# ==========================================================

# Demo GPS location.
# Replace this later with real GPS from your device/GPS module.

GPS_LOCATION = "12.9716° N, 77.5946° E"


# ==========================================================
# TWILIO SETTINGS
# ==========================================================

# Recommended: store these in Streamlit Secrets.
#
# .streamlit/secrets.toml
#
# TWILIO_ACCOUNT_SID = "your_account_sid"
# TWILIO_AUTH_TOKEN = "your_auth_token"
# TWILIO_PHONE_NUMBER = "+1234567890"


def send_sms(phone_number, message):

    try:

        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_phone = st.secrets["TWILIO_PHONE_NUMBER"]

        client = Client(
            account_sid,
            auth_token
        )

        sms = client.messages.create(
            body=message,
            from_=twilio_phone,
            to=phone_number
        )

        return True, sms.sid

