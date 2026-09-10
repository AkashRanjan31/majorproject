"""
decision_tree.py
----------------
Decision Tree Classifier with depth tuning.
"""
from sklearn.tree import DecisionTreeClassifier


def build() -> DecisionTreeClassifier:
    return DecisionTreeClassifier(max_depth=12, min_samples_split=5, random_state=42)
