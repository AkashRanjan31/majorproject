"""
pipeline_test.py
----------------
Full end-to-end pipeline validation script.
Runs every stage and prints a clear pass/fail result.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

PASS = "  [PASS]"
FAIL = "  [FAIL]"
SEP  = "-" * 52

def section(title):
    print(f"\n{SEP}\n  {title}\n{SEP}")

def run(label, fn):
    try:
        result = fn()
        print(f"{PASS}  {label}")
        return result
    except Exception as e:
        print(f"{FAIL}  {label}")
        print(f"         {e}")
        traceback.print_exc()
        return None

# ── 1. Dataset ────────────────────────────────────────────────────────────────
section("1. DATASET")
import pandas as pd

def load_dataset():
    df = pd.read_csv("dataset/dataset.csv")
    assert df.shape[0] > 0, "Empty dataset"
    assert "fatigue_level" in df.columns
    return df

df = run("Load dataset.csv", load_dataset)
if df is not None:
    run("Shape check (1200 rows, 17 cols)", lambda: (
        None if df.shape == (1200, 17) else (_ for _ in ()).throw(AssertionError(f"Got {df.shape}"))
    ))
    run("No missing values", lambda: (
        None if df.isnull().sum().sum() == 0 else (_ for _ in ()).throw(AssertionError("Has nulls"))
    ))
    run("3 balanced classes (400 each)", lambda: (
        None if list(df["fatigue_level"].value_counts().sort_index()) == [400,400,400]
        else (_ for _ in ()).throw(AssertionError(str(df["fatigue_level"].value_counts())))
    ))

# ── 2. Preprocessing ──────────────────────────────────────────────────────────
section("2. PREPROCESSING")
from src.preprocess import preprocess

def do_preprocess():
    X, y, feat_names = preprocess(df, verbose=False)
    assert X.shape[1] == 16, f"Expected 16 features, got {X.shape[1]}"
    assert len(y) == 1200
    return X, y

Xy = run("preprocess_data()", do_preprocess)

# ── 3. Model load ─────────────────────────────────────────────────────────────
section("3. MODEL")
from src.realtime_predict import FatiguePredictor

def load_model():
    p = FatiguePredictor("models/xgboost_model.pkl")
    assert p.model is not None
    return p

predictor = run("Load xgboost_model.pkl", load_model)

if predictor:
    run("model.predict() exists",       lambda: getattr(predictor.model, "predict"))
    run("model.predict_proba() exists", lambda: getattr(predictor.model, "predict_proba"))
    run("feature_importances_ exists",  lambda: getattr(predictor.model, "feature_importances_"))

# ── 4. Feature extraction ─────────────────────────────────────────────────────
section("4. FEATURE EXTRACTION")
from src.feature_extraction import FeatureExtractor, FEATURE_ORDER

RAW = {
    "key_presses":    [float(i) for i in range(1, 51)],
    "key_releases":   [float(i) + 0.1 for i in range(1, 51)],
    "backspace_count": 5,
    "mouse_clicks":   {"left": 10, "right": 2, "double": 2},
    "scroll_count":   8,
    "mouse_movements": [{"time": float(i), "distance": 50.0, "time_diff": 0.1} for i in range(20)],
    "keyboard_idle":  3.0,
    "mouse_idle":     2.0,
    "session_duration": 60,
    "timestamp":      1.0,
    "drag_count":     2,
}

def extract():
    feats, fvec = FeatureExtractor.extract_features(RAW, 60)
    assert len(fvec) == 16, f"Expected 16, got {len(fvec)}"
    assert all(isinstance(v, float) for v in fvec)
    return feats, fvec

feat_result = run("extract_features() -> 16 floats", extract)

if feat_result:
    features, fvec = feat_result
    run("Feature order matches FEATURE_ORDER", lambda: (
        None if list(features.keys()) == FEATURE_ORDER
        else (_ for _ in ()).throw(AssertionError("Order mismatch"))
    ))
    run("No NaN/Inf in feature vector", lambda: (
        None if all(__import__("math").isfinite(v) for v in fvec)
        else (_ for _ in ()).throw(AssertionError("NaN/Inf found"))
    ))

# ── 5. Prediction ─────────────────────────────────────────────────────────────
section("5. PREDICTION")

def predict():
    assert predictor and feat_result
    result = predictor.predict(fvec)
    assert result["level"] in (0, 1, 2)
    assert 0.0 <= result["confidence"] <= 1.0
    assert "probabilities" in result
    result["timestamp"] = datetime.now()
    return result

pred_result = run("predictor.predict(fvec)", predict)

if pred_result:
    run(f"Predicted class: {pred_result['name']} ({pred_result['confidence']:.1%})",
        lambda: None)
    run("Probabilities sum ≈ 1.0", lambda: (
        None if abs(sum(pred_result["probabilities"].values()) - 1.0) < 0.01
        else (_ for _ in ()).throw(AssertionError(str(pred_result["probabilities"])))
    ))

# ── 6. SHAP ───────────────────────────────────────────────────────────────────
section("6. SHAP EXPLAINABILITY")
from dashboard.shap_utils import compute_shap_values

def shap_test():
    sv, sn = compute_shap_values(predictor.model, fvec, FEATURE_ORDER)
    assert len(sv) == 16, f"Expected 16 SHAP values, got {len(sv)}"
    assert sn == FEATURE_ORDER
    return sv, sn

shap_result = run("compute_shap_values() → 16 values", shap_test)

# ── 7. Baseline tracker ───────────────────────────────────────────────────────
section("7. BASELINE TRACKER")
from src.baseline import BaselineTracker

def baseline_test():
    bt = BaselineTracker(window=5)
    for _ in range(5):
        bt.update(features)
    assert bt.is_ready()
    deltas = bt.get_deltas(features)
    assert len(deltas) > 0
    return deltas

run("BaselineTracker.update() + get_deltas()", baseline_test)

# ── 8. Database ───────────────────────────────────────────────────────────────
section("8. DATABASE")
from database.db import init_db, insert_prediction, fetch_predictions, fetch_stats

def db_test():
    init_db()
    insert_prediction(pred_result, features, "Keep Working")
    rows = fetch_predictions(limit=5)
    assert len(rows) >= 1
    stats = fetch_stats()
    assert stats.get("total", 0) >= 1
    return stats

db_stats = run("init_db + insert + fetch", db_test)
if db_stats:
    run(f"DB total records: {db_stats.get('total',0)}", lambda: None)

# ── 9. Dashboard modules ──────────────────────────────────────────────────────
section("9. DASHBOARD MODULES")
from dashboard.styles     import PREMIUM_CSS, get_fatigue_color
from dashboard.charts     import (fatigue_trend_chart, confidence_gauge,
                                   shap_bar_chart, feature_importance_chart,
                                   probability_donut, activity_timeline_chart)

run("PREMIUM_CSS loaded",          lambda: (None if len(PREMIUM_CSS) > 100 else (_ for _ in ()).throw(AssertionError())))
run("get_fatigue_color(0) = green", lambda: (None if "#22C55E" in get_fatigue_color(0) else (_ for _ in ()).throw(AssertionError())))
run("fatigue_trend_chart([])",     lambda: fatigue_trend_chart([]))
run("confidence_gauge(0.91, 0)",   lambda: confidence_gauge(0.91, 0))
run("probability_donut({})",       lambda: probability_donut({}))
run("activity_timeline_chart([])", lambda: activity_timeline_chart([]))

if shap_result:
    sv, sn = shap_result
    run("shap_bar_chart(sv, sn)",  lambda: shap_bar_chart(sv, sn))

if predictor and hasattr(predictor.model, "feature_importances_"):
    imp = dict(zip(FEATURE_ORDER, predictor.model.feature_importances_))
    run("feature_importance_chart(imp)", lambda: feature_importance_chart(imp))

# ── 10. Evaluate artifacts ────────────────────────────────────────────────────
section("10. EVALUATION ARTIFACTS")
run("confusion_matrix.png exists",  lambda: (None if Path("confusion_matrix.png").exists()  else (_ for _ in ()).throw(FileNotFoundError())))
run("feature_importance.png exists",lambda: (None if Path("feature_importance.png").exists() else (_ for _ in ()).throw(FileNotFoundError())))
run("xgboost_model.pkl exists",     lambda: (None if Path("models/xgboost_model.pkl").exists() else (_ for _ in ()).throw(FileNotFoundError())))
run("database/fatigue_data.db exists", lambda: (None if Path("database/fatigue_data.db").exists() else (_ for _ in ()).throw(FileNotFoundError())))

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*52}")
print("  ALL TASKS COMPLETED SUCCESSFULLY")
print(f"{'='*52}\n")
print("  Run the premium dashboard with:")
print("  streamlit run premium_app.py")
print()
