"""
realtime_app.py
---------------
Real-time mental fatigue detection — enterprise dashboard.
Launch: streamlit run realtime_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="NeuroSense AI — Mental Fatigue Detection",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import subprocess
import sys
import time
import atexit
from datetime import datetime
from collections import deque
import time as _time
from pathlib import Path

from src.config import get_config
from src.logger import setup_logger
from src.monitor import ActivityMonitor
from src.feature_extraction import FeatureExtractor, FEATURE_ORDER, TemporalFeatureBuffer
from src.realtime_predict import FatiguePredictor
from src.ensemble_predict import EnsemblePredictor
from src.baseline import BaselineTracker
from src.history import (
    build_prediction_record,
    generate_session_id,
    generate_prediction_id,
    save_prediction,
    load_prediction_history,
)
from database.db import init_db, insert_prediction, fetch_predictions, fetch_stats
from dashboard.shap_utils import compute_shap_values

from ui.styles import inject_css
from ui.sidebar import render_sidebar
from ui.header import render_header
from ui.pages.dashboard import render_dashboard_page
from ui.pages.live_monitor import render_live_monitor_page
from ui.pages.analytics import render_analytics_page
from ui.pages.history import render_history_page
from ui.pages.reports import render_reports_page
from ui.pages.settings import render_settings_page
from ui.pages.privacy import render_privacy_page
from ui.pages.about import render_about_page
from ui.pages.model import render_model_page

logger = setup_logger(__name__)
config = get_config()

_REC: dict[int, str] = {
    0: "Keep Working — You are alert and focused.",
    1: "Consider a Short Break — Mild fatigue detected.",
    2: "Take a 10-Minute Break — Moderate fatigue detected.",
    3: "Take Immediate Rest — High fatigue detected.",
}


def _init_state():
    defaults = {
        "page": "Dashboard",
        "monitor": None,
        "predictor": None,
        "initialized": False,
        "session_start": datetime.now(),
        "prediction_count": 0,
        "break_count": 0,
        "history": deque(maxlen=config.MAX_HISTORY_SIZE),
        "timeline": deque(maxlen=config.MAX_TIMELINE_SIZE),
        "events": deque(maxlen=50),
        "baseline": BaselineTracker(window=20),
        "last_prediction": None,
        "last_features": None,
        "last_shap": ([], []),
        "last_temporal": {},
        "temporal_buffer": TemporalFeatureBuffer(maxlen=10),
        "use_ensemble": True,
        "ensemble_predictor": None,
        "window_size": config.WINDOW_SIZE,
        "refresh_rate": 5,
        "prev_level": 0,
        "session_id": generate_session_id(),
        "pred_sequence": 0,
        "sidebar_collapsed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _initialize():
    # Guard: if monitor already exists and is alive, do not recreate it.
    # This prevents double-init on Streamlit reruns.
    existing = st.session_state.get("monitor")
    if existing is not None and existing.is_alive():
        st.session_state.initialized = True
        return True
    try:
        init_db()
        st.session_state.predictor = FatiguePredictor(config.MODEL_PATH)
        # Try to load ensemble; fall back to single model silently
        try:
            st.session_state.ensemble_predictor = EnsemblePredictor()
            st.session_state.use_ensemble = True
            logger.info("Ensemble predictor loaded.")
        except Exception as e:
            st.session_state.ensemble_predictor = None
            st.session_state.use_ensemble = False
            logger.warning(f"Ensemble not available ({e}), using single model.")
        monitor = ActivityMonitor(window_size=st.session_state.window_size)
        monitor.start()
        st.session_state.monitor = monitor
        st.session_state.initialized = True
        st.session_state.session_start = datetime.now()
        logger.info("Dashboard initialized — listeners started.")
        return True
    except Exception as e:
        logger.error(f"Init failed: {e}")
        st.error(f"Initialization failed: {e}")
        return False


def _get_prediction():
    try:
        mon = st.session_state.monitor
        pred_obj = st.session_state.predictor
        if not mon or not pred_obj:
            return None, None
        raw = mon.get_raw_data()
        features, fvec = FeatureExtractor.extract_features(
            raw, window_size=st.session_state.window_size
        )

        # ── Temporal features ──────────────────────────────────────────
        tb = st.session_state.temporal_buffer
        temporal = tb.compute(features)
        tb.update(features)
        st.session_state.last_temporal = temporal

        # ── Prediction: ensemble or single model ───────────────────────
        _pred_start = _time.time()
        ensemble = st.session_state.get("ensemble_predictor")
        if ensemble and st.session_state.use_ensemble:
            prediction = ensemble.predict(fvec)
        else:
            prediction = pred_obj.predict(fvec)
        prediction["timestamp"] = datetime.now()

        try:
            shap_vals, shap_names = compute_shap_values(
                pred_obj.model, fvec, FEATURE_ORDER
            )
            st.session_state.last_shap = (shap_vals, shap_names)
        except Exception:
            pass

        st.session_state.baseline.update(features)

        entry = {
            "timestamp": prediction["timestamp"],
            "level": prediction["level"],
            "name": prediction["name"],
            "confidence": prediction["confidence"],
        }
        st.session_state.history.append(entry)
        st.session_state.timeline.append({
            "timestamp": prediction["timestamp"],
            **{k: features.get(k, 0) for k in [
                "typing_speed", "cursor_speed", "key_press_count",
                "mouse_click_count", "scroll_count", "idle_time",
            ]},
        })
        st.session_state.events.append({
            "timestamp": prediction["timestamp"],
            "key_press_count": features.get("key_press_count", 0),
            "mouse_click_count": features.get("mouse_click_count", 0),
            "cursor_speed": features.get("cursor_speed", 0),
            "level": prediction["level"],
        })

        if prediction["level"] >= 2 and st.session_state.prev_level < 2:
            st.session_state.break_count += 1
        st.session_state.prev_level = prediction["level"]

        rec_text = _REC.get(prediction["level"], "")
        prediction["recommendation"] = rec_text
        insert_prediction(prediction, features, rec_text)

        st.session_state.pred_sequence += 1
        pred_record = build_prediction_record(
            session_id=st.session_state.session_id,
            prediction_id=generate_prediction_id(st.session_state.pred_sequence),
            row_id=st.session_state.pred_sequence,
            prediction=prediction,
            features=features,
            prediction_start_time=_pred_start,
        )
        save_prediction(pred_record)

        st.session_state.prediction_count += 1
        st.session_state.last_prediction = prediction
        st.session_state.last_features = features
        return prediction, features
    except Exception as e:
        logger.warning(f"Prediction error: {e}")
        return None, None


def _cleanup():
    try:
        if st.session_state.get("monitor"):
            st.session_state.monitor.stop()
    except Exception:
        pass


def main():
    _init_state()
    inject_css()

    if not st.session_state.initialized:
        with st.spinner("🧠 Initializing NeuroSense AI..."):
            if not _initialize():
                return
        st.rerun()

    atexit.register(_cleanup)

    page = render_sidebar()
    if page and page != st.session_state.page:
        st.session_state.page = page
    page = st.session_state.page

    # ── Floating widget launcher ───────────────────────────────────────────
    if st.sidebar.button("🧠 Launch Floating Widget", use_container_width=True):
        widget_path = str(Path(__file__).resolve().parent / "floating_widget.py")
        subprocess.Popen([sys.executable, widget_path],
                         creationflags=subprocess.CREATE_NEW_CONSOLE
                         if sys.platform == "win32" else 0)
    render_header(
        session_start=st.session_state.session_start,
        prediction_count=st.session_state.prediction_count,
        is_monitoring=st.session_state.initialized,
    )

    prediction, features = _get_prediction()

    if page == "Dashboard":
        render_dashboard_page(
            prediction=prediction,
            features=features,
            history=list(st.session_state.history),
            timeline=list(st.session_state.timeline),
            events=list(st.session_state.events),
            shap_data=st.session_state.last_shap,
            baseline_tracker=st.session_state.baseline,
            session_start=st.session_state.session_start,
            prediction_count=st.session_state.prediction_count,
            break_count=st.session_state.break_count,
            is_monitoring=st.session_state.initialized,
            model_loaded=st.session_state.predictor is not None,
        )
    elif page == "Live Monitor":
        render_live_monitor_page(
            prediction=prediction,
            features=features,
            events=list(st.session_state.events),
            monitor=st.session_state.monitor,
        )
    elif page == "Analytics":
        render_analytics_page(records=fetch_predictions(limit=500))
    elif page == "Fatigue Trends":
        render_analytics_page(
            records=fetch_predictions(limit=500), default_tab="trends"
        )
    elif page == "History":
        render_history_page(
            df=load_prediction_history(limit=1000),
            current_session_id=st.session_state.session_id,
        )
    elif page == "Reports":
        render_reports_page(
            history=list(st.session_state.history),
            db_records=fetch_predictions(limit=1000),
        )
    elif page == "Settings":
        render_settings_page()
    elif page == "Privacy":
        render_privacy_page()
    elif page == "Model":
        render_model_page(predictor=st.session_state.predictor)
    elif page == "About":
        render_about_page()

    # Use st.empty + a short sleep so Streamlit can render the frame
    # before the next rerun.  Do NOT sleep for the full refresh_rate here
    # because that blocks the Streamlit thread and makes the UI appear frozen.
    # The listeners run in daemon threads and are unaffected by this sleep.
    time.sleep(1)
    st.rerun()


if __name__ == "__main__":
    main()
