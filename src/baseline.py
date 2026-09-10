"""
baseline.py
-----------
Personalized baseline tracker: learns each user's normal behavior
and compares current features against their rolling average.
"""

from collections import deque
import numpy as np
from src.logger import setup_logger

logger = setup_logger(__name__)

_TRACKED = [
    'typing_speed', 'key_press_count', 'cursor_speed',
    'mouse_click_count', 'idle_time', 'idle_mouse_time', 'backspace_count',
]

_MIN_SAMPLES = 3  # minimum windows before baseline is considered valid


class BaselineTracker:
    """Rolling-window personalized baseline for behavioral features."""

    def __init__(self, window: int = 20):
        self._window = window
        self._history: dict[str, deque] = {k: deque(maxlen=window) for k in _TRACKED}

    def update(self, features: dict) -> None:
        """Add a new feature observation to the baseline."""
        for key in _TRACKED:
            val = features.get(key)
            if val is not None and np.isfinite(float(val)):
                self._history[key].append(float(val))

    def get_baseline(self) -> dict:
        """Return mean baseline values (None if not enough data)."""
        if not self.is_ready():
            return {}
        return {k: float(np.mean(self._history[k])) for k in _TRACKED}

    def get_deltas(self, features: dict) -> dict:
        """
        Return per-feature delta vs baseline as percentage change.
        Positive = higher than baseline, negative = lower.
        """
        baseline = self.get_baseline()
        if not baseline:
            return {}
        deltas = {}
        for key in _TRACKED:
            current = features.get(key, 0.0)
            base = baseline.get(key, 0.0)
            if base != 0:
                deltas[key] = (float(current) - base) / abs(base) * 100.0
            else:
                deltas[key] = 0.0
        return deltas

    def is_ready(self) -> bool:
        """True once enough samples have been collected."""
        return all(len(v) >= _MIN_SAMPLES for v in self._history.values())

    @property
    def sample_count(self) -> int:
        return min(len(v) for v in self._history.values())
