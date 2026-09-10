"""
evaluate.py
-----------
Evaluate the trained XGBoost model.
"""

from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import load_dataset
from src.preprocess import preprocess
from src.train_model import MODEL_PATH, train_model


def evaluate_model() -> None:
    """Print metrics and save evaluation graphs."""
    if not MODEL_PATH.exists():
        print("Saved model not found. Training first...")
        model, X_test, y_test, feature_names = train_model()
        class_names = ["Normal", "Moderate Fatigue", "High Fatigue"]
    else:
        saved = joblib.load(MODEL_PATH)
        model = saved["model"]
        feature_names = saved["feature_names"]
        class_names = saved.get("class_names", ["Normal", "Moderate Fatigue", "High Fatigue"])

        dataset = load_dataset()
        X, y, _ = preprocess(dataset, verbose=False)
        _, X_test, _, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    print("\n========== EVALUATION ==========")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
    print(f"Recall   : {recall_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")
    print(f"F1 Score : {f1_score(y_test, y_pred, average='weighted', zero_division=0):.4f}")

    labels = sorted(y_test.unique().tolist())
    names = [class_names[label] if label < len(class_names) else str(label) for label in labels]

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=labels, target_names=names, zero_division=0))

    save_confusion_matrix(y_test, y_pred, labels, names)
    save_feature_importance(model, feature_names)

    if len(labels) == 2:
        save_binary_roc_curve(y_test, y_prob[:, 1])
    else:
        print("\nROC curve skipped because the current problem has more than two classes.")


def save_confusion_matrix(y_test, y_pred, labels: list[int], names: list[str]) -> None:
    """Save the confusion matrix graph."""
    matrix = confusion_matrix(y_test, y_pred, labels=labels)
    plt.figure(figsize=(7, 5))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", xticklabels=names, yticklabels=names)
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "confusion_matrix.png", dpi=120)
    plt.close()
    print("Saved confusion_matrix.png")


def save_binary_roc_curve(y_test, positive_probabilities) -> None:
    """Save ROC curve only for binary classification."""
    fpr, tpr, _ = roc_curve(y_test, positive_probabilities)
    auc_score = roc_auc_score(y_test, positive_probabilities)

    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, label=f"AUC = {auc_score:.2f}")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "roc_curve.png", dpi=120)
    plt.close()
    print("Saved roc_curve.png")


def save_feature_importance(model, feature_names: list[str]) -> None:
    """Save a feature importance bar chart."""
    importance = pd.Series(model.feature_importances_, index=feature_names).sort_values(ascending=False)

    plt.figure(figsize=(10, 6))
    importance.plot(kind="bar", color="steelblue")
    plt.title("XGBoost Feature Importance")
    plt.ylabel("Importance Score")
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / "feature_importance.png", dpi=120)
    plt.close()

    print("Saved feature_importance.png")
    print("\nTop 5 features:")
    print(importance.head(5).to_string())


if __name__ == "__main__":
    evaluate_model()
