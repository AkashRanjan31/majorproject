"""
knn.py
------
k-Nearest Neighbors — baseline model from HAIS 2013 paper.
"""
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build() -> Pipeline:
    """Return a scaled KNN pipeline (scaling is critical for KNN)."""
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", KNeighborsClassifier(n_neighbors=7, weights="distance", metric="euclidean")),
    ])
