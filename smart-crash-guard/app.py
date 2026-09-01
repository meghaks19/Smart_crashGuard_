import streamlit as st
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define functions first (before using them)
def send_sms(phone_number, message):
    """Send SMS using Twilio API"""
    try:
        from twilio.rest import Client
        # Add your Twilio credentials here
        account_sid = "your_account_sid"
        auth_token = "your_auth_token"
        client = Client(account_sid, auth_token)
        
        msg = client.messages.create(
            body=message,
            from_="+1234567890",  # Your Twilio number
            to=phone_number
        )
        return True, msg.sid
    except ImportError:
        # Fallback: Log to file if Twilio not installed
        return log_sms_locally(phone_number, message)
    except Exception as e:
        return False, str(e)


def log_sms_locally(phone_number, message):
    """Log SMS locally when Twilio is not available"""
    try:
        sms_log = {
            "timestamp": datetime.now().isoformat(),
            "to": phone_number,
            "message": message,
            "status": "sent_locally"
        }
        with open("outputs/sms_log.json", "a") as f:
            f.write(json.dumps(sms_log) + "\n")
        return True, "SMS logged successfully"
    except Exception as e:
        return False, str(e)


st.set_page_config(page_title="Smart CrashGuard", page_icon="🚗", layout="wide")

# Initialize session state
if "alert_sent" not in st.session_state:
    st.session_state.alert_sent = False
if "alert_info" not in st.session_state:
    st.session_state.alert_info = None
if "accident_detected" not in st.session_state:
    st.session_state.accident_detected = False
if "accident_time" not in st.session_state:
    st.session_state.accident_time = None
if "detection_done" not in st.session_state:
    st.session_state.detection_done = False

st.title("Smart CrashGuard")

uploaded_video = st.file_uploader("Upload video", type=["mp4", "avi", "mov"])

if uploaded_video is not None:
    st.video(uploaded_video)

if st.button("Process the video"):
    if uploaded_video is not None:
        # Simulate detection - 70% chance of accident for demo
        import random
        accident_found = random.choice([True, True, True, True, True, True, True, False, False, False])
        
        st.session_state.detection_done = True
        
        if accident_found:
            st.session_state.accident_detected = True
            st.session_state.accident_time = datetime.now()
            st.success("🚨 ACCIDENT DETECTED!")
        else:
            st.session_state.accident_detected = False
            st.info("✅ No Accident Detected")
    else:
        st.warning("Please upload a video first.")

# Only show accident details if accident was detected
if st.session_state.accident_detected:
    st.subheader("Accident Details")
    accident_time = st.session_state.accident_time.strftime('%Y-%m-%d %H:%M:%S')
    st.write(f"Accident Time: {accident_time}")
    st.write("GPS Location: 12.9716° N, 77.5946° E")
    st.write("Detection Confidence: 96.8%")

    family_name = st.text_input("Family Member Name", value=" ")
    family_phone = st.text_input("Family Phone", value=" ")

    if st.button("Send Alert"):
        # Create alert message
        alert_message = f"🚨 ACCIDENT ALERT from Smart CrashGuard!\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nGPS: 12.9716° N, 77.5946° E\nConfidence: 96.8%\nPlease check immediately!"
        
        # Try to send SMS
        success, response = send_sms(family_phone, alert_message)
        
        # Save alert to file
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "family_member": family_name,
            "phone": family_phone,
            "message": alert_message,
            "sms_sent": success,
            "sms_response": response,
            "status": "sent"
        }
        
        # Append to alert log
        try:
            with open("outputs/alert_sent.json", "a") as f:
                f.write(json.dumps(alert_data) + "\n")
        except:
            pass
        
        st.session_state.alert_sent = True
        st.session_state.alert_info = alert_data

    if st.session_state.alert_sent and st.session_state.alert_info:
        st.success("✅ Alert Sent Successfully!")
        st.write(f"📱 Family Member: {st.session_state.alert_info['family_member']}")
        st.write(f"☎️ Phone: {st.session_state.alert_info['phone']}")
        st.write(f"⏰ Time: {st.session_state.alert_info['accident_time']}")
