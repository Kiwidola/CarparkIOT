from parking3d import build_parking_scene

fig = build_parking_scene(slot_status)
st.plotly_chart(fig, use_container_width=True)
