"""
multi_train.py
--------------
Train all 14 models, collect metrics, rank them, and save every artifact.
"""

import sys
import time
import tracemalloc
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    precision_score, recall_score, roc_auc_score,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import load_dataset
from src.preprocess import preprocess
from src.logger import setup_logger
from src.config import get_config
from src.models import MODEL_REGISTRY

logger = setup_logger(__name__)
config = get_config()

MODELS_DIR = Path(config.MODELS_DIR)
CLASS_NAMES = config.CLASS_NAMES


def _roc_auc(model, X_test, y_test) -> float:
    """Compute OvR macro ROC-AUC; return 0.0 on failure."""
    try:
        proba = model.predict_proba(X_test)
        n_classes = len(np.unique(y_test))
        if proba.shape[1] < n_classes:
            return 0.0
        return float(roc_auc_score(y_test, proba, multi_class="ovr", average="macro"))
    except Exception:
        return 0.0


def train_all() -> pd.DataFrame:
    """Train every model in MODEL_REGISTRY and return a ranked comparison DataFrame."""
    dataset = load_dataset()
    X, y, feature_names = preprocess(dataset, verbose=False)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for name, builder in MODEL_REGISTRY.items():
        logger.info(f"Training {name}...")
        print(f"\n{'='*50}\nTraining: {name}\n{'='*50}")

        model = builder()

        # ── Training time ──────────────────────────────────────────────
        tracemalloc.start()
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_time = time.perf_counter() - t0
        _, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # ── Inference time ─────────────────────────────────────────────
        t1 = time.perf_counter()
        y_pred = model.predict(X_test)
        pred_time = time.perf_counter() - t1
        inference_speed = len(X_test) / pred_time if pred_time > 0 else 0

        # ── Core metrics ───────────────────────────────────────────────
        acc    = accuracy_score(y_test, y_pred)
        bal_acc= balanced_accuracy_score(y_test, y_pred)
        prec   = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec    = recall_score(y_test, y_pred, average="weighted", zero_division=0)
        f1     = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
        auc    = _roc_auc(model, X_test, y_test)

        # ── Cross-validation ───────────────────────────────────────────
        cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy", n_jobs=-1)
        cv_mean   = float(cv_scores.mean())
        cv_std    = float(cv_scores.std())

        # ── Model size on disk ─────────────────────────────────────────
        model_path = MODELS_DIR / f"{name}.pkl"
        artifact = {
            "model": model,
            "feature_names": feature_names,
            "class_names": CLASS_NAMES,
            "metrics": {
                "accuracy":          acc,
                "balanced_accuracy": bal_acc,
                "f1":                f1,
                "macro_f1":          macro_f1,
                "weighted_f1":       f1,
                "precision":         prec,
                "recall":            rec,
                "roc_auc":           auc,
            },
        }
        joblib.dump(artifact, model_path)
        model_size_kb = model_path.stat().st_size / 1024

        row = {
            "Model":            name,
            "Accuracy":         round(acc, 4),
            "Balanced_Acc":     round(bal_acc, 4),
            "Precision":        round(prec, 4),
            "Recall":           round(rec, 4),
            "F1_Score":         round(f1, 4),
            "Macro_F1":         round(macro_f1, 4),
            "ROC_AUC":          round(auc, 4),
            "CV_Accuracy":      round(cv_mean, 4),
            "CV_Std":           round(cv_std, 4),
            "Train_Time_s":     round(train_time, 3),
            "Pred_Time_ms":     round(pred_time * 1000, 3),
            "Memory_MB":        round(mem_peak / 1024 / 1024, 3),
            "Model_Size_KB":    round(model_size_kb, 1),
            "Inference_Speed":  round(inference_speed, 0),
        }
        results.append(row)
        print(f"  Accuracy={acc:.4f}  F1={f1:.4f}  AUC={auc:.4f}  CV={cv_mean:.4f}±{cv_std:.4f}")

    df_results = pd.DataFrame(results)

    # ── Composite rank score (weighted) ───────────────────────────────
    df_results["Rank_Score"] = (
        0.30 * df_results["Accuracy"] +
        0.25 * df_results["F1_Score"] +
        0.20 * df_results["ROC_AUC"] +
        0.15 * df_results["CV_Accuracy"] +
        0.10 * df_results["Precision"]
    )
    df_results = df_results.sort_values("Rank_Score", ascending=False).reset_index(drop=True)
    df_results["Rank"] = df_results.index + 1

    # ── Save comparison CSV ────────────────────────────────────────────
    csv_path = MODELS_DIR / "model_comparison.csv"
    df_results.to_csv(csv_path, index=False)
    logger.info(f"Comparison saved -> {csv_path}")

    # ── Copy best model as best_model.pkl ─────────────────────────────
    best_name = df_results.iloc[0]["Model"]
    best_src  = MODELS_DIR / f"{best_name}.pkl"
    best_dst  = MODELS_DIR / "best_model.pkl"
    joblib.dump(joblib.load(best_src), best_dst)

    print(f"\n{'='*50}")
    print(f"BEST MODEL: {best_name}  (Rank Score={df_results.iloc[0]['Rank_Score']:.4f})")
    print(f"Saved -> {best_dst}")
    print(f"{'='*50}")
    print("\nFull Ranking:")
    print(df_results[["Rank", "Model", "Accuracy", "F1_Score", "ROC_AUC", "CV_Accuracy"]].to_string(index=False))

    return df_results


if __name__ == "__main__":
    train_all()
