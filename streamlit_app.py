"""
Car parking system using iot
------------------------------
A Streamlit app that fetches live parking-slot status data from a public
Google Sheets CSV export, renders interactive Sketchfab 3D car models for 
occupied slots, and displays a color-coded history table.
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Optional auto-refresh support.
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Car parking system using iot",
    page_icon="🚗",
    layout="wide",
)

CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRzZ4yMJDfD8GF3mxFffCaJ1"
    "HtPvT4g1bLyUeszj1ioFaxgvYw1oyvKXSpJgnzovyFzMGOf0f0z5tzZ/pub?output=csv"
)

# ----------------------------------------------------------------------
# Data fetching
# ----------------------------------------------------------------------
@st.cache_data(ttl=10, show_spinner=False)
def fetch_parking_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, header=None)
    return df

def get_latest_status(df: pd.DataFrame):
    last_row = df.iloc[-1]
    
    slot_statuses = []
    for i in range(-3, 0):
        raw_value = str(last_row.iloc[i]).strip().lower()
        status = "Occupied" if "occ" in raw_value else "Free"
        slot_statuses.append(status)

    return slot_statuses

# ----------------------------------------------------------------------
# Sketchfab 3D Model Embed Helper (Preserves Original Colors & Textures)
# ----------------------------------------------------------------------
def render_car_model(slot_name: str):
    """Embeds the official Sketchfab 3D viewer component for an occupied slot."""
    html_code = f"""
    <div style="background-color: #1e293b; padding: 10px; border-radius: 10px; border: 2px solid #ef4444; text-align: center;">
        <h4 style="color: #f87171; margin-bottom: 8px; font-family: sans-serif;">🚗 {slot_name}: Occupied</h4>
        <div class="sketchfab-embed-wrapper" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
            <iframe title="2003 BMW M3 GTR | Voxel" frameborder="0" allowfullscreen mozallowfullscreen="true" webkitallowfullscreen="true" allow="autoplay; fullscreen; xr-spatial-tracking" xr-spatial-tracking execution-while-out-of-viewport execution-while-not-rendered web-share src="https://sketchfab.com/models/5cf0fc2da4d74c798fc3ca2c261a1499/embed" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe>
        </div>
        <p style="font-size: 11px; margin-top: 6px; color: #94a3b8; font-family: sans-serif;">
            Model by <a href="https://sketchfab.com/Fenrate" target="_blank" style="color: #38bdf8;">Fenrate</a> on Sketchfab
        </p>
    </div>
    """
    components.html(html_code, height=340)

def render_empty_slot(slot_name: str):
    """Renders a clean placeholder card for a free parking slot."""
    html_code = f"""
    <div style="background-color: #064e3b; padding: 40px 10px; border-radius: 10px; border: 2px solid #22c55e; text-align: center; height: 280px; display: flex; flex-direction: column; justify-content: center;">
        <h3 style="color: #4ade80; margin: 0; font-family: sans-serif;">🅿️ {slot_name}</h3>
        <p style="color: #86efac; font-size: 18px; font-weight: bold; margin-top: 10px; font-family: sans-serif;">STATUS: FREE</p>
        <p style="color: #d1fae5; font-size: 13px; font-family: sans-serif;">Ready for parking</p>
    </div>
    """
    components.html(html_code, height=340)

# ----------------------------------------------------------------------
# App layout & Execution
# ----------------------------------------------------------------------
def main():
    # --- Title ---
    st.title("Car parking system using iot")
    
    # --- Top Control ---
    if st.button("🔄 Refresh Data"):
        fetch_parking_data.clear()   
        st.rerun()

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=10_000, key="parking_autorefresh")

    # --- Fetch Data ---
    try:
        data = fetch_parking_data(CSV_URL)
        slot_statuses = get_latest_status(data)
        fetch_error = None
    except Exception as exc:
        data = None
        slot_statuses = ["Free", "Free", "Free"]
        fetch_error = str(exc)

    if fetch_error:
        st.error(f"Could not fetch live data: {fetch_error}")
        return

    # --- Live 3D Slot Display ---
    st.caption("Live Interactive Parking Slots (Powered by Sketchfab 3D Viewer)")
    
    cols = st.columns(3)
    for idx, (col, status) in enumerate(zip(cols, slot_statuses)):
        slot_name = f"Slot {idx + 1}"
        with col:
            if status == "Occupied":
                render_car_model(slot_name)
            else:
                render_empty_slot(slot_name)

    # --- History Table (Bottom) ---
    st.divider()
    st.subheader("Parking Log History")
    
    if data is not None:
        history_df = data.copy()
        
        num_cols = len(history_df.columns)
        if num_cols == 6:
            history_df.columns = ["ID", "Timestamp", "Sensor Log", "Slot 1", "Slot 2", "Slot 3"]
        elif num_cols == 5:
            history_df.columns = ["Timestamp", "Sensor Log", "Slot 1", "Slot 2", "Slot 3"]
        else:
            history_df.columns = [f"Data Column {i+1}" for i in range(num_cols)]
            
        # REMOVE the Sensor Log column completely
        if "Sensor Log" in history_df.columns:
            history_df = history_df.drop(columns=["Sensor Log"])
            
        # Newest logs on top
        history_df = history_df.iloc[::-1].reset_index(drop=True)
        
        # --- Add Color to the table ---
        def highlight_status(val):
            text_val = str(val).strip().lower()
            if text_val == "occupied":
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;' # Soft Red
            elif text_val == "free":
                return 'background-color: #dcfce7; color: #166534; font-weight: bold;' # Soft Green
            return ''
        
        slot_cols = [c for c in history_df.columns if "Slot" in c]
        
        try:
            if hasattr(history_df.style, "map"):
                styled_df = history_df.style.map(highlight_status, subset=slot_cols)
            else:
                styled_df = history_df.style.applymap(highlight_status, subset=slot_cols)
                
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        except Exception:
            st.dataframe(history_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
