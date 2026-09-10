"""
config.py
---------
Centralised configuration for the Mental Fatigue Detection system.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class AppConfig:
    """Application configuration with env-var overrides."""

    # Monitoring
    WINDOW_SIZE: int = 60
    MAX_BUFFER_SIZE: int = 1000
    PREDICTION_INTERVAL: int = 30

    # Model
    MODEL_PATH: str = str(PROJECT_ROOT / "models" / "best_model.pkl")
    MODELS_DIR: str = str(PROJECT_ROOT / "models")

    # Fatigue classes (5-class)
    CLASS_NAMES: list = field(default_factory=lambda: [
        "Normal", "Low Fatigue", "Moderate Fatigue", "High Fatigue", "Critical Fatigue"
    ])
    CLASS_COLORS: list = field(default_factory=lambda: [
        "#22c55e", "#84cc16", "#f59e0b", "#ef4444", "#7c3aed"
    ])
    CLASS_EMOJIS: list = field(default_factory=lambda: ["🟢", "🟡", "🟠", "🔴", "🟣"])

    # Fatigue thresholds (0–100 score)
    FATIGUE_THRESHOLDS: dict = field(default_factory=lambda: {
        "break": 60, "water": 50, "stretch": 55, "eye_exercise": 45,
        "walk": 65, "meditation": 70, "breathing": 40
    })

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # History
    MAX_HISTORY_SIZE: int = 200
    MAX_TIMELINE_SIZE: int = 200
    HISTORY_DIR: str = str(PROJECT_ROOT / "history")
    HISTORY_FILE: str = "prediction_history.csv"

    # Resource limits
    MAX_MOUSE_MOVEMENTS_PER_WINDOW: int = 10000
    MAX_KEY_EVENTS_PER_WINDOW: int = 5000

    # Personalization
    BASELINE_WINDOW_COUNT: int = 10   # windows needed to build baseline
    BASELINE_PATH: str = str(PROJECT_ROOT / "models" / "user_baseline.pkl")

    # Model metadata
    MODEL_NAME: str = "XGBoost"
    MODEL_VERSION: str = "1.0.0"

    # Evaluation output
    PLOTS_DIR: str = str(PROJECT_ROOT / "plots")

    @classmethod
    def from_env(cls):
        return cls(
            WINDOW_SIZE=int(os.getenv("WINDOW_SIZE", "60")),
            MODEL_PATH=os.getenv("MODEL_PATH", str(PROJECT_ROOT / "models" / "best_model.pkl")),
            PREDICTION_INTERVAL=int(os.getenv("PREDICTION_INTERVAL", "30")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        )


def get_config() -> AppConfig:
    return AppConfig.from_env()
