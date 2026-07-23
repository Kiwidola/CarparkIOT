import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Optional auto-refresh support
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
def fetch_parking_data(url: str):
    return pd.read_csv(url, header=None)


def get_latest_status(df):
    last_row = df.iloc[-1]

    slot_statuses = []

    for i in range(-3, 0):
        value = str(last_row.iloc[i]).strip().lower()

        if "occ" in value:
            slot_statuses.append("Occupied")
        else:
            slot_statuses.append("Free")

    return slot_statuses


# ----------------------------------------------------------------------
# Geometry
# ----------------------------------------------------------------------

SLOT_WIDTH = 3.0
SLOT_DEPTH = 5.0
SLOT_GAP = 1.5

SLOT_CENTERS = [
    i * (SLOT_WIDTH + SLOT_GAP)
    for i in range(3)
]


def make_slot_floor_full(x_center, color):

    x0 = x_center - SLOT_WIDTH / 2
    x1 = x_center + SLOT_WIDTH / 2

    y0 = 0
    y1 = SLOT_DEPTH

    return go.Mesh3d(
        x=[x0, x1, x1, x0],
        y=[y0, y0, y1, y1],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color=color,
        opacity=0.85,
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
    )


def make_slot_border(x_center):

    x0 = x_center - SLOT_WIDTH / 2
    x1 = x_center + SLOT_WIDTH / 2

    y0 = 0
    y1 = SLOT_DEPTH

    return go.Scatter3d(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        z=[0.01] * 5,
        mode="lines",
        line=dict(color="white", width=4),
        hoverinfo="skip",
        showlegend=False,
    )


def make_box(x0, x1, y0, y1, z0, z1, color, opacity=1):

    xs = [x0, x0, x1, x1, x0, x0, x1, x1]
    ys = [y0, y1, y1, y0, y0, y1, y1, y0]
    zs = [z0, z0, z0, z0, z1, z1, z1, z1]

    return go.Mesh3d(
        x=xs,
        y=ys,
        z=zs,
        i=[0,0,4,4,0,0,1,1,2,2,3,3],
        j=[1,2,5,6,1,5,2,6,3,7,0,4],
        k=[2,3,6,7,5,4,6,5,7,6,4,7],
        color=color,
        opacity=opacity,
        flatshading=True,
        hoverinfo="skip",
        showscale=False,
    )


# ----------------------------------------------------------------------
# Procedural Car (No STL)
# ----------------------------------------------------------------------

def make_car(x_center):

    traces = []

    car_width = SLOT_WIDTH * 0.65
    car_length = SLOT_DEPTH * 0.72

    x0 = x_center - car_width / 2
    x1 = x_center + car_width / 2

    y0 = (SLOT_DEPTH - car_length) / 2
    y1 = y0 + car_length

    # Body
    traces.append(
        make_box(
            x0,
            x1,
            y0,
            y1,
            0.28,
            0.70,
            "#2563eb"
        )
    )

    # Roof
    margin = car_width * 0.18

    traces.append(
        make_box(
            x0 + margin,
            x1 - margin,
            y0 + car_length * 0.22,
            y1 - car_length * 0.20,
            0.70,
            1.10,
            "#1d4ed8"
        )
    )

    # Windows
    traces.append(
        make_box(
            x0 + margin,
            x1 - margin,
            y1 - car_length * 0.25,
            y1 - car_length * 0.18,
            0.72,
            1.05,
            "#87CEEB",
            0.65
        )
    )

    traces.append(
        make_box(
            x0 + margin,
            x1 - margin,
            y0 + car_length * 0.18,
            y0 + car_length * 0.25,
            0.72,
            1.05,
            "#87CEEB",
            0.65
        )
    )

    # Wheels
    wheel_width = 0.12
    wheel_length = 0.8
    wheel_height = 0.28

    wheel_x = car_width / 2 - wheel_width / 2
    wheel_y = car_length * 0.23

    for wx in [
        x_center - wheel_x - wheel_width,
        x_center + wheel_x - wheel_width,
    ]:
        for wy in [
            y0 + wheel_y,
            y1 - wheel_y - wheel_length,
        ]:

            traces.append(
                make_box(
                    wx,
                    wx + wheel_width,
                    wy,
                    wy + wheel_length,
                    0.03,
                    wheel_height,
                    "#111111",
                )
            )

    # Headlights
    traces.append(
        make_box(
            x0 + 0.15,
            x0 + 0.30,
            y1 - 0.08,
            y1,
            0.42,
            0.52,
            "#fff799",
        )
    )

    traces.append(
        make_box(
            x1 - 0.30,
            x1 - 0.15,
            y1 - 0.08,
            y1,
            0.42,
            0.52,
            "#fff799",
        )
    )

    # Tail lights
    traces.append(
        make_box(
            x0 + 0.15,
            x0 + 0.30,
            y0,
            y0 + 0.08,
            0.42,
            0.52,
            "#ff4444",
        )
    )

    traces.append(
        make_box(
            x1 - 0.30,
            x1 - 0.15,
            y0,
            y0 + 0.08,
            0.42,
            0.52,
            "#ff4444",
        )
    )

    return traces
# ----------------------------------------------------------------------
# Build 3D Parking Scene
# ----------------------------------------------------------------------

def build_parking_scene(slot_statuses):

    fig = go.Figure()

    for idx, (x_center, status) in enumerate(zip(SLOT_CENTERS, slot_statuses)):

        floor_color = "#dc2626" if status == "Occupied" else "#16a34a"

        fig.add_trace(make_slot_floor_full(x_center, floor_color))
        fig.add_trace(make_slot_border(x_center))

        if status == "Occupied":
            for trace in make_car(x_center):
                fig.add_trace(trace)

        # Status text
        fig.add_trace(
            go.Scatter3d(
                x=[x_center],
                y=[SLOT_DEPTH / 2],
                z=[2.2],
                mode="text",
                text=[status],
                textfont=dict(size=15, color="white"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # Slot number
        fig.add_trace(
            go.Scatter3d(
                x=[x_center],
                y=[-0.5],
                z=[0.05],
                mode="text",
                text=[f"Slot {idx + 1}"],
                textfont=dict(size=13, color="#cbd5e1"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.update_layout(

        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(
                visible=False,
                range=[0, 3]
            ),
            aspectmode="data",
            camera=dict(
                eye=dict(
                    x=1.5,
                    y=-1.8,
                    z=1.2
                )
            ),
            bgcolor="rgba(0,0,0,0)",
        ),

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=480,
    )

    return fig


# ----------------------------------------------------------------------
# Streamlit App
# ----------------------------------------------------------------------

def main():

    st.title("Car parking system using IoT")

    if st.button("🔄 Refresh Data"):
        fetch_parking_data.clear()
        st.rerun()

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(
            interval=10000,
            key="parking_refresh"
        )

    try:
        data = fetch_parking_data(CSV_URL)
        slot_statuses = get_latest_status(data)

    except Exception as exc:
        st.error(f"Could not fetch data: {exc}")
        return

    st.caption("Click and drag to rotate the parking lot.")

    fig = build_parking_scene(slot_statuses)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

    st.divider()

    st.subheader("Parking Log History")

    history_df = data.copy()

    num_cols = len(history_df.columns)

    if num_cols == 6:
        history_df.columns = [
            "ID",
            "Timestamp",
            "Sensor Log",
            "Slot 1",
            "Slot 2",
            "Slot 3",
        ]

    elif num_cols == 5:
        history_df.columns = [
            "Timestamp",
            "Sensor Log",
            "Slot 1",
            "Slot 2",
            "Slot 3",
        ]

    else:
        history_df.columns = [
            f"Column {i+1}"
            for i in range(num_cols)
        ]

    if "Sensor Log" in history_df.columns:
        history_df = history_df.drop(columns=["Sensor Log"])

    history_df = history_df.iloc[::-1].reset_index(drop=True)

    def highlight_status(val):

        text = str(val).strip().lower()

        if text == "occupied":
            return (
                "background-color:#fee2e2;"
                "color:#991b1b;"
                "font-weight:bold;"
            )

        elif text == "free":
            return (
                "background-color:#dcfce7;"
                "color:#166534;"
                "font-weight:bold;"
            )

        return ""

    slot_cols = [
        c for c in history_df.columns
        if "Slot" in c
    ]

    try:

        if hasattr(history_df.style, "map"):
            styled = history_df.style.map(
                highlight_status,
                subset=slot_cols,
            )
        else:
            styled = history_df.style.applymap(
                highlight_status,
                subset=slot_cols,
            )

        st.dataframe(
            styled,
            hide_index=True,
            use_container_width=True,
        )

    except Exception:

        st.dataframe(
            history_df,
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
