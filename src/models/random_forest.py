"""
random_forest.py
----------------
Random Forest Classifier.
"""
from sklearn.ensemble import RandomForestClassifier


def build() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42, n_jobs=-1)
