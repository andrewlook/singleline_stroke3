# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/11_display.ipynb.

# %% ../nbs/11_display.ipynb 3
from __future__ import absolute_import, division, print_function

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

from io import BytesIO
import base64
import logging
import numpy as np
import IPython.display
from string import Template
import PIL.Image

# %% auto 0
__all__ = ['log', 'plot_strokes', 'create_animation', 'show_video', 'randcolor', 'render_strokes', 'render_deltas',
           'serialize_array', 'image', 'images']

# %% ../nbs/11_display.ipynb 6
def plot_strokes(
    strokes,
    target_size=200,
    lw=2,
    bounding_boxes=False,
    transparent=False,
    frameon=False,
    fname=None,
):
    fig = plt.figure(frameon=frameon)
    ax = plt.axes(
        xlim=(0, target_size + 0.1 * target_size),
        ylim=(-target_size - 0.1 * target_size),
    )
    # remove the frame; https://stackoverflow.com/questions/14908576/how-to-remove-frame-from-a-figure
    fig.patch.set_visible(False)
    ax.patch.set_visible(False)
    ax.set_facecolor("white")
    ax.axis("off")
    ax.grid = False
    ax.set_xticks([])
    ax.set_yticks([])

    lines = []
    for s in strokes:
        (line,) = ax.plot([], [], lw=lw)
        line.set_data(s[:, 0], -s[:, 1])
        if transparent:
            line.set_color("black")
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
        plt.savefig(buf, format="png", transparent=transparent)
        plt.close()
        img = Image.open(buf)
        img.save(fname)
        buf.seek(0)
        buf.truncate()

# %% ../nbs/11_display.ipynb 8
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

# %% ../nbs/11_display.ipynb 9
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

# %% ../nbs/11_display.ipynb 11
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

# %% ../nbs/11_display.ipynb 12
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

# %% ../nbs/11_display.ipynb 14
### SOURCE:

# Copyright 2018 The Lucid Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# create logger with module name, e.g. lucid.misc.io.array_to_image
log = logging.getLogger(__name__)


def _normalize_array(array, domain=(0, 1)):
    """Given an arbitrary rank-3 NumPy array, produce one representing an image.

    This ensures the resulting array has a dtype of uint8 and a domain of 0-255.

    Args:
      array: NumPy array representing the image
      domain: expected range of values in array,
        defaults to (0, 1), if explicitly set to None will use the array's
        own range of values and normalize them.

    Returns:
      normalized PIL.Image
    """
    # first copy the input so we're never mutating the user's data
    array = np.array(array)
    # squeeze helps both with batch=1 and B/W and PIL's mode inference
    array = np.squeeze(array)
    assert len(array.shape) <= 3
    assert np.issubdtype(array.dtype, np.number)
    assert not np.isnan(array).any()

    low, high = np.min(array), np.max(array)
    if domain is None:
        message = "No domain specified, normalizing from measured (~%.2f, ~%.2f)"
        log.debug(message, low, high)
        domain = (low, high)

    # clip values if domain was specified and array contains values outside of it
    if low < domain[0] or high > domain[1]:
        message = "Clipping domain from (~{:.2f}, ~{:.2f}) to (~{:.2f}, ~{:.2f})."
        log.info(message.format(low, high, domain[0], domain[1]))
        array = array.clip(*domain)

    min_value, max_value = np.iinfo(np.uint8).min, np.iinfo(np.uint8).max  # 0, 255
    # convert signed to unsigned if needed
    if np.issubdtype(array.dtype, np.inexact):
        offset = domain[0]
        if offset != 0:
            array -= offset
            log.debug("Converting inexact array by subtracting -%.2f.", offset)
        if domain[0] != domain[1]:
            scalar = max_value / (domain[1] - domain[0])
            if scalar != 1:
                array *= scalar
                log.debug("Converting inexact array by scaling by %.2f.", scalar)

    return array.clip(min_value, max_value).astype(np.uint8)


def _serialize_normalized_array(array, fmt="png", quality=70):
    """Given a normalized array, returns byte representation of image encoding.

    Args:
      array: NumPy array of dtype uint8 and range 0 to 255
      fmt: string describing desired file format, defaults to 'png'
      quality: specifies compression quality from 0 to 100 for lossy formats

    Returns:
      image data as BytesIO buffer
    """
    dtype = array.dtype
    assert np.issubdtype(dtype, np.unsignedinteger)
    assert np.max(array) <= np.iinfo(dtype).max
    assert array.shape[-1] > 1  # array dims must have been squeezed

    image = PIL.Image.fromarray(array)
    image_bytes = BytesIO()
    image.save(image_bytes, fmt, quality=quality)
    # TODO: Python 3 could save a copy here by using `getbuffer()` instead.
    image_data = image_bytes.getvalue()
    return image_data


def serialize_array(array, domain=(0, 1), fmt="png", quality=70):
    """Given an arbitrary rank-3 NumPy array,
    returns the byte representation of the encoded image.

    Args:
      array: NumPy array of dtype uint8 and range 0 to 255
      domain: expected range of values in array, see `_normalize_array()`
      fmt: string describing desired file format, defaults to 'png'
      quality: specifies compression quality from 0 to 100 for lossy formats

    Returns:
      image data as BytesIO buffer
    """
    normalized = _normalize_array(array, domain=domain)
    return _serialize_normalized_array(normalized, fmt=fmt, quality=quality)


def _display_html(html_str):
    IPython.display.display(IPython.display.HTML(html_str))


def _image_url(array, fmt="png", mode="data", quality=90, domain=None):
    """Create a data URL representing an image from a PIL.Image.

    Args:
      image: a numpy array
      mode: presently only supports "data" for data URL

    Returns:
      URL representing image
    """
    supported_modes = "data"
    if mode not in supported_modes:
        message = "Unsupported mode '%s', should be one of '%s'."
        raise ValueError(message, mode, supported_modes)

    image_data = serialize_array(array, fmt=fmt, quality=quality, domain=domain)
    base64_byte_string = base64.b64encode(image_data).decode("ascii")
    return "data:image/" + fmt.upper() + ";base64," + base64_byte_string


# public functions


def _image_html(array, w=None, domain=None, fmt="png"):
    url = _image_url(array, domain=domain, fmt=fmt)
    style = "image-rendering: pixelated; image-rendering: crisp-edges;"
    if w is not None:
        style += "width: {w}px;".format(w=w)
    return """<img src="{url}" style="{style}">""".format(**locals())


def image(array, domain=None, w=None, format="png", **kwargs):
    """Display an image.

    Args:
      array: NumPy array representing the image
      fmt: Image format e.g. png, jpeg
      domain: Domain of pixel values, inferred from min & max values if None
      w: width of output image, scaled using nearest neighbor interpolation.
        size unchanged if None
    """

    _display_html(_image_html(array, w=w, domain=domain, fmt=format))


def images(arrays, labels=None, domain=None, w=None):
    """Display a list of images with optional labels.

    Args:
      arrays: A list of NumPy arrays representing images
      labels: A list of strings to label each image.
        Defaults to show index if None
      domain: Domain of pixel values, inferred from min & max values if None
      w: width of output image, scaled using nearest neighbor interpolation.
        size unchanged if None
    """

    s = '<div style="display: flex; flex-direction: row;">'
    for i, array in enumerate(arrays):
        label = labels[i] if labels is not None else i
        img_html = _image_html(array, w=w, domain=domain)
        s += """<div style="margin-right:10px; margin-top: 4px;">
              {label} <br/>
              {img_html}
            </div>""".format(
            **locals()
        )
    s += "</div>"
    _display_html(s)
