import anndata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

def _fig_to_base64(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    plt.close(fig) # Important: close figure to free memory
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return f"data:image/png;base64,{image_base64}"

def plot_visium_brain(file_path, feature):
    try:
        data1 = anndata.read_h5ad(file_path)

        fig = plt.figure(figsize=(5,5))
        
        # Determine Image key (safe first key)
        img_key = list(data1.uns["spatial"].keys())[0]
        plt.imshow(data1.uns["spatial"][img_key]["images"]["hires"]) 

        # Plot Data Logic
        x_coords = data1.obs["imagecol"]
        y_coords = data1.obs["imagerow"]
        values = None
        size_scale = 1.0 # Default Size
        
        # Check if Feature is Gene
        if feature in data1.var_names:
            idx = list(data1.var_names).index(feature)
            values = data1.X[:, idx]
            # Handle sparse matrix if needed
            if hasattr(values, "toarray"):
                values = values.toarray().flatten()
            
            # Simple threshold for size? Or simple scatter
            sizes = np.where(values == 0, 0.5, 2.5) # Generic size logic
            
        # Check if Feature is LR Pair
        elif "lr_summary" in data1.uns and feature in data1.uns['lr_summary'].index:
             idx = data1.uns['lr_summary'].index.get_loc(feature)
             values = data1.obsm['lr_scores'].T[idx]
             sizes = np.where(values == 0, 0.5, 2.5)
             
        if values is None:
            print(f"Feature {feature} not found in {file_path}")
            return None # Or return empty plot

        sc = plt.scatter(x_coords, y_coords, s=sizes, c=values, cmap="jet")
        plt.colorbar(sc, shrink=0.6, pad=0.02) # shrink fits colorbar nicely
        plt.axis('off')
        
        return _fig_to_base64(fig)
    except Exception as e:
        print(f"Error in plot_visium_brain for {file_path}: {e}")
        return None

def plot_stomics_brain(file_path, feature):
    try:
        data = anndata.read_h5ad(file_path)

        fig = plt.figure(figsize=(5,5))
        
        # Plot Data Logic
        x_coords = data.obs["imagecol"]
        y_coords = -data.obs["imagerow"]
        values = None
        
        if feature in data.var_names:
            idx = list(data.var_names).index(feature)
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

        sc = plt.scatter(x_coords, y_coords, s=sizes, c=values, cmap="jet")
        plt.colorbar(sc, shrink=0.6, pad=0.02)
        plt.axis('off')
        
        return _fig_to_base64(fig)
    except Exception as e:
        print(f"Error in plot_stomics_brain for {file_path}: {e}")
        return None
