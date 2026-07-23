import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Assuming parking3d is a local module you've created
from parking3d import build_parking_scene

# -------------------------
# 1. Page Config (MUST be the first Streamlit command)
# -------------------------
st.set_page_config(
    page_title="Smart Parking Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 2. CSS Styling
# -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0f172a;
}

.stApp {
    background: #0f172a;
}

h1, h2, h3, h4 {
    color: white;
}

div[data-testid="metric-container"] {
    background: #1e293b;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 0px 12px rgba(0,0,0,.25);
}

section[data-testid="stSidebar"] {
    background: #111827;
}

.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# 3. Sidebar
# -------------------------
st.sidebar.title("🚗 Smart Parking")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Parking", "History", "Analytics", "Settings"]
)

st.sidebar.divider()

auto_refresh = st.sidebar.toggle("Auto Refresh", True)
dark = st.sidebar.toggle("Dark Mode", True)
show_labels = st.sidebar.toggle("Show Labels", True)

st.sidebar.divider()
st.sidebar.success("🟢 System Online")

# -------------------------
# 4. Data Initialization (MUST precede visual generation)
# -------------------------
slot_status = [
    "Occupied",
    "Free",
    "Occupied"
]

occupied = slot_status.count("Occupied")
free = slot_status.count("Free")
total = len(slot_status)

# -------------------------
# 5. Header Section
# -------------------------
left, right = st.columns([6, 1])

with left:
    st.title("🚗 Smart Parking Dashboard")
    st.caption(f"Last Updated : {datetime.now().strftime('%H:%M:%S')}")

with right:
    st.success("Online")

# -------------------------
# 6. KPI Cards
# -------------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Slots", total)
c2.metric("Available", free)
c3.metric("Occupied", occupied)
c4.metric("Occupancy", f"{occupied/total:.0%}")

st.divider()

# -------------------------
# 7. 3D Parking Lot Visualization
# -------------------------
st.subheader("Live 3D View")

# Generate the figure using the now-defined slot_status
fig = build_parking_scene(slot_status)

# Display the plotly chart in the main dashboard area
st.plotly_chart(fig, use_container_width=True)
