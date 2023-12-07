# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/07_svg_dataset.ipynb.

# %% auto 0
__all__ = ['stroke_rdp_deltas', 'svgs_to_deltas']

# %% ../../nbs/07_svg_dataset.ipynb 6
from .path_transforms import svg_to_strokes
from .stroke3 import strokes_to_deltas, rdp_strokes


def stroke_rdp_deltas(rescaled_strokes, epsilon=2.0):
    rdp_strokes = rdp_strokes(rescaled_strokes, epsilon)
    deltas = strokes_to_deltas(rdp_strokes)

    ## roundtrip / sanity check
    # _rdp_strokes = stroke3.deltas_to_strokes(deltas)
    # display_plot.plot_strokes(_rdp_strokes)

    return deltas, rescaled_strokes

# %% ../../nbs/07_svg_dataset.ipynb 7
import os

import numpy as np

from .display_svg import render_deltas, render_strokes
from .display_plot import *
from .stroke3 import *
from .svg_files import enumerate_files
from .path_joining import merge_until, splice_until


def svgs_to_deltas(
    input_dir,
    output_dir=None,
    target_size=200,
    total_n=1000,
    min_n=3,
    epsilon=1.0,
    limit=None,
):
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    dataset = []
    for i, fname in enumerate(enumerate_files(input_dir)):
        if limit and i > limit:
            break
        input_fname = os.path.join(input_dir, fname)

        try:
            rescaled_strokes = svg_to_strokes(input_fname, total_n=total_n, min_n=min_n)

            joined_strokes, _ = merge_until(rescaled_strokes, dist_threshold=10.0)
            spliced_strokes, _ = splice_until(joined_strokes, dist_threshold=30.0)

            print(
                f"{fname}: {len(rescaled_strokes)} strokes -> {len(joined_strokes)} joined -> {len(spliced_strokes)} spliced"
            )

            deltas = stroke_rdp_deltas(spliced_strokes, epsilon=epsilon)
            dataset.append(deltas)

            # monitor number of points before/after applying RDP path simplification algorithm
            raw_points = np.vstack(rescaled_strokes).shape[0]
            rdp_points = deltas.shape[0]
            print(f"{input_fname} points: raw={raw_points}, rdp={rdp_points}")

            if output_dir:

                def new_suffix(fname, suffix):
                    return os.path.join(output_dir, fname.replace(".svg", suffix))

                plot_strokes(
                    rescaled_strokes, fname=new_suffix(fname, ".0_strokes.png")
                )
                plot_strokes(joined_strokes, fname=new_suffix(fname, ".1_joined.png"))
                plot_strokes(spliced_strokes, fname=new_suffix(fname, ".2_spliced.png"))
                plot_strokes(
                    deltas_to_strokes(deltas), fname=new_suffix(fname, ".3_deltas.png")
                )

                with open(
                    new_suffix(fname, ".raw.svg"), "w", encoding="utf-8"
                ) as raw_out:
                    raw_dwg = render_strokes(rescaled_strokes, target_size=target_size)
                    raw_dwg.write(raw_out, pretty=True)
                    print(f"\twrote {raw_output_fname}")

                with open(
                    new_suffix(fname, ".preproc.svg"), "w", encoding="utf-8"
                ) as preproc_out:
                    preproc_dwg = render_deltas(deltas, target_size=target_size)
                    preproc_dwg.save(preproc_output_fname)
                    print(f"\twrote {preproc_output_fname}")
        except Exception as e:
            print(f"error processing {input_fname}: {e}")
            raise e
    return np.array(dataset, dtype=object)
