# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_path_transforms.ipynb.

# %% auto 0
__all__ = ['transform_paths', 'rescale_strokes', 'rdpify', 'identity_xform', 'scale_xform', 'translate_xform', 'rotate_xform',
           'BoundingBox', 'bb_rank2', 'bb_rank3']

# %% ../nbs/04_path_transforms.ipynb 5
def transform_paths(paths, global_transform=None):
    if not global_transform:
        return paths
    transformed_strokes = []
    for path_strokes in paths:
        strokes = [apply_transform(s, global_transform) for s in path_strokes]
        transformed_strokes.append(strokes)
    return transformed_strokes


def rescale_strokes(all_strokes, target_size):
    # even though we want to default to keeping paths separate (until we can do bbox checking),
    # we do want a global max/min coord so that we can rescale all points within the same space.
    vstack_coords = np.vstack(all_strokes)
    # print(f"vstack_coords.shape={vstack_coords.shape}")
    vstack_bounding_box = bb_rank2(vstack_coords)
    vstack_rescale_transform = vstack_bounding_box.normalization_xform(target_size)
    
    all_rescaled_strokes = [apply_transform(c[:,:2], vstack_rescale_transform)[:,:2] for c in all_strokes]
    return np.array(all_rescaled_strokes, dtype=object)


def rdpify(strokes, epsilon=1.0):
    return [rdp(s, epsilon=epsilon) for s in strokes]


# %% ../nbs/04_path_transforms.ipynb 6
def identity_xform():
    return np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

# %% ../nbs/04_path_transforms.ipynb 7
def scale_xform(scale_x, scale_y):
    return np.array([[scale_x, 0, 0], [0, scale_y, 0], [0, 0, 1]])

# %% ../nbs/04_path_transforms.ipynb 8
def translate_xform(translate_x, translate_y):
    return np.array([[1, 0, translate_x], [0, 1, translate_y], [0, 0, 1]])

# %% ../nbs/04_path_transforms.ipynb 9
def rotate_xform(rotate_angle):
    if rotate_angle % 360 == 0:
        return identity_xform()
    theta = np.radians(rotate_angle)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    return np.array([[cos_theta, -sin_theta, 0], [sin_theta, cos_theta, 0], [0, 0, 1]])

# %% ../nbs/04_path_transforms.ipynb 10
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

# %% ../nbs/04_path_transforms.ipynb 11
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

# %% ../nbs/04_path_transforms.ipynb 12
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
