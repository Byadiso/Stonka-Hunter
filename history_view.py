import streamlit as st
import os
import cv2
from datetime import datetime

SAVE_DIR = "detections"

def show_history_tab():
    st.subheader("📂 Detection History")

    if not os.path.exists(SAVE_DIR):
        st.info("No detection history available yet.")
        return

    files = [
        f for f in os.listdir(SAVE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if not files:
        st.info("No detection images found.")
        return

    files.sort(reverse=True)
    st.caption(f"📸 Total saved detections: {len(files)}")

    for file in files:
        path = os.path.join(SAVE_DIR, file)

        try:
            ts = file.replace("detection_", "").replace(".jpg", "")
            time_str = datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M")
        except:
            time_str = "Unknown time"

        with st.expander(f"🕒 Detection at {time_str}"):
            img = cv2.imread(path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            st.image(img, use_container_width=True)

            if st.button("🗑️ Delete Detection", key=file):
                os.remove(path)
                st.success("Detection deleted")
                st.experimental_rerun()
