"""
logistic_regression.py
----------------------
Logistic Regression with StandardScaler pipeline.
"""
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000, C=1.0, random_state=42, n_jobs=-1)),
    ])
