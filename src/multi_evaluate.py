"""
multi_evaluate.py
-----------------
Generate publication-quality comparison plots and per-model evaluation artifacts.
"""

import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_recall_curve, roc_auc_score, roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.load_data import load_dataset
from src.preprocess import preprocess
from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)
config  = get_config()

MODELS_DIR  = Path(config.MODELS_DIR)
PLOTS_DIR   = PROJECT_ROOT / "plots"
CLASS_NAMES = config.CLASS_NAMES
PALETTE     = config.CLASS_COLORS
N_CLASSES   = len(CLASS_NAMES)

_STYLE = {"figure.facecolor": "white", "axes.facecolor": "#f8f9fa",
          "axes.grid": True, "grid.alpha": 0.4}


def _save(fig, name: str):
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved -> {path.name}")


# ── 1. Model Comparison Bar Chart ─────────────────────────────────────────────
def plot_model_comparison(df: pd.DataFrame):
    metrics = ["Accuracy", "F1_Score", "ROC_AUC", "CV_Accuracy"]
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle("Model Comparison — All 14 Classifiers", fontsize=16, fontweight="bold")
        colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(df)))
        for ax, metric in zip(axes.flat, metrics):
            bars = ax.barh(df["Model"], df[metric], color=colors)
            ax.set_xlabel(metric.replace("_", " "), fontsize=11)
            ax.set_xlim(0, 1.05)
            ax.bar_label(bars, fmt="%.4f", padding=3, fontsize=8)
            ax.set_title(metric.replace("_", " "), fontsize=12, fontweight="bold")
            # Highlight best
            best_idx = df[metric].idxmax()
            bars[best_idx].set_edgecolor("gold")
            bars[best_idx].set_linewidth(2.5)
        plt.tight_layout()
    _save(fig, "model_comparison_bar.png")


# ── 2. Radar / Spider Chart ────────────────────────────────────────────────────
def plot_radar(df: pd.DataFrame):
    metrics = ["Accuracy", "Precision", "Recall", "F1_Score", "ROC_AUC", "CV_Accuracy"]
    top5 = df.head(5)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    with plt.rc_context({"figure.facecolor": "white"}):
        fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={"polar": True})
        cmap = plt.cm.tab10
        for i, (_, row) in enumerate(top5.iterrows()):
            vals = [row[m] for m in metrics] + [row[metrics[0]]]
            ax.plot(angles, vals, "o-", linewidth=2, label=row["Model"], color=cmap(i))
            ax.fill(angles, vals, alpha=0.08, color=cmap(i))
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.replace("_", "\n") for m in metrics], fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_title("Top-5 Models — Radar Chart", fontsize=14, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15))
    _save(fig, "radar_chart.png")


# ── 3. Heatmap of all metrics ──────────────────────────────────────────────────
def plot_metrics_heatmap(df: pd.DataFrame):
    cols = ["Accuracy", "Precision", "Recall", "F1_Score", "ROC_AUC", "CV_Accuracy"]
    heat = df.set_index("Model")[cols]
    with plt.rc_context({"figure.facecolor": "white"}):
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(heat, annot=True, fmt=".4f", cmap="YlOrRd", linewidths=0.5,
                    linecolor="white", ax=ax, vmin=0, vmax=1,
                    annot_kws={"size": 9})
        ax.set_title("Model Performance Heatmap", fontsize=14, fontweight="bold")
        ax.set_xlabel("")
        plt.xticks(rotation=30, ha="right")
    _save(fig, "metrics_heatmap.png")


# ── 4. Training Time vs Accuracy scatter ──────────────────────────────────────
def plot_time_vs_accuracy(df: pd.DataFrame):
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(11, 7))
        scatter = ax.scatter(df["Train_Time_s"], df["Accuracy"],
                             s=df["Model_Size_KB"] / 2 + 40,
                             c=df["F1_Score"], cmap="plasma", alpha=0.85, edgecolors="k", linewidths=0.5)
        for _, row in df.iterrows():
            ax.annotate(row["Model"], (row["Train_Time_s"], row["Accuracy"]),
                        textcoords="offset points", xytext=(6, 4), fontsize=8)
        plt.colorbar(scatter, ax=ax, label="F1 Score")
        ax.set_xlabel("Training Time (seconds)", fontsize=12)
        ax.set_ylabel("Accuracy", fontsize=12)
        ax.set_title("Training Time vs Accuracy\n(bubble size = model file size)", fontsize=13, fontweight="bold")
    _save(fig, "time_vs_accuracy.png")


# ── 5. Per-model Confusion Matrix ─────────────────────────────────────────────
def plot_confusion_matrices(models_data: dict, y_test, X_test):
    n = len(models_data)
    cols = 4
    rows = (n + cols - 1) // cols
    with plt.rc_context({"figure.facecolor": "white"}):
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4.5))
        axes = axes.flat
        for ax, (name, model) in zip(axes, models_data.items()):
            y_pred = model.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                        xticklabels=[c[:3] for c in CLASS_NAMES],
                        yticklabels=[c[:3] for c in CLASS_NAMES],
                        linewidths=0.3, linecolor="white")
            ax.set_title(name, fontsize=10, fontweight="bold")
            ax.set_xlabel("Predicted", fontsize=8)
            ax.set_ylabel("Actual", fontsize=8)
            ax.tick_params(labelsize=7)
        for ax in list(axes)[len(models_data):]:
            ax.set_visible(False)
        fig.suptitle("Confusion Matrices — All Models", fontsize=15, fontweight="bold")
        plt.tight_layout()
    _save(fig, "all_confusion_matrices.png")


# ── 6. Multi-class ROC Curves (top 5 models) ──────────────────────────────────
def plot_roc_curves(models_data: dict, X_test, y_test, top_n: int = 5):
    y_bin = label_binarize(y_test, classes=list(range(N_CLASSES)))
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, min(top_n, len(models_data)),
                                 figsize=(5 * min(top_n, len(models_data)), 5))
        if top_n == 1:
            axes = [axes]
        cmap = plt.cm.tab10
        for ax, (name, model) in zip(axes, list(models_data.items())[:top_n]):
            try:
                proba = model.predict_proba(X_test)
                for i, cls in enumerate(CLASS_NAMES):
                    fpr, tpr, _ = roc_curve(y_bin[:, i], proba[:, i])
                    auc = roc_auc_score(y_bin[:, i], proba[:, i])
                    ax.plot(fpr, tpr, color=cmap(i), lw=1.5, label=f"{cls[:8]} (AUC={auc:.2f})")
                ax.plot([0, 1], [0, 1], "k--", lw=0.8)
                ax.set_title(name, fontsize=10, fontweight="bold")
                ax.set_xlabel("FPR", fontsize=9)
                ax.set_ylabel("TPR", fontsize=9)
                ax.legend(fontsize=7)
            except Exception:
                ax.set_title(f"{name}\n(ROC N/A)")
        fig.suptitle("Multi-class ROC Curves (OvR) — Top Models", fontsize=13, fontweight="bold")
        plt.tight_layout()
    _save(fig, "roc_curves_multiclass.png")


# ── 7. Precision-Recall Curves ────────────────────────────────────────────────
def plot_pr_curves(models_data: dict, X_test, y_test, top_n: int = 5):
    y_bin = label_binarize(y_test, classes=list(range(N_CLASSES)))
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, min(top_n, len(models_data)),
                                 figsize=(5 * min(top_n, len(models_data)), 5))
        if top_n == 1:
            axes = [axes]
        cmap = plt.cm.tab10
        for ax, (name, model) in zip(axes, list(models_data.items())[:top_n]):
            try:
                proba = model.predict_proba(X_test)
                for i, cls in enumerate(CLASS_NAMES):
                    prec_arr, rec_arr, _ = precision_recall_curve(y_bin[:, i], proba[:, i])
                    ax.plot(rec_arr, prec_arr, color=cmap(i), lw=1.5, label=cls[:8])
                ax.set_title(name, fontsize=10, fontweight="bold")
                ax.set_xlabel("Recall", fontsize=9)
                ax.set_ylabel("Precision", fontsize=9)
                ax.legend(fontsize=7)
            except Exception:
                ax.set_title(f"{name}\n(PR N/A)")
        fig.suptitle("Precision-Recall Curves — Top Models", fontsize=13, fontweight="bold")
        plt.tight_layout()
    _save(fig, "pr_curves.png")


# ── 8. Feature Importance (top 3 tree models) ─────────────────────────────────
def plot_feature_importance(models_data: dict, feature_names: list, top_n_features: int = 20):
    tree_models = {n: m for n, m in models_data.items()
                   if hasattr(m, "feature_importances_")}
    if not tree_models:
        return
    n = min(3, len(tree_models))
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, n, figsize=(8 * n, 8))
        if n == 1:
            axes = [axes]
        for ax, (name, model) in zip(axes, list(tree_models.items())[:n]):
            imp = pd.Series(model.feature_importances_, index=feature_names)
            imp = imp.nlargest(top_n_features).sort_values()
            colors = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(imp)))
            imp.plot(kind="barh", ax=ax, color=colors)
            ax.set_title(f"{name}\nFeature Importance", fontsize=11, fontweight="bold")
            ax.set_xlabel("Importance Score", fontsize=9)
        plt.tight_layout()
    _save(fig, "feature_importance_comparison.png")


# ── 9. Cross-validation box plot ──────────────────────────────────────────────
def plot_cv_boxplot(models_data: dict, X, y):
    from sklearn.model_selection import cross_val_score
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(14, 6))
        all_scores, labels = [], []
        for name, model in models_data.items():
            scores = cross_val_score(model, X, y, cv=5, scoring="accuracy", n_jobs=-1)
            all_scores.append(scores)
            labels.append(name)
        bp = ax.boxplot(all_scores, tick_labels=labels, patch_artist=True, notch=False)
        colors = plt.cm.tab20(np.linspace(0, 1, len(labels)))
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
        ax.set_ylabel("5-Fold CV Accuracy", fontsize=11)
        ax.set_title("Cross-Validation Accuracy Distribution", fontsize=13, fontweight="bold")
    _save(fig, "cv_boxplot.png")


# ── 10. Rank leaderboard table ────────────────────────────────────────────────
def plot_leaderboard(df: pd.DataFrame):
    cols = ["Rank", "Model", "Accuracy", "F1_Score", "ROC_AUC", "CV_Accuracy",
            "Train_Time_s", "Model_Size_KB"]
    sub = df[cols].head(14)
    with plt.rc_context({"figure.facecolor": "white"}):
        fig, ax = plt.subplots(figsize=(16, 6))
        ax.axis("off")
        tbl = ax.table(
            cellText=sub.values,
            colLabels=sub.columns,
            cellLoc="center",
            loc="center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1.2, 1.6)
        # Header style
        for j in range(len(cols)):
            tbl[0, j].set_facecolor("#6366f1")
            tbl[0, j].set_text_props(color="white", fontweight="bold")
        # Rank 1 highlight
        for j in range(len(cols)):
            tbl[1, j].set_facecolor("#fef08a")
        ax.set_title("Model Leaderboard", fontsize=14, fontweight="bold", pad=20)
    _save(fig, "model_leaderboard.png")


# ── Main ───────────────────────────────────────────────────────────────────────
def evaluate_all():
    print("\n" + "=" * 60)
    print("MULTI-MODEL EVALUATION")
    print("=" * 60)

    csv_path = MODELS_DIR / "model_comparison.csv"
    if not csv_path.exists():
        print("model_comparison.csv not found. Run multi_train.py first.")
        return

    df = pd.read_csv(csv_path)

    dataset = load_dataset()
    X, y, feature_names = preprocess(dataset, verbose=False)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

    # Load all saved models (ranked order)
    models_data = {}
    for name in df["Model"]:
        pkl = MODELS_DIR / f"{name}.pkl"
        if pkl.exists():
            saved = joblib.load(pkl)
            models_data[name] = saved["model"]

    print(f"\nLoaded {len(models_data)} models. Generating plots...")

    plot_model_comparison(df)
    plot_radar(df)
    plot_metrics_heatmap(df)
    plot_time_vs_accuracy(df)
    plot_confusion_matrices(models_data, y_test, X_test)
    plot_roc_curves(models_data, X_test, y_test)
    plot_pr_curves(models_data, X_test, y_test)
    plot_feature_importance(models_data, feature_names)
    plot_cv_boxplot(models_data, X, y)
    plot_leaderboard(df)

    # Per-model classification reports
    print("\n-- Classification Reports --")
    for name, model in models_data.items():
        y_pred = model.predict(X_test)
        print(f"\n{name}:")
        print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0))

    print(f"\nAll plots saved to: {PLOTS_DIR}")
    print(f"Best model: {df.iloc[0]['Model']}  (Accuracy={df.iloc[0]['Accuracy']:.4f})")


if __name__ == "__main__":
    evaluate_all()
