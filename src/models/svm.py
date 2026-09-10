"""
svm.py
------
Support Vector Machine with RBF kernel and StandardScaler pipeline.
"""
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def build() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVC(kernel="rbf", C=10, gamma="scale", probability=True, random_state=42)),
    ])
