from pathlib import Path

import anndata
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import base64
import hashlib
from app.core.config import settings


def _cache_key(file_path, feature):
    mtime = os.path.getmtime(file_path)
    key_string = f"{file_path}|{mtime}|{feature}"
    h = hashlib.md5(key_string.encode()).hexdigest()
    return settings.CACHE_PATH / f"{h}.png"


def _create_png(fig) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    plt.close(fig)
    return buffer.getvalue()


def _png_to_base64(png_bytes):
    image_base64 = base64.b64encode(png_bytes).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"


def _write_to_cache(png_bytes: bytes):
    settings.CACHE_PATH.mkdir(exist_ok=True, parents=True)
    settings.CACHE_PATH.write_bytes(png_bytes)


def plot_visium(file_path, feature):
    cache_path = _cache_key(file_path, feature)
    if cache_path.exists():
        return _png_to_base64(cache_path.read_bytes())

    try:
        data = anndata.read_h5ad(file_path, backed='r')

        fig = plt.figure(figsize=(5, 5))

        # Determine Image key (safe first key)
        img_key = list(data.uns["spatial"].keys())[0]
        plt.imshow(data.uns["spatial"][img_key]["images"]["hires"])

        # Plot Data Logic
        x_coords = data.obs["imagecol"]
        y_coords = data.obs["imagerow"]
        values = None

        # Check if Feature is Gene
        if feature in data.var_names:
            idx = data.var_names.get_loc(feature)
            values = data.X[:, idx]
            # Handle sparse matrix if needed
            if hasattr(values, "toarray"):
                values = values.toarray().flatten()

            # Simple threshold for size? Or simple scatter
            sizes = np.where(values == 0, 0.5, 2.5)  # Generic size logic

        # Check if Feature is LR Pair
        elif "lr_summary" in data.uns and feature in data.uns['lr_summary'].index:
            idx = data.uns['lr_summary'].index.get_loc(feature)
            values = data.obsm['lr_scores'].T[idx]
            sizes = np.where(values == 0, 0.5, 2.5)

        if values is None:
            print(f"Feature {feature} not found in {file_path}")
            return None  # Or return empty plot

        sc = plt.scatter(
            x_coords, y_coords, s=sizes, c=values, cmap="jet", rasterized=True,
        )
        plt.colorbar(sc, shrink=0.6, pad=0.02)  # shrink fits colorbar nicely
        plt.axis('off')

        # Create PNG, write to cache, base64 encode
        png_bytes = _create_png(fig)
        _write_to_cache(png_bytes)
        return _png_to_base64(png_bytes)
    except Exception as e:
        print(f"Error in plotting Visium for {file_path}: {e}")
        return None


def plot_stomics(file_path, feature):
    cache_path = _cache_key(file_path, feature)
    if cache_path.exists():
        return _png_to_base64(cache_path.read_bytes())

    try:
        data = anndata.read_h5ad(file_path, backed='r')

        fig = plt.figure(figsize=(5, 5))

        # Plot Data Logic
        x_coords = data.obs["imagecol"]
        y_coords = -data.obs["imagerow"]
        values = None

        if feature in data.var_names:
            idx = data.var_names.get_loc(feature)
            values = data.X[:, idx]
            if hasattr(values, "toarray"):
                values = values.toarray().flatten()
            sizes = np.where(values == 0, 0.1, 0.5)

        elif "lr_summary" in data.uns and feature in data.uns['lr_summary'].index:
            idx = data.uns['lr_summary'].index.get_loc(feature)
            values = data.obsm['lr_scores'].T[idx]
            sizes = np.where(values == 0, 0.1, 0.5)

        if values is None:
            print(f"Feature {feature} not found in {file_path}")
            return None

        sc = plt.scatter(
            x_coords, y_coords, s=sizes, c=values, cmap="jet", rasterized=True,
        )
        plt.colorbar(sc, shrink=0.6, pad=0.02)
        plt.axis('off')

        # Create PNG, write to cache, base64 encode
        png_bytes = _create_png(fig)
        _write_to_cache(cache_path, png_bytes)
        return _png_to_base64(png_bytes)
    except Exception as e:
        print(f"Error in plotting STomics for {file_path}: {e}")
        return None
