"""
personalization.py
------------------
Per-user baseline learning and personalised fatigue scoring.
Compares current behaviour against the user's own normal baseline.
"""

import sys
from pathlib import Path
from collections import deque

import joblib
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)
config = get_config()

BASELINE_PATH = Path(config.BASELINE_PATH)
BASELINE_WINDOW_COUNT = config.BASELINE_WINDOW_COUNT


class UserBaseline:
    """
    Learns a user's normal behavioural baseline from the first N windows.
    Computes a personalised fatigue deviation score.
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.windows: deque = deque(maxlen=BASELINE_WINDOW_COUNT * 3)
        self.baseline_mean: np.ndarray | None = None
        self.baseline_std: np.ndarray | None = None
        self.is_calibrated: bool = False
        self._calibration_count: int = 0

    def update(self, feature_vector: list) -> None:
        """Add a new feature window to the baseline buffer."""
        self.windows.append(np.array(feature_vector, dtype=float))
        self._calibration_count += 1

        if self._calibration_count >= BASELINE_WINDOW_COUNT and not self.is_calibrated:
            self._calibrate()

    def _calibrate(self) -> None:
        """Compute mean and std from collected windows."""
        data = np.array(list(self.windows))
        self.baseline_mean = data.mean(axis=0)
        self.baseline_std  = np.where(data.std(axis=0) < 1e-6, 1.0, data.std(axis=0))
        self.is_calibrated = True
        logger.info(f"Baseline calibrated for user '{self.user_id}' "
                    f"from {len(self.windows)} windows.")

    def deviation_score(self, feature_vector: list) -> dict:
        """
        Compute how much the current window deviates from the baseline.
        Returns a dict with per-feature z-scores and an overall deviation %.
        """
        if not self.is_calibrated:
            return {"calibrated": False, "windows_collected": self._calibration_count,
                    "windows_needed": BASELINE_WINDOW_COUNT}

        current = np.array(feature_vector, dtype=float)
        z_scores = (current - self.baseline_mean) / self.baseline_std
        overall_deviation = float(np.mean(np.abs(z_scores)))
        # Map to 0-100 scale (z=2 → ~100%)
        deviation_pct = min(100.0, overall_deviation / 2.0 * 100.0)

        return {
            "calibrated": True,
            "deviation_pct": round(deviation_pct, 1),
            "z_scores": z_scores.tolist(),
            "top_deviating_features": self._top_deviating(z_scores),
        }

    def _top_deviating(self, z_scores: np.ndarray, top_n: int = 5) -> list:
        """Return the top N most deviating feature indices and their z-scores."""
        idx = np.argsort(np.abs(z_scores))[::-1][:top_n]
        return [{"feature_idx": int(i), "z_score": round(float(z_scores[i]), 3)} for i in idx]

    def personalised_fatigue_score(self, model_score: int, feature_vector: list) -> int:
        """
        Blend the model's class prediction (0-4) with the personal deviation score.
        Returns a 0-100 personalised fatigue score.
        """
        model_pct = model_score / 4.0 * 100.0
        dev = self.deviation_score(feature_vector)
        if not dev.get("calibrated"):
            return int(model_pct)
        dev_pct = dev["deviation_pct"]
        # 70% model, 30% personal deviation
        return int(0.70 * model_pct + 0.30 * dev_pct)

    def save(self, path: Path | None = None) -> None:
        path = path or BASELINE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        logger.info(f"Baseline saved → {path}")

    @staticmethod
    def load(path: Path | None = None) -> "UserBaseline":
        path = path or BASELINE_PATH
        if path.exists():
            obj = joblib.load(path)
            logger.info(f"Baseline loaded from {path}")
            return obj
        logger.info("No saved baseline found. Creating new baseline.")
        return UserBaseline()
