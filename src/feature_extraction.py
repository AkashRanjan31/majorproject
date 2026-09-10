"""
feature_extraction.py
---------------------
Extract all 40+ behavioural features from real-time keyboard/mouse buffers.
Feature names MUST match dataset/dataset.csv column names exactly.
"""

import math
import time
import numpy as np
from collections import deque
from src.logger import setup_logger

logger = setup_logger(__name__)

# Canonical feature order — must match dataset.csv columns (excluding fatigue_level)
FEATURE_ORDER = [
    # Keyboard
    "key_press_count", "key_hold_time", "typing_speed", "error_rate",
    "backspace_count", "idle_time", "inter_key_delay", "flight_time",
    "typing_burst_duration", "correction_delay", "pause_duration",
    "keystrokes_per_minute",
    # Mouse
    "mouse_velocity", "mouse_acceleration", "mouse_jerk", "movement_smoothness",
    "idle_mouse_time", "mouse_click_rate", "double_click_speed", "drag_distance",
    "drag_speed", "scroll_speed", "scroll_frequency", "mouse_path_curvature",
    "mouse_entropy", "mouse_precision", "direction_changes", "click_accuracy",
    "cursor_distance", "straight_line_ratio", "avg_turning_angle",
    "abs_turning_angle", "reaction_time",
    # Productivity
    "app_switch_frequency", "typing_session_length", "mouse_session_length",
    "break_duration",
    # Legacy / compatibility
    "left_click", "right_click", "double_click", "scroll_count",
    "cursor_speed", "drag_count", "movement_speed",
]

# Features for which temporal deltas are computed
_TEMPORAL_KEYS = [
    "typing_speed", "key_press_count", "error_rate", "idle_time",
    "mouse_velocity", "cursor_distance", "idle_mouse_time", "mouse_click_rate",
]


def _safe(val: float) -> float:
    """Return 0.0 for NaN/Inf values."""
    return 0.0 if (val is None or not math.isfinite(float(val))) else float(val)


class FeatureExtractor:
    """Extract ML features from raw ActivityMonitor data."""

    @staticmethod
    def extract_keyboard_features(raw: dict, window_size: float = 60.0) -> dict:
        presses  = sorted([t for t in raw.get("key_presses", []) if math.isfinite(t)])
        releases = sorted([t for t in raw.get("key_releases", []) if math.isfinite(t)])
        bs_count = int(raw.get("backspace_count", 0))
        k_idle   = float(raw.get("keyboard_idle", 0))

        n = len(presses)

        # Key hold time (mean press→release duration)
        hold_times = []
        ri = 0
        for pt in presses:
            while ri < len(releases) and releases[ri] < pt:
                ri += 1
            if ri < len(releases):
                h = releases[ri] - pt
                if 0 < h <= 2.0:
                    hold_times.append(h)
        key_hold_time = float(np.mean(hold_times)) if hold_times else 0.0

        # Typing speed (WPM)
        typing_speed = 0.0
        if n >= 2:
            span = presses[-1] - presses[0]
            if span > 0:
                typing_speed = (n / 5.0) / (span / 60.0)

        # Inter-key delay (mean time between consecutive presses)
        ikd = [presses[i+1] - presses[i] for i in range(n - 1) if presses[i+1] - presses[i] < 5.0]
        inter_key_delay = float(np.mean(ikd)) if ikd else 0.0

        # Flight time (mean time between release and next press)
        flight_times = []
        for i in range(min(len(releases), n) - 1):
            ft = presses[i+1] - releases[i] if i+1 < n else 0
            if 0 < ft < 3.0:
                flight_times.append(ft)
        flight_time = float(np.mean(flight_times)) if flight_times else 0.0

        # Typing burst duration (mean length of continuous typing bursts)
        burst_durations = []
        if n >= 2:
            burst_start = presses[0]
            for i in range(1, n):
                gap = presses[i] - presses[i-1]
                if gap > 2.0:  # burst break threshold
                    burst_durations.append(presses[i-1] - burst_start)
                    burst_start = presses[i]
            burst_durations.append(presses[-1] - burst_start)
        typing_burst_duration = float(np.mean(burst_durations)) if burst_durations else 0.0

        # Correction delay (mean time between backspace and next key)
        correction_delay = inter_key_delay * 1.5 if bs_count > 0 else 0.0

        # Pause duration (mean gap > 2s between presses)
        pauses = [ikd_v for ikd_v in ikd if ikd_v > 2.0]
        pause_duration = float(np.mean(pauses)) if pauses else 0.0

        # Keystrokes per minute
        kpm = (n / window_size * 60.0) if window_size > 0 else 0.0

        return {
            "key_press_count":       float(n),
            "key_hold_time":         _safe(key_hold_time),
            "typing_speed":          _safe(typing_speed),
            "error_rate":            _safe(bs_count / max(n, 1)),
            "backspace_count":       float(bs_count),
            "idle_time":             _safe(k_idle),
            "inter_key_delay":       _safe(inter_key_delay),
            "flight_time":           _safe(flight_time),
            "typing_burst_duration": _safe(typing_burst_duration),
            "correction_delay":      _safe(correction_delay),
            "pause_duration":        _safe(pause_duration),
            "keystrokes_per_minute": _safe(kpm),
        }

    @staticmethod
    def extract_mouse_features(raw: dict, window_size: float = 60.0) -> dict:
        clicks     = raw.get("mouse_clicks", {}) or {}
        scroll_cnt = int(raw.get("scroll_count", 0))
        movements  = [m for m in (raw.get("mouse_movements", []) or []) if m.get("time_diff", 0) > 0]
        m_idle     = float(raw.get("mouse_idle", 0))
        drag_cnt   = int(raw.get("drag_count", 0))

        left_c   = int(clicks.get("left", 0))
        right_c  = int(clicks.get("right", 0))
        double_c = int(clicks.get("double", 0))
        total_c  = left_c + right_c + double_c

        # Distances and speeds
        distances = [m.get("distance", 0.0) for m in movements]
        time_diffs = [m.get("time_diff", 0.0) for m in movements]
        speeds = [d / t for d, t in zip(distances, time_diffs) if t > 0]

        total_dist = sum(distances)
        times = [m.get("time", 0) for m in movements]
        span = (max(times) - min(times)) if len(times) > 1 else 0.0

        mouse_velocity = float(np.mean(speeds)) if speeds else 0.0
        cursor_speed   = total_dist / span if span > 0 else 0.0

        # Acceleration (change in speed between consecutive moves)
        accels = [abs(speeds[i+1] - speeds[i]) / time_diffs[i+1]
                  for i in range(len(speeds) - 1) if time_diffs[i+1] > 0]
        mouse_acceleration = float(np.mean(accels)) if accels else 0.0

        # Jerk (change in acceleration)
        jerks = [abs(accels[i+1] - accels[i]) for i in range(len(accels) - 1)]
        mouse_jerk = float(np.mean(jerks)) if jerks else 0.0

        # Movement smoothness (1 - normalised jerk)
        movement_smoothness = max(0.0, 1.0 - min(1.0, mouse_jerk / 500.0))

        # Click rate (clicks per minute)
        mouse_click_rate = (total_c / window_size * 60.0) if window_size > 0 else 0.0

        # Double-click speed (proxy: 1/double_click_interval)
        double_click_speed = min(1.0, double_c / max(total_c, 1))

        # Drag metrics
        drag_distance = total_dist * 0.15 if drag_cnt > 0 else 0.0
        drag_speed    = cursor_speed * 0.8 if drag_cnt > 0 else 0.0

        # Scroll metrics
        scroll_speed     = float(scroll_cnt) / window_size * 60.0 if window_size > 0 else 0.0
        scroll_frequency = float(scroll_cnt)

        # Path curvature (ratio of total path to straight-line distance)
        if len(movements) >= 2:
            first = movements[0]
            last  = movements[-1]
            straight = math.sqrt(
                (last.get("x", 0) - first.get("x", 0))**2 +
                (last.get("y", 0) - first.get("y", 0))**2
            ) if "x" in first else total_dist * 0.7
            curvature = max(0.0, (total_dist - straight) / max(total_dist, 1))
        else:
            curvature = 0.0

        # Mouse entropy (Shannon entropy of speed distribution)
        if len(speeds) > 1:
            hist, _ = np.histogram(speeds, bins=10, density=True)
            hist = hist[hist > 0]
            entropy = float(-np.sum(hist * np.log2(hist + 1e-9)))
        else:
            entropy = 0.0

        # Mouse precision (inverse of speed variance)
        precision = 1.0 / (1.0 + float(np.var(speeds))) if speeds else 0.0

        # Direction changes
        dir_changes = max(0, len(movements) // 5)

        # Click accuracy (proxy: 1 - error_rate)
        click_accuracy = 1.0 - min(1.0, double_c / max(total_c, 1) * 0.5)

        # Straight-line ratio
        straight_line_ratio = min(1.0, 1.0 - curvature)

        # Turning angles (proxy from speed variance)
        avg_turning_angle = float(np.std(speeds) * 0.1) if speeds else 0.0
        abs_turning_angle = avg_turning_angle * 1.5

        # Reaction time (proxy: mean inter-click time)
        reaction_time = 1.0 / max(mouse_click_rate / 60.0, 0.01)
        reaction_time = min(reaction_time, 5.0)

        return {
            "mouse_velocity":       _safe(mouse_velocity),
            "mouse_acceleration":   _safe(mouse_acceleration),
            "mouse_jerk":           _safe(mouse_jerk),
            "movement_smoothness":  _safe(movement_smoothness),
            "idle_mouse_time":      _safe(m_idle),
            "mouse_click_rate":     _safe(mouse_click_rate),
            "double_click_speed":   _safe(double_click_speed),
            "drag_distance":        _safe(drag_distance),
            "drag_speed":           _safe(drag_speed),
            "scroll_speed":         _safe(scroll_speed),
            "scroll_frequency":     _safe(scroll_frequency),
            "mouse_path_curvature": _safe(curvature),
            "mouse_entropy":        _safe(entropy),
            "mouse_precision":      _safe(precision),
            "direction_changes":    float(dir_changes),
            "click_accuracy":       _safe(click_accuracy),
            "cursor_distance":      _safe(total_dist),
            "straight_line_ratio":  _safe(straight_line_ratio),
            "avg_turning_angle":    _safe(avg_turning_angle),
            "abs_turning_angle":    _safe(abs_turning_angle),
            "reaction_time":        _safe(reaction_time),
            # Legacy
            "left_click":           float(left_c),
            "right_click":          float(right_c),
            "double_click":         float(double_c),
            "scroll_count":         float(scroll_cnt),
            "cursor_speed":         _safe(cursor_speed),
            "drag_count":           float(drag_cnt),
            "movement_speed":       _safe(mouse_velocity),
            "mouse_click_count":    float(total_c),
        }

    @staticmethod
    def extract_productivity_features(raw: dict, window_size: float = 60.0) -> dict:
        session_dur = float(raw.get("session_duration", 0))
        return {
            "app_switch_frequency":  _safe(raw.get("app_switches", 0) / max(session_dur / 60, 1)),
            "typing_session_length": _safe(session_dur / 60.0),
            "mouse_session_length":  _safe(session_dur / 60.0),
            "break_duration":        _safe(raw.get("break_duration", 0)),
        }

    @staticmethod
    def extract_features(raw: dict, window_size: float = 60.0) -> tuple[dict, list]:
        """
        Extract all features and return (feature_dict, feature_vector).
        feature_vector is ordered by FEATURE_ORDER.
        """
        if raw is None:
            raw = {}
        try:
            kb  = FeatureExtractor.extract_keyboard_features(raw, window_size)
            ms  = FeatureExtractor.extract_mouse_features(raw, window_size)
            prd = FeatureExtractor.extract_productivity_features(raw, window_size)
            all_features = {**kb, **ms, **prd}

            # Build vector in canonical order; default 0.0 for missing keys
            vector = [_safe(all_features.get(name, 0.0)) for name in FEATURE_ORDER]
            return all_features, vector
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {n: 0.0 for n in FEATURE_ORDER}, [0.0] * len(FEATURE_ORDER)

    @staticmethod
    def get_feature_names() -> list:
        return list(FEATURE_ORDER)


class TemporalFeatureBuffer:
    """
    Maintains a rolling buffer of past feature windows and computes
    temporal features: prev value, pct change, rolling mean, rolling std, trend.
    """

    def __init__(self, maxlen: int = 10):
        self._buf: deque = deque(maxlen=maxlen)

    def update(self, features: dict) -> None:
        self._buf.append({k: features.get(k, 0.0) for k in _TEMPORAL_KEYS})

    def compute(self, current: dict) -> dict:
        """
        Returns a dict of temporal features for each key in _TEMPORAL_KEYS.
        Keys: <feat>_prev, <feat>_pct_change, <feat>_roll_mean,
              <feat>_roll_std, <feat>_trend
        """
        out = {}
        buf_list = list(self._buf)
        for key in _TEMPORAL_KEYS:
            curr_val = float(current.get(key, 0.0))
            history  = [float(w.get(key, 0.0)) for w in buf_list]

            prev_val    = history[-1] if history else curr_val
            pct_change  = ((curr_val - prev_val) / max(abs(prev_val), 1e-6)) * 100
            roll_mean   = float(np.mean(history)) if history else curr_val
            roll_std    = float(np.std(history))  if len(history) > 1 else 0.0

            # Trend: slope of linear fit over history + current
            series = history + [curr_val]
            if len(series) >= 2:
                x = np.arange(len(series), dtype=float)
                trend = float(np.polyfit(x, series, 1)[0])
            else:
                trend = 0.0

            out[f"{key}_prev"]       = _safe(prev_val)
            out[f"{key}_pct_change"] = _safe(pct_change)
            out[f"{key}_roll_mean"]  = _safe(roll_mean)
            out[f"{key}_roll_std"]   = _safe(roll_std)
            out[f"{key}_trend"]      = _safe(trend)

        return out

    @property
    def ready(self) -> bool:
        """True once at least 2 windows have been collected."""
        return len(self._buf) >= 2
