def build_parking_scene(slot_status):
    fig = go.Figure()

    # Theme colors
    color_occupied = '#ef4444' # Red car block
    color_free = '#22c55e'     # Green floating indicator
    color_lines = '#cbd5e1'    # White/gray parking lines

    # Dimensions
    slot_width = 4
    slot_length = 8
    spacing = 1.5

    for i, status in enumerate(slot_status):
        x_offset = i * (slot_width + spacing)

        # 1. Draw Parking Slot Lines (U-shape)
        fig.add_trace(go.Scatter3d(
            x=[x_offset, x_offset, x_offset + slot_width, x_offset + slot_width],
            y=[slot_length, 0, 0, slot_length],
            z=[0, 0, 0, 0],
            mode='lines',
            line=dict(color=color_lines, width=5),
            hoverinfo='skip'
        ))

        if status == "Occupied":
            # 2. Draw 3D Car (Solid Block)
            # 8 Vertices for a 3D rectangular box
            x_c = [x_offset+0.5, x_offset+3.5, x_offset+3.5, x_offset+0.5,
                   x_offset+0.5, x_offset+3.5, x_offset+3.5, x_offset+0.5]
            y_c = [0.5, 0.5, 7.5, 7.5, 0.5, 0.5, 7.5, 7.5]
            z_c = [0, 0, 0, 0, 2.5, 2.5, 2.5, 2.5] # Car height = 2.5

            # 12 triangles to form the 6 faces of the 3D box
            i_faces = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
            j_faces = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
            k_faces = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]

            fig.add_trace(go.Mesh3d(
                x=x_c, y=y_c, z=z_c,
                i=i_faces, j=j_faces, k=k_faces,
                color=color_occupied,
                opacity=0.85,
                name=f'Slot {i+1}',
                text=f'Slot {i+1} (Occupied)',
                hoverinfo='text'
            ))
        else:
            # 3. Floating Indicator for Free Slots
            fig.add_trace(go.Scatter3d(
                x=[x_offset + slot_width/2],
                y=[slot_length/2],
                z=[1.5],
                mode='markers+text',
                marker=dict(size=8, color=color_free, symbol='diamond'),
                text=['AVAILABLE'],
                textposition='top center',
                textfont=dict(color=color_free, size=12, family="Inter"),
                name=f'Slot {i+1}',
                hoverinfo='text'
            ))

    # 4. Clean up the camera and layout for an isometric view
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=''),
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.2, y=-1.8, z=1.5) # Sets a cool isometric angle
            ),
            aspectmode='data' # Keeps the 3D proportions realistic
        ),
        paper_bgcolor='#0f172a',
        margin=dict(l=0, r=0, b=0, t=0),
        height=450,
        showlegend=False
    )
    return fig
