"""
realtime_predict.py
-------------------
Real-time fatigue prediction using the best trained model.
Supports 5-class classification and personalised scoring.
"""

import os
import joblib
import numpy as np
from pathlib import Path

from src.logger import setup_logger
from src.config import get_config
from src.personalization import UserBaseline

logger = setup_logger(__name__)
config = get_config()

FATIGUE_LEVELS = {
    0: {"name": "Normal",           "emoji": "🟢", "color": "#22c55e"},
    1: {"name": "Low Fatigue",      "emoji": "🟡", "color": "#84cc16"},
    2: {"name": "Moderate Fatigue", "emoji": "🟠", "color": "#f59e0b"},
    3: {"name": "High Fatigue",     "emoji": "🔴", "color": "#ef4444"},
    4: {"name": "Critical Fatigue", "emoji": "🟣", "color": "#7c3aed"},
}

RECOMMENDATIONS = {
    0: [],
    1: ["💧 Stay hydrated", "🧘 Take a short breathing break"],
    2: ["☕ Take a 5-minute break", "👁️ Do eye exercises", "💧 Drink water"],
    3: ["🚶 Take a 15-minute walk", "🧘 Meditate for 5 minutes", "🤸 Stretch your body"],
    4: ["🛑 Stop working immediately", "😴 Rest for 30+ minutes",
        "🚶 Walk outside", "🧘 Deep breathing exercise"],
}


class FatiguePredictor:
    """Real-time fatigue predictor with personalisation support."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or config.MODEL_PATH
        self.model = None
        self.feature_names: list = []
        self.class_names: list = config.CLASS_NAMES
        self.baseline = UserBaseline.load()
        self._load_model()

    def _load_model(self):
        path = Path(self.model_path)
        if not path.exists():
            # Fallback: try best_model.pkl
            alt = Path(config.MODELS_DIR) / "best_model.pkl"
            if alt.exists():
                path = alt
            else:
                raise FileNotFoundError(
                    f"No model found at {self.model_path}. Run src/multi_train.py first."
                )
        saved = joblib.load(path)
        if isinstance(saved, dict):
            self.model         = saved["model"]
            self.feature_names = saved.get("feature_names", [])
            self.class_names   = saved.get("class_names", config.CLASS_NAMES)
        else:
            self.model = saved
        logger.info(f"Model loaded: {type(self.model).__name__} from {path}")

    def predict(self, feature_vector: list) -> dict:
        """Predict fatigue from a feature vector. Returns full result dict."""
        if self.model is None:
            raise ValueError("Model not loaded.")

        X = np.array(feature_vector).reshape(1, -1)
        pred_class = int(self.model.predict(X)[0])

        proba = np.zeros(len(self.class_names))
        if hasattr(self.model, "predict_proba"):
            raw_proba = self.model.predict_proba(X)[0]
            proba[:len(raw_proba)] = raw_proba
        else:
            proba[pred_class] = 1.0

        confidence = float(proba[pred_class])
        info = FATIGUE_LEVELS.get(pred_class, FATIGUE_LEVELS[0])

        # Personalised score
        self.baseline.update(feature_vector)
        personal_score = self.baseline.personalised_fatigue_score(pred_class, feature_vector)
        deviation = self.baseline.deviation_score(feature_vector)

        return {
            "level":            pred_class,
            "name":             info["name"],
            "emoji":            info["emoji"],
            "color":            info["color"],
            "confidence":       round(confidence * 100, 1),
            "fatigue_score":    personal_score,
            "probabilities":    {self.class_names[i]: round(float(p) * 100, 1)
                                 for i, p in enumerate(proba)},
            "recommendations":  RECOMMENDATIONS.get(pred_class, []),
            "baseline_deviation": deviation,
        }

    def save_baseline(self):
        self.baseline.save()
