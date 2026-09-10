"""
models/__init__.py
------------------
Model registry — maps model names to builder functions.
LightGBM and CatBoost are optional; they are skipped if not installed.
Install with: pip install lightgbm catboost
"""

from src.models.knn import build as knn
from src.models.decision_tree import build as decision_tree
from src.models.random_forest import build as random_forest
from src.models.xgboost_model import build as xgboost
from src.models.extra_trees import build as extra_trees
from src.models.adaboost import build as adaboost
from src.models.gradient_boosting import build as gradient_boosting
from src.models.hist_gradient_boosting import build as hist_gradient_boosting
from src.models.logistic_regression import build as logistic_regression
from src.models.svm import build as svm
from src.models.naive_bayes import build as naive_bayes
from src.models.mlp import build as mlp

MODEL_REGISTRY: dict = {
    "KNN":                  knn,
    "DecisionTree":         decision_tree,
    "RandomForest":         random_forest,
    "XGBoost":              xgboost,
    "ExtraTrees":           extra_trees,
    "AdaBoost":             adaboost,
    "GradientBoosting":     gradient_boosting,
    "HistGradientBoosting": hist_gradient_boosting,
    "LogisticRegression":   logistic_regression,
    "SVM":                  svm,
    "NaiveBayes":           naive_bayes,
    "MLP":                  mlp,
}

# Optional: LightGBM
try:
    from src.models.lightgbm_model import build as lightgbm
    MODEL_REGISTRY["LightGBM"] = lightgbm
except ImportError:
    print("[INFO] LightGBM not installed — skipping. Install with: pip install lightgbm")

# Optional: CatBoost
try:
    from src.models.catboost_model import build as catboost
    MODEL_REGISTRY["CatBoost"] = catboost
except ImportError:
    print("[INFO] CatBoost not installed — skipping. Install with: pip install catboost")
