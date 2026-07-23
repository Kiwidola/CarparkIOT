import plotly.graph_objects as go

SLOT_WIDTH = 3
SLOT_DEPTH = 5
SLOT_GAP = 1.5

SLOT_CENTERS = [
    i * (SLOT_WIDTH + SLOT_GAP)
    for i in range(3)
]


def make_box(x0, x1, y0, y1, z0, z1, color, opacity=1):

    xs = [x0,x0,x1,x1,x0,x0,x1,x1]
    ys = [y0,y1,y1,y0,y0,y1,y1,y0]
    zs = [z0,z0,z0,z0,z1,z1,z1,z1]

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


def make_ground():

    return make_box(
        -3,
        SLOT_CENTERS[-1] + 5,
        -5,
        SLOT_DEPTH + 6,
        -0.1,
        0,
        "#404040",
    )


def make_grass():

    return make_box(
        -5,
        SLOT_CENTERS[-1] + 7,
        SLOT_DEPTH + 1,
        SLOT_DEPTH + 4,
        -0.05,
        0,
        "#2e7d32",
    )


def make_slot(x_center, occupied):

    color = "#ef4444" if occupied else "#22c55e"

    x0 = x_center - SLOT_WIDTH / 2
    x1 = x_center + SLOT_WIDTH / 2

    return make_box(
        x0,
        x1,
        0,
        SLOT_DEPTH,
        0,
        0.02,
        color,
        0.9,
    )


def make_car(x_center):

    traces = []

    body_width = SLOT_WIDTH * 0.65
    body_length = SLOT_DEPTH * 0.75

    x0 = x_center - body_width / 2
    x1 = x_center + body_width / 2

    y0 = (SLOT_DEPTH - body_length) / 2
    y1 = y0 + body_length

    traces.append(
        make_box(
            x0,
            x1,
            y0,
            y1,
            0.25,
            0.75,
            "#2563eb",
        )
    )

    traces.append(
        make_box(
            x0 + .25,
            x1 - .25,
            y0 + .7,
            y1 - .7,
            .75,
            1.15,
            "#1d4ed8",
        )
    )

    return traces
