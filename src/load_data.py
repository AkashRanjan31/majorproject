"""
load_data.py
------------
Load and inspect the dataset.
"""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_CSV = PROJECT_ROOT / "dataset" / "dataset.csv"
sys.path.insert(0, str(PROJECT_ROOT))


def load_dataset() -> pd.DataFrame:
    """
    Load dataset.csv if it exists. If not, create it from the raw TSV files.
    """
    if DATASET_CSV.exists():
        return pd.read_csv(DATASET_CSV)

    print("dataset/dataset.csv not found. Building it from raw TSV files...")
    from src.feature_engineering import build_feature_dataset

    return build_feature_dataset(save_csv=True)


def analyze_dataset(df: pd.DataFrame) -> None:
    """Display basic dataset information required for Step 1."""
    print("\n========== DATASET ANALYSIS ==========")
    print(f"Shape: {df.shape}")

    print("\nFirst five rows:")
    print(df.head().to_string(index=False))

    print("\nColumn data types:")
    print(df.dtypes.to_string())

    print("\nMissing values:")
    print(df.isnull().sum().to_string())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nStatistics:")
    print(df.describe(include="all").to_string())

    target = find_target_column(df)
    print(f"\nDetected target column: {target}")
    print(f"Number of classes: {df[target].nunique()}")
    print("\nClass distribution:")
    print(df[target].value_counts().sort_index().to_string())


def find_target_column(df: pd.DataFrame) -> str:
    """Automatically find the target column used for fatigue prediction."""
    possible_targets = ["fatigue_level", "fatigue_label", "Fatigue_Val", "target", "label", "class"]
    for column in possible_targets:
        if column in df.columns:
            return column
    return df.columns[-1]


if __name__ == "__main__":
    dataset = load_dataset()
    analyze_dataset(dataset)
