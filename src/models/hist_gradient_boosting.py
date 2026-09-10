"""
hist_gradient_boosting.py
-------------------------
Histogram-based Gradient Boosting Classifier (fast, handles large data).
"""
from sklearn.ensemble import HistGradientBoostingClassifier


def build() -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_depth=6, random_state=42)
