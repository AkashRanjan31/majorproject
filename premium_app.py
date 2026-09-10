"""
premium_app.py
--------------
Enterprise-grade premium dashboard for AI-Based Mental Fatigue Detection.
"""

import streamlit as st
import time
import atexit
from datetime import datetime
from collections import deque
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Page config MUST be first ─────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Fatigue Detection",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.monitor import ActivityMonitor
from src.feature_extraction import FeatureExtractor, FEATURE_ORDER
from src.realtime_predict import FatiguePredictor
from src.config import get_config
from src.logger import setup_logger
from src.baseline import BaselineTracker
from dashboard.styles import PREMIUM_CSS
from dashboard.components import (
    render_header, render_kpi_cards, render_keyboard_analytics,
    render_mouse_analytics, render_break_recommendation,
    render_system_health, render_privacy_panel, render_baseline_table,
    render_session_stats, render_live_event_table, render_history_table,
    render_reports_panel,
)
from dashboard.charts import (
    fatigue_trend_chart, confidence_gauge, shap_bar_chart,
    feature_importance_chart, probability_donut, activity_timeline_chart,
    keyboard_metrics_chart, mouse_metrics_chart,
    analytics_bar, prediction_distribution, hourly_heatmap,
)
from dashboard.shap_utils import compute_shap_values
from database.db import init_db, insert_prediction, fetch_predictions, fetch_stats

logger = setup_logger(__name__)
config = get_config()

_REC_LABELS = {0: "Keep Working", 1: "Consider Short Break", 2: "Take 10-Min Break", 3: "Immediate Rest"}

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "monitor":            None,
        "predictor":          None,
        "app_initialized":    False,
        "session_start":      datetime.now(),
        "prediction_count":   0,
        "break_count":        0,
        "prediction_history": deque(maxlen=config.MAX_HISTORY_SIZE),
        "activity_timeline":  deque(maxlen=config.MAX_TIMELINE_SIZE),
        "event_log":          deque(maxlen=50),
        "baseline":           BaselineTracker(window=20),
        "last_prediction":    None,
        "last_features":      None,
        "shap_vals":          [],
        "shap_names":         [],
        "page":               "Dashboard",
        "window_size":        60,
        "prev_level":         0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()
init_db()


# ── Init / prediction helpers ─────────────────────────────────────────────────
def _initialize() -> bool:
    try:
        st.session_state.predictor = FatiguePredictor(config.MODEL_PATH)
        st.session_state.monitor   = ActivityMonitor(window_size=st.session_state.window_size)
        st.session_state.monitor.start()
        st.session_state.app_initialized = True
        st.session_state.session_start   = datetime.now()
        logger.info("App initialized")
        return True
    except Exception as e:
        logger.error("Init failed: %s", e)
        return False


def _get_prediction():
    mon  = st.session_state.monitor
    pred = st.session_state.predictor
    if not mon or not pred:
        return None, None
    try:
        raw = mon.get_raw_data()
        features, fvec = FeatureExtractor.extract_features(raw, st.session_state.window_size)
        result = pred.predict(fvec)
        result["timestamp"] = datetime.now()
        return result, features
    except Exception as e:
        logger.warning("Prediction error: %s", e)
        return None, None


def _update_state(prediction, features):
    ss = st.session_state
    ss.last_prediction  = prediction
    ss.last_features    = features
    ss.prediction_count += 1

    lvl = prediction.get("level", 0)
    if lvl > ss.prev_level:
        ss.break_count += 1
    ss.prev_level = lvl

    ss.prediction_history.append({
        "timestamp":  prediction["timestamp"],
        "level":      lvl,
        "confidence": prediction.get("confidence", 0),
        "name":       prediction.get("name", ""),
    })
    ss.baseline.update(features)
    ss.activity_timeline.append({
        "timestamp":        prediction["timestamp"],
        "typing_speed":     features.get("typing_speed", 0),
        "cursor_speed":     features.get("cursor_speed", 0),
        "key_press_count":  features.get("key_press_count", 0),
        "mouse_click_count":features.get("mouse_click_count", 0),
        "scroll_count":     features.get("scroll_count", 0),
        "backspace_count":  features.get("backspace_count", 0),
    })
    ss.event_log.append({
        "timestamp":        prediction["timestamp"],
        "key_press_count":  features.get("key_press_count", 0),
        "mouse_click_count":features.get("mouse_click_count", 0),
        "cursor_speed":     features.get("cursor_speed", 0),
        "level":            lvl,
    })

    # SHAP (compute once per prediction)
    try:
        sv, sn = compute_shap_values(pred.model, fvec, FEATURE_ORDER)
        ss.shap_vals  = sv
        ss.shap_names = sn
    except Exception:
        pass

    # Persist to DB
    rec_label = _REC_LABELS.get(lvl, "")
    insert_prediction(prediction, features, rec_label)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
          <div class="logo-icon">🧠</div>
          <div>
            <div class="logo-text">FatigueAI</div>
            <div class="logo-sub">Mental Health Monitor</div>
          </div>
        </div>""", unsafe_allow_html=True)

        pages = [
            ("🏠", "Dashboard"),
            ("📡", "Live Monitor"),
            ("📈", "Analytics"),
            ("📋", "History"),
            ("📄", "Reports"),
            ("🔒", "Privacy"),
            ("⚙️", "Settings"),
        ]
        for icon, name in pages:
            active = "active" if st.session_state.page == name else ""
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state.page = name

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:.72rem;color:#475569;padding:.5rem;">
          <div>Model: <b style="color:#60a5fa;">XGBoost</b></div>
          <div>Window: <b style="color:#a78bfa;">{st.session_state.window_size}s</b></div>
          <div>DB: <b style="color:#22C55E;">SQLite</b></div>
        </div>""", unsafe_allow_html=True)


# ── Pages ─────────────────────────────────────────────────────────────────────
def _page_dashboard(prediction, features):
    ss = st.session_state

    render_kpi_cards(prediction, features, ss.session_start)
    st.markdown("<br>", unsafe_allow_html=True)

    # Row: trend + gauge + donut
    c1, c2, c3 = st.columns([3, 1.5, 1.5])
    with c1:
        st.markdown('<div class="section-title">📈 Live Fatigue Trend</div>', unsafe_allow_html=True)
        st.plotly_chart(fatigue_trend_chart(list(ss.prediction_history)),
                        use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.markdown('<div class="section-title">🎯 Confidence</div>', unsafe_allow_html=True)
        lvl = prediction.get("level", 0) if prediction else 0
        conf = prediction.get("confidence", 0) if prediction else 0
        st.plotly_chart(confidence_gauge(conf, lvl),
                        use_container_width=True, config={"displayModeBar": False})
    with c3:
        st.markdown('<div class="section-title">📊 Probability</div>', unsafe_allow_html=True)
        probs = prediction.get("probabilities", {}) if prediction else {}
        st.plotly_chart(probability_donut(probs),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # Row: keyboard + mouse analytics
    c4, c5 = st.columns(2)
    with c4:
        render_keyboard_analytics(features)
    with c5:
        render_mouse_analytics(features)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row: break recommendation + system health
    c6, c7 = st.columns([2, 1])
    with c6:
        st.markdown('<div class="section-title">💡 Break Recommendation</div>', unsafe_allow_html=True)
        render_break_recommendation(prediction)
    with c7:
        render_system_health(
            is_monitoring=bool(ss.monitor and ss.monitor.is_monitoring),
            model_loaded=bool(ss.predictor),
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Row: SHAP + feature importance
    c8, c9 = st.columns(2)
    with c8:
        st.markdown('<div class="section-title">🔍 SHAP Explainability</div>', unsafe_allow_html=True)
        if ss.shap_vals:
            st.plotly_chart(shap_bar_chart(ss.shap_vals, ss.shap_names),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="card" style="color:#94A3B8;font-size:.85rem;padding:1rem;">SHAP values will appear after first prediction.</div>', unsafe_allow_html=True)
    with c9:
        st.markdown('<div class="section-title">⭐ Feature Importance</div>', unsafe_allow_html=True)
        if ss.predictor and hasattr(ss.predictor.model, "feature_importances_"):
            imp = dict(zip(FEATURE_ORDER, ss.predictor.model.feature_importances_))
            st.plotly_chart(feature_importance_chart(imp),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown('<div class="card" style="color:#94A3B8;font-size:.85rem;padding:1rem;">Feature importance loads after model init.</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Baseline + session stats
    c10, c11 = st.columns(2)
    with c10:
        deltas   = ss.baseline.get_deltas(features) if features else {}
        baseline = ss.baseline.get_baseline()
        render_baseline_table(deltas, features or {}, baseline)
    with c11:
        render_session_stats(ss.session_start, ss.prediction_count,
                             list(ss.prediction_history), ss.break_count)

    st.markdown("<br>", unsafe_allow_html=True)
    render_live_event_table(list(ss.event_log))


def _page_live_monitor(prediction, features):
    st.markdown('<div class="section-title">📡 Live Monitor — Raw Data</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**⌨️ Keyboard Features**")
        if features:
            for k in ["key_press_count","key_hold_time","typing_speed","error_rate","backspace_count","idle_time"]:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:.83rem;"><span style="color:#94A3B8;">{k.replace("_"," ").title()}</span><span style="color:#60a5fa;font-weight:600;">{features.get(k,0):.4f}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**🖱️ Mouse Features**")
        if features:
            for k in ["mouse_click_count","left_click","right_click","double_click","scroll_count","cursor_speed","cursor_distance","drag_count","movement_speed","idle_mouse_time"]:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:.83rem;"><span style="color:#94A3B8;">{k.replace("_"," ").title()}</span><span style="color:#a78bfa;font-weight:600;">{features.get(k,0):.4f}</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(keyboard_metrics_chart(features or {}), use_container_width=True, config={"displayModeBar": False})
    with c4:
        st.plotly_chart(mouse_metrics_chart(features or {}), use_container_width=True, config={"displayModeBar": False})

    if prediction:
        lvl   = prediction.get("level", 0)
        conf  = prediction.get("confidence", 0)
        name  = prediction.get("name", "")
        color = {0:"#22C55E",1:"#FACC15",2:"#F97316",3:"#EF4444"}.get(lvl,"#94A3B8")
        st.markdown(f"""
        <div class="card" style="margin-top:1rem;border-top:3px solid {color};">
          <div style="display:flex;gap:2rem;align-items:center;">
            <div><div style="font-size:.7rem;color:#94A3B8;text-transform:uppercase;">Prediction</div>
                 <div style="font-size:1.4rem;font-weight:800;color:{color};">{name}</div></div>
            <div><div style="font-size:.7rem;color:#94A3B8;text-transform:uppercase;">Confidence</div>
                 <div style="font-size:1.4rem;font-weight:800;color:{color};">{conf:.1%}</div></div>
            <div><div style="font-size:.7rem;color:#94A3B8;text-transform:uppercase;">Timestamp</div>
                 <div style="font-size:.9rem;font-weight:600;font-family:monospace;">{prediction['timestamp'].strftime('%H:%M:%S')}</div></div>
          </div>
        </div>""", unsafe_allow_html=True)


def _page_analytics():
    records = fetch_predictions(limit=500)
    st.markdown('<div class="section-title">📈 Analytics Overview</div>', unsafe_allow_html=True)

    tab_d, tab_w, tab_m = st.tabs(["Daily", "Weekly", "Monthly"])
    with tab_d:
        st.plotly_chart(analytics_bar(records, "daily"),  use_container_width=True, config={"displayModeBar": False})
    with tab_w:
        st.plotly_chart(analytics_bar(records, "weekly"), use_container_width=True, config={"displayModeBar": False})
    with tab_m:
        st.plotly_chart(analytics_bar(records, "monthly"),use_container_width=True, config={"displayModeBar": False})

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(prediction_distribution(records), use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(hourly_heatmap(records), use_container_width=True, config={"displayModeBar": False})

    st.plotly_chart(activity_timeline_chart(list(st.session_state.activity_timeline)),
                    use_container_width=True, config={"displayModeBar": False})


def _page_history():
    records = fetch_predictions(limit=300)
    render_history_table(records)


def _page_reports():
    history = list(st.session_state.prediction_history)
    render_reports_panel(history)


def _page_privacy():
    render_privacy_panel()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
      <div style="font-size:.85rem;color:#94A3B8;line-height:1.8;">
        This system monitors only <b style="color:#F8FAFC;">statistical patterns</b> of keyboard and mouse behavior.
        No keystrokes, passwords, or typed text are ever recorded or stored.
        All data remains on your local machine and is never transmitted externally.
        The SQLite database stores only numeric feature aggregates and fatigue predictions.
      </div>
    </div>""", unsafe_allow_html=True)


def _page_settings():
    st.markdown('<div class="section-title">⚙️ Settings</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Prediction Window**")
        ws = st.select_slider("Window Size (seconds)", options=[30, 60, 120],
                              value=st.session_state.window_size, label_visibility="collapsed")
        if ws != st.session_state.window_size:
            st.session_state.window_size = ws
            st.info("Restart monitoring to apply new window size.")
        st.markdown("**Notifications**")
        st.toggle("Break Reminders", value=True)
        st.toggle("Sound Alerts",    value=False)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**Model Info**")
        if st.session_state.predictor:
            info = st.session_state.predictor.get_model_info()
            for k, v in info.items():
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:.82rem;"><span style="color:#94A3B8;">{k}</span><span style="color:#60a5fa;">{v}</span></div>', unsafe_allow_html=True)
        else:
            st.info("Model not loaded yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    db_stats = fetch_stats()
    if db_stats:
        st.markdown('<div class="section-title">🗄️ Database Stats</div>', unsafe_allow_html=True)
        cols = st.columns(4)
        labels = [("Total Records","total"),("Avg Fatigue","avg_f"),("Max Fatigue","max_f"),("Avg Confidence","avg_c")]
        for col, (label, key) in zip(cols, labels):
            val = db_stats.get(key, 0) or 0
            col.metric(label, f"{val:.2f}" if isinstance(val, float) else str(val))


# ── Init screen ───────────────────────────────────────────────────────────────
def _init_screen():
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;">
      <div style="font-size:4rem;margin-bottom:1rem;">🧠</div>
      <div style="font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa);
           -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem;">
        AI-Based Mental Fatigue Detection
      </div>
      <div style="color:#94A3B8;font-size:.9rem;margin-bottom:2rem;">
        Real-Time Keyboard &amp; Mouse Monitoring · XGBoost · SHAP
      </div>
    </div>""", unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        if st.button("🚀 Start Monitoring", use_container_width=True):
            with st.spinner("Initializing monitoring system…"):
                if _initialize():
                    st.success("✅ System initialized successfully!")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ Initialization failed. Check permissions and try again.")
        st.markdown("""
        <div style="background:#111827;border-radius:12px;padding:1rem 1.5rem;margin-top:1rem;font-size:.82rem;color:#94A3B8;line-height:1.8;">
          <b style="color:#F8FAFC;">Requirements:</b><br>
          • Python keyboard/mouse listener permissions<br>
          • Windows: Run normally (no admin needed)<br>
          • Trained XGBoost model at <code>models/xgboost_model.pkl</code>
        </div>""", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    _sidebar()

    if not st.session_state.app_initialized:
        _init_screen()
        return

    # Get fresh prediction
    prediction, features = _get_prediction()
    if prediction and features:
        _update_state(prediction, features)

    pred = st.session_state.last_prediction
    feat = st.session_state.last_features

    # Header
    render_header(
        session_start=st.session_state.session_start,
        prediction_count=st.session_state.prediction_count,
        is_monitoring=bool(st.session_state.monitor and st.session_state.monitor.is_monitoring),
    )

    # Route pages
    page = st.session_state.page
    if page == "Dashboard":
        _page_dashboard(pred, feat)
    elif page == "Live Monitor":
        _page_live_monitor(pred, feat)
    elif page == "Analytics":
        _page_analytics()
    elif page == "History":
        _page_history()
    elif page == "Reports":
        _page_reports()
    elif page == "Privacy":
        _page_privacy()
    elif page == "Settings":
        _page_settings()

    # Footer
    st.markdown(f"""
    <div style="text-align:center;color:#334155;font-size:.72rem;padding:1.5rem 0 .5rem;border-top:1px solid rgba(255,255,255,.05);margin-top:1.5rem;">
      🧠 FatigueAI &nbsp;·&nbsp; XGBoost &nbsp;·&nbsp; SHAP &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; Streamlit
      &nbsp;·&nbsp; Window: {st.session_state.window_size}s
      &nbsp;·&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>""", unsafe_allow_html=True)

    # Auto-refresh
    time.sleep(st.session_state.window_size)
    st.rerun()


def _cleanup():
    try:
        if st.session_state.get("monitor"):
            st.session_state.monitor.stop()
    except Exception:
        pass


atexit.register(_cleanup)

if __name__ == "__main__":
    main()
