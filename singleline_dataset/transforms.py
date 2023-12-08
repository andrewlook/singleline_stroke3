# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_transforms.ipynb.

# %% auto 0
__all__ = ['apply_transform', 'identity_xform', 'scale_xform', 'translate_xform', 'rotate_xform', 'BoundingBox', 'bb_rank2',
           'bb_rank3', 'strokes_to_points', 'points_to_deltas', 'strokes_to_deltas', 'deltas_to_points',
           'points_to_strokes', 'deltas_to_strokes', 'rdp_strokes', 'stroke_rdp_deltas']

# %% ../nbs/02_transforms.ipynb 4
from dataclasses import dataclass

import numpy as np

# %% ../nbs/02_transforms.ipynb 6
def apply_transform(coords_2d, xform):
    assert coords_2d.shape[1] == 2
    assert xform.shape[0] == 3
    assert xform.shape[1] == 3

    coords_full = np.concatenate([coords_2d, np.ones((coords_2d.shape[0], 1))], axis=1)
    assert coords_full.shape[0] == coords_2d.shape[0]
    assert coords_full.shape[1] == 3

    return xform.dot(coords_full.transpose()).transpose()

# %% ../nbs/02_transforms.ipynb 7
def identity_xform():
    return np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

# %% ../nbs/02_transforms.ipynb 8
def scale_xform(scale_x, scale_y):
    return np.array([[scale_x, 0, 0], [0, scale_y, 0], [0, 0, 1]])

# %% ../nbs/02_transforms.ipynb 9
def translate_xform(translate_x, translate_y):
    return np.array([[1, 0, translate_x], [0, 1, translate_y], [0, 0, 1]])

# %% ../nbs/02_transforms.ipynb 10
def rotate_xform(rotate_angle):
    if rotate_angle % 360 == 0:
        return identity_xform()
    theta = np.radians(rotate_angle)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    return np.array([[cos_theta, -sin_theta, 0], [sin_theta, cos_theta, 0], [0, 0, 1]])

# %% ../nbs/02_transforms.ipynb 12
@dataclass
class BoundingBox:
    xmin: float
    xmax: float
    xrange: float
    ymin: float
    ymax: float
    yrange: float

    def normalization_xform(self, scale=1.0):
        max_range = self.xrange if self.xrange > self.yrange else self.yrange
        return scale_xform(scale / max_range, scale / max_range).dot(
            translate_xform(-self.xmin, -self.ymin)
        )

# %% ../nbs/02_transforms.ipynb 13
def bb_rank2(coords):
    xmin = coords[:, 0].min()
    xmax = coords[:, 0].max()
    xrange = xmax - xmin
    # print(f"xrange, xmin, xmax = {xrange, xmin, xmax}")

    ymin = coords[:, 1].min()
    ymax = coords[:, 1].max()
    yrange = ymax - ymin
    # print(f"yrange, ymin, ymax = {yrange, ymin, ymax}")

    return BoundingBox(
        xmin=xmin, xmax=xmax, xrange=xrange, ymin=ymin, ymax=ymax, yrange=yrange
    )

# %% ../nbs/02_transforms.ipynb 14
def bb_rank3(coords):
    xmin = coords[:, :, 0].min()
    xmax = coords[:, :, 0].max()
    xrange = xmax - xmin
    # print(f"xrange, xmin, xmax = {xrange, xmin, xmax}")

    ymin = coords[:, :, 1].min()
    ymax = coords[:, :, 1].max()
    yrange = ymax - ymin
    # print(f"yrange, ymin, ymax = {yrange, ymin, ymax}")

    return BoundingBox(
        xmin=xmin, xmax=xmax, xrange=xrange, ymin=ymin, ymax=ymax, yrange=yrange
    )

# %% ../nbs/02_transforms.ipynb 16
def strokes_to_points(strokes):
    all = []
    for s in strokes:
        eoc_col = np.zeros((s.shape[0], 1))
        eoc_col[-1, 0] = 1
        all.append(np.concatenate([s[:, :2], eoc_col], axis=1))
    return np.vstack(all)


def points_to_deltas(points):
    p2 = points.copy()
    # first row should stay the same
    # cols 0,1 of every row onwards should be a delta from the previous row.
    p2[1:, :2] = points[1:, :2] - points[:-1, :2]
    return p2


def strokes_to_deltas(strokes):
    points = strokes_to_points(strokes)
    return points_to_deltas(points)

# %% ../nbs/02_transforms.ipynb 17
def deltas_to_points(_seq):
    seq = np.zeros_like(_seq)
    seq[:, 0:2] = np.cumsum(_seq[:, 0:2], axis=0)
    seq[:, 2] = _seq[:, 2]
    return seq


def points_to_strokes(_seq):
    strokes = np.split(_seq, np.where(_seq[:, 2] > 0)[0] + 1)
    return [
        s for s in strokes if len(s) > 0
    ]  # split sometimes returns an empty array at the end


def deltas_to_strokes(_seq):
    points = deltas_to_points(_seq)
    return points_to_strokes(points)

# %% ../nbs/02_transforms.ipynb 19
from rdp import rdp


def rdp_strokes(strokes, epsilon=1.0):
    return [rdp(s, epsilon=epsilon) for s in strokes]

# %% ../nbs/02_transforms.ipynb 20
def stroke_rdp_deltas(rescaled_strokes, epsilon=2.0):
    rdp_result = rdp_strokes(rescaled_strokes, epsilon)
    deltas = strokes_to_deltas(rdp_result)

    ## roundtrip / sanity check
    # _rdp_result = stroke3.deltas_to_strokes(deltas)
    # default.plot_strokes(_rdp_result)

    return deltas
