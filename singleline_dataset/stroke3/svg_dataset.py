# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/07_svg_dataset.ipynb.

# %% auto 0
__all__ = ['svg_to_stroke_deltas', 'svgs_to_deltas']

# %% ../../nbs/07_svg_dataset.ipynb 6
from .path_helpers import discretize_paths
from singleline_dataset.stroke3.path_transforms import (
    rdpify,
    rescale_strokes,
    transform_paths,
)
from .stroke3 import strokes_to_deltas
from .svg_files import load_svg
from .svg_transforms import svg_to_transforms


def svg_to_stroke_deltas(
    input_fname, total_n=1000, min_n=3, target_size=200, epsilon=2.0
):
    paths, attributes, svg_attributes, svg_root = load_svg(input_fname)
    all_strokes = discretize_paths(paths, total_n=total_n, min_n=min_n)

    globally_rescaled_strokes = transform_paths(
        all_strokes, global_transform=svg_to_transforms(svg_root)
    )

    rescaled_strokes = rescale_strokes(globally_rescaled_strokes, target_size)
    rdp_strokes = rdpify(rescaled_strokes, epsilon)
    deltas = strokes_to_deltas(rdp_strokes)

    ## roundtrip / sanity check
    # _rdp_strokes = stroke3.deltas_to_strokes(deltas)
    # display_plot.plot_strokes(_rdp_strokes)

    return deltas, rescaled_strokes

# %% ../../nbs/07_svg_dataset.ipynb 7
import os

import numpy as np

from .display_svg import render_deltas, render_strokes
from .svg_files import enumerate_files


def svgs_to_deltas(input_dir, output_dir=None, target_size=200, **kwargs):
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    dataset = []
    for fname in enumerate_files(input_dir):
        input_fname = os.path.join(input_dir, fname)

        try:
            deltas, rescaled_strokes = svg_to_stroke_deltas(
                input_fname, target_size=target_size, **kwargs
            )
            dataset.append(deltas)

            # monitor number of points before/after applying RDP path simplification algorithm
            raw_points = np.vstack(rescaled_strokes).shape[0]
            rdp_points = deltas.shape[0]
            print(f"{input_fname} points: raw={raw_points}, rdp={rdp_points}")

            if output_dir:
                raw_output_fname = os.path.join(
                    output_dir, fname.replace(".svg", ".raw.svg")
                )
                preproc_output_fname = os.path.join(
                    output_dir, fname.replace(".svg", ".preproc.svg")
                )

                with open(raw_output_fname, "w", encoding="utf-8") as raw_out:
                    raw_dwg = render_strokes(rescaled_strokes, target_size=target_size)
                    raw_dwg.write(raw_out, pretty=True)
                    print(f"\twrote {raw_output_fname}")

                with open(preproc_output_fname, "w", encoding="utf-8") as preproc_out:
                    preproc_dwg = render_deltas(deltas, target_size=target_size)
                    preproc_dwg.save(preproc_output_fname)
                    print(f"\twrote {preproc_output_fname}")
        except Exception as e:
            print(f"error processing {input_fname}: {e}")
    return np.array(dataset, dtype=object)
