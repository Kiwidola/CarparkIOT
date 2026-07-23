from parking3d import *
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from parking3d import build_parking_scene

fig = build_parking_scene(slot_status)
st.plotly_chart(fig, use_container_width=True)
st.set_page_config(
    page_title="Smart Parking Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CSS
# -------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html,body,[class*="css"]{
font-family:'Inter',sans-serif;
background:#0f172a;
}

.stApp{
background:#0f172a;
}

h1,h2,h3,h4{
color:white;
}

div[data-testid="metric-container"]{
background:#1e293b;
padding:20px;
border-radius:15px;
box-shadow:0px 0px 12px rgba(0,0,0,.25);
}

section[data-testid="stSidebar"]{
background:#111827;
}

.block-container{
padding-top:1rem;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar
# -------------------------

st.sidebar.title("🚗 Smart Parking")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Parking",
        "History",
        "Analytics",
        "Settings"
    ]
)

st.sidebar.divider()

auto_refresh = st.sidebar.toggle(
    "Auto Refresh",
    True
)

dark = st.sidebar.toggle(
    "Dark Mode",
    True
)

show_labels = st.sidebar.toggle(
    "Show Labels",
    True
)

st.sidebar.divider()

st.sidebar.success("🟢 System Online")

# -------------------------
# Fake data
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
# Header
# -------------------------

left,right=st.columns([6,1])

with left:
    st.title("🚗 Smart Parking Dashboard")
    st.caption(
        f"Last Updated : {datetime.now().strftime('%H:%M:%S')}"
    )

with right:
    st.success("Online")

# -------------------------
# KPI Cards
# -------------------------

c1,c2,c3,c4=st.columns(4)

c1.metric(
    "Total Slots",
    total
)

c2.metric(
    "Available",
    free
)

c3.metric(
    "Occupied",
    occupied
)

c4.metric(
    "Occupancy",
    f"{occupied/total:.0%}"
)

st.divider()

# -------------------------
# Placeholder
# -------------------------

st.info(
    "Next part will add the new 3D parking lot."
)
