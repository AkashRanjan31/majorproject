"""
catboost_model.py
-----------------
CatBoost Classifier.
"""
from catboost import CatBoostClassifier


def build() -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=300,
        learning_rate=0.08,
        depth=6,
        random_seed=42,
        verbose=0,
    )
