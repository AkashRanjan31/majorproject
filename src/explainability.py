"""
explainability.py
-----------------
SHAP-based global and local explanations + permutation importance.
Generates publication-quality explainability plots.
"""

import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import load_dataset
from src.preprocess import preprocess
from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)
config = get_config()

MODELS_DIR  = Path(config.MODELS_DIR)
PLOTS_DIR   = PROJECT_ROOT / "plots"
CLASS_NAMES = config.CLASS_NAMES


def _save(fig, name: str):
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved -> {path.name}")


def _load_best_model():
    path = MODELS_DIR / "best_model.pkl"
    if not path.exists():
        raise FileNotFoundError("best_model.pkl not found. Run multi_train.py first.")
    saved = joblib.load(path)
    return saved["model"], saved["feature_names"], saved.get("class_names", CLASS_NAMES)


def _load_best_tree_model():
    """
    Load the highest-ranked tree-based model for SHAP analysis.
    Falls back to best_model if no tree model is found.
    """
    csv_path = MODELS_DIR / "model_comparison.csv"
    tree_names = ["XGBoost", "RandomForest", "ExtraTrees", "GradientBoosting",
                  "HistGradientBoosting", "DecisionTree", "LightGBM", "CatBoost"]
    if csv_path.exists():
        import pandas as pd
        df = pd.read_csv(csv_path)
        for name in df["Model"]:
            if name in tree_names:
                pkl = MODELS_DIR / f"{name}.pkl"
                if pkl.exists():
                    saved = joblib.load(pkl)
                    logger.info(f"Using {name} for SHAP analysis")
                    return saved["model"], saved["feature_names"], saved.get("class_names", CLASS_NAMES)
    return _load_best_model()


def compute_shap_values(model, X_sample: pd.DataFrame):
    """Return SHAP explainer and values. Supports tree models and Pipelines."""
    import shap
    from sklearn.pipeline import Pipeline

    # Unwrap Pipeline: transform X with all steps except the final estimator
    inner_model = model
    X_transformed = X_sample.copy()
    if isinstance(model, Pipeline):
        inner_model = model[-1]  # final estimator
        # Apply all preprocessing steps
        for _, step in model.steps[:-1]:
            X_transformed = step.transform(X_transformed)
        X_transformed = pd.DataFrame(X_transformed, columns=X_sample.columns)

    try:
        explainer = shap.TreeExplainer(inner_model)
        shap_values = explainer.shap_values(X_transformed)
        # Wrap so callers get consistent (explainer, shap_values) with original X
        return explainer, shap_values
    except Exception:
        try:
            background = shap.sample(X_transformed, min(100, len(X_transformed)))
            explainer = shap.KernelExplainer(model.predict_proba, background)
            shap_values = explainer.shap_values(X_transformed.iloc[:50])
            return explainer, shap_values
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            return None, None


def plot_shap_summary(shap_values, X_sample: pd.DataFrame, feature_names: list):
    """Global SHAP summary beeswarm plot."""
    import shap
    try:
        # For multi-class, shap_values is a list; use class with highest mean |SHAP|
        if isinstance(shap_values, list):
            mean_abs = [np.abs(sv).mean() for sv in shap_values]
            sv = shap_values[int(np.argmax(mean_abs))]
        else:
            sv = shap_values

        fig, ax = plt.subplots(figsize=(10, 8))
        shap.summary_plot(sv, X_sample, feature_names=feature_names,
                          show=False, plot_size=None)
        ax = plt.gca()
        ax.set_title("SHAP Feature Importance (Global)", fontsize=13, fontweight="bold")
        _save(fig, "shap_summary.png")
    except Exception as e:
        logger.error(f"SHAP summary plot failed: {e}")


def plot_shap_bar(shap_values, feature_names: list):
    """Global mean |SHAP| bar chart."""
    try:
        sv = shap_values
        # Handle list-of-arrays (old SHAP multi-class) or 3D array (new SHAP)
        if isinstance(sv, list):
            mean_abs = np.mean([np.abs(s).mean(axis=0) for s in sv], axis=0)
        elif isinstance(sv, np.ndarray) and sv.ndim == 3:
            # shape: (samples, features, classes) — mean over samples and classes
            mean_abs = np.abs(sv).mean(axis=(0, 2))
        else:
            mean_abs = np.abs(sv).mean(axis=0)

        imp = pd.Series(mean_abs, index=feature_names).sort_values(ascending=True).tail(20)
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(imp)))
        fig, ax = plt.subplots(figsize=(10, 8))
        imp.plot(kind="barh", ax=ax, color=colors)
        ax.set_title("Mean |SHAP| -- Global Feature Importance", fontsize=13, fontweight="bold")
        ax.set_xlabel("Mean |SHAP Value|", fontsize=11)
        _save(fig, "shap_bar.png")
    except Exception as e:
        logger.error(f"SHAP bar plot failed: {e}")


def plot_shap_local(explainer, X_sample: pd.DataFrame, feature_names: list,
                    sample_idx: int = 0, class_idx: int = 0):
    """Local SHAP waterfall for a single prediction."""
    import shap
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        shap_vals = explainer(X_sample.iloc[[sample_idx]])
        if hasattr(shap_vals, "values") and shap_vals.values.ndim == 3:
            # Multi-class: pick class_idx
            vals = shap_vals.values[0, :, class_idx]
            base = shap_vals.base_values[0, class_idx]
        else:
            vals = shap_vals.values[0]
            base = shap_vals.base_values[0] if hasattr(shap_vals, "base_values") else 0

        # Manual waterfall
        sorted_idx = np.argsort(np.abs(vals))[-15:]
        feat_vals = [feature_names[i] for i in sorted_idx]
        shap_v    = vals[sorted_idx]
        colors    = ["#ef4444" if v > 0 else "#22c55e" for v in shap_v]
        ax.barh(feat_vals, shap_v, color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(f"Local SHAP Explanation — Sample #{sample_idx}\n"
                     f"Class: {CLASS_NAMES[class_idx]}", fontsize=12, fontweight="bold")
        ax.set_xlabel("SHAP Value (impact on prediction)", fontsize=10)
        _save(fig, f"shap_local_sample{sample_idx}.png")
    except Exception as e:
        logger.error(f"Local SHAP plot failed: {e}")


def plot_permutation_importance(model, X_test: pd.DataFrame, y_test, feature_names: list):
    """Permutation importance plot."""
    from sklearn.inspection import permutation_importance
    try:
        result = permutation_importance(model, X_test, y_test, n_repeats=10,
                                        random_state=42, n_jobs=-1)
        imp = pd.Series(result.importances_mean, index=feature_names).sort_values(ascending=True).tail(20)
        err = pd.Series(result.importances_std, index=feature_names).reindex(imp.index)
        colors = plt.cm.coolwarm(np.linspace(0.1, 0.9, len(imp)))
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.barh(imp.index, imp.values, xerr=err.values, color=colors, capsize=3)
        ax.set_title("Permutation Feature Importance", fontsize=13, fontweight="bold")
        ax.set_xlabel("Mean Accuracy Decrease", fontsize=11)
        _save(fig, "permutation_importance.png")
    except Exception as e:
        logger.error(f"Permutation importance failed: {e}")


def explain_prediction(feature_vector: list, feature_names: list) -> dict:
    """
    Generate a human-readable explanation for a single prediction.
    Returns dict with fatigue level, score, and top contributing features.
    """
    model, feat_names, class_names = _load_best_model()
    import shap, numpy as np

    X = pd.DataFrame([feature_vector], columns=feat_names)
    pred_class = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    confidence = float(proba[pred_class])
    fatigue_score = int(pred_class / (len(class_names) - 1) * 100)

    # SHAP local explanation
    try:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X)
        if isinstance(shap_vals, list):
            sv = shap_vals[pred_class][0]
        else:
            sv = shap_vals[0]
        top_idx = np.argsort(np.abs(sv))[::-1][:5]
        reasons = []
        for i in top_idx:
            direction = "increased" if sv[i] > 0 else "decreased"
            reasons.append({
                "feature": feat_names[i],
                "value": round(float(feature_vector[i]), 3),
                "shap": round(float(sv[i]), 4),
                "direction": direction,
            })
    except Exception:
        reasons = []

    return {
        "fatigue_level": pred_class,
        "fatigue_name": class_names[pred_class],
        "fatigue_score": fatigue_score,
        "confidence": round(confidence * 100, 1),
        "probabilities": {class_names[i]: round(float(p) * 100, 1) for i, p in enumerate(proba)},
        "reasons": reasons,
    }


def run_full_explainability():
    """Run all explainability analyses on the best model."""
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline

    print("\n" + "=" * 60)
    print("EXPLAINABILITY ANALYSIS")
    print("=" * 60)

    model, feature_names, class_names = _load_best_tree_model()
    dataset = load_dataset()
    X, y, _ = preprocess(dataset, verbose=False)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

    X_sample = X_test.copy()
    X_sample.columns = feature_names

    print(f"\nModel: {type(model).__name__}")
    print(f"Features: {len(feature_names)}")
    print("Computing SHAP values...")

    explainer, shap_values = compute_shap_values(model, X_sample)

    if shap_values is not None:
        plot_shap_summary(shap_values, X_sample, feature_names)
        plot_shap_bar(shap_values, feature_names)
        plot_shap_local(explainer, X_sample, feature_names, sample_idx=0)

    plot_permutation_importance(model, X_test, y_test, feature_names)
    print("\nExplainability analysis complete.")


if __name__ == "__main__":
    run_full_explainability()
