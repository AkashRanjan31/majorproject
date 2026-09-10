"""
realtime_predict.py (Production Version)
----------------------------------------
Real-time prediction using the trained XGBoost model.
Includes error handling, logging, and model validation.
"""

import os
import joblib
import numpy as np
from pathlib import Path
import logging
from src.logger import setup_logger

logger = setup_logger(__name__)


FATIGUE_LEVELS = {
    0: {'name': 'Normal', 'emoji': '🟢', 'color': 'green'},
    1: {'name': 'Moderate Fatigue', 'emoji': '🟡', 'color': 'yellow'},
    2: {'name': 'High Fatigue', 'emoji': '🔴', 'color': 'red'}
}


class FatiguePredictor:
    """Make real-time fatigue predictions using XGBoost model."""

    def __init__(self, model_path='models/xgboost_model.pkl'):
        """
        Initialize predictor with trained model.

        Args:
            model_path: Path to saved XGBoost model
        """
        self.model_path = model_path
        self.model = None
        self.load_model()

    def load_model(self):
        """Load the trained XGBoost model with validation."""
        try:
            # Check if path exists
            if not os.path.exists(self.model_path):
                # Try relative to current directory
                alt_path = os.path.join(os.getcwd(), self.model_path)
                if os.path.exists(alt_path):
                    self.model_path = alt_path
                else:
                    raise FileNotFoundError(f"Model not found at {self.model_path} or {alt_path}")

            logger.info(f"Loading model from: {self.model_path}")
            loaded = joblib.load(self.model_path)
            
            # Handle case where joblib loads a dict with the model inside
            if isinstance(loaded, dict) and 'model' in loaded:
                self.model = loaded['model']
                logger.info("Model extracted from dict")
            elif hasattr(loaded, 'predict'):  # It's an actual model
                self.model = loaded
            else:
                # Try to get it from the dict if it's the first value
                if isinstance(loaded, dict):
                    self.model = next((v for v in loaded.values() if hasattr(v, 'predict')), None)
                    if self.model is None:
                        raise ValueError(f"Could not find model object in loaded data: {type(loaded)}")
                else:
                    raise ValueError(f"Loaded object is not a model: {type(loaded)}")
            
            logger.info(f"Model loaded successfully from: {self.model_path}")
            logger.info(f"Model type: {type(self.model).__name__}")
            
            # Validate model
            self._validate_model()
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _validate_model(self):
        """Validate that the model has required methods."""
        try:
            if not hasattr(self.model, 'predict'):
                raise ValueError("Model does not have predict method")
            if not hasattr(self.model, 'predict_proba'):
                logger.warning("Model does not have predict_proba method")
            logger.info("Model validation passed")
        except Exception as e:
            logger.error(f"Model validation failed: {e}")
            raise

    def predict(self, feature_vector):
        """
        Predict fatigue level from feature vector with validation.

        Args:
            feature_vector: List of 16 features in correct order

        Returns:
            dict: Prediction result with level, name, confidence, probabilities
        """
        if self.model is None:
            raise ValueError("Model not loaded")

        try:
            # Validate feature vector
            if not isinstance(feature_vector, (list, tuple, np.ndarray)):
                raise TypeError(f"Feature vector must be list/tuple/array, got {type(feature_vector)}")
            
            if len(feature_vector) != 16:
                logger.warning(f"Feature vector size {len(feature_vector)} != expected 16")

            # Ensure correct shape
            features = np.array(feature_vector).reshape(1, -1)

            # Make prediction
            prediction = self.model.predict(features)[0]
            
            # Get prediction probabilities
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(features)[0]
                confidence = float(probabilities[int(prediction)])
            else:
                probabilities = np.zeros(3)
                probabilities[int(prediction)] = 1.0
                confidence = 1.0

            fatigue_info = FATIGUE_LEVELS[int(prediction)]

            result = {
                'level': int(prediction),
                'name': fatigue_info['name'],
                'emoji': fatigue_info['emoji'],
                'color': fatigue_info['color'],
                'confidence': float(confidence),
                'probabilities': {
                    'normal': float(probabilities[0]) if len(probabilities) > 0 else 0.0,
                    'moderate': float(probabilities[1]) if len(probabilities) > 1 else 0.0,
                    'high': float(probabilities[2]) if len(probabilities) > 2 else 0.0,
                }
            }
            
            logger.debug(f"Prediction: {result['name']} (confidence: {confidence:.2%})")
            return result
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise

    @staticmethod
    def get_fatigue_level_info(level):
        """Get info for a specific fatigue level."""
        return FATIGUE_LEVELS.get(level, FATIGUE_LEVELS[0])

    def get_model_info(self):
        """Get information about the loaded model."""
        try:
            if self.model is None:
                return {"error": "Model not loaded"}
            
            return {
                "type": type(self.model).__name__,
                "path": self.model_path,
                "has_predict": hasattr(self.model, 'predict'),
                "has_predict_proba": hasattr(self.model, 'predict_proba'),
                "classes": getattr(self.model, 'classes_', None),
                "n_features": getattr(self.model, 'n_features_in_', None)
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"error": str(e)}
