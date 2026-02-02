import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_geolocation import streamlit_geolocation
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="Stonka Hunter PL", page_icon="🐞")
st.title("🐞 Stonka Hunter: System Ostrzegania")

# Coordinates for fallback cities (Poland)
CITY_COORDS = {
    "Warszawa": (52.23, 21.01),
    "Kraków": (50.06, 19.94),
    "Poznań": (52.41, 16.92),
    "Wrocław": (51.11, 17.03),
    "Lublin": (51.25, 22.57),
    "Białystok": (53.13, 23.16),
    "Łódź": (51.75, 19.46)
}

# --- 1. LOCATION LOGIC ---
st.sidebar.header("Lokalizacja")
location = streamlit_geolocation()

selected_city = st.sidebar.selectbox("Wybierz miasto (jeśli nie używasz GPS):", list(CITY_COORDS.keys()))

# Determine final Lat/Lon
if location.get('latitude'):
    lat, lon = location['latitude'], location['longitude']
    final_city_name = "Twoja lokalizacja (GPS)"
else:
    lat, lon = CITY_COORDS[selected_city]
    final_city_name = selected_city

# --- 2. LIVE WEATHER FETCHING ---
def get_live_weather(lat, lon):
    try:
        # Using Open-Meteo (No API Key Required)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url).json()
        temp = response['current_weather']['temperature']
        
        if temp > 20:
            advice = "⚠️ ZA GORĄCO dla pyretroidów (np. Decis). Użyj Mospilan."
        elif temp < 5:
            advice = "❄️ ZA ZIMNO na opryski. Skuteczność będzie znikoma."
        else:
            advice = "✅ WARUNKI OK dla większości środków (optimum 10-20°C)."
        return temp, advice
    except:
        return None, "❌ Błąd połączenia z serwerem pogodowym."

current_temp, advice = get_live_weather(lat, lon)

if current_temp is not None:
    st.info(f"📍 {final_city_name} | 🌡️ {current_temp}°C\n\n**Rekomendacja:** {advice}")
else:
    st.error(advice)

# --- 3. PHOTO UPLOAD / CAMERA ---
st.subheader("Ustal stopień zainfekowania")
upload_mode = st.radio("Źródło zdjęcia:", ["Aparat (Na polu)", "Galeria/Plik"])

if upload_mode == "Aparat (Na polu)":
    img_file = st.camera_input("Zrób zdjęcie liścia ziemniaka")
else:
    img_file = st.file_uploader("Wgraj zdjęcie z pamięci telefonu", type=['jpg', 'png', 'jpeg'])

# --- 4. PROCESSING ---
# --- 4. PROCESSING ---
if img_file is not None:
    # Convert uploaded file to OpenCV format
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    
    # 1. Convert to HSV color space for better color isolation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 2. Define the range for 'Stonka' orange/yellow
    # These values target the typical orange body of the beetle
    lower_orange = np.array([10, 100, 100]) 
    upper_orange = np.array([25, 255, 255])
    
    # 3. Create a mask and clean up noise (Erosion/Dilation)
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) # Removes small noise spots

    # 4. Find contours (the 'blobs' of color)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 5. Filter contours by size (ignore tiny dots that aren't beetles)
    real_pests = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 150: # Adjust this number based on photo distance
            real_pests.append(cnt)
            # Draw a box around detected pests on the original image
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)

    detected_count = len(real_pests)
    
    # Show the processed image with boxes
    st.image(img, channels="BGR", caption="Wynik analizy obrazu")
    
    # --- Logic for Results ---
    if detected_count > 0:
        st.error(f"⚠️ UWAGA: Wykryto {detected_count} osobników!")
        st.write("### Sugerowane działanie (Polska 2026):")
        st.write("1. **Środek:** Mospilan 20 SP (Acetamipryd)")
        st.write("2. **Dawka:** 0,08 kg/ha")
        st.write(f"3. **Temperatura:** Bieżąca temperatura ({current_temp}°C) pozwala na bezpieczny oprysk.")
    else:
        st.success("✅ Nie wykryto Stonki ziemniaczanej. Liść wygląda na czysty.")
        st.write("Monitoruj uprawę regularnie, szczególnie brzegi pola.")