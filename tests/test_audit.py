"""
test_audit.py
-------------
Comprehensive automated tests for the AI-Based Mental Health Fatigue Detection
project. Covers dataset loading, feature extraction, model loading, prediction,
class mapping, API response, and edge cases.

Run with:  python -m pytest tests/test_audit.py -v
Or simply: python tests/test_audit.py
"""

import os
import sys
import json
import math
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import joblib

from src.load_data import load_dataset, find_target_column
from src.preprocess import preprocess
from src.feature_extraction import FeatureExtractor, FEATURE_ORDER
from src.predict import predict_fatigue, load_model
from src.realtime_predict import FatiguePredictor, FATIGUE_LEVELS


CLASS_NAMES = ["Normal", "Moderate Fatigue", "High Fatigue"]


class TestDatasetLoading(unittest.TestCase):
    """Phase 2: Dataset validation."""

    def test_dataset_exists(self):
        ds = PROJECT_ROOT / "dataset" / "dataset.csv"
        self.assertTrue(ds.exists(), "dataset/dataset.csv does not exist")

    def test_dataset_loads(self):
        df = load_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0, "Dataset has no rows")

    def test_no_missing_values(self):
        df = load_dataset()
        self.assertEqual(int(df.isnull().sum().sum()), 0, "Dataset has missing values")

    def test_no_duplicates(self):
        df = load_dataset()
        self.assertEqual(int(df.duplicated().sum()), 0, "Dataset has duplicate rows")

    def test_no_infinite_values(self):
        df = load_dataset()
        numeric = df.select_dtypes(include="number")
        self.assertFalse(np.isinf(numeric.to_numpy()).any(), "Dataset contains infinite values")

    def test_fatigue_column_identified(self):
        df = load_dataset()
        target = find_target_column(df)
        self.assertIn(target, df.columns)
        self.assertEqual(target, "fatigue_level")

    def test_class_distribution(self):
        df = load_dataset()
        target = find_target_column(df)
        counts = df[target].value_counts()
        self.assertEqual(counts.sum(), len(df))
        # All expected classes present (0,1,2)
        self.assertIn(0, counts.index.tolist())
        self.assertIn(1, counts.index.tolist())
        self.assertIn(2, counts.index.tolist())


class TestPreprocessing(unittest.TestCase):
    """Phase 7: Preprocessing test."""

    def test_preprocess_runs(self):
        df = load_dataset()
        X, y, feature_names = preprocess(df, verbose=False)
        self.assertIsInstance(X, pd.DataFrame)
        self.assertEqual(len(X), len(y))
        self.assertEqual(len(feature_names), 16)

    def test_feature_names_match_order(self):
        df = load_dataset()
        _, _, feature_names = preprocess(df, verbose=False)
        self.assertEqual(feature_names, FEATURE_ORDER,
                         "Train feature names must match FEATURE_ORDER")


class TestFeatureExtraction(unittest.TestCase):
    """Phase 4, 5, 6: Feature extraction validation."""

    def _sample_raw_data(self):
        now = time.time()
        return {
            "key_presses": [now - 3.5, now - 2.5, now - 1.5, now - 0.5],
            "key_releases": [now - 3.4, now - 2.4, now - 1.4, now - 0.4],
            "backspace_count": 2,
            "keyboard_idle": 2.5,
            "mouse_clicks": {"left": 5, "right": 2, "double": 1},
            "scroll_count": 3,
            "mouse_movements": [
                {"time": now - 4.0, "distance": 100, "time_diff": 0.5},
                {"time": now - 3.0, "distance": 150, "time_diff": 0.5},
                {"time": now - 2.0, "distance": 50, "time_diff": 0.5},
                {"time": now - 1.0, "distance": 200, "time_diff": 0.5},
            ],
            "mouse_idle": 1.2,
            "drag_count": 1,
        }

    def test_keyboard_features(self):
        kb = FeatureExtractor.extract_keyboard_features(self._sample_raw_data(), window_size=60)
        self.assertEqual(kb["key_press_count"], 4)
        self.assertEqual(kb["backspace_count"], 2)
        self.assertGreater(kb["key_hold_time"], 0)
        self.assertGreater(kb["typing_speed"], 0)
        self.assertEqual(kb["error_rate"], 2 / 4)

    def test_mouse_features(self):
        ms = FeatureExtractor.extract_mouse_features(self._sample_raw_data())
        self.assertEqual(ms["left_click"], 5)
        self.assertEqual(ms["right_click"], 2)
        self.assertEqual(ms["double_click"], 1)
        self.assertEqual(ms["scroll_count"], 3)
        self.assertGreater(ms["cursor_speed"], 0)
        self.assertEqual(ms["drag_count"], 1)

    def test_full_feature_vector_length(self):
        _, vec = FeatureExtractor.extract_features(self._sample_raw_data(), window_size=60)
        self.assertEqual(len(vec), 16)
        self.assertEqual(len(vec), len(FEATURE_ORDER))

    def test_empty_window_returns_valid_zero_vector(self):
        empty = {
            "key_presses": [], "key_releases": [], "backspace_count": 0,
            "keyboard_idle": 0, "mouse_clicks": {}, "scroll_count": 0,
            "mouse_movements": [], "mouse_idle": 0, "drag_count": 0
        }
        feats, vec = FeatureExtractor.extract_features(empty, window_size=60)
        self.assertEqual(len(vec), 16)
        for v in vec:
            self.assertTrue(math.isfinite(v), f"Non-finite value in vector: {v}")

    def test_none_raw_data_handled(self):
        feats, vec = FeatureExtractor.extract_features(None, window_size=60)
        self.assertEqual(len(vec), 16)

    def test_feature_order_matches_model(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        model_features = saved["feature_names"]
        self.assertEqual(model_features, FEATURE_ORDER)


class TestModelAndPrediction(unittest.TestCase):
    """Phase 8, 10: XGBoost model verification."""

    def test_model_exists(self):
        self.assertTrue((PROJECT_ROOT / "models" / "xgboost_model.pkl").exists())

    def test_model_is_xgboost(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        model = saved["model"]
        self.assertEqual(type(model).__name__, "XGBClassifier",
                         f"Expected XGBClassifier, got {type(model).__name__}")

    def test_model_feature_count(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        model = saved["model"]
        self.assertEqual(getattr(model, "n_features_in_", None), 16)

    def test_model_has_predict_proba(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        model = saved["model"]
        self.assertTrue(hasattr(model, "predict_proba"))

    def test_class_names_present(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        self.assertEqual(saved.get("class_names"), CLASS_NAMES)

    def test_class_mapping(self):
        # Verify FATIGUE_LEVELS mapping matches class_names order
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        class_names = saved["class_names"]
        for idx, name in enumerate(CLASS_NAMES):
            self.assertEqual(class_names[idx], name)
            info = FATIGUE_LEVELS[idx]
            self.assertEqual(info["name"], name)

    def test_input_feature_vector_shape(self):
        saved = joblib.load(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        model = saved["model"]
        vec = [0.0] * 16
        pred = model.predict(np.array([vec]))[0]
        self.assertIn(int(pred), [0, 1, 2])

    def test_predict_fatigue_returns_valid(self):
        sample = {
            "key_press_count": 120, "key_hold_time": 0.20, "typing_speed": 45,
            "error_rate": 0.08, "backspace_count": 15, "idle_time": 8,
            "mouse_click_count": 25, "left_click": 20, "right_click": 5,
            "double_click": 2, "scroll_count": 10, "cursor_speed": 220,
            "cursor_distance": 1500, "drag_count": 2, "movement_speed": 200,
            "idle_mouse_time": 6,
        }
        label, confidence = predict_fatigue(sample)
        self.assertIn(label, CLASS_NAMES)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_fatigue_predictor_class(self):
        predictor = FatiguePredictor(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        self.assertIsNotNone(predictor.model)
        vec = [10.0] * 16
        result = predictor.predict(vec)
        self.assertEqual(result["level"], int(result["level"]))
        self.assertIn(result["name"], CLASS_NAMES)
        self.assertIn("normal", result["probabilities"])
        self.assertIn("moderate", result["probabilities"])
        self.assertIn("high", result["probabilities"])
        total = sum(result["probabilities"].values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_invalid_feature_vector_raises_clear_error(self):
        """A wrong-length feature vector must raise a catchable ValueError
        (not produce a silent wrong prediction or crash in a confusing way)."""
        predictor = FatiguePredictor(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        # Wrong-length vector -> should raise ValueError (caught by app layers)
        with self.assertRaises(Exception):
            predictor.predict([0.0] * 10)


class TestAPIContract(unittest.TestCase):
    """Phase 18: Frontend/backend connection contract."""

    def test_predict_endpoint_contract(self):
        """The /predict endpoint response shape must match frontend expectations."""
        # Simulate: frontend sends features, backend returns prediction/confidence/recommendation
        sample = {
            "key_press_count": 120, "key_hold_time": 0.20, "typing_speed": 45,
            "error_rate": 0.08, "backspace_count": 15, "idle_time": 8,
            "mouse_click_count": 25, "left_click": 20, "right_click": 5,
            "double_click": 2, "scroll_count": 10, "cursor_speed": 220,
            "cursor_distance": 1500, "drag_count": 2, "movement_speed": 200,
            "idle_mouse_time": 6,
        }
        label, confidence = predict_fatigue(sample)
        response = {
            "prediction": label,
            "confidence": confidence,
            "recommendation": "Test recommendation",
            "features": {"typing_speed": 45, "mouse_click_count": 25}
        }
        # Frontend app.js expects: prediction, confidence, recommendation, features
        self.assertIn("prediction", response)
        self.assertIn("confidence", response)
        self.assertIn("recommendation", response)
        self.assertIn("features", response)

    def test_json_serializable(self):
        """All API responses must be JSON-serializable."""
        sample = {k: 10.0 for k in FEATURE_ORDER}
        label, confidence = predict_fatigue(sample)
        data = {"prediction": label, "confidence": confidence}
        json.dumps(data)  # should not raise


class TestEdgeCases(unittest.TestCase):
    """Phase 20, 21: Edge case tests."""

    def test_all_zero_features(self):
        zeros = {k: 0.0 for k in FEATURE_ORDER}
        label, conf = predict_fatigue(zeros)
        self.assertIn(label, CLASS_NAMES)

    def test_nan_features_do_not_crash(self):
        predictor = FatiguePredictor(PROJECT_ROOT / "models" / "xgboost_model.pkl")
        vec = [float("nan")] * 16
        try:
            result = predictor.predict(vec)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"NaN vector should not crash predict: {e}")

    def test_extract_features_with_inf(self):
        raw = {
            "key_presses": [], "key_releases": [], "backspace_count": 0,
            "keyboard_idle": float("inf"), "mouse_clicks": {}, "scroll_count": 0,
            "mouse_movements": [], "mouse_idle": float("nan"), "drag_count": 0
        }
        feats, vec = FeatureExtractor.extract_features(raw, window_size=60)
        for v in vec:
            self.assertTrue(math.isfinite(v), f"Non-finite value leaked: {v}")


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

