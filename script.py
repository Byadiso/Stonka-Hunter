import streamlit as st
import os
import cv2
import numpy as np
import requests
from ultralytics import YOLO
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Stonka Hunter",
    page_icon="🐞",
    layout="centered"
)

# Custom CSS for a cleaner look and to fix the geolocation button layout
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Fix for the Geolocation Button: Removing the weird 'Text' gap */
    div[data-testid="stVerticalBlock"] div.stButton button {
        width: 100%;
    }
    
    /* Target the specific container of the geolocation icon to remove the label space */
    .st-emotion-cache-1offfwp {
        display: none !important;
    }

    /* Styling the metric cards */
    [data-testid="stMetricValue"] {
        color: #1f77b4 !important;
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #555555 !important;
    }
    
    /* Custom container for the location button to give it context */
    .geo-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INTRO SECTION ---
st.title("🐞 Stonka Hunter")
st.markdown("""
**Stonka-Hunter** is a computer vision application built with **Streamlit** and **YOLOv8**. 
It is designed to help farmers identify and track the **Colorado Potato Beetle** (*Leptinotarsa decemlineata*), 
commonly known as **Stonka**, in real-time.
""")

# --- DIRECTORY SETUP ---
SAVE_DIR = "detections"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- MODEL LOADING ---
@st.cache_resource
def load_model():
    MODEL_PATH = "runs/detect/stonka_model3/weights/best.pt"
    try:
        if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
            return YOLO(MODEL_PATH)
        else:
            raise ValueError("Model file missing or invalid")
    except Exception as e:
        st.sidebar.warning("⚠️ Using Fallback Model (YOLOv8n)")
        return YOLO("yolov8n.pt") 

model = load_model()
class_names = model.names 

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Detection Settings")
conf_thresh = st.sidebar.slider("Confidence Threshold", 0.05, 1.0, 0.10, help="Lower this if Beetles are being missed.")
iou_thresh = st.sidebar.slider("IOU Threshold", 0.1, 1.0, 0.45)

st.sidebar.divider()
st.sidebar.header("📍 Location & Weather")

# --- IMPROVED LOCATION UX ---
# We create a visual "card" for the button so the user knows what to do
with st.sidebar:
    st.write("🛰️ **Field Geolocation**")
    st.caption("Enable GPS to get local field weather:")
    # This renders the button. The CSS above hides the phantom text.
    location = streamlit_geolocation()

CITY_COORDS = {
    "Warsaw": (52.23, 21.01), "Krakow": (50.06, 19.94),
    "Poznan": (52.41, 16.92), "Wroclaw": (51.11, 17.03),
    "Lublin": (51.25, 22.57), "Bialystok": (53.13, 23.16),
    "Lodz": (51.75, 19.46)
}

selected_city = st.sidebar.selectbox("City Fallback (If GPS off)", list(CITY_COORDS.keys()))

if location.get("latitude"):
    lat, lon = location["latitude"], location["longitude"]
    location_name = "Precise GPS"
    st.sidebar.success("✅ GPS Coordinates Locked")
else:
    lat, lon = CITY_COORDS[selected_city]
    location_name = f"Manual: {selected_city}"

def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        data = requests.get(url, timeout=5).json()
        return data["current_weather"]["temperature"]
    except:
        return None

current_temp = get_weather(lat, lon)

# --- MAIN DASHBOARD METRICS ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Location Status", location_name)
with col2:
    if current_temp is not None:
        st.metric("Field Temperature", f"{current_temp}°C")
    else:
        st.metric("Temperature", "N/A")

# --- IMAGE INPUT ---
st.subheader("📸 Field Image Input")
mode = st.radio("Choose source:", ["Upload Image", "Camera (On-field)"], horizontal=True)

if mode == "Camera (On-field)":
    image_file = st.camera_input("Take a photo of the potato leaf")
else:
    image_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if image_file is not None:
    bytes_data = np.frombuffer(image_file.read(), np.uint8)
    img = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
    
    results = model(img, conf=conf_thresh, iou=iou_thresh)
    boxes = results[0].boxes

    stonka_count = 0
    other_insects = {}

    for box in boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = class_names[cls_id].title()
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if "Beetle" in label or "Stonka" in label:
            color = (0, 0, 255) 
            stonka_count += 1
            display_label = f"⚠️ STONKA {conf:.2f}"
        else:
            color = (0, 255, 255) 
            other_insects[label] = other_insects.get(label, 0) + 1
            display_label = f"{label} {conf:.2f}"

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.putText(img, display_label, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    st.image(img, channels="BGR", use_container_width=True)

    # --- MESSAGING ---
    if stonka_count > 0:
        st.error(f"🚨 **CRITICAL ALERT:** {stonka_count} Stonka Beetle(s) detected!")
        if current_temp is not None and current_temp < 15:
            st.warning("ℹ️ **Biotech Note:** Temp < 15°C. Beetle activity is low and pesticide efficacy may vary.")
    elif other_insects:
        st.warning("💡 **Field Observation:** No Stonka found, but other species detected.")
        with st.expander("Show Biodiversity Details"):
            for name, count in other_insects.items():
                st.write(f"- **{name}**: {count}")
    else:
        st.success("✅ **Field Clear:** No pests detected.")

    # --- SAVE ---
    st.divider()
    if st.button("💾 Save Detection Report"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SAVE_DIR}/detection_{timestamp}.jpg"
        summary_text = f"Stonka: {stonka_count} | Temp: {current_temp}C"
        cv2.putText(img, summary_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imwrite(filename, img)
        st.success(f"Saved to {filename}")

st.markdown("---")
st.caption("Developed by B.D • Powered by YOLOv8 & Streamlit")