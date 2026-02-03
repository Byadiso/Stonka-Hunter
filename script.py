import streamlit as st
import os
import cv2
import numpy as np
import requests
from ultralytics import YOLO
from streamlit_geolocation import streamlit_geolocation
from datetime import datetime


st.set_page_config(
    page_title="Pest Hunter PRO",
    page_icon="🐞",
    layout="centered"
)

st.title("🐞 Pest Hunter PRO – Stonka AI Detection")


SAVE_DIR = "detections"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)


@st.cache_resource
def load_model():
    MODEL_PATH = "runs/detect/stonka_model3/weights/best.pt"
    try:
        if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
            st.success("✅ Loaded trained Stonka model")
            return YOLO(MODEL_PATH)
        else:
            raise ValueError("Model file missing or invalid")
    except Exception as e:
        st.warning("⚠️ Trained model not usable — falling back to YOLOv8n")
        st.caption(f"Reason: {e}")
        return YOLO("yolov8n.pt") 

model = load_model()
class_names = model.names 


st.sidebar.header("⚙️ Detection Settings")
conf_thresh = st.sidebar.slider("Confidence Threshold", 0.05, 1.0, 0.20, help="Lower this if Beetles are being missed.")
iou_thresh = st.sidebar.slider("IOU Threshold", 0.1, 1.0, 0.45)

st.sidebar.divider()
st.sidebar.header("📍 Location Settings")
location = streamlit_geolocation()

CITY_COORDS = {
    "Warsaw": (52.23, 21.01), "Krakow": (50.06, 19.94),
    "Poznan": (52.41, 16.92), "Wroclaw": (51.11, 17.03),
    "Lublin": (51.25, 22.57), "Bialystok": (53.13, 23.16),
    "Lodz": (51.75, 19.46)
}

selected_city = st.sidebar.selectbox("Select City (Manual Fallback)", list(CITY_COORDS.keys()))

if location.get("latitude"):
    lat, lon = location["latitude"], location["longitude"]
    location_name = "Your GPS Location"
else:
    lat, lon = CITY_COORDS[selected_city]
    location_name = selected_city


def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        data = requests.get(url, timeout=5).json()
        return data["current_weather"]["temperature"]
    except:
        return None

current_temp = get_weather(lat, lon)
if current_temp is not None:
    st.info(f"📍 {location_name} | 🌡️ {current_temp}°C")
else:
    st.warning("⚠️ Weather service currently unavailable.")


st.subheader("📸 Field Image Input")
mode = st.radio("Choose image source:", ["Camera (On-field)", "Upload Image"])

if mode == "Camera (On-field)":
    image_file = st.camera_input("Take a photo of the potato leaf")
else:
    image_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])


if image_file is not None:
    bytes_data = np.frombuffer(image_file.read(), np.uint8)
    img = cv2.imdecode(bytes_data, cv2.IMREAD_COLOR)
    original_img = img.copy() 

    results = model(img, conf=conf_thresh, iou=iou_thresh)
    boxes = results[0].boxes

    stonka_count = 0
    other_insects = {}

    for box in boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = class_names[cls_id].title()
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if "Beetle" in label:
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

    
    st.image(img, channels="BGR", caption=f"Detection Results")

    if stonka_count > 0:
        st.error(f"🚨 ALERT: {stonka_count} STONKA (BEETLES) DETECTED!")
        if stonka_count >= 5:
            st.balloons()
    
    if other_insects:
        st.divider()
        st.write("🔍 **Other Insects Identified:**")
        for name, count in other_insects.items():
            st.write(f"- {name}: {count}")
        
    if stonka_count == 0 and not other_insects:
        st.success("✅ Field looks clear.")

  
    st.divider()
    if st.button("💾 Save Detection to History"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SAVE_DIR}/detection_{timestamp}.jpg"
        
       
        summary_text = f"Stonka: {stonka_count} | Temp: {current_temp}C"
        cv2.putText(img, summary_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imwrite(filename, img)
        st.success(f"Report saved as {filename}")


st.markdown("---")
st.caption("Powered by YOLOv8 • Save feature enabled 💾")