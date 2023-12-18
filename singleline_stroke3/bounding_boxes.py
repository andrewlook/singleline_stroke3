# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_bounding_boxes.ipynb.

# %% auto 0
__all__ = ['plot_intersection', 'overlapping_bboxes', 'single_pass_merge_bboxes', 'log', 'separate_non_overlapping',
           'group_and_rescale_overlapping_strokes']

# %% ../nbs/06_bounding_boxes.ipynb 4
from itertools import combinations
import os
from pprint import pprint

import matplotlib.patches as patches
import matplotlib.pyplot as plt

import numpy as np

from .dataset import *
from .display import *
from .fileorg import *
from .strokes import *
from .svg import *
from .transforms import *

# %% ../nbs/06_bounding_boxes.ipynb 15
def plot_intersection(stroke_a, stroke_b, extra_bb=None, title=None):
    lw = 2
    target_size = 200

    fig = plt.figure()
    if title:
        fig.suptitle(title)
    ax = plt.axes(
        xlim=(0, target_size + 0.1 * target_size),
        ylim=(-target_size - 0.1 * target_size),
    )
    ax.set_facecolor("white")

    lines = []

    strokes = [stroke_a, stroke_b]
    bbs = [BoundingBox.create(s) for s in strokes]

    for s in strokes:
        (line,) = ax.plot([], [], lw=lw)
        line.set_data(s[:, 0], -s[:, 1])
        lines.append(line)

    for bb in bbs:
        rect = patches.Rectangle(
            (bb.xmin, -bb.ymin),
            bb.xrange,
            -bb.yrange,
            linewidth=1,
            edgecolor="g",
            facecolor="none",
        )
        # Add the patch to the Axes
        ax.add_patch(rect)

    if extra_bb:
        rect = patches.Rectangle(
            (extra_bb.xmin, -extra_bb.ymin),
            extra_bb.xrange,
            -extra_bb.yrange,
            linewidth=3,
            edgecolor="r",
            facecolor="none",
        )
        # Add the patch to the Axes
        ax.add_patch(rect)

# %% ../nbs/06_bounding_boxes.ipynb 35
def overlapping_bboxes(bboxes):
    max_iou_val = {}
    max_iou_idx = {}
    for a, b in combinations(range(len(bboxes)), 2):
        iou = bboxes[a].iou(bboxes[b])
        if a not in max_iou_val or max_iou_val[a] < iou:
            max_iou_val[a] = iou
            max_iou_idx[a] = b
        if b not in max_iou_val or max_iou_val[b] < iou:
            max_iou_val[b] = iou
            max_iou_idx[b] = a
    return max_iou_val, max_iou_idx

# %% ../nbs/06_bounding_boxes.ipynb 40
def single_pass_merge_bboxes(stroke_idxs, bboxes, iou_threshold=0.05, debug=False):
    assert len(stroke_idxs) == len(bboxes)
    next_stroke_idxs = []
    next_bboxes = []

    max_iou_val, max_iou_idx = overlapping_bboxes(bboxes)
    bb_idxs = max_iou_val.keys()
    removed = []
    for a in bb_idxs:
        if a in removed:
            log(f"{a}: already joined ", debug)
            continue
        b = max_iou_idx[a]
        iou = max_iou_val[a]
        if iou >= iou_threshold:
            log(
                f"{a}-{b}: JOIN max IOU = {iou} for strokes ({stroke_idxs[a]}, {stroke_idxs[b]})",
                debug,
            )
            # remove the joined strokes from consideration for joins in this pass
            removed.append(a)
            removed.append(b)
            # save the combined stroke lists to return
            next_stroke_idxs.append(stroke_idxs[a] + stroke_idxs[b])
            # save a merged bounding box, representing the union of the lists of strokes.
            next_bboxes.append(bboxes[a].merge(bboxes[b]))
        elif iou == 0:
            log(f"{a}-{b}: NO INTERSECTION", debug)
        else:
            log(f"{a}-{b}: IOU value {iou} is below threshold", debug)

    for i in range(len(bboxes)):
        if i in removed:
            log(f"SKIP: {i} has already been removed in: {removed}", debug)
            continue
        log(f"KEEP: {i}", debug)
        next_stroke_idxs.append(stroke_idxs[i])
        next_bboxes.append(bboxes[i])
    log("---------", debug)
    return next_stroke_idxs, next_bboxes


def log(msg, debug=False):
    if debug:
        print(msg)

# %% ../nbs/06_bounding_boxes.ipynb 50
def separate_non_overlapping(strokes, iou_threshold=0.05):
    stroke_idxs = [[i] for i in range(len(strokes))]
    bboxes = [BoundingBox.create(s) for s in strokes]

    next_stroke_idxs, next_bboxes = [], []

    while True:
        next_stroke_idxs, next_bboxes = single_pass_merge_bboxes(
            stroke_idxs, bboxes, iou_threshold=iou_threshold
        )
        if len(next_stroke_idxs) == len(stroke_idxs):
            break
        stroke_idxs = next_stroke_idxs
        bboxes = next_bboxes
    return stroke_idxs, bboxes

# %% ../nbs/06_bounding_boxes.ipynb 58
def group_and_rescale_overlapping_strokes(orig_strokes, min_area=500, target_size=200):
    stroke_groups, bboxes = separate_non_overlapping(orig_strokes)
    for sg, bb in zip(stroke_groups, bboxes):
        strokes = [orig_strokes[i] for i in sg]
        if bb.area() < min_area:
            continue
        rescaled = rescale_strokes(strokes, target_size=target_size)
        yield rescaled
