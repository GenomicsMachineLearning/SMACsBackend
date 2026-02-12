from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core.config import settings
from app.plotting import plot_visium_brain, plot_stomics_brain
from app.metadata import MetadataService
import pandas as pd
import os

router = APIRouter()

# Load LR Database once
LR_DB_PATH = "/scratch/user/s4634945/group_scratch/github_Softwares/SMACsBackend/connectome_cellchat_cellphone_celltalk.txt"

# Try to load it safely
try:
    if os.path.exists(LR_DB_PATH):
        # Assuming it's CSV based on the head command output (quoted fields, comma separated?)
        # "","Ligand.gene.symbol","Receptor.gene.symbol"
        lr_df = pd.read_csv(LR_DB_PATH, index_col=0) 
        # Normalize columns for easier search
        lr_df.columns = [c.strip() for c in lr_df.columns]
        # Ensure string type for search
        lr_df['Ligand.gene.symbol'] = lr_df['Ligand.gene.symbol'].astype(str)
        lr_df['Receptor.gene.symbol'] = lr_df['Receptor.gene.symbol'].astype(str)
    else:
        print(f"Warning: LR Database not found at {LR_DB_PATH}")
        lr_df = pd.DataFrame(columns=["Ligand.gene.symbol", "Receptor.gene.symbol"])
except Exception as e:
    print(f"Error loading LR Database: {e}")
    lr_df = pd.DataFrame(columns=["Ligand.gene.symbol", "Receptor.gene.symbol"])


@router.get("/search_lr")
async def search_lr(query: str = Query(..., min_length=1, description="Gene symbol to search")):
    if lr_df.empty:
        return []
    
    q = query.lower()
    # Case insensitive search in both columns
    mask = (lr_df['Ligand.gene.symbol'].str.lower().str.contains(q)) | \
           (lr_df['Receptor.gene.symbol'].str.lower().str.contains(q))
    
@router.get("/features")
async def get_features(mode: str = Query(..., description="Mode: 'Genes' or 'Ligand-Receptor'")):
    if mode.lower() == "genes":
        return settings.GENES_LIST
    elif mode.lower() == "ligand-receptor":
        return settings.LR_PAIRS_LIST
    else:
        return []

@router.get("/stats")
async def get_stats(
    organ: str = Query(..., description="Organ name"),
    technology: str = Query(..., description="Technology"),
    mode: str = Query("Ligand-Receptor", description="Genes or Ligand-Receptor") 
):
    try:
        # Get Stats (Fast)
        young_stats = MetadataService.get_stats_for_group(organ, technology, "Young")
        aged_stats = MetadataService.get_stats_for_group(organ, technology, "Aged")
        
        return {
            "stats": {
                "young": { "header": "Young Samples", "cell_stats": young_stats },
                "aged":  { "header": "Aged Samples",  "cell_stats": aged_stats }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plot")
async def get_plot(
    organ: str = Query(..., description="Organ name"),
    technology: str = Query(..., description="Technology"),
    feature: str = Query(None, description="Gene or LR Pair"),
    mode: str = Query("Ligand-Receptor", description="Genes or Ligand-Receptor") 
):
    try:
        # Default feature if not provided
        if not feature:
            feature = "C1qa_Cd33" # Default fallback
            
        # 1. Get List of Files
        young_files = MetadataService.get_sample_files(organ, technology, "young", mode)
        aged_files = MetadataService.get_sample_files(organ, technology, "aged", mode)
        
        # 2. Logic to choose plotter
        plot_func = None
        if technology.lower() == "visium":
            plot_func = plot_visium_brain 
        elif technology.lower() == "stomics":
            plot_func = plot_stomics_brain
        else:
            raise HTTPException(status_code=400, detail=f"Technology '{technology}' not supported.")

        # 3. Generate Plots
        response_data = {
            "young": [],
            "aged": []
        }
        
        def process_files(file_list, target_list):
            for file_info in file_list:
                try:
                    # Pass feature to plotter
                    img_base64 = plot_func(file_info['path'], feature)
                    if img_base64:
                        target_list.append({
                            "id": file_info['id'],
                            "image": img_base64,
                            "label": file_info['label']
                        })
                except Exception as e:
                    print(f"Skipping file {file_info['path']}: {e}")

        process_files(young_files, response_data["young"])
        process_files(aged_files, response_data["aged"])

        return response_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
