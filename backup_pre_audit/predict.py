"""
predict.py
----------
Load the saved XGBoost model and predict fatigue for new feature values.
"""

from pathlib import Path
import sys

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "xgboost_model.pkl"
sys.path.insert(0, str(PROJECT_ROOT))


def load_model():
    """Load the trained model package from disk."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run: python src/train_model.py")
    return joblib.load(MODEL_PATH)


def predict_fatigue(feature_values: dict) -> tuple[str, float]:
    """
    Predict fatigue label and confidence from a dictionary of feature values.
    """
    saved = load_model()
    model = saved["model"]
    feature_names = saved["feature_names"]
    class_names = saved.get("class_names", ["Normal", "Moderate Fatigue", "High Fatigue"])

    row = pd.DataFrame([[feature_values.get(feature, 0) for feature in feature_names]], columns=feature_names)
    prediction = int(model.predict(row)[0])
    probabilities = model.predict_proba(row)[0]
    confidence = float(probabilities[prediction])

    label = class_names[prediction] if prediction < len(class_names) else str(prediction)
    return label, confidence


if __name__ == "__main__":
    sample = {
        "key_press_count": 120,
        "key_hold_time": 0.20,
        "typing_speed": 45,
        "error_rate": 0.08,
        "backspace_count": 15,
        "idle_time": 8,
        "mouse_click_count": 25,
        "left_click": 20,
        "right_click": 5,
        "double_click": 2,
        "scroll_count": 10,
        "cursor_speed": 220,
        "cursor_distance": 1500,
        "drag_count": 2,
        "movement_speed": 200,
        "idle_mouse_time": 6,
    }
    predicted_label, confidence_score = predict_fatigue(sample)
    print(f"Prediction: {predicted_label}")
    print(f"Confidence: {confidence_score:.2%}")
