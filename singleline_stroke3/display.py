# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_display.ipynb.

# %% auto 0
__all__ = ['plot_strokes', 'create_animation', 'show_video', 'randcolor', 'render_strokes', 'render_deltas']

# %% ../nbs/01_display.ipynb 3
import base64
import io
import random

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import svgwrite
from IPython.display import HTML, display
from matplotlib import animation
from PIL import Image
from .transforms import BoundingBox

# %% ../nbs/01_display.ipynb 6
def plot_strokes(strokes, target_size=200, lw=2, bounding_boxes=False, fname=None):
    fig = plt.figure()
    ax = plt.axes(
        xlim=(0, target_size + 0.1 * target_size),
        ylim=(-target_size - 0.1 * target_size),
    )
    ax.set_facecolor("white")

    # remove the axis
    ax.grid = False
    ax.set_xticks([])
    ax.set_yticks([])

    # remove the frame; https://stackoverflow.com/questions/14908576/how-to-remove-frame-from-a-figure
    fig.patch.set_visible(False)
    # plt.box(False)

    lines = []
    for s in strokes:
        (line,) = ax.plot([], [], lw=lw)
        line.set_data(s[:, 0], -s[:, 1])
        lines.append(line)
        if bounding_boxes:
            bb = BoundingBox.create(s)
            rect = patches.Rectangle(
                (bb.xmin, -bb.ymin),
                bb.xrange,
                -bb.yrange,
                linewidth=1,
                edgecolor="g",
                facecolor="none",
            )
            ax.add_patch(rect)

    if not fname:
        plt.show()
        return
    with io.BytesIO() as buf:
        plt.savefig(buf, format="png")
        plt.close()
        img = Image.open(buf)
        img.save(fname)
        buf.seek(0)
        buf.truncate()

# %% ../nbs/01_display.ipynb 8
def create_animation(
    strokes, fname="video.mp4", fps=60, target_size=200, lw=2, trailing_frames=30
):
    seq_length = np.vstack(strokes).shape[0]
    print(seq_length)

    i = 0
    j = 0

    # First set up the figure, the axis, and the plot element we want to animate
    fig = plt.figure()
    ax = plt.axes(xlim=(0, target_size + 2 * lw), ylim=(-target_size - 2 * lw, 0))
    ax.set_facecolor("white")
    (line,) = ax.plot([], [], lw=lw)

    # remove the axis
    ax.grid = False
    ax.set_xticks([])
    ax.set_yticks([])
    # remove the frame
    fig.patch.set_visible(False)

    # initialization function: plot the background of each frame
    def init():
        line.set_data([], [])
        return (line,)

    # animation function.  This is called sequentially
    def animate(frame):
        nonlocal i, j, line
        if i < len(strokes):
            x = strokes[i][:, 0]
            y = strokes[i][:, 1]
            line.set_data(x[0:j], -y[0:j])

            if j >= len(x):
                i += 1
                j = 0
                (line,) = ax.plot([], [], lw=lw)
            else:
                j += 1
        else:
            # if i has already incremented past all the strokes,
            # that means this is a "trailing frame" (meant to leave
            # the finished drawing onscreen for a moment).
            pass
        return (line,)

    # call the animator.  blit=True means only re-draw the parts that have changed.
    total_frames = seq_length + len(strokes) + trailing_frames
    anim = animation.FuncAnimation(
        fig, animate, init_func=init, frames=total_frames, blit=True
    )
    plt.close()

    # save the animation as an mp4.
    anim.save(fname, fps=fps, extra_args=["-vcodec", "libx264"])

# %% ../nbs/01_display.ipynb 9
def show_video(fname="video.mp4"):
    """
    create_animation(strokes, fname="video.mp4", lw=2)
    show_video("video.mp4")
    """
    video = io.open(fname, "r+b").read()
    encoded = base64.b64encode(video)
    html_data = f"""<video alt="video" autoplay loop>
                    <source src="data:video/mp4;base64,{encoded.decode('ascii')}" type="video/mp4" />
                </video>"""
    display(HTML(data=html_data))

# %% ../nbs/01_display.ipynb 11
def randcolor(min_color_intensity=0, max_color_intensity=255):
    def _randc():
        return str(random.randint(min_color_intensity, max_color_intensity))

    return f"rgb({_randc()},{_randc()},{_randc()})"


# | export
def render_strokes(strokes, target_size=200, stroke_width=1):
    dwg = svgwrite.Drawing(size=(f"{target_size}px", f"{target_size}px"), debug=True)
    the_color = randcolor()

    for points in strokes:
        prev = None
        for row in points:
            x, y = row[0], row[1]
            pt = (x, y)
            if prev:
                # dist = np.linalg.norm(np.array(pt) - np.array(prev))
                # if dist < 60:
                dwg.add(dwg.line(prev, pt, stroke=the_color, stroke_width=stroke_width))
            prev = pt
        the_color = randcolor()
    return dwg

# %% ../nbs/01_display.ipynb 12
def render_deltas(deltas, target_size=200, color_mode=True, stroke_width=1, factor=1.0):
    dwg = svgwrite.Drawing(size=(target_size, target_size))
    dwg.add(
        dwg.rect(
            insert=(0, 0),
            size=(target_size, target_size),
            fill="white",
        )
    )

    lift_pen = 1
    abs_x = 0
    abs_y = 0
    the_color = "#000"
    if color_mode:
        the_color = randcolor()

    for i in range(len(deltas)):
        x = round(float(deltas[i, 0]) * factor, 3)
        y = round(float(deltas[i, 1]) * factor, 3)

        prev_x = round(abs_x, 3)
        prev_y = round(abs_y, 3)

        abs_x += x
        abs_y += y

        if lift_pen == 1:
            p = "M " + str(abs_x) + "," + str(abs_y) + " "
            if color_mode:
                the_color = randcolor()
        else:
            p = (
                "M "
                + str(prev_x)
                + ","
                + str(prev_y)
                + " L "
                + str(abs_x)
                + ","
                + str(abs_y)
                + " "
            )

        lift_pen = deltas[i, 2]

        dwg.add(dwg.path(p).stroke(the_color, stroke_width).fill(the_color))
    return dwg
