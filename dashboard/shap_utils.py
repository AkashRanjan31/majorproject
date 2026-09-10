"""
shap_utils.py
-------------
SHAP explainability helpers: compute values and return chart-ready data.
Handles both legacy shap_values list API and new Explanation object API.
"""

import numpy as np
from src.logger import setup_logger

logger = setup_logger(__name__)


def compute_shap_values(model, feature_vector: list, feature_names: list) -> tuple[list[float], list[str]]:
    """
    Compute SHAP values for a single prediction.

    Returns (shap_vals, feature_names) as plain Python floats for the
    dominant class, or ([], []) if SHAP is unavailable.
    """
    try:
        import shap

        X = np.array(feature_vector, dtype=float).reshape(1, -1)
        explainer = shap.TreeExplainer(model)
        raw = explainer.shap_values(X)

        # New SHAP API returns an Explanation object
        if hasattr(raw, "values"):
            arr = np.array(raw.values)
            # shape: (1, n_features) binary  OR  (1, n_features, n_classes) multi-class
            if arr.ndim == 3:
                # pick class with largest absolute sum
                abs_sums = np.abs(arr[0]).sum(axis=0)
                idx = int(np.argmax(abs_sums))
                sv = arr[0, :, idx]
            elif arr.ndim == 2:
                sv = arr[0]
            else:
                sv = arr.flatten()

        # Legacy API returns list of arrays (one per class) or single array
        elif isinstance(raw, list):
            abs_sums = [float(np.abs(np.array(sv)).sum()) for sv in raw]
            idx = int(np.argmax(abs_sums))
            sv = np.array(raw[idx]).flatten()
        else:
            sv = np.array(raw).flatten()

        return [float(v) for v in sv[:len(feature_names)]], list(feature_names)

    except ImportError:
        logger.warning("shap not installed – explainability disabled")
        return [], []
    except Exception as e:
        logger.warning("SHAP computation failed: %s", e)
        return [], []
