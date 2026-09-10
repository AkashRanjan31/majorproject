"""
extra_trees.py
--------------
Extra Trees Classifier (Extremely Randomized Trees).
"""
from sklearn.ensemble import ExtraTreesClassifier


def build() -> ExtraTreesClassifier:
    return ExtraTreesClassifier(n_estimators=200, random_state=42, n_jobs=-1)
