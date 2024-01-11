# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_embeddings.ipynb.

# %% auto 0
__all__ = ['DEFAULT_DATA_HOME', 'PRETRAINED_MODEL_PATH', 'PRETRAINED_CHECKPOINT', 'DEFAULT_BATCH_SIZE', 'load_resnet',
           'SketchbookEpoch', 'sketchbook_dataloaders', 'batch_fnames_and_images', 'predict_embeddings', 'Hook',
           'embed_dir', 'pd_series_to_embs', 'train_kmeans', 'cluster_assigner', 'show_cluster', 'show_all_clusters',
           'categorize_files']

# %% ../nbs/01_embeddings.ipynb 4
import math
import json

import pandas as pd
import numpy as np
import faiss
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
from fastai.vision.all import *

from .fileorg import *

# %% ../nbs/01_embeddings.ipynb 6
DEFAULT_DATA_HOME = singleline_data_home("../data_home")
PRETRAINED_MODEL_PATH = "models/epoch-20231128/01_FLAT"
PRETRAINED_CHECKPOINT = "model_20231121_2epochs"
# LATEST_MODEL = (PRETRAINED_DATA_ROOT, PRETRAINED_CHECKPOINT)


def load_resnet(
    data_home=DEFAULT_DATA_HOME,
    model_path=PRETRAINED_MODEL_PATH,
    model_checkpoint=PRETRAINED_CHECKPOINT,
):
    model_data_root = data_home / model_path

    # dummy dataloader with the right number of target classes,
    # so that the learner has the correct number of output neurons to load the model weights.
    dls2 = ImageDataLoaders.from_path_func(
        model_data_root,
        get_image_files(model_data_root),
        lambda p: os.path.basename(os.path.dirname(p)),
        item_tfms=Resize(224),
        seed=42,
        shuffle=False,
        valid_pct=0.0,
    )
    learn = vision_learner(dls2, resnet34, metrics=error_rate)
    learn.load(model_checkpoint)

    return learn

# %% ../nbs/01_embeddings.ipynb 15
class SketchbookEpoch:
    def __init__(self, epoch, data_home="../data_home"):
        self.data_home = singleline_data_home(default=data_home)
        self.epoch = epoch
        self.raster_epoch = self.data_home / f"raster/epoch-{epoch}"
        self.stroke3_epoch = self.data_home / f"stroke3/epoch-{epoch}"

    def dir_01_FLAT(self):
        return self.raster_epoch / "01_FLAT"

    def dir_02_CATEGORIZED(self):
        return self.raster_epoch / "02_CATEGORIZED"

    def dir_03_HANDLABELED(self):
        return self.raster_epoch / "03_HANDLABELED"

    def dir_04_CROP(self):
        return self.raster_epoch / "04_CROP"

    def dir_05_STROKE3(self):
        return self.raster_epoch / "05_STROKE3"

    def dir_06_BBOXSEP(self):
        return self.raster_epoch / "06_BBOXSEP"

    def dir_07_FILTER(self):
        return self.raster_epoch / "07_FILTER"

    def tsv_01_FLAT(self):
        return self.raster_epoch / "01_FLAT.tsv"

    def tsv_02_CATEGORIZED(self):
        return self.raster_epoch / "02_CATEGORIZED.tsv"

    def tsv_03_HANDLABELED(self):
        return self.raster_epoch / "03_HANDLABELED.tsv"

    def tsv_04_CROP(self):
        return self.raster_epoch / "04_CROP.tsv"

    def tsv_05_STROKE3(self):
        return self.raster_epoch / "05_STROKE3.tsv"

    def tsv_06_BBOXSEP(self):
        return self.raster_epoch / "06_BBOXSEP.tsv"

    def tsv_07_FILTER(self):
        return self.raster_epoch / "07_FILTER.tsv"

# %% ../nbs/01_embeddings.ipynb 20
DEFAULT_BATCH_SIZE = 64


def sketchbook_dataloaders(sketchbooks_dir, **kwargs):
    """Loads image data and label based on parent folder - minimum data needed to train CNN"""
    path = Path(sketchbooks_dir)

    files = get_image_files(path)

    path_func = lambda p: os.path.basename(os.path.dirname(p))

    dataloaders = ImageDataLoaders.from_path_func(
        path,
        files,
        path_func,
        item_tfms=Resize(224),
        batch_size=DEFAULT_BATCH_SIZE,
        **kwargs
    )
    return dataloaders

# %% ../nbs/01_embeddings.ipynb 23
def batch_fnames_and_images(sketchbooks_dir):
    """
    Prepare data to compute embeddings over all images and store
    them along with a reference to the underlying filename.
    """
    ordered_dls = sketchbook_dataloaders(
        sketchbooks_dir, seed=42, shuffle=False, valid_pct=0.0
    )

    # compute the number of batches
    num_batches = math.ceil(len(ordered_dls.train.items) / DEFAULT_BATCH_SIZE)
    assert num_batches == len(ordered_dls.train)
    batched_fnames = [
        # ensure filenames are relative to the input dir
        [
            str(s).replace(f"{str(sketchbooks_dir)}/", "")
            for s in ordered_dls.train.items[i * 64 : (i + 1) * 64]
        ]
        for i in range(num_batches)
    ]
    print(
        f"total items: {len(ordered_dls.train.items)}, num batches: {len(batched_fnames)}"
    )
    return batched_fnames, ordered_dls

# %% ../nbs/01_embeddings.ipynb 27
def predict_embeddings(model, xb):
    # import pdb
    # pdb.set_trace()
    with torch.no_grad():
        with Hook(model[-1][-2]) as hook:
            output = model.to("cpu").eval()(xb.to("cpu"))
            act = hook.stored
    return act.cpu().numpy()


class Hook:
    def __init__(self, m):
        self.hook = m.register_forward_hook(self.hook_func)

    def hook_func(self, m, i, o):
        self.stored = o.detach().clone()

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        self.hook.remove()

# %% ../nbs/01_embeddings.ipynb 30
def embed_dir(input_dir, learner, strip_dir=None):
    """
    Get images paired with their filenames, grouped into batches.
    Compute embeddings and yield JSON records including embedding + filename,
    so the data can be stored for downstream processes that need embeddings
    mapped to specific files (ex. clustering/visual search and taking some
    action like moving files based on the results).

    TODO: remove the 'data_home' literal part of `orig_fname`,
          so the TSV's can be dir-independent (relative to their data_root)
    """
    batched_fnames, ordered_dls = batch_fnames_and_images(input_dir)
    with torch.no_grad(), learner.no_logging():
        for i, batch in enumerate(zip(batched_fnames, ordered_dls.train)):
            batched_fnames, (x, y) = batch
            bs = len(batched_fnames)
            assert bs == x.shape[0]
            assert bs == y.shape[0]

            activations = predict_embeddings(learner.model, x)
            assert bs == activations.shape[0]

            for j in range(bs):
                y_j = y[j]
                fname_j = batched_fnames[j]
                if strip_dir:
                    fname_j = str(fname_j).replace(f"{strip_dir}/", "")
                emb_j = activations[j]
                # label: what parent dir exists in the dataset we're processing
                label_j = ordered_dls.vocab[y_j]
                # # pred_label: prediction made relative to the vocab of the learner's model
                # # (may be different than what's in the dataloader we're using for input).
                # x_j = x[j]
                # pred_label_j, pred_idx_j, pred_probs_j = learner.predict(x_j.cpu())
                yield {
                    "idx": j + i * bs,
                    "indiv_fname": os.path.basename(fname_j),
                    "orig_fname": fname_j,
                    "label": label_j,
                    # "pred_label": pred_label_j,
                    # "pred_idx": pred_idx_j.cpu().numpy(),
                    # "pred_probs": ",".join(
                    #     [f"{p:04f}" for p in pred_probs_j.cpu().numpy()]
                    # ),
                    "emb_csv": ",".join([str(f) for f in list(emb_j)]),
                }

# %% ../nbs/01_embeddings.ipynb 36
import numpy as np


def pd_series_to_embs(df_emb_csv: pd.Series):
    arrs = [np.array([float(f) for f in s.split(",")]) for s in list(df_emb_csv)]
    embs = np.stack(arrs)
    embs = embs.astype(np.float32)
    return embs

# %% ../nbs/01_embeddings.ipynb 39
import faiss
import json


def train_kmeans(embs, ncentroids=16, seed=42, niter=20):
    emb_dim = embs.shape[1]
    index = faiss.IndexFlatL2(emb_dim)
    index.add(embs)

    ncentroids = 16
    niter = 20
    verbose = True
    kmeans = faiss.Kmeans(
        emb_dim, ncentroids, niter=niter, verbose=verbose, gpu=True, seed=42
    )
    kmeans.train(embs)

    return kmeans

# %% ../nbs/01_embeddings.ipynb 48
def cluster_assigner(cluster_centroids, cluster_to_label=None):
    emb_dim = cluster_centroids.shape[1]
    kmeans_index = faiss.IndexFlatL2(emb_dim)
    kmeans_index.add(cluster_centroids)

    def __knn_assigner(embs):
        knn_dist, knn_clusterid = kmeans_index.search(embs, 1)
        knn_label = (
            [cluster_to_label[str(i[0])] for i in knn_clusterid]
            if cluster_to_label
            else [None] * len(knn_clusterid)
        )
        return knn_dist, knn_clusterid, knn_label

    return __knn_assigner

# %% ../nbs/01_embeddings.ipynb 57
def show_cluster(clusters_df, clusters, idx, colname="orig_fname", prefix=None):
    imgs = [Image.open(prefix / clusters_df.iloc[i][colname]) for i in clusters[idx]]

    fig = plt.figure(figsize=(16.0, 16.0))
    grid = ImageGrid(
        fig,
        111,  # similar to subplot(111)
        nrows_ncols=(4, 4),  # creates 2x2 grid of axes
        axes_pad=0.1,  # pad between axes in inch.
    )

    for ax, im in zip(grid, imgs):
        # Iterating over the grid returns the Axes.
        ax.imshow(im)

    plt.show()

# %% ../nbs/01_embeddings.ipynb 58
def show_all_clusters(
    clusters_df,
    clusters,
    cluster_idxs=None,
    title=None,
    colname="orig_fname",
    prefix=None,
):
    select_idxs = cluster_idxs if cluster_idxs else range(len(clusters))
    num_clusters = len(select_idxs)
    examples_per_cluster = 16
    fig = plt.figure(figsize=(16.0, float(num_clusters)))
    grid = ImageGrid(
        fig,
        111,  # similar to subplot(111)
        nrows_ncols=(num_clusters, examples_per_cluster),
        axes_pad=0.02,
    )
    for row, cluster_idx in enumerate(select_idxs):
        imgs = [
            Image.open(prefix / clusters_df.iloc[i][colname])
            for i in clusters[cluster_idx]
        ]

        for col, im in enumerate(imgs):
            total_idx = col + row * examples_per_cluster
            ax = grid[total_idx]
            ax.grid = False
            ax.set_xticks([])
            ax.set_yticks([])
            if col == 0:
                ax.set_ylabel(f"{cluster_idx}  ", rotation=0)
            ax.imshow(im)
    if title:
        fig.suptitle(
            title
            if cluster_idxs is None
            else f"{title} (Cluster IDs: {','.join([str(i) for i in select_idxs])})"
        )
    plt.show()

# %% ../nbs/01_embeddings.ipynb 66
import math
import os
import shutil

from PIL import Image


def categorize_files(cdf, epoch, prev_epoch=None):
    existing_categorized = L(
        os.path.basename(f) for f in get_image_files(epoch.dir_02_CATEGORIZED())
    )
    prev_handlabeled = (
        L(os.path.basename(f) for f in get_image_files(prev_epoch.dir_03_HANDLABELED()))
        if prev_epoch
        else []
    )

    for idx in range(len(cdf)):
        row = cdf.iloc[idx]

        indiv_fname = row.indiv_fname
        if prev_handlabeled and indiv_fname in prev_handlabeled:
            print(
                f"already hand-labeled in 03_HANDLABELED (PREV epoch) - skipping {indiv_fname} (to avoid duplicate work)"
            )
            continue

        if indiv_fname in existing_categorized:
            print(
                f"already copied to 02_CATEGORIZED (curr epoch) - skipping {indiv_fname}"
            )
            continue

        orig_abs_path = epoch.dir_01_FLAT() / row.orig_fname
        categorized_abs_path = epoch.dir_02_CATEGORIZED() / row.categorized_path

        categorized_dir = os.path.dirname(categorized_abs_path)
        if not os.path.isdir(categorized_dir):
            os.makedirs(categorized_dir)

        print(f"writing to {categorized_abs_path}")
        shutil.copy(orig_abs_path, categorized_abs_path)
