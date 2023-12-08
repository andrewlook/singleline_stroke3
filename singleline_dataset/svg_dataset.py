# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_svg_dataset.ipynb.

# %% auto 0
__all__ = ['stroke_rdp_deltas', 'svgs_to_deltas']

# %% ../nbs/07_svg_dataset.ipynb 4
from singeline_dataset.path_transforms import *
from singeline_dataset.stroke3 import *

# %% ../nbs/07_svg_dataset.ipynb 6
def stroke_rdp_deltas(rescaled_strokes, epsilon=2.0):
    rdp_result = rdp_strokes(rescaled_strokes, epsilon)
    deltas = strokes_to_deltas(rdp_result)

    ## roundtrip / sanity check
    # _rdp_result = stroke3.deltas_to_strokes(deltas)
    # default.plot_strokes(_rdp_result)

    return deltas

# %% ../nbs/07_svg_dataset.ipynb 7
import os

import numpy as np

from singeline_dataset.default import *
from singeline_dataset.default import render_deltas, render_strokes
from singeline_dataset.path_joining import merge_until, splice_until
from singeline_dataset.stroke3 import *
from singeline_dataset.svg_files import enumerate_files


def svgs_to_deltas(
    input_dir,
    output_dir=None,
    target_size=200,
    total_n=1000,
    min_n=3,
    epsilon=1.0,
    limit=None,
):
    if output_dir:
        svg_dir = os.path.join(output_dir, "svg")
        png_dir = os.path.join(output_dir, "png")
        for d in [svg_dir, png_dir]:
            if not os.path.isdir(d):
                os.makedirs(d)

    all_files = enumerate_files(input_dir)
    print(f"found {len(all_files)} in {input_dir}")
    dataset = []
    for i, fname in enumerate(all_files):
        if limit and i > limit:
            break
        input_fname = os.path.join(input_dir, fname)

        try:
            rescaled_strokes = svg_to_strokes(input_fname, total_n=total_n, min_n=min_n)

            joined_strokes, _ = merge_until(rescaled_strokes, dist_threshold=15.0)
            spliced_strokes, _ = splice_until(joined_strokes, dist_threshold=40.0)

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

                def new_suffix(subdir, fname, suffix):
                    sd = os.path.join(output_dir, subdir)
                    if not os.path.isdir(sd):
                        os.makedirs(sd)
                    return os.path.join(sd, fname.replace(".svg", suffix))

                final_n_strokes = len(spliced_strokes)
                subdir = f"png/{final_n_strokes:02d}"
                plot_strokes(
                    rescaled_strokes, fname=new_suffix(subdir, fname, ".0_strokes.png")
                )
                plot_strokes(
                    joined_strokes, fname=new_suffix(subdir, fname, ".1_joined.png")
                )
                plot_strokes(
                    spliced_strokes, fname=new_suffix(subdir, fname, ".2_spliced.png")
                )
                plot_strokes(
                    deltas_to_strokes(deltas),
                    fname=new_suffix(subdir, fname, ".3_deltas.png"),
                )

                # raw_output_fname = new_suffix('svg', fname, ".raw.svg")
                # with open(raw_output_fname, "w", encoding="utf-8") as raw_out:
                #     raw_dwg = render_strokes(rescaled_strokes, target_size=target_size)
                #     raw_dwg.write(raw_out, pretty=True)
                #     print(f"\twrote {raw_output_fname}")

                # preproc_output_fname = new_suffix('svg', fname, ".preproc.svg")
                # with open(preproc_output_fname, "w", encoding="utf-8") as preproc_out:
                #     preproc_dwg = render_deltas(deltas, target_size=target_size)
                #     preproc_dwg.save(preproc_output_fname)
                #     print(f"\twrote {preproc_output_fname}")
        except Exception as e:
            print(f"error processing idx={i} input_fname={input_fname}: {e}")
            # raise e
    return np.array(dataset, dtype=object)
