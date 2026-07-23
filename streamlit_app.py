"""
Car parking system using iot
------------------------------
A Streamlit app that fetches live parking-slot status data from a public
Google Sheets CSV export, and renders an interactive, rotatable 3D model
of a 3-space parking lot using Plotly.

Run with:
    streamlit run app.py
"""
#aaaaaaaa
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Optional auto-refresh support. If the package isn't installed, the app
# still works fine with the manual "Refresh" button.
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
    """
    Fetch the parking log CSV from Google Sheets.
    The sheet has no header row, so columns are read positionally:
        0 -> Index/Row Number
        1 -> Timestamp
        2 -> Log Type
        3 -> Slot 1 status
        4 -> Slot 2 status
        5 -> Slot 3 status
    """
    df = pd.read_csv(url, header=None)
    return df


def get_latest_status(df: pd.DataFrame):
    """Extract the most recent row and return slot statuses + metadata."""
    last_row = df.iloc[-1]

    timestamp = str(last_row[1]).strip()
    log_type = str(last_row[2]).strip()

    # Normalise text so "free"/"FREE"/" Free " all behave the same way.
    slot_statuses = []
    for col in (3, 4, 5):
        raw_value = str(last_row[col]).strip().lower()
        status = "Occupied" if "occ" in raw_value else "Free"
        slot_statuses.append(status)

    return timestamp, log_type, slot_statuses


# ----------------------------------------------------------------------
# 3D geometry helpers
# ----------------------------------------------------------------------
SLOT_WIDTH = 3.0     # size of a parking slot along X
SLOT_DEPTH = 5.0     # size of a parking slot along Y
SLOT_GAP = 1.5        # gap between adjacent slots
SLOT_CENTERS = [i * (SLOT_WIDTH + SLOT_GAP) for i in range(3)]  # x-centers


def make_slot_floor(x_center: float, color: str) -> go.Mesh3d:
    """
    Build a flat rectangular floor plane for one parking slot,
    colored green (free) or red (occupied).
    """
    x0, x1 = x_center - SLOT_WIDTH / 2, x_center + SLOT_WIDTH / 2
    y0, y1 = 0.0, SLOT_DEPTH

    # 4 corners of the rectangle at z = 0
    xs = [x0, x1, x1, x0]
    ys = [y0, y0, y1, y1]
    zs = [0, 0, 0, 0]

    return go.Mesh3d(
        x=xs, y=ys, z=zs,
        i=[0], j=[1], k=[2],          # first triangle
        # two triangles make the rectangle: (0,1,2) and (0,2,3)
        color=color,
        opacity=0.85,
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
        name="",
    )


def make_slot_floor_full(x_center: float, color: str) -> go.Mesh3d:
    """Rectangle floor built from two triangles (proper full quad)."""
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
    """Draw a thin white outline around a slot so slots are visually separated."""
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
    """
    Build a solid rectangular box (Mesh3d) spanning the given bounds.
    Used as a building block for the stylized 3D car.
    """
    xs = [x0, x0, x1, x1, x0, x0, x1, x1]
    ys = [y0, y1, y1, y0, y0, y1, y1, y0]
    zs = [z0, z0, z0, z0, z1, z1, z1, z1]

    # 12 triangles forming the 6 faces of the box
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
    """
    Build a simple stylized car out of two stacked boxes:
    a wider/lower body and a narrower/higher cabin, centered in the slot.
    Returns a list of Plotly Mesh3d traces.
    """
    car_width = SLOT_WIDTH * 0.6
    car_length = SLOT_DEPTH * 0.6
    x0 = x_center - car_width / 2
    x1 = x_center + car_width / 2
    y0 = SLOT_DEPTH / 2 - car_length / 2
    y1 = SLOT_DEPTH / 2 + car_length / 2

    body = make_box(x0, x1, y0, y1, 0.15, 0.8, color="#1f4fd8")

    cabin_margin_x = car_width * 0.2
    cabin_margin_y = car_length * 0.25
    cabin = make_box(
        x0 + cabin_margin_x, x1 - cabin_margin_x,
        y0 + cabin_margin_y, y1 - cabin_margin_y,
        0.8, 1.3, color="#0f2d80",
    )

    return [body, cabin]


def build_parking_scene(slot_statuses: list) -> go.Figure:
    """Assemble the full 3D scene: 3 slots, floors, borders, cars, labels."""
    fig = go.Figure()

    for idx, (x_center, status) in enumerate(zip(SLOT_CENTERS, slot_statuses)):
        floor_color = "#e03131" if status == "Occupied" else "#2f9e44"

        fig.add_trace(make_slot_floor_full(x_center, floor_color))
        fig.add_trace(make_slot_border(x_center))

        if status == "Occupied":
            for car_trace in make_car(x_center):
                fig.add_trace(car_trace)

        # Text label above the slot: "Free" / "Occupied"
        fig.add_trace(go.Scatter3d(
            x=[x_center], y=[SLOT_DEPTH / 2], z=[2.4],
            mode="text",
            text=[status],
            textfont=dict(size=16, color="white"),
            hoverinfo="skip",
            showlegend=False,
        ))

        # Slot number label
        fig.add_trace(go.Scatter3d(
            x=[x_center], y=[-0.6], z=[0.05],
            mode="text",
            text=[f"Slot {idx + 1}"],
            textfont=dict(size=13, color="#cccccc"),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False, range=[0, 3]),
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=-1.8, z=1.2)),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=600,
    )
    return fig


# ----------------------------------------------------------------------
# App layout & Execution
# ----------------------------------------------------------------------
def main():
    st.title("Car parking system using iot")
    st.caption("Live 3-space parking monitor powered by IoT sensor data")

    col_refresh, col_auto = st.columns([1, 3])

    with col_refresh:
        if st.button("🔄 Refresh"):
            fetch_parking_data.clear()   # force a fresh pull from the sheet
            st.rerun()

    with col_auto:
        if AUTOREFRESH_AVAILABLE:
            # Auto-refresh the whole app every 10 seconds.
            st_autorefresh(interval=10_000, key="parking_autorefresh")
            st.caption("Auto-refreshing every 10 seconds")
        else:
            st.caption(
                "Auto-refresh not installed — click Refresh to pull the latest "
                "data, or run `pip install streamlit-autorefresh` for automatic "
                "updates."
            )

    # --- Fetch and parse the data -----------------------------------------
    try:
        data = fetch_parking_data(CSV_URL)
        timestamp, log_type, slot_statuses = get_latest_status(data)
        fetch_error = None
    except Exception as exc:
        data = None
        timestamp, log_type = "N/A", "N/A"
        slot_statuses = ["Free", "Free", "Free"]
        fetch_error = str(exc)

    if fetch_error:
        st.error(f"Could not fetch live data from the sheet: {fetch_error}")
    else:
        st.success(f"Last log: **{timestamp}**  |  Log type: **{log_type}**")

    # --- Status summary cards ----------------------------------------------
    status_cols = st.columns(3)
    for i, (col, status) in enumerate(zip(status_cols, slot_statuses)):
        with col:
            if status == "Occupied":
                st.error(f"🚗 Slot {i + 1}: **Occupied**")
            else:
                st.success(f"🅿️ Slot {i + 1}: **Free**")

    # --- 3D visualization ----------------------------------------------------
    st.subheader("3D Parking Lot (click and drag to rotate)")
    fig = build_parking_scene(slot_statuses)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    # --- Raw data (optional, for debugging) ---------------------------------
    with st.expander("Show raw sheet data"):
        if data is not None:
            st.dataframe(data.tail(10), use_container_width=True)
        else:
            st.write("No data available.")

if __name__ == "__main__":
    main()
