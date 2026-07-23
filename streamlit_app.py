import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# -------------------------
# 1. Page Config (MUST be first)
# -------------------------
st.set_page_config(
    page_title="Smart Parking Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 2. 3D Parking Function (Moved here to prevent ImportError)
# -------------------------
def build_parking_scene(slot_status):
    fig = go.Figure()

    # Define simple 3D coordinates for the parking slots (x, y, z)
    x_coords = [0, 5, 10]
    y_coords = [0, 0, 0]
    z_coords = [0, 0, 0]

    # Map slot status to colors (Red for Occupied, Green for Free)
    colors = ['#ef4444' if status == 'Occupied' else '#22c55e' for status in slot_status]
    hover_texts = [f"Slot {i+1}: {status}" for i, status in enumerate(slot_status)]

    # Draw the parking spots as 3D markers
    fig.add_trace(go.Scatter3d(
        x=x_coords, y=y_coords, z=z_coords,
        mode='markers',
        marker=dict(size=40, color=colors, symbol='square', line=dict(width=2, color='white')),
        text=hover_texts, hoverinfo='text'
    ))

    # Clean up the 3D grid layout to match your dark theme
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            bgcolor='#0f172a'
        ),
        paper_bgcolor='#0f172a',
        margin=dict(l=0, r=0, b=0, t=0),
        height=400
    )
    return fig

# -------------------------
# 3. CSS Styling
# -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #0f172a; }
.stApp { background: #0f172a; }
h1, h2, h3, h4 { color: white; }
div[data-testid="metric-container"] {
    background: #1e293b; padding: 20px; border-radius: 15px; box-shadow: 0px 0px 12px rgba(0,0,0,.25);
}
section[data-testid="stSidebar"] { background: #111827; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# 4. Sidebar
# -------------------------
st.sidebar.title("🚗 Smart Parking")
page = st.sidebar.radio("Navigation", ["Dashboard", "Parking", "History", "Analytics", "Settings"])
st.sidebar.divider()
auto_refresh = st.sidebar.toggle("Auto Refresh", True)
dark = st.sidebar.toggle("Dark Mode", True)
show_labels = st.sidebar.toggle("Show Labels", True)
st.sidebar.divider()
st.sidebar.success("🟢 System Online")

# -------------------------
# 5. Data Initialization
# -------------------------
slot_status = ["Occupied", "Free", "Occupied"]

occupied = slot_status.count("Occupied")
free = slot_status.count("Free")
total = len(slot_status)

# -------------------------
# 6. Header Section
# -------------------------
left, right = st.columns([6, 1])
with left:
    st.title("🚗 Smart Parking Dashboard")
    st.caption(f"Last Updated : {datetime.now().strftime('%H:%M:%S')}")
with right:
    st.success("Online")

# -------------------------
# 7. KPI Cards
# -------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Slots", total)
c2.metric("Available", free)
c3.metric("Occupied", occupied)
c4.metric("Occupancy", f"{occupied/total:.0%}")
st.divider()

# -------------------------
# 8. 3D Parking Lot Visualization
# -------------------------
st.subheader("Live 3D View")

# Generate the figure using the data and display it
fig = build_parking_scene(slot_status)
st.plotly_chart(fig, use_container_width=True)
