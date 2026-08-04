"""
IoT Car Parking System Viewer — Streamlit edition
Run with:  streamlit run app.py
"""

import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRzZ4yMJDfD8GF3mxFffCaJ1"
    "HtPvT4g1bLyUeszj1ioFaxgvYw1oyvKXSpJgnzovyFzMGOf0f0z5tzZ/pub?output=csv"
)
BAY_LABELS = ["P-01", "P-02", "P-03"]

st.set_page_config(
    page_title="IoT Car Parking System Viewer",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "floor" not in st.session_state:
    st.session_state.floor = "ground"

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --bg: #0a0f1c;
  --panel: #111a2ecc;
  --panel-2: #16233d;
  --border: #23304c;
  --border-soft: #1a2540;
  --text: #eaf0fb;
  --text-dim: #8a96b8;
  --text-dimmer: #5c6889;
  --free: #34d97a;
  --free-soft: rgba(52, 217, 122, 0.12);
  --occupied: #ff5d6c;
  --occupied-soft: rgba(255, 93, 108, 0.12);
  --amber: #ffb020;
  --amber-soft: rgba(255, 176, 32, 0.12);
  --accent: #4f8cff;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.2rem; max-width: 1180px; }

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

.stApp {
  background:
    radial-gradient(circle at 12% 0%, rgba(79,140,255,0.10), transparent 45%),
    radial-gradient(circle at 88% 10%, rgba(52,217,122,0.08), transparent 40%),
    var(--bg);
  color: var(--text);
}

/* ---- Brand ---- */
.brand { display:flex; align-items:center; gap:10px; padding-top:4px; }
.brand-mark {
  width:34px; height:34px; border-radius:9px;
  background:linear-gradient(135deg,#4f8cff,#34d97a);
  display:flex; align-items:center; justify-content:center; font-size:16px;
}
.brand-text { font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:16px; }

/* ---- Nav buttons ---- */
div[data-testid="stButton"] > button {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid var(--border-soft) !important;
  color: var(--text-dim) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 13.5px !important;
  padding: 6px 10px !important;
  transition: all .15s ease;
}
div[data-testid="stButton"] > button:hover {
  border-color: rgba(79,140,255,0.5) !important;
  color: var(--text) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
  background: rgba(79,140,255,0.16) !important;
  border-color: rgba(79,140,255,0.55) !important;
  color: var(--text) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: rgba(79,140,255,0.22) !important;
}

/* ---- Page header ---- */
.page-title { font-family:'Space Grotesk',sans-serif; font-size:26px; font-weight:600; margin:4px 0 2px; }
.page-subtitle { color:var(--text-dim); font-size:14px; margin-bottom: 6px;}

/* ---- Live tag ---- */
.live-tag {
  display:inline-flex; align-items:center; gap:8px;
  background: var(--panel); border:1px solid var(--border);
  padding:8px 14px; border-radius:999px; font-size:12.5px; color:var(--text-dim); font-weight:500;
}
.live-dot { width:8px; height:8px; border-radius:50%; background:var(--free);
  animation: pulseDot 1.8s infinite; }
.live-dot.amber { background:var(--amber); animation-name: pulseAmber; }
.live-dot.red { background:var(--occupied); animation-name: pulseRed; }
@keyframes pulseDot { 0%{box-shadow:0 0 0 0 rgba(52,217,122,.55);} 70%{box-shadow:0 0 0 7px rgba(52,217,122,0);} 100%{box-shadow:0 0 0 0 rgba(52,217,122,0);} }
@keyframes pulseAmber { 0%{box-shadow:0 0 0 0 rgba(255,176,32,.55);} 70%{box-shadow:0 0 0 7px rgba(255,176,32,0);} 100%{box-shadow:0 0 0 0 rgba(255,176,32,0);} }
@keyframes pulseRed { 0%{box-shadow:0 0 0 0 rgba(255,93,108,.55);} 70%{box-shadow:0 0 0 7px rgba(255,93,108,0);} 100%{box-shadow:0 0 0 0 rgba(255,93,108,0);} }
.timestamp-mono { font-family:'IBM Plex Mono',monospace; color:var(--text); }

.error-banner {
  background: var(--occupied-soft); border:1px solid rgba(255,93,108,0.35);
  color:#ffb3ba; font-size:13px; padding:12px 16px; border-radius:10px; margin: 10px 0;
}

/* ---- Metric cards ---- */
.metric-card {
  display:flex; align-items:center; gap:12px;
  background: var(--panel); border:1px solid var(--border); border-radius:14px;
  padding:16px; backdrop-filter: blur(10px);
}
.metric-icon { width:38px; height:38px; min-width:38px; border-radius:10px;
  display:flex; align-items:center; justify-content:center; font-size:18px; }
.tone-neutral .metric-icon { background: rgba(79,140,255,0.14); color:var(--accent); }
.tone-free .metric-icon { background: var(--free-soft); color:var(--free); }
.tone-occupied .metric-icon { background: var(--occupied-soft); color:var(--occupied); }
.tone-amber .metric-icon { background: var(--amber-soft); color:var(--amber); }
.metric-value { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:600; line-height:1.1; }
.metric-label { color:var(--text-dim); font-size:12px; margin-top:2px; }

/* ---- Panel ---- */
.panel { background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:20px; backdrop-filter: blur(10px); margin-bottom: 6px;}
.panel-title { font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:600; margin:0 0 4px 0; }
.panel-hint { color:var(--text-dimmer); font-size:12px; font-family:'IBM Plex Mono',monospace; }

/* ---- Lot strip ---- */
.lot-strip { display:flex; align-items:center; gap:10px; color:var(--text-dimmer);
  font-family:'IBM Plex Mono',monospace; font-size:10.5px; letter-spacing:.12em; margin: 10px 0 16px; }
.lot-strip-line { flex:1; height:1px; background: repeating-linear-gradient(90deg, var(--border) 0 8px, transparent 8px 14px); }
.lot-strip-arrow { color: var(--accent); font-size:13px; }

/* ---- Bay card ---- */
.bay-card { position:relative; border:2px dashed var(--border); border-radius:14px; padding:16px;
  text-align:center; background:var(--panel-2); }
.bay-card.is-free { border-color: rgba(52,217,122,0.4); background: radial-gradient(circle at 50% 0%, rgba(52,217,122,0.12), var(--panel-2) 70%); }
.bay-card.is-occupied { border-color: rgba(255,93,108,0.4); background: radial-gradient(circle at 50% 0%, rgba(255,93,108,0.12), var(--panel-2) 70%); }
.bay-card.is-unknown { opacity:.55; }
.bay-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.bay-id { font-family:'IBM Plex Mono',monospace; font-size:12px; color:var(--text-dim); }
.bay-sensor { display:flex; align-items:center; gap:4px; font-size:9.5px; color:var(--text-dimmer); letter-spacing:.08em;}
.bay-sensor-dot { width:5px; height:5px; border-radius:50%; background:var(--accent); animation: pulseBlue 2.2s infinite; }
@keyframes pulseBlue { 0%{box-shadow:0 0 0 0 rgba(79,140,255,.5);} 70%{box-shadow:0 0 0 5px rgba(79,140,255,0);} 100%{box-shadow:0 0 0 0 rgba(79,140,255,0);} }
.bay-icon { font-size:30px; margin:6px 0 6px; }
.bay-status-label { font-weight:600; font-size:14px; }
.is-free .bay-status-label { color: var(--free); }
.is-occupied .bay-status-label { color: var(--occupied); }
.bay-substatus { color:var(--text-dimmer); font-size:11px; margin-top:2px; font-family:'IBM Plex Mono',monospace; }

/* ---- Contact (UPDATED) ---- */
.contact-card { 
  display:flex; align-items:center; gap:16px; 
  background:var(--panel); border:1px solid var(--border);
  border-radius:14px; padding:20px; text-decoration:none; color:var(--text); 
  transition: border-color 0.2s ease;
}
.contact-card:hover { border-color: rgba(79,140,255,0.4); }
.contact-icon-box { 
  width:48px; height:48px; min-width:48px; border-radius:12px; 
  display:flex; align-items:center; justify-content:center; 
}
.contact-details { display:flex; flex-direction:column; gap:4px; }
.contact-label { color:var(--text-dim); font-size:12px; text-transform:uppercase; letter-spacing:.05em; font-weight:600;}
.contact-value { font-size:16px; font-weight:600; color:var(--text); }

/* ---- About ---- */
.feature-card { background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:18px; height: 100%;}
.feature-icon { width:38px; height:38px; border-radius:10px; background: rgba(79,140,255,0.14); color:var(--accent);
  display:flex; align-items:center; justify-content:center; margin-bottom:10px; font-size:18px;}
.feature-title { font-weight:600; font-size:14.5px; margin-bottom:4px; }
.feature-text { color:var(--text-dim); font-size:13px; line-height:1.6; margin:0; }

.step-card { background:var(--panel-2); border:1px solid var(--border); border-radius:12px; padding:16px; height:100%;}
.step-number { font-family:'IBM Plex Mono',monospace; color:var(--accent); font-size:12px; }
.step-title { font-weight:600; font-size:14.5px; margin:6px 0 4px; }
.step-text { color:var(--text-dim); font-size:12.5px; line-height:1.6; margin:0; }

.footer-note { text-align:center; color:var(--text-dimmer); font-size:11.5px; margin-top: 30px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

@st.cache_data(ttl=5, show_spinner=False)
def fetch_data() -> pd.DataFrame:
    resp = requests.get(CSV_URL, timeout=10)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), header=None, dtype=str, keep_default_na=False)
    df = df.iloc[:, :5].copy()
    df.columns = ["timestamp", "log_type", "spot1", "spot2", "spot3"][: df.shape[1]]
    
    # 1. FIX: Parse timestamps and forcefully sort chronologically
    df["ts"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
    df = df.sort_values(by="ts").reset_index(drop=True)
    return df

def load_data():
    try:
        df = fetch_data()
        if df.empty:
            return None, "error"
        return df, "live"
    except Exception:
        return None, "error"

# --------------------------------------------------------------------------
# Top navigation
# --------------------------------------------------------------------------

col_logo, col_nav = st.columns([2, 5], gap="small")
with col_logo:
    st.markdown(
        '<div class="brand"><span class="brand-mark">📡</span>'
        '<span class="brand-text">IoT Parking Viewer</span></div>',
        unsafe_allow_html=True,
    )

NAV_ITEMS = [
    ("dashboard", "Live Dashboard"),
    ("history", "History"),
    ("contact", "Contact"),
    ("about", "About Us"),
]

with col_nav:
    nav_cols = st.columns(len(NAV_ITEMS))
    for col, (key, label) in zip(nav_cols, NAV_ITEMS):
        with col:
            kind = "primary" if st.session_state.page == key else "secondary"
            if st.button(label, key=f"nav_{key}", type=kind, use_container_width=True):
                st.session_state.page = key
                st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Page: Live Dashboard
# --------------------------------------------------------------------------

@st.fragment(run_every=5)
def render_dashboard():
    df, status = load_data()
    
    bay_cols = ["spot1", "spot2", "spot3"]
    bays = []
    
    if df is not None and not df.empty:
        latest = df.iloc[-1]
        for i, col in enumerate(bay_cols):
            raw = str(latest.get(col, "")).strip()
            is_free = raw.lower() == "free"
            bays.append({
                "id": BAY_LABELS[i],
                "status": "free" if is_free else ("unknown" if raw == "" else "occupied"),
                "raw": raw or "No signal",
            })
        latest_ts = latest["ts"]
    else:
        latest_ts = None
        bays = [{"id": b, "status": "unknown", "raw": "No signal"} for b in BAY_LABELS]

    free_count = sum(1 for b in bays if b["status"] == "free")
    occupied_count = sum(1 for b in bays if b["status"] == "occupied")
    total_bays = len(bays)
    occupancy_rate = round(occupied_count / total_bays * 100) if total_bays else 0

    left, right = st.columns([3, 2])
    with left:
        st.markdown('<div class="page-title">Live Dashboard</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="page-subtitle">Real-time bay occupancy from the ground-floor sensor array</div>',
            unsafe_allow_html=True,
        )
    with right:
        dot_class = "" if status == "live" else "red"
        label = "Live" if status == "live" else "Signal lost"
        ts_str = latest_ts.strftime("%H:%M:%S") if pd.notna(latest_ts) else "--:--:--"
        st.markdown(
            f'<div style="text-align:right; padding-top:8px;">'
            f'<span class="live-tag"><span class="live-dot {dot_class}"></span>{label}'
            f'&nbsp;&middot;&nbsp;<span class="timestamp-mono">{ts_str}</span></span></div>',
            unsafe_allow_html=True,
        )

    if status == "error":
        st.markdown(
            '<div class="error-banner">Couldn\'t reach the sensor feed. Retrying automatically '
            'every 5 seconds &mdash; the dashboard will resume the moment the sheet responds.</div>',
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4 = st.columns(4)
    metric_defs = [
        (m1, "neutral", "🅿️", "Total Bays", total_bays if total_bays else "--"),
        (m2, "free", "✅", "Available", free_count if total_bays else "--"),
        (m3, "occupied", "🚗", "Occupied", occupied_count if total_bays else "--"),
        (m4, "amber", "📊", "Occupancy Rate", f"{occupancy_rate}%" if total_bays else "--"),
    ]
    for col, tone, icon, label, value in metric_defs:
        with col:
            st.markdown(
                f'<div class="metric-card tone-{tone}">'
                f'<span class="metric-icon">{icon}</span>'
                f'<div><div class="metric-value">{value}</div>'
                f'<div class="metric-label">{label}</div></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            '<div class="panel-title">Lot &amp; Floor Navigation</div>'
            '<div class="panel-hint">Select a zone to inspect its bays</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        f1, f2, f3 = st.columns(3)
        with f1:
            if st.button("Ground Floor · Bays 1–3", key="floor_ground",
                         type="primary" if st.session_state.floor == "ground" else "secondary",
                         use_container_width=True):
                st.session_state.floor = "ground"
                st.rerun()
        with f2:
            if st.button("🔒 Level 2 · Awaiting sensors", key="floor_l2", disabled=True, use_container_width=True):
                pass
        with f3:
            if st.button("🔒 Rooftop · Awaiting sensors", key="floor_roof", disabled=True, use_container_width=True):
                pass

        st.markdown(
            '<div class="lot-strip"><span>ENTRANCE</span><span class="lot-strip-line"></span>'
            '<span class="lot-strip-arrow">&rarr;</span><span class="lot-strip-line"></span>'
            '<span>EXIT</span></div>',
            unsafe_allow_html=True,
        )

        bay_data = bays if bays else [{"id": b, "status": "unknown", "raw": "No signal"} for b in BAY_LABELS]
        cols = st.columns(3)
        for col, bay in zip(cols, bay_data):
            with col:
                status_class = f"is-{bay['status']}"
                icon = "✅" if bay["status"] == "free" else ("🚗" if bay["status"] == "occupied" else "❔")
                label = "Free" if bay["status"] == "free" else ("Occupied" if bay["status"] == "occupied" else "Unknown")
                st.markdown(
                    f'<div class="bay-card {status_class}">'
                    f'<div class="bay-top"><span class="bay-id">{bay["id"]}</span>'
                    f'<span class="bay-sensor"><span class="bay-sensor-dot"></span>SNSR</span></div>'
                    f'<div class="bay-icon">{icon}</div>'
                    f'<div class="bay-status-label">{label}</div>'
                    f'<div class="bay-substatus">{bay["raw"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Page: History
# --------------------------------------------------------------------------

@st.fragment(run_every=5)
def render_history():
    df, status = load_data()
    
    st.markdown('<div class="page-title">Occupancy History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Trends derived from every logged reading in the sensor feed</div>',
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.markdown(
            '<div class="error-banner">No historical readings available yet.</div>',
            unsafe_allow_html=True,
        )
        return

    bay_cols = ["spot1", "spot2", "spot3"]
    hist = df.dropna(subset=["ts"]).copy()
    for col in bay_cols:
        hist[col] = hist[col].str.lower()
    hist["Occupied"] = hist[bay_cols].apply(lambda r: sum(v == "occupied" for v in r), axis=1)
    hist["Free"] = hist[bay_cols].apply(lambda r: sum(v == "free" for v in r), axis=1)

    # To avoid rendering thousands of points, sample down if needed while preserving trend
    if len(hist) > 400:
        step = max(1, len(hist) // 400)
        hist = hist.iloc[::step]

    records = len(df)
    total_bays = len(BAY_LABELS)
    peak_occupied = int(hist["Occupied"].max()) if not hist.empty else 0
    avg_occupied = round(hist["Occupied"].mean(), 1) if not hist.empty else 0.0

    m1, m2, m3 = st.columns(3)
    for col, tone, icon, label, value in [
        (m1, "neutral", "🗂️", "Records Logged", records),
        (m2, "occupied", "📈", "Peak Occupied", f"{peak_occupied} / {total_bays or 3}"),
        (m3, "amber", "📊", "Average Occupied", avg_occupied),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card tone-{tone}">'
                f'<span class="metric-icon">{icon}</span>'
                f'<div><div class="metric-value">{value}</div>'
                f'<div class="metric-label">{label}</div></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    
    # --- CHART UPDATE ---
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Occupancy Over Time</div>', unsafe_allow_html=True)

    fig = go.Figure()
    
    # 2. FIX: Replaced mode="lines" with a Step Chart (shape='hv') and removed area fill
    fig.add_trace(go.Scatter(
        x=hist["ts"], y=hist["Free"], name="Free", mode="lines",
        line=dict(color="#34d97a", width=2.5, shape='hv'),
    ))
    fig.add_trace(go.Scatter(
        x=hist["ts"], y=hist["Occupied"], name="Occupied", mode="lines",
        line=dict(color="#ff5d6c", width=2.5, shape='hv'),
    ))
    
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a96b8", family="IBM Plex Mono"),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="#1e2944", tickfont=dict(size=11), dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#8a96b8")),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    # --- TABLE UPDATE ---
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Recent Activity Log</div>', unsafe_allow_html=True)
    
    # 3. FIX: Filter the top 50 descending, format columns, and render in standard Streamlit dataframe component
    recent_df = df.dropna(subset=["ts"]).sort_values(by="ts", ascending=False).head(50)
    display_df = recent_df[["timestamp", "log_type", "spot1", "spot2", "spot3"]].copy()
    display_df.columns = ["Timestamp", "Log Type", "Spot 1", "Spot 2", "Spot 3"]
    
    # st.dataframe inherently scrolls vertically when height is applied
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Page: Contact
# --------------------------------------------------------------------------

def render_contact():
    st.markdown('<div class="page-title">Contact</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Questions about a reading, an outage, or the sensor hardware &mdash; reach out directly</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    
    # 4. FIX: Use clean Lucide-style SVGs mapped directly into the UI components
    phone_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>'
    
    email_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"></rect><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path></svg>'

    with c1:
        st.markdown(
            f'<a class="contact-card" href="tel:+660932639626">'
            f'<div class="contact-icon-box tone-free">{phone_svg}</div>'
            f'<div class="contact-details"><span class="contact-label">Phone</span>'
            f'<span class="contact-value">+66 093 263 9626</span></div></a>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<a class="contact-card" href="mailto:kiwi0096@abachiangmai.com">'
            f'<div class="contact-icon-box tone-amber">{email_svg}</div>'
            f'<div class="contact-details"><span class="contact-label">Email</span>'
            f'<span class="contact-value">kiwi0096@abachiangmai.com</span></div></a>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="panel"><p style="color:var(--text-dim); font-size:13.5px; line-height:1.6; margin:0;">'
        'For fastest response on a live incident (a bay stuck showing the wrong status, or the feed '
        'going offline), call directly. For general questions about the system or a partnership '
        'enquiry, email works best.</p></div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------
# Page: About
# --------------------------------------------------------------------------

def render_about():
    st.markdown('<div class="page-title">About the System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">IoT Car Parking System &mdash; how the sensors get from bay to browser</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel"><p style="color:var(--text-dim); font-size:14.5px; line-height:1.75; margin:0;">'
        'The IoT Car Parking System is a lightweight monitoring pipeline built to answer one question '
        'at a glance: which bays are free, right now. A sensor node above each parking bay detects '
        'whether a vehicle is present, timestamps the reading, and logs it centrally. This dashboard '
        'polls that log continuously and renders it as a live, color-coded map of the lot.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    f3, f4 = st.columns(2)
    features = [
        (f1, "🧠", "Sensor Nodes", "An ultrasonic distance sensor per bay reads the space beneath it every few seconds and classifies it as Free or Occupied."),
        (f2, "📶", "Wireless Uplink", "Each reading is pushed over Wi-Fi from the microcontroller to a central logging endpoint, no wiring back to a server room required."),
        (f3, "🗂️", "Sheet-Based Log", "Readings land as timestamped rows in a published Google Sheet, giving the project a durable, inspectable data trail for free."),
        (f4, "🛰️", "Live Dashboard", "This viewer polls the sheet on an interval, parses the newest row for current status, and charts the full history over time."),
    ]
    for col, icon, title, text in features:
        with col:
            st.markdown(
                f'<div class="feature-card"><span class="feature-icon">{icon}</span>'
                f'<div class="feature-title">{title}</div>'
                f'<p class="feature-text">{text}</p></div>',
                unsafe_allow_html=True,
            )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">How it works</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    steps = [
        (s1, "01", "Sense", "A sensor above each bay detects vehicle presence and stamps the moment."),
        (s2, "02", "Log", "The reading is appended as a new row to the published spreadsheet."),
        (s3, "03", "Visualize", "The dashboard fetches the sheet, grabs the latest row, and updates the grid."),
    ]
    for col, num, title, text in steps:
        with col:
            st.markdown(
                f'<div class="step-card"><span class="step-number">{num}</span>'
                f'<div class="step-title">{title}</div>'
                f'<p class="step-text">{text}</p></div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------

PAGES = {
    "dashboard": render_dashboard,
    "history": render_history,
    "contact": render_contact,
    "about": render_about,
}
PAGES.get(st.session_state.page, render_dashboard)()

st.markdown(
    '<div class="footer-note">IoT Car Parking System Viewer &middot; Live data via published Google Sheet</div>',
    unsafe_allow_html=True,
)
