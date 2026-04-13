import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter()

FILE_MAP = {
    "organ_genes": "TableS1_SMACs_DEGs_5_organs.csv",
    "cell_type_degs": "TableS4_SMACs_CellType_DEGs_both_tech.csv",
    "de_lr_pairs": "TableS2_SMACs_DELRs_5_organs.csv",
    "conserved_lr_pairs": "TableS6_aging_LR_pairs_consistent_2tech_5organs.csv",
    "de_lr_pairs_human": "Human_consistent_DELRs.csv",
}

# Load all dataframes once at startup
dfs = {}
for key, filename in FILE_MAP.items():
    path = settings.DATA_STORAGE_PATH / filename
    try:
        if path.exists():
            df = pd.read_csv(path, index_col=0)
            df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
            dfs[key] = df
        else:
            print(f"Warning: Data file not found at {path}")
            dfs[key] = pd.DataFrame()
    except Exception as e:
        print(f"Error loading {key}: {e}")
        dfs[key] = pd.DataFrame()

# Load metadata once
meta_path = settings.DATA_STORAGE_PATH / "Multiorgan_Metadata.csv"
try:
    if meta_path.exists():
        meta_df = pd.read_csv(meta_path)
    else:
        print(f"Warning: Metadata file not found at {meta_path}")
        meta_df = pd.DataFrame()
except Exception as e:
    print(f"Error loading metadata: {e}")
    meta_df = pd.DataFrame()


@router.get("/data_search")
async def search_data(
        category: str = Query(..., description="Category of data to search"),
        query: str = Query("", description="Query to filter results"),
        species: str = Query("mouse", description="Organism"),
):
    try:
        # Resolve the human variant for de_lr_pairs
        key = f"{category}_human" if category == "de_lr_pairs" and species == "human" else category
        df = dfs.get(key)
        if df is None:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        if df.empty:
            return {"results": [], "total_matches": 0}

        if query:
            q = query.lower()
            if category == "organ_genes":
                mask = df['gene'].astype(str).str.lower().str.contains(q)
            elif category == "cell_type_degs":
                mask = df['genes'].astype(str).str.lower().str.contains(q) | \
                       df['cell_type'].astype(str).str.lower().str.contains(q)
            elif category == "de_lr_pairs":
                mask = df['LR pairs'].astype(str).str.lower().str.contains(q)
            elif category == "conserved_lr_pairs":
                mask = df['feature'].astype(str).str.lower().str.contains(q)
            else:
                mask = pd.Series(False, index=df.index)

            result_df = df[mask]
            total = int(mask.sum())
        else:
            result_df = df
            total = len(df)

        result_df = result_df.head(100).fillna("")
        return {"results": result_df.to_dict(orient="records"), "total_matches": total}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explore_organ")
async def explore_organ(organ: str = Query(..., description="Organ name")):
    try:
        if meta_df.empty:
            return {"stats": [], "summary": {}}

        # Filter by tech_org ending with the organ name or containing it
        tech_org = meta_df['tech_org'].astype(str).str.lower()
        mask = tech_org.str.endswith(organ.lower()) | tech_org.str.contains(
            f"_{organ.lower()}",
        )
        sub_df = meta_df[mask]

        if sub_df.empty:
            return {"stats": [], "summary": {}}

        # Group by sample to get sample-level info
        sample_stats = sub_df.groupby('orig.ident_2').agg(
            {
                'aged': 'first',
                'tech_org': 'first',
                'nFeature_Spatial': 'mean',
                'orig.ident_2': 'count'
            },
        ).rename(columns={'orig.ident_2': 'cell_count'}).reset_index()

        yes_count = len(sample_stats[sample_stats['aged'] == 'Yes'])
        no_count = len(sample_stats[sample_stats['aged'] == 'No'])

        return {
            "stats": sample_stats.to_dict(orient="records"),
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