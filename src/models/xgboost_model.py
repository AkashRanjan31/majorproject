"""
xgboost_model.py
----------------
XGBoost Classifier.
"""
from xgboost import XGBClassifier


def build() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=300,
        learning_rate=0.08,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
        verbosity=0,
    )
