import json
import os

import pandas as pd

from app.core.config import settings

DATA_DIR = str(settings.DATA_STORAGE_PATH)
LR_DIR = str(settings.LR_DIR)
GENES_DIR = str(settings.GENES_DIR)


class MetadataService:
    @staticmethod
    def _load_sample_config():
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "sample_metadata.json",
            )
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sample config: {e}")
            return {}

    @staticmethod
    def get_sample_files(
            organ: str, technology: str, age_group: str, mode: str = "Ligand-Receptor",
    ):
        """
        Returns a list of dictionaries with 'id', 'path', 'label' for valid samples.
        """
        organ_key = organ.lower()
        tech_key = technology.lower()
        target_age = age_group.lower()  # 'young' or 'aged'

        # Select Directory based on Mode
        if mode.lower() == "genes":
            base_dir = GENES_DIR
        else:
            base_dir = LR_DIR

        # Load Config
        config = MetadataService._load_sample_config()

        # Get rules for this specific combination
        # Structure: config[tech][organ]['aged'/'young'] -> list of filenames
        tech_config = config.get(tech_key, {})
        organ_config = tech_config.get(organ_key, {})

        if not organ_config:
            return []

        # Get Filenames List
        filenames = organ_config.get(target_age, [])

        results = []
        for fname in filenames:
            full_path = os.path.join(base_dir, fname)

            # Check if file exists (optional, but good for safety)
            # if not os.path.exists(full_path): continue 

            label = fname.replace(".pkl", "")
            results.append(
                {
                    "id": label,
                    "path": full_path,
                    "label": label
                },
            )

        return results

    @staticmethod
    def get_stats_for_group(organ: str, technology: str, age_group: str):
        organ_cap = organ.capitalize()
        csv_path = os.path.join(DATA_DIR, f"{organ_cap}_Proportions.csv")

        if not os.path.exists(csv_path):
            return "Stats not available."

        try:
            # Load CSV
            df = pd.read_csv(csv_path)

            # Sanitize Columns
            if 'Tech' in df.columns:
                df['Tech'] = df['Tech'].astype(str).str.strip()
            if 'age' in df.columns:
                df['age'] = df['age'].astype(str).str.strip()

            # Map filters
            # Tech in CSV: "Visium" or "STOmics" (Check case)
            target_tech = "Visium" if technology.lower() == "visium" else "STOmics"

            # Age in CSV: "Aged" or "Young"
            target_age = "Aged" if age_group.lower() == "aged" else "Young"

            # Filter
            mask = (df['Tech'] == target_tech) & (df['age'] == target_age)
            subset = df[mask]

            if subset.empty:
                print(
                    f"Stats Debug: Filter failed for {target_tech}/{target_age} in {csv_path}",
                )
                print(f"Available Techs: {df['Tech'].unique()}")
                print(f"Available Ages: {df['age'].unique()}")
                return "No stats data found."

            # Columns to average: All except metadata
            numeric_cols = subset.select_dtypes(
                include=['float64', 'float32', 'int'],
            ).columns

            # Calculate Mean
            means = subset[numeric_cols].mean()

            # Sort by value desc
            means = means.sort_values(ascending=False)

            # Format string: "CellType: XX%\n..."
            lines = []
            for cell, val in means.items():
                if val < 0.01: continue  # Skip < 1%
                lines.append(f"{cell}: {(val * 100):.1f}%")

            return "\n".join(lines)

        except Exception as e:
            return f"Error: {str(e)}"
