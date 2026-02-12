from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
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
    
# Hardcoded Feature Lists
GENES_LIST = """
Apoe B2m Ctsd Grn Apod Cd44 Cfh Efemp1 C1qa Gdf15 Agt Ntn4 Vegfa Mmp2 H2-D1 H2-K1 Trf Anxa2 Cst3 Anxa1 Bgn C1qb C4b Cd84 Cp Csf1 F13a1 Lgals1 Lgals3 Ly86 Penk Serping1 Vwf Sdc1 Ccl5 Cdh4 C3 Cd248 Dkk3 Entpd1 Pltp Ptprc Thy1 Tnfsf13b Tnxb Vcam1 Adm Cd14 Icam1 Lair1 S100a4 S100a8 Slpi Spn Timp1 Ccl12 Ccn2 Lcn2 Ftl1 Vim Itgb1 Cd44 Il2rg Eng Cd63 Cd74 C3ar1 C5ar1 Cd53 Cd84 Gpnmb Itgal Pirb Tlr2 Sdc1 Tlr4 Cdh4 Cd248 Cd36 Cd72 Csf3r Gpc1 Itga4 Itgax Lrp1 Ptprc Thy1 Cxcr4 Icam1 Il4ra Lair1 Ramp3 Spn Tnfrsf12a Trem2 Tyrobp
""".split()

LR_PAIRS_LIST = """
Bgn_Tlr2 Timp1_Itgb1 Timp1_Lrp1 Lgals3_Itgb3 C1qa_Cd33 Icam1_Itgam Icam1_Itgb2 Ccl5_Sdc4 Gnai2_C5ar1 Lgals3_Itgb1 C1qb_Cd33 Ccl5_Ccrl2 Vcam1_Itgb2 Lgals3_Mertk Cd14_Tlr2 Cd14_Itgb2 Sema6d_Trem2 Hmgb1_Tlr1 Anxa2_Tlr2 Mrc1_Ptprc Adam10_Gpnmb Angptl2_Pirb Cd14_Tlr4 Sema4d_Cd72 Icam1_Itgax Hmgb1_Tlr2 Ccl4_Ccr5 Lcn2_Slc22a17 Plau_Itgb2 St6gal1_Cd22 Bsg_Spn
""".split()

@router.get("/features")
async def get_features(mode: str = Query(..., description="Mode: 'Genes' or 'Ligand-Receptor'")):
    if mode.lower() == "genes":
        return GENES_LIST
    elif mode.lower() == "ligand-receptor":
        return LR_PAIRS_LIST
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
