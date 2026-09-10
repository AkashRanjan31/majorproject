"""
gradient_boosting.py
--------------------
Scikit-learn Gradient Boosting Classifier.
"""
from sklearn.ensemble import GradientBoostingClassifier


def build() -> GradientBoostingClassifier:
    return GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42)
