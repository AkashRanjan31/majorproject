"""
train_model.py
--------------
Train only an XGBoost Classifier and save it with joblib.
"""

from pathlib import Path
import sys

import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "xgboost_model.pkl"
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import load_dataset
from src.preprocess import preprocess


def train_model():
    """Load data, preprocess it, split it, train XGBoost, and save the model."""
    dataset = load_dataset()
    X, y, feature_names = preprocess(dataset, verbose=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    print("\n========== TRAINING ==========")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples : {len(X_test)}")

    model = XGBClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="mlogloss",
    )

    model.fit(X_train, y_train)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_names": feature_names,
            "class_names": ["Normal", "Moderate Fatigue", "High Fatigue"],
        },
        MODEL_PATH,
    )

    print(f"Model saved to: {MODEL_PATH}")
    return model, X_test, y_test, feature_names


if __name__ == "__main__":
    train_model()
