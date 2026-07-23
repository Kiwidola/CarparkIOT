"""
Car parking system using iot
------------------------------
A Streamlit app that fetches live parking-slot status data from a public
Google Sheets CSV export. It uses A-Frame (HTML5) to render a 3D parking lot 
with internet-sourced 3D models, and displays a color-coded history table.
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
    
    # Normalise text so "free"/"FREE"/" Free " all behave the same way.
    slot_statuses = []
    
    # We use negative indexing (-3, -2, -1) to always grab the LAST 3 columns.
    for i in range(-3, 0):
        raw_value = str(last_row.iloc[i]).strip().lower()
        status = "Occupied" if "occ" in raw_value else "Free"
        slot_statuses.append(status)

    return slot_statuses

# ----------------------------------------------------------------------
# A-Frame 3D HTML Generator
# ----------------------------------------------------------------------
def build_aframe_scene(slot_statuses: list) -> str:
    """
    Builds an HTML string using A-Frame to render the 3D scene.
    Loads a public 3D GLTF car model from the Khronos GitHub repository.
    """
    slots_html = ""
    # X positions for the 3 slots
    centers = [-3.5, 0, 3.5]
    
    for idx, (x, status) in enumerate(zip(centers, slot_statuses)):
        if status == "Occupied":
            color = "#e03131" # Red
            # Render the 3D model if occupied
            car_html = f'<a-entity gltf-model="#carModel" position="{x} 0 0.5" rotation="0 -90 0" scale="1.5 1.5 1.5"></a-entity>'
        else:
            color = "#2f9e44" # Green
            car_html = "" # Empty slot
        
        slots_html += f"""
        <!-- Slot {idx+1} Floor -->
        <a-plane position="{x} 0 0" rotation="-90 0 0" width="3" height="5.5" color="{color}" material="opacity: 0.8; transparent: true"></a-plane>
        
        <!-- Slot {idx+1} White Border -->
        <a-box position="{x} -0.05 0" width="3.2" height="0.1" depth="5.7" color="#ffffff"></a-box>

        <!-- Status Text Label on Floor -->
        <a-entity position="{x} 0.1 -3.2" rotation="-90 0 0">
            <a-text value="Slot {idx+1}\\n{status}" align="center" color="#ffffff" width="6"></a-text>
        </a-entity>
        {car_html}
        """

    # Assemble the full HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://aframe.io/releases/1.4.2/aframe.min.js"></script>
        <!-- Orbit controls allow you to click and drag to turn the camera -->
        <script src="https://unpkg.com/aframe-orbit-controls@1.3.2/dist/aframe-orbit-controls.min.js"></script>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0E1117;">
        <a-scene embedded background="color: #0E1117;" renderer="antialias: true">
            <a-assets>
                <!-- This pulls a real 3D model file (.glb) directly from the internet! -->
                <a-asset-item id="carModel" src="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb"></a-asset-item>
            </a-assets>

            {slots_html}

            <!-- Lighting -->
            <a-light type="ambient" color="#ffffff" intensity="0.6"></a-light>
            <a-light type="directional" color="#ffffff" intensity="0.8" position="-2 4 2"></a-light>

            <!-- Camera (starts positioned diagonally above the slots) -->
            <a-entity camera look-controls orbit-controls="target: 0 0 0; minDistance: 5; maxDistance: 30; initialPosition: 0 7 10; rotateSpeed: 0.5"></a-entity>
        </a-scene>
    </body>
    </html>
    """
    return html

# ----------------------------------------------------------------------
# App layout & Execution
# ----------------------------------------------------------------------
def main():
    # --- Top Control ---
    if st.button("🔄 Refresh Data"):
        fetch_parking_data.clear()   
        st.rerun()

    if AUTOREFRESH_AVAILABLE:
        # Runs silently in the background
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

    # --- 3D Visualization ---
    st.caption("Click and drag to rotate the parking lot")
    html_code = build_aframe_scene(slot_statuses)
    # Embed the HTML directly into Streamlit
    components.html(html_code, height=500)

    # --- History Table (Bottom) ---
    st.divider()
    st.subheader("Parking Log History")
    
    if data is not None:
        history_df = data.copy()
        
        # Determine columns dynamically
        num_cols = len(history_df.columns)
        if num_cols == 6:
            history_df.columns = ["ID", "Timestamp", "Sensor Log", "Slot 1", "Slot 2", "Slot 3"]
        elif num_cols == 5:
            history_df.columns = ["Timestamp", "Sensor Log", "Slot 1", "Slot 2", "Slot 3"]
        else:
            history_df.columns = [f"Data Column {i+1}" for i in range(num_cols)]
            
        # REMOVE the 3_Sec_Log column
        if "Sensor Log" in history_df.columns:
            history_df = history_df.drop(columns=["Sensor Log"])
            
        # Reverse the dataframe so the newest logs appear at the top
        history_df = history_df.iloc[::-1].reset_index(drop=True)
        
        # --- Add Color to the table ---
        def highlight_status(val):
            # Check if the text matches occupied or free
            text_val = str(val).strip().lower()
            if text_val == "occupied":
                return 'background-color: #ffe3e3; color: #c92a2a; font-weight: bold;' # Light Red
            elif text_val == "free":
                return 'background-color: #d3f9d8; color: #2b8a3e; font-weight: bold;' # Light Green
            return ''
        
        # Apply the color styling only to the Slot columns
        slot_cols = [c for c in history_df.columns if "Slot" in c]
        
        try:
            # Modern pandas uses .map() for styling
            if hasattr(history_df.style, "map"):
                styled_df = history_df.style.map(highlight_status, subset=slot_cols)
            else:
                styled_df = history_df.style.applymap(highlight_status, subset=slot_cols)
                
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        except Exception:
            # Fallback just in case styling fails
            st.dataframe(history_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
