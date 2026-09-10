"""
lightgbm_model.py
-----------------
LightGBM Classifier.
"""
from lightgbm import LGBMClassifier


def build() -> LGBMClassifier:
    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.08,
        max_depth=6,
        random_state=42,
        verbose=-1,
    )
