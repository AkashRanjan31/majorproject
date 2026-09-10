"""
ensemble_predict.py
-------------------
Soft-voting ensemble: XGBoost + LightGBM + CatBoost.
Falls back gracefully if LightGBM or CatBoost are not installed/trained.
"""

import numpy as np
import joblib
from pathlib import Path
from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)
config = get_config()

MODELS_DIR = Path(config.MODELS_DIR)

# Weights: XGBoost gets highest weight as the primary model
_WEIGHTS = {"XGBoost": 0.50, "LightGBM": 0.30, "CatBoost": 0.20}

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


class EnsemblePredictor:
    """
    Weighted soft-voting ensemble of XGBoost, LightGBM, CatBoost.
    Automatically uses whichever models are available.
    """

    def __init__(self):
        self.models: dict = {}        # name → sklearn-compatible model
        self.feature_names: list = []
        self.class_names: list = config.CLASS_NAMES
        self._load_models()

    def _load_models(self):
        for name in ("XGBoost", "LightGBM", "CatBoost"):
            path = MODELS_DIR / f"{name}.pkl"
            if not path.exists():
                logger.info(f"Ensemble: {name}.pkl not found — skipping")
                continue
            try:
                saved = joblib.load(path)
                model = saved["model"] if isinstance(saved, dict) else saved
                if not self.feature_names and isinstance(saved, dict):
                    self.feature_names = saved.get("feature_names", [])
                    self.class_names   = saved.get("class_names", config.CLASS_NAMES)
                self.models[name] = model
                logger.info(f"Ensemble: loaded {name}")
            except Exception as e:
                logger.warning(f"Ensemble: failed to load {name}: {e}")

        if not self.models:
            raise FileNotFoundError(
                "No ensemble models found. Run python main.py first."
            )
        logger.info(f"Ensemble ready with: {list(self.models.keys())}")

    @property
    def model_names(self) -> list[str]:
        return list(self.models.keys())

    def predict(self, feature_vector: list) -> dict:
        """
        Weighted soft-voting prediction.
        Returns full result dict including per-model probabilities.
        """
        X = np.array(feature_vector, dtype=float).reshape(1, -1)
        n_classes = len(self.class_names)

        # Collect weighted probabilities
        total_weight = 0.0
        ensemble_proba = np.zeros(n_classes)
        per_model: dict[str, list] = {}

        for name, model in self.models.items():
            w = _WEIGHTS.get(name, 0.25)
            try:
                raw = model.predict_proba(X)[0]
                # Pad/trim to n_classes
                proba = np.zeros(n_classes)
                proba[:len(raw)] = raw[:n_classes]
                ensemble_proba += w * proba
                total_weight   += w
                per_model[name] = [round(float(p) * 100, 1) for p in proba]
            except Exception as e:
                logger.warning(f"Ensemble: {name} predict_proba failed: {e}")

        if total_weight == 0:
            raise ValueError("All ensemble models failed to predict.")

        ensemble_proba /= total_weight  # normalise
        pred_class  = int(np.argmax(ensemble_proba))
        confidence  = float(ensemble_proba[pred_class]) * 100
        info        = FATIGUE_LEVELS.get(pred_class, FATIGUE_LEVELS[0])

        return {
            "level":           pred_class,
            "name":            info["name"],
            "emoji":           info["emoji"],
            "color":           info["color"],
            "confidence":      round(confidence, 1),
            "fatigue_score":   round(pred_class / max(n_classes - 1, 1) * 100, 1),
            "probabilities":   {self.class_names[i]: round(float(p) * 100, 1)
                                for i, p in enumerate(ensemble_proba)},
            "per_model_proba": per_model,
            "models_used":     list(self.models.keys()),
            "recommendations": RECOMMENDATIONS.get(pred_class, []),
        }
