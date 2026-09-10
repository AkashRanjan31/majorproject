"""
adaboost.py
-----------
AdaBoost Classifier.
"""
from sklearn.ensemble import AdaBoostClassifier


def build() -> AdaBoostClassifier:
    return AdaBoostClassifier(n_estimators=200, learning_rate=0.5, random_state=42)
