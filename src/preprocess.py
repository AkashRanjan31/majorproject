"""
preprocess.py
-------------
Clean and prepare the dataset for multi-model training.
Handles 5-class fatigue labels and all 40+ features.
"""

from pathlib import Path
import sys

import pandas as pd
from sklearn.preprocessing import LabelEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import find_target_column


def preprocess(df: pd.DataFrame, verbose: bool = True) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """
    Clean dataset: remove duplicates, fill missing values, encode categoricals.
    Returns (X, y, feature_names).
    Note: Scaling is NOT applied here — models that need it (KNN, SVM, LR, MLP)
    include a StandardScaler in their own Pipeline.
    """
    if verbose:
        print(f"\n{'='*40}\nPREPROCESSING\n{'='*40}")
        print(f"Input shape: {df.shape}")

    df = df.copy()
    target_col = find_target_column(df)

    # Remove duplicates
    n_dup = df.duplicated().sum()
    df = df.drop_duplicates()
    if verbose and n_dup:
        print(f"Removed {n_dup} duplicate rows")

    # Fill missing values
    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna(df[col].mode()[0])

    # Encode categorical features (not target)
    for col in df.columns:
        if col == target_col:
            continue
        if df[col].dtype == "object":
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    # Encode target if needed
    if df[target_col].dtype == "object":
        df[target_col] = LabelEncoder().fit_transform(df[target_col].astype(str))

    y = df[target_col].astype(int)
    X = df.drop(columns=[target_col])

    non_numeric = X.select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        raise ValueError(f"Non-numeric feature columns remain: {non_numeric}")

    feature_names = list(X.columns)

    if verbose:
        print(f"Features: {len(feature_names)}")
        print(f"Samples : {len(X)}")
        print(f"Classes : {sorted(y.unique().tolist())}")
        print("Class balance:")
        print(y.value_counts().sort_index().to_string())

    return X, y, feature_names
