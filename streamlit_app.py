import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Smart Parking Dashboard", page_icon="🚗", layout="wide")

st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] {font-family: 'Inter', sans-serif;}
.block-container {padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🚗 Smart Parking")
st.sidebar.checkbox("Auto Refresh", True)
st.sidebar.checkbox("Dark Mode", False)

st.title("🚗 Smart Parking Dashboard")
st.caption(f"Last updated: {datetime.now():%H:%M:%S}")

total=3
occupied=1
free=2
c1,c2,c3,c4=st.columns(4)
c1.metric("Total",total)
c2.metric("Free",free)
c3.metric("Occupied",occupied)
c4.metric("Occupancy",f"{occupied/total:.0%}")

fig=go.Figure()
fig.add_bar(x=["Free","Occupied"],y=[free,occupied])
st.plotly_chart(fig,use_container_width=True)

st.subheader("Parking History")
st.dataframe(pd.DataFrame({"Time":["10:00","10:05"],"Slot":[1,2],"Status":["Occupied","Free"]}),use_container_width=True)
