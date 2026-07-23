"""
Car parking system using iot
------------------------------
A Streamlit app that fetches live parking-slot status data from a public
Google Sheets CSV export, renders an interactive 3D lot with correctly oriented .stl car models, 
and displays a color-coded history table.
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Optional auto-refresh support.
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# Optional trimesh support for external 3D models (.stl, etc.).
try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False

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
# 3D Geometry Helpers (.STL Model with Fixed Orientation + Fallback)
# ----------------------------------------------------------------------
SLOT_WIDTH = 3.0     
SLOT_DEPTH = 5.0     
SLOT_GAP = 1.5        
SLOT_CENTERS = [i * (SLOT_WIDTH + SLOT_GAP) for i in range(3)] 

def make_slot_floor_full(x_center: float, color: str) -> go.Mesh3d:
    x0, x1 = x_center - SLOT_WIDTH / 2, x_center + SLOT_WIDTH / 2
    y0, y1 = 0.0, SLOT_DEPTH
    xs = [x0, x1, x1, x0]
    ys = [y0, y0, y1, y1]
    zs = [0, 0, 0, 0]
    return go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=[0, 0], j=[1, 2], k=[2, 3],
        color=color,
        opacity=0.85,
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
        name="",
    )

def make_slot_border(x_center: float) -> go.Scatter3d:
    x0, x1 = x_center - SLOT_WIDTH / 2, x_center + SLOT_WIDTH / 2
    y0, y1 = 0.0, SLOT_DEPTH
    xs = [x0, x1, x1, x0, x0]
    ys = [y0, y0, y1, y1, y0]
    zs = [0.01] * 5
    return go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="lines",
        line=dict(color="white", width=4),
        hoverinfo="skip",
        showlegend=False,
    )

def make_box(x0, x1, y0, y1, z0, z1, color, opacity=1.0):
    xs = [x0, x0, x1, x1, x0, x0, x1, x1]
    ys = [y0, y1, y1, y0, y0, y1, y1, y0]
    zs = [z0, z0, z0, z0, z1, z1, z1, z1]

    i_idx = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j_idx = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k_idx = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]

    return go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=i_idx, j=j_idx, k=k_idx,
        color=color,
        opacity=opacity,
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
        name="",
    )

def make_car(x_center: float) -> list:
    """Loads a local .stl 3D car model, fixes the upside-down and facing direction, and positions it."""
    stl_files = ["car.stl", "scene.stl", "model.stl"]
    found_file = None
    
    for f in stl_files:
        if os.path.exists(f):
            found_file = f
            break
            
    if TRIMESH_AVAILABLE and found_file:
        try:
            mesh = trimesh.load(found_file)
            
            # Handle if trimesh loads it as a scene
            if isinstance(mesh, trimesh.Scene):
                mesh = mesh.dump(concatenate=True)
                
            if isinstance(mesh, trimesh.Trimesh) and len(mesh.vertices) > 0:
                vertices = mesh.vertices
                faces = mesh.faces
                
                # Center before rotating
                vertices = vertices - vertices.mean(axis=0)
                
                # Apply corrected rotations:
                # 1. Rotate around Z by 270 degrees to correct heading direction
                angle_z = np.radians(270)
                R_z = np.array([
                    [np.cos(angle_z), -np.sin(angle_z), 0],
                    [np.sin(angle_z), np.cos(angle_z), 0],
                    [0, 0, 1]
                ])
                
                # 2. Rotate around X by 90 degrees to flip it right-side up onto its wheels
                angle_x = np.radians(90)
                R_x = np.array([
                    [1, 0, 0],
                    [0, np.cos(angle_x), -np.sin(angle_x)],
                    [0, np.sin(angle_x), np.cos(angle_x)]
                ])
                
                vertices = np.dot(vertices, R_z.T)
                vertices = np.dot(vertices, R_x.T)
                
                # Auto-scale to fit inside the parking slot nicely
                extents = mesh.extents
                max_extent = max(extents)
                if max_extent > 0:
                    target_size = SLOT_DEPTH * 0.65
                    scale_factor = target_size / max_extent
                    vertices = vertices * scale_factor
                
                # Final centering check
                vertices_centered = vertices - vertices.mean(axis=0)
                
                car_trace = go.Mesh3d(
                    x=vertices_centered[:, 0] + x_center,
                    y=vertices_centered[:, 1] + (SLOT_DEPTH / 2),
                    z=vertices_centered[:, 2] + 0.35, # Lift slightly above floor
                    i=faces[:, 0],
                    j=faces[:, 1],
                    k=faces[:, 2],
                    color="#2563eb",  # Car body color
                    flatshading=True,
                    hoverinfo="skip",
                    name="",
                )
                return [car_trace]
        except Exception:
            pass # Fall back to procedural if any parsing error occurs

    # Fallback procedural car model if file is missing
    car_width = SLOT_WIDTH * 0.62
    car_length = SLOT_DEPTH * 0.65
    
    x0 = x_center - car_width / 2
    x1 = x_center + car_width / 2
    y_center = SLOT_DEPTH / 2
    y0 = y_center - car_length / 2
    y1 = y_center + car_length / 2

    traces = []
    
    # Wheels
    wheel_w = 0.12
    wheel_l = 0.9
    wheel_h = 0.28
    wx_offset = car_width / 2 - 0.02
    wy_offset = car_length * 0.28
    
    for wx in [x_center - wx_offset - wheel_w, x_center + wx_offset]:
        for wy in [y_center - wy_offset, y_center + wy_offset - 0.1]:
            traces.append(make_box(wx, wx + wheel_w, wy, wy + wheel_l, 0.04, wheel_h, color="#0f172a"))

    # Chassis & Cabin
    traces.append(make_box(x0, x1, y0, y1, 0.25, 0.68, color="#2563eb"))
    cabin_margin_x = car_width * 0.14
    traces.append(make_box(
        x0 + cabin_margin_x, x1 - cabin_margin_x,
        y0 + car_length * 0.26, y1 - car_length * 0.22,
        0.68, 1.22, color="#1d4ed8",
    ))

    return traces

def build_parking_scene(slot_statuses: list) -> go.Figure:
    fig = go.Figure()

    for idx, (x_center, status) in enumerate(zip(SLOT_CENTERS, slot_statuses)):
        floor_color = "#dc2626" if status == "Occupied" else "#16a34a"

        fig.add_trace(make_slot_floor_full(x_center, floor_color))
        fig.add_trace(make_slot_border(x_center))

        if status == "Occupied":
            for car_trace in make_car(x_center):
                fig.add_trace(car_trace)

        # Status text label
        fig.add_trace(go.Scatter3d(
            x=[x_center], y=[SLOT_DEPTH / 2], z=[2.2],
            mode="text",
            text=[status],
            textfont=dict(size=15, color="white"),
            hoverinfo="skip",
            showlegend=False,
        ))

        # Slot number label
        fig.add_trace(go.Scatter3d(
            x=[x_center], y=[-0.5], z=[0.05],
            mode="text",
            text=[f"Slot {idx + 1}"],
            textfont=dict(size=13, color="#cbd5e1"),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False, range=[0, 3]),
            aspectmode="data",
            camera=dict(eye=dict(x=1.5, y=-1.8, z=1.2)),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=480,
    )
    return fig

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

    # --- 3D Visualization ---
    st.caption("Click and drag to rotate the 3D parking lot model")
    fig = build_parking_scene(slot_statuses)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
