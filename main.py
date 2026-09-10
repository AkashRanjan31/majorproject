"""
main.py
-------
Full research pipeline: dataset → train all models → evaluate → explain.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def _banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def main():
    _banner("STEP 1 — Build Dataset")
    from dataset.create_dataset import df  # runs on import
    print(f"Dataset ready: {df.shape}")

    _banner("STEP 2 — Train All 14 Models")
    from src.multi_train import train_all
    df_results = train_all()

    _banner("STEP 3 — Evaluate & Generate Plots")
    from src.multi_evaluate import evaluate_all
    evaluate_all()

    _banner("STEP 4 — Explainability (SHAP)")
    from src.explainability import run_full_explainability
    run_full_explainability()

    _banner("PIPELINE COMPLETE")
    best = df_results.iloc[0]
    print(f"Best Model : {best['Model']}")
    print(f"Accuracy   : {best['Accuracy']:.4f}")
    print(f"F1 Score   : {best['F1_Score']:.4f}")
    print(f"ROC AUC    : {best['ROC_AUC']:.4f}")
    print(f"CV Accuracy: {best['CV_Accuracy']:.4f}")
    print(f"\nPlots saved to: {PROJECT_ROOT / 'plots'}")
    print(f"Models saved to: {PROJECT_ROOT / 'models'}")


if __name__ == "__main__":
    main()
