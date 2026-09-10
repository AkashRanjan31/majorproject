"""
feature_extraction.py (Production Version)
-------------------------------------------
Extract behavioral features from raw keyboard and mouse data.
Features must match the training dataset format.
Optimized for performance and error handling.
"""

import math
import numpy as np
import logging
from src.logger import setup_logger

logger = setup_logger(__name__)


# Feature order - MUST match training dataset
FEATURE_ORDER = [
    'key_press_count',
    'key_hold_time',
    'typing_speed',
    'error_rate',
    'backspace_count',
    'idle_time',
    'mouse_click_count',
    'left_click',
    'right_click',
    'double_click',
    'scroll_count',
    'cursor_speed',
    'cursor_distance',
    'drag_count',
    'movement_speed',
    'idle_mouse_time'
]


class FeatureExtractor:
    """Extract ML features from raw activity data with optimized algorithms."""

    @staticmethod
    def extract_keyboard_features(raw_data, window_size=60):
        """
        Extract keyboard features.

        Args:
            raw_data: Raw keyboard/mouse data from monitor
            window_size: Time window in seconds

        Returns:
            dict: Keyboard features
        """
        try:
            key_presses = sorted(raw_data.get('key_presses', []))
            key_releases = sorted(raw_data.get('key_releases', []))
            backspace_count = raw_data.get('backspace_count', 0)
            keyboard_idle = raw_data.get('keyboard_idle', 0)

            # Guard against infinite values
            key_presses = [t for t in key_presses if math.isfinite(t)]
            key_releases = [t for t in key_releases if math.isfinite(t)]

            # Key press count
            key_press_count = len(key_presses)

            # Key hold time - pair presses with following releases
            key_hold_time = 0.0
            if key_presses and key_releases:
                hold_durations = []
                release_idx = 0

                for press_time in key_presses:
                    # Find next release after this press
                    while release_idx < len(key_releases) and key_releases[release_idx] < press_time:
                        release_idx += 1

                    if release_idx < len(key_releases):
                        hold = key_releases[release_idx] - press_time
                        if 0 <= hold <= 2.0:  # clip to plausible ranges
                            hold_durations.append(hold)

                if hold_durations:
                    key_hold_time = np.mean(hold_durations)

            # Typing speed (WPM - approximate from key presses)
            # Assuming average word is 5 characters
            typing_speed = 0.0
            if window_size > 0 and key_press_count > 0:
                # Effective active time: from first press to last press (or window)
                if len(key_presses) >= 2:
                    span = key_presses[-1] - key_presses[0]
                    if span > 0:
                        typing_speed = (key_press_count / 5.0) / (span / 60.0)
                    else:
                        typing_speed = 0.0
                else:
                    typing_speed = 0.0

            # Error rate (backspace as proxy for errors)
            error_rate = backspace_count / max(key_press_count, 1)

            return {
                'key_press_count': float(key_press_count),
                'key_hold_time': float(key_hold_time),
                'typing_speed': float(typing_speed),
                'error_rate': float(error_rate),
                'backspace_count': float(backspace_count),
                'idle_time': float(keyboard_idle)
            }
        except Exception as e:
            logger.error(f"Error extracting keyboard features: {e}")
            return {
                'key_press_count': 0.0,
                'key_hold_time': 0.0,
                'typing_speed': 0.0,
                'error_rate': 0.0,
                'backspace_count': 0.0,
                'idle_time': 0.0
            }

    @staticmethod
    def extract_mouse_features(raw_data):
        """
        Extract mouse features.

        Args:
            raw_data: Raw keyboard/mouse data from monitor

        Returns:
            dict: Mouse features
        """
        try:
            mouse_clicks = raw_data.get('mouse_clicks', {}) or {}
            scroll_count = raw_data.get('scroll_count', 0)
            mouse_movements = raw_data.get('mouse_movements', []) or []
            mouse_idle = raw_data.get('mouse_idle', 0)
            drag_count = raw_data.get('drag_count', 0)

            # Click counts
            left_click = mouse_clicks.get('left', 0)
            right_click = mouse_clicks.get('right', 0)
            double_click = mouse_clicks.get('double', 0)
            mouse_click_count = left_click + right_click + double_click

            # Movement metrics
            moves = [m for m in mouse_movements if m.get('time_diff', 0) > 0]
            total_distance = sum(m.get('distance', 0) for m in moves)

            # Cursor speed (pixels per second) using WINDOW SPAN not sum of diffs.
            # Training uses: total_distance / (last_time - first_time)
            cursor_speed = 0.0
            movement_speed = 0.0

            if len(moves) >= 1:
                times = [m.get('time', 0) for m in moves]
                span = (max(times) - min(times)) if len(times) > 1 else 0.0
                if span > 0 and total_distance > 0:
                    cursor_speed = total_distance / span
                    movement_speed = cursor_speed

            return {
                'mouse_click_count': float(mouse_click_count),
                'left_click': float(left_click),
                'right_click': float(right_click),
                'double_click': float(double_click),
                'scroll_count': float(scroll_count),
                'cursor_speed': float(cursor_speed),
                'cursor_distance': float(total_distance),
                'drag_count': float(drag_count),
                'movement_speed': float(movement_speed),
                'idle_mouse_time': float(mouse_idle)
            }
        except Exception as e:
            logger.error(f"Error extracting mouse features: {e}")
            return {
                'mouse_click_count': 0.0,
                'left_click': 0.0,
                'right_click': 0.0,
                'double_click': 0.0,
                'scroll_count': 0.0,
                'cursor_speed': 0.0,
                'cursor_distance': 0.0,
                'drag_count': 0.0,
                'movement_speed': 0.0,
                'idle_mouse_time': 0.0
            }

    @staticmethod
    def extract_features(raw_data, window_size=60):
        """
        Extract all features in correct order with validation.

        Args:
            raw_data: Raw data from ActivityMonitor.get_raw_data()
            window_size: Time window in seconds

        Returns:
            tuple: (all_features dict, feature_vector list)
        """
        try:
            if raw_data is None:
                raw_data = {}

            keyboard_features = FeatureExtractor.extract_keyboard_features(raw_data, window_size)
            mouse_features = FeatureExtractor.extract_mouse_features(raw_data)

            # Combine all features
            all_features = {**keyboard_features, **mouse_features}

            # Create feature vector in correct order
            feature_vector = [all_features[name] for name in FEATURE_ORDER]

            # Validate feature vector values (no NaN/Inf allowed)
            for i, val in enumerate(feature_vector):
                if val is None or not math.isfinite(float(val)):
                    feature_vector[i] = 0.0
                    all_features[FEATURE_ORDER[i]] = 0.0

            # Validate feature vector
            if len(feature_vector) != len(FEATURE_ORDER):
                logger.error(f"Feature vector size mismatch: {len(feature_vector)} vs {len(FEATURE_ORDER)}")
                raise ValueError("Feature vector size does not match expected size")

            return all_features, feature_vector
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return default features on error
            default_features = {name: 0.0 for name in FEATURE_ORDER}
            return default_features, [0.0] * len(FEATURE_ORDER)

    @staticmethod
    def get_feature_names():
        """Get feature names in correct order."""
        return FEATURE_ORDER

