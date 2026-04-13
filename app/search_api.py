import pandas as pd
import os
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

# Read from SMACsBackend data dir as specified
DATA_DIR = "/scratch/user/s4634945/group_scratch/github_Softwares/repos/SMACsBackend/data"

FILE_MAP = {
    "organ_genes": "TableS1_SMACs_DEGs_5_organs.csv",
    "cell_type_degs": "TableS4_SMACs_CellType_DEGs_both_tech.csv",
    "de_lr_pairs": "TableS2_SMACs_DELRs_5_organs.csv",
    "conserved_lr_pairs": "TableS6_aging_LR_pairs_consistent_2tech_5organs.csv",
}

dfs = {}

def get_df(category, species="mouse"):
    key = f"{category}_{species}"
    if key not in dfs:
        if category == "de_lr_pairs" and species == "human":
            path = os.path.join(DATA_DIR, "Human_consistent_DELRs.csv")
        else:
            if category not in FILE_MAP:
                raise ValueError("Invalid category")
            path = os.path.join(DATA_DIR, FILE_MAP[category])
            
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path} (make sure the data directory and files exist)")
        df = pd.read_csv(path, index_col=0)
        
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        dfs[key] = df
    return dfs[key]

@router.get("/data_search")
async def search_data(
    category: str = Query(..., description="Category of data to search"),
    query: str = Query("", description="Query to filter results"),
    species: str = Query("mouse", description="Organism")
):
    try:
        df = get_df(category, species)
        
        if query:
            q = query.lower()
            if category == "organ_genes":
                mask = df['gene'].astype(str).str.lower().str.contains(q)
            elif category == "cell_type_degs":
                mask = df['genes'].astype(str).str.lower().str.contains(q) | df['cell_type'].astype(str).str.lower().str.contains(q)
            elif category == "de_lr_pairs":
                mask = df['LR pairs'].astype(str).str.lower().str.contains(q)
            elif category == "conserved_lr_pairs":
                mask = df['feature'].astype(str).str.lower().str.contains(q)
            else:
                mask = pd.Series(False, index=df.index)
            
            result_df = df[mask]
        else:
            result_df = df
            
        result_df = result_df.head(100).fillna("")
        return {"results": result_df.to_dict(orient="records"), "total_matches": len(df[mask] if query else df)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

MULTI_ORGAN_META = os.path.join(DATA_DIR, "Multiorgan_Metadata.csv")
meta_df = None

def get_meta_df():
    global meta_df
    if meta_df is None:
        if os.path.exists(MULTI_ORGAN_META):
            meta_df = pd.read_csv(MULTI_ORGAN_META)
        else:
            raise FileNotFoundError(f"Metadata file not found: {MULTI_ORGAN_META}")
    return meta_df

@router.get("/explore_organ")
async def explore_organ(organ: str = Query(..., description="Organ name")):
    try:
        df = get_meta_df()
        
        # Filter by tech_org ending with the organ name or containing it
        mask = df['tech_org'].astype(str).str.lower().str.endswith(organ.lower()) | df['tech_org'].astype(str).str.lower().str.contains(f"_{organ.lower()}")
        sub_df = df[mask]
        
        if sub_df.empty:
            return {"stats": [], "summary": {}}
            
        # We need:
        # Number of replicates
        # Bar charts / stats for 'aged' (Yes/No)
        # Average nFeature_Spatial by sample
        
        # Group by sample (orig.ident_2) to get the sample-level info
        # Taking mode/first for tech_org and aged, and mean for nFeature_Spatial
        sample_stats = sub_df.groupby('orig.ident_2').agg({
            'aged': 'first',
            'tech_org': 'first',
            'nFeature_Spatial': 'mean',
            'orig.ident_2': 'count' # using count as number of spots/cells
        }).rename(columns={'orig.ident_2': 'cell_count'}).reset_index()
        
        # summary stats
        yes_count = len(sample_stats[sample_stats['aged'] == 'Yes'])
        no_count = len(sample_stats[sample_stats['aged'] == 'No'])
        
        results = sample_stats.to_dict(orient="records")
        return {
            "stats": results,
            "summary": {
                "total_samples": len(sample_stats),
                "aged_samples": yes_count,
                "young_samples": no_count,
                "total_cells": int(sub_df.shape[0])
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
