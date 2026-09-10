"""
_evaluate_xgboost.py
--------------------
Full honest evaluation of the XGBoost model on unseen test data.
Run: python _evaluate_xgboost.py
"""

import sys
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score,
    precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

SEP = "=" * 52

# ── STEP 1: Find the XGBoost model ────────────────────────────────────────────
print(SEP)
print("STEP 1 — LOCATING XGBOOST MODEL")
print(SEP)

candidates = [
    PROJECT_ROOT / "models" / "XGBoost.pkl",
    PROJECT_ROOT / "models" / "xgboost_model.pkl",
    PROJECT_ROOT / "models" / "best_model.pkl",
]

xgb_model = None
xgb_path  = None
feature_names_saved = []
class_names_saved   = []

for path in candidates:
    if not path.exists():
        print(f"  NOT FOUND : {path.name}")
        continue
    saved = joblib.load(str(path))
    model = saved["model"] if isinstance(saved, dict) else saved
    algo  = type(model).__name__
    print(f"  FOUND     : {path.name}  →  algorithm = {algo}")
    if "XGB" in algo and xgb_model is None:
        xgb_model = model
        xgb_path  = path
        if isinstance(saved, dict):
            feature_names_saved = saved.get("feature_names", [])
            class_names_saved   = saved.get("class_names", [])
        print(f"  SELECTED  : {path.name}")

if xgb_model is None:
    print("ERROR: No XGBoost model found. Run python src/train_model.py first.")
    sys.exit(1)

print(f"\n  Model file : {xgb_path.name}")
print(f"  Algorithm  : {type(xgb_model).__name__}")
print(f"  Saved feature count : {len(feature_names_saved)}")
print(f"  Saved class names   : {class_names_saved}")

# ── STEP 2: Load dataset ───────────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 2 — LOADING DATASET")
print(SEP)

from src.load_data import load_dataset
from src.preprocess import preprocess

dataset = load_dataset()
print(f"  Dataset file : dataset/dataset.csv")
print(f"  Raw shape    : {dataset.shape}")
print(f"  Columns      : {list(dataset.columns)}")

# ── STEP 3: Data quality check ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 3 — DATA QUALITY CHECK")
print(SEP)

missing = dataset.isnull().sum().sum()
dupes   = dataset.duplicated().sum()
inf_cnt = np.isinf(dataset.select_dtypes(include=[np.number])).sum().sum()

print(f"  Missing values  : {missing}")
print(f"  Duplicate rows  : {dupes}")
print(f"  Infinite values : {inf_cnt}")

target_col = "fatigue_level"
print(f"  Target column   : {target_col}")
print(f"  Class distribution:")
print(dataset[target_col].value_counts().sort_index().to_string())

# Check for synthetic generation
create_ds = PROJECT_ROOT / "dataset" / "create_dataset.py"
is_synthetic = create_ds.exists()
print(f"\n  Dataset type    : {'SYNTHETIC (create_dataset.py found)' if is_synthetic else 'REAL'}")

# ── STEP 4: Preprocess and create proper test split ────────────────────────────
print(f"\n{SEP}")
print("STEP 4 — CREATING PROPER TEST SET (80/20 stratified, random_state=42)")
print(SEP)

X, y, feature_names = preprocess(dataset, verbose=False)

# Use the same split as training (same seed → same test set)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print(f"  Total samples  : {len(X)}")
print(f"  Train samples  : {len(X_train)}")
print(f"  Test samples   : {len(X_test)}")
print(f"  Features used  : {len(feature_names)}")
print(f"  Classes        : {sorted(y.unique().tolist())}")

# Align feature order to what the model was trained on
if feature_names_saved and list(feature_names_saved) != list(feature_names):
    print(f"\n  WARNING: Feature order mismatch — reordering to saved feature list")
    try:
        X_train = X_train[feature_names_saved]
        X_test  = X_test[feature_names_saved]
        feature_names = list(feature_names_saved)
    except KeyError as e:
        print(f"  ERROR: Missing feature {e} — using dataset feature order")

# ── STEP 5 & 6: Predict and calculate accuracy ────────────────────────────────
print(f"\n{SEP}")
print("STEP 5 & 6 — PREDICT AND CALCULATE ACCURACY")
print(SEP)

y_pred_test  = xgb_model.predict(X_test)
y_pred_train = xgb_model.predict(X_train)

correct   = int((y_pred_test == y_test).sum())
incorrect = int((y_pred_test != y_test).sum())
total     = len(y_test)
accuracy  = correct / total * 100

train_acc = accuracy_score(y_train, y_pred_train) * 100
test_acc  = accuracy  # same value, named clearly

print(f"\n  Correct Predictions   : {correct}")
print(f"  Incorrect Predictions : {incorrect}")
print(f"  Total Test Samples    : {total}")
print(f"\n  Accuracy : {accuracy:.4f} / 100")

# ── STEP 7: Additional metrics ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 7 — ADDITIONAL METRICS")
print(SEP)

precision_w  = precision_score(y_test, y_pred_test, average="weighted", zero_division=0) * 100
recall_w     = recall_score(y_test, y_pred_test, average="weighted", zero_division=0) * 100
f1_w         = f1_score(y_test, y_pred_test, average="weighted", zero_division=0) * 100
f1_macro     = f1_score(y_test, y_pred_test, average="macro", zero_division=0) * 100
bal_acc      = balanced_accuracy_score(y_test, y_pred_test) * 100
gen_gap      = train_acc - test_acc

print(f"  Precision (weighted) : {precision_w:.4f}%")
print(f"  Recall (weighted)    : {recall_w:.4f}%")
print(f"  F1 Score (weighted)  : {f1_w:.4f}%")
print(f"  Macro F1             : {f1_macro:.4f}%")
print(f"  Balanced Accuracy    : {bal_acc:.4f}%")
print(f"  Training Accuracy    : {train_acc:.4f}%")
print(f"  Test Accuracy        : {test_acc:.4f}%")
print(f"  Generalization Gap   : {gen_gap:.4f}%")

# ── STEP 8: Confusion matrix ───────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 8 — CONFUSION MATRIX")
print(SEP)

classes = sorted(y.unique().tolist())
if class_names_saved and len(class_names_saved) == len(classes):
    labels = class_names_saved
else:
    labels = [f"Class {c}" for c in classes]

cm = confusion_matrix(y_test, y_pred_test, labels=classes)
print(f"\n  Rows = Actual, Columns = Predicted")
print(f"  Classes: {labels}\n")

header = "  {:>20s}".format("") + "".join(f"  {l[:12]:>12s}" for l in labels)
print(header)
for i, row in enumerate(cm):
    row_str = "  {:>20s}".format(labels[i][:20]) + "".join(f"  {v:>12d}" for v in row)
    print(row_str)

print("\n  Confusion analysis:")
for i in range(len(classes)):
    for j in range(len(classes)):
        if i != j and cm[i][j] > 0:
            print(f"    {cm[i][j]:>4d} samples of '{labels[i]}' predicted as '{labels[j]}'")

# ── STEP 9: Class-wise accuracy ────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 9 — CLASS-WISE PERFORMANCE")
print(SEP)

report = classification_report(
    y_test, y_pred_test,
    labels=classes,
    target_names=labels,
    zero_division=0,
    output_dict=True,
)
for lbl in labels:
    r = report.get(lbl, {})
    print(f"\n  {lbl}")
    print(f"    Precision : {r.get('precision', 0)*100:.2f}%")
    print(f"    Recall    : {r.get('recall',    0)*100:.2f}%")
    print(f"    F1        : {r.get('f1-score',  0)*100:.2f}%")
    print(f"    Support   : {int(r.get('support', 0))}")

# ── STEP 10: Overfitting check ─────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 10 — OVERFITTING CHECK")
print(SEP)

print(f"  Training Accuracy : {train_acc:.4f}%")
print(f"  Test Accuracy     : {test_acc:.4f}%")
print(f"  Generalization Gap: {gen_gap:.4f}%")

if gen_gap > 10:
    overfit_verdict = "YES — gap > 10%"
elif gen_gap > 5:
    overfit_verdict = "POSSIBLE — gap > 5%"
elif train_acc >= 99.9 and test_acc >= 99.9:
    overfit_verdict = "POSSIBLE — both train and test are suspiciously perfect (synthetic data)"
else:
    overfit_verdict = "NO"
print(f"  Overfitting       : {overfit_verdict}")

# ── STEP 11: Data leakage check ────────────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 11 — DATA LEAKAGE CHECK")
print(SEP)

leakage_detected = False

# Check 1: duplicate rows across train/test
train_idx = set(X_train.index)
test_idx  = set(X_test.index)
overlap   = train_idx & test_idx
print(f"  Index overlap (train ∩ test) : {len(overlap)} rows")
if overlap:
    leakage_detected = True
    print("  WARNING: Same rows appear in both train and test!")

# Check 2: feature correlation with target
corr = X.corrwith(y.astype(float)).abs().sort_values(ascending=False)
top5 = corr.head(5)
print(f"\n  Top-5 feature correlations with target:")
for feat, val in top5.items():
    flag = "  ← HIGH CORRELATION" if val > 0.95 else ""
    print(f"    {feat:35s}: {val:.4f}{flag}")
    if val > 0.95:
        leakage_detected = True

# Check 3: synthetic data
if is_synthetic:
    print(f"\n  Synthetic dataset detected — same generator creates train+test")
    print(f"  No participant/session IDs → no participant-wise leakage possible")
    print(f"  BUT: synthetic ranges are deterministic → model learns the generator, not real fatigue")

print(f"\n  Leakage verdict: {'YES — see warnings above' if leakage_detected else 'NO direct leakage detected'}")

# ── STEP 12: Synthetic data warning ───────────────────────────────────────────
print(f"\n{SEP}")
print("STEP 12 — SYNTHETIC DATA WARNING")
print(SEP)

if is_synthetic:
    print("  Dataset Type: SYNTHETIC")
    print()
    print("  The measured accuracy represents performance on the synthetic")
    print("  dataset and should NOT be interpreted as real-world mental")
    print("  fatigue detection accuracy.")
    print()
    if test_acc >= 99.9:
        print("  XGBoost achieved 100/100 accuracy on the current synthetic")
        print("  test set. DO NOT claim '100% real-world accuracy'.")
    else:
        print(f"  XGBoost achieved {test_acc:.2f}/100 on the synthetic test set.")

# ── STEP 13 & 14: Real-time system and feature match check ────────────────────
print(f"\n{SEP}")
print("STEP 13 & 14 — REAL-TIME SYSTEM & FEATURE MATCH")
print(SEP)

from src.feature_extraction import FEATURE_ORDER

rt_features  = list(FEATURE_ORDER)
train_feats  = list(feature_names)

print(f"  Training feature count  : {len(train_feats)}")
print(f"  Real-time feature count : {len(rt_features)}")

# Check which training features are present in real-time extraction
missing_in_rt   = [f for f in train_feats if f not in rt_features]
extra_in_rt     = [f for f in rt_features if f not in train_feats]
order_match     = (train_feats == rt_features[:len(train_feats)])

print(f"\n  Features in training but NOT in real-time extractor : {missing_in_rt or 'None'}")
print(f"  Features in real-time extractor but NOT in training : {extra_in_rt or 'None'}")
print(f"  Feature order match (first {len(train_feats)})      : {order_match}")

rt_pass = (len(missing_in_rt) == 0)

# Check realtime_predict.py loads XGBoost
rt_pred_path = PROJECT_ROOT / "src" / "realtime_predict.py"
rt_pred_text = rt_pred_path.read_text() if rt_pred_path.exists() else ""
uses_best_model = "best_model.pkl" in rt_pred_text
uses_xgb_model  = "xgboost_model.pkl" in rt_pred_text or "XGBoost.pkl" in rt_pred_text

# Determine what best_model.pkl actually contains
best_path = PROJECT_ROOT / "models" / "best_model.pkl"
best_algo = "unknown"
if best_path.exists():
    bm = joblib.load(str(best_path))
    bm_model = bm["model"] if isinstance(bm, dict) else bm
    best_algo = type(bm_model).__name__

print(f"\n  realtime_predict.py loads : {'best_model.pkl' if uses_best_model else 'xgboost_model.pkl'}")
print(f"  best_model.pkl algorithm  : {best_algo}")
xgb_in_rt = "XGB" in best_algo or uses_xgb_model
print(f"  XGBoost used in real-time : {xgb_in_rt}")

# Check for hardcoded/mock predictions
mock_flags = ["random.choice", "hardcoded", "mock", "demo_pred", "fake"]
mock_found = [f for f in mock_flags if f in rt_pred_text.lower()]
print(f"  Mock/hardcoded predictions: {mock_found or 'None found'}")

rt_xgb_pass = xgb_in_rt and not mock_found

# ── FINAL REPORT ───────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("FINAL REPORT")
print(SEP)

print(f"""
MODEL:
  XGBoost  ({type(xgb_model).__name__})
  File: {xgb_path.name}

DATASET:
  dataset/dataset.csv

DATASET TYPE:
  {'SYNTHETIC' if is_synthetic else 'REAL'}

TOTAL SAMPLES:
  {len(X)}

TEST SAMPLES:
  {total}

CORRECT PREDICTIONS:
  {correct}

INCORRECT PREDICTIONS:
  {incorrect}

{SEP}
FINAL ACCURACY
{SEP}

  {accuracy:.4f} / 100

{SEP}

PRECISION (weighted):
  {precision_w:.4f}%

RECALL (weighted):
  {recall_w:.4f}%

F1 SCORE (weighted):
  {f1_w:.4f}%

MACRO F1:
  {f1_macro:.4f}%

BALANCED ACCURACY:
  {bal_acc:.4f}%

TRAINING ACCURACY:
  {train_acc:.4f}%

TEST ACCURACY:
  {test_acc:.4f}%

GENERALIZATION GAP:
  {gen_gap:.4f}%

DATA LEAKAGE:
  {'YES' if leakage_detected else 'NO'}

OVERFITTING:
  {overfit_verdict}

REAL-TIME FEATURE MATCH:
  {'PASS' if rt_pass else 'FAIL — ' + str(missing_in_rt)}

REAL-TIME XGBOOST:
  {'PASS' if rt_xgb_pass else 'FAIL — best_model.pkl contains ' + best_algo}
""")

print(SEP)
print("FINAL VERDICT")
print(SEP)
print(f"""
1. ACTUAL XGBOOST ACCURACY OUT OF 100:
   {accuracy:.4f} / 100

2. IS THIS ACCURACY TRUSTWORTHY?
   {'NO — synthetic data, model learns the generator not real fatigue' if is_synthetic else 'YES — real data used'}

3. IS THERE DATA LEAKAGE?
   {'YES — see Step 11' if leakage_detected else 'NO direct index/feature leakage. However, synthetic data means train and test come from the same generator with the same statistical distributions — this inflates accuracy.'}

4. IS THERE OVERFITTING?
   {overfit_verdict}

5. IS THE DATASET SYNTHETIC OR REAL?
   {'SYNTHETIC — generated by dataset/create_dataset.py with deterministic class ranges' if is_synthetic else 'REAL'}

6. IS THE MODEL SUITABLE FOR REAL-TIME PREDICTION?
   {'TECHNICALLY YES — pipeline is wired correctly. BUT accuracy on real users is unknown.' if rt_xgb_pass and rt_pass else 'PARTIALLY — feature or model mismatch detected, see Steps 13-14'}

7. WHAT TO IMPROVE BEFORE USING IN A RESEARCH PAPER:
   a) Collect REAL keyboard/mouse data from actual users with verified fatigue labels
   b) Use participant-wise train/test split (no user appears in both sets)
   c) Increase NOISE or use overlapping class ranges to get realistic accuracy
   d) Report accuracy on real data, not synthetic
   e) Add cross-validation with participant-level folds (LeaveOneGroupOut)
   f) Current synthetic accuracy ({accuracy:.2f}/100) must be labelled
      "synthetic benchmark" — NOT "real-world accuracy"
""")
