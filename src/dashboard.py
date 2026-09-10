"""
dashboard.py
------------
Streamlit dashboard for real-time fatigue monitoring.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time


def setup_dashboard():
    """Configure Streamlit page."""
    st.set_page_config(
        page_title="Real-Time Mental Fatigue Detection",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("🧠 AI-Based Mental Fatigue Detection")
    st.markdown("*Real-time monitoring using keyboard and mouse behavior*")


def display_fatigue_status(prediction):
    """Display current fatigue level with colored indicator."""
    if prediction is None:
        st.warning("⏳ Collecting initial data...")
        return

    col1, col2 = st.columns(2)

    with col1:
        # Main status card
        emoji = prediction['emoji']
        level_name = prediction['name']
        confidence = prediction['confidence']
        color = prediction['color']

        # Create colored box with status
        if color == 'green':
            st.success(f"### {emoji} {level_name}\n**Confidence:** {confidence:.1%}")
        elif color == 'yellow':
            st.warning(f"### {emoji} {level_name}\n**Confidence:** {confidence:.1%}")
        else:
            st.error(f"### {emoji} {level_name}\n**Confidence:** {confidence:.1%}")

    with col2:
        # Confidence breakdown
        st.markdown("### Confidence Scores")
        probs = prediction['probabilities']
        prob_data = pd.DataFrame({
            'Level': ['Normal', 'Moderate', 'High'],
            'Probability': [probs['normal'], probs['moderate'], probs['high']]
        })
        st.bar_chart(prob_data.set_index('Level'))


def display_metrics(activity_data):
    """Display live activity metrics."""
    if activity_data is None:
        st.info("Waiting for data...")
        return

    st.markdown("### 📊 Live Activity Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "⌨️ Typing Speed",
            f"{activity_data['typing_speed']:.1f} WPM",
            delta=None
        )

    with col2:
        st.metric(
            "🖱️ Mouse Clicks",
            f"{activity_data['mouse_click_count']:.0f}",
            delta=None
        )

    with col3:
        st.metric(
            "🖥️ Cursor Speed",
            f"{activity_data['cursor_speed']:.0f} px/s",
            delta=None
        )

    with col4:
        st.metric(
            "📜 Scrolls",
            f"{activity_data['scroll_count']:.0f}",
            delta=None
        )

    # Row 2
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            "📝 Key Presses",
            f"{activity_data['key_press_count']:.0f}",
            delta=None
        )

    with col6:
        st.metric(
            "🔙 Backspaces",
            f"{activity_data['backspace_count']:.0f}",
            delta=None
        )

    with col7:
        st.metric(
            "⏸️ Keyboard Idle",
            f"{activity_data['idle_time']:.1f}s",
            delta=None
        )

    with col8:
        st.metric(
            "⏸️ Mouse Idle",
            f"{activity_data['idle_mouse_time']:.1f}s",
            delta=None
        )


def display_history(history_data):
    """Display prediction history chart."""
    if not history_data or len(history_data) < 2:
        st.info("Waiting for prediction history...")
        return

    st.markdown("### 📈 Fatigue Level History")

    df = pd.DataFrame(history_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # Create chart
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(df['timestamp'], df['level'], marker='o', linestyle='-', linewidth=2, markersize=6)
    ax.fill_between(df['timestamp'], df['level'], alpha=0.3)
    ax.set_ylabel('Fatigue Level', fontsize=10)
    ax.set_xlabel('Time', fontsize=10)
    ax.set_ylim(-0.5, 2.5)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(['Normal (0)', 'Moderate (1)', 'High (2)'])
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    st.pyplot(fig)


def display_activity_timeline(timeline_data):
    """Display activity metrics over time."""
    if not timeline_data or len(timeline_data) < 2:
        st.info("Waiting for activity timeline...")
        return

    st.markdown("### 📊 Activity Timeline")

    df = pd.DataFrame(timeline_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df['timestamp'], df['typing_speed'], label='Typing Speed (WPM)', marker='o', color='blue')
        ax.set_ylabel('WPM', fontsize=10)
        ax.set_xlabel('Time', fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df['timestamp'], df['cursor_speed'], label='Cursor Speed (px/s)', marker='o', color='green')
        ax.set_ylabel('Pixels/Second', fontsize=10)
        ax.set_xlabel('Time', fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)


def display_session_info(session_info):
    """Display session information."""
    if session_info is None:
        return

    st.markdown("### ℹ️ Session Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        start_time = datetime.fromtimestamp(session_info['start_time'])
        st.write(f"**Started:** {start_time.strftime('%H:%M:%S')}")

    with col2:
        duration = session_info['duration']
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        st.write(f"**Duration:** {minutes}m {seconds}s")

    with col3:
        st.write(f"**Predictions:** {session_info['prediction_count']}")


# Break recommendation config
_BREAK_CONFIG = {
    0: ('✅ Keep Working', 'success', 'You are alert and focused. No break needed.'),
    1: ('☕ Consider a Short Break', 'warning', 'Mild fatigue detected. A 2–5 minute break can help.'),
    2: ('🛑 Take a 10-Minute Break', 'error', 'High fatigue detected. Rest your eyes and step away from the screen.'),
}


def display_break_recommendation(prediction: dict) -> None:
    """Display a break recommendation based on the predicted fatigue level."""
    if prediction is None:
        return
    level = prediction.get('level', 0)
    label, kind, detail = _BREAK_CONFIG.get(level, _BREAK_CONFIG[0])
    getattr(st, kind)(f"### {label}\n{detail}")


def display_shap_explanation(model, feature_vector: list, feature_names: list) -> None:
    """Display SHAP-based top feature contributions for the current prediction."""
    try:
        import shap
        import numpy as np
        import matplotlib.pyplot as plt

        X = np.array(feature_vector).reshape(1, -1)
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)  # shape: (n_classes, 1, n_features) or (1, n_features)

        # For multi-class XGBoost shap_values is a list of arrays
        if isinstance(shap_values, list):
            # Pick the class with highest predicted probability
            abs_sums = [abs(sv[0]).sum() for sv in shap_values]
            sv = shap_values[int(abs_sums.index(max(abs_sums)))][0]
        else:
            sv = shap_values[0]

        # Build sorted importance table
        pairs = sorted(zip(feature_names, sv), key=lambda x: abs(x[1]), reverse=True)[:8]
        labels = [p[0].replace('_', ' ').title() for p in pairs]
        values = [p[1] for p in pairs]
        colors = ['#ef4444' if v > 0 else '#22c55e' for v in values]

        fig, ax = plt.subplots(figsize=(7, 3))
        bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1])
        ax.axvline(0, color='gray', linewidth=0.8)
        ax.set_xlabel('SHAP value (impact on fatigue score)', fontsize=9)
        ax.set_title('Top Feature Contributions', fontsize=10)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        st.info("Install `shap` to enable explainability: `pip install shap`")
    except Exception as e:
        st.warning(f"SHAP explanation unavailable: {e}")


def display_baseline_comparison(deltas: dict) -> None:
    """Display how current behavior compares to the user's personal baseline."""
    if not deltas:
        st.info("⏳ Building your personal baseline... (needs a few more windows)")
        return

    st.markdown("#### 👤 vs Your Personal Baseline")
    _LABELS = {
        'typing_speed': '⌨️ Typing Speed',
        'key_press_count': '📝 Key Presses',
        'cursor_speed': '🖱️ Cursor Speed',
        'mouse_click_count': '🖱️ Mouse Clicks',
        'idle_time': '⏸️ Keyboard Idle',
        'idle_mouse_time': '⏸️ Mouse Idle',
        'backspace_count': '🔙 Backspaces',
    }
    cols = st.columns(len(deltas))
    for col, (key, delta) in zip(cols, deltas.items()):
        label = _LABELS.get(key, key)
        col.metric(label, f"{delta:+.1f}%")


def display_sidebar():
    """Display sidebar controls."""
    st.sidebar.markdown("### ⚙️ Settings")

    refresh_rate = st.sidebar.slider(
        "Update interval (seconds)",
        min_value=5,
        max_value=120,
        value=30,
        step=5
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📌 About

    This application monitors keyboard and mouse behavior in real-time
    and predicts mental fatigue levels using an AI model.

    **Features tracked:**
    - Keyboard: typing speed, key hold time, error rate
    - Mouse: clicks, movements, scrolling
    - Idle times and behavioral patterns

    **Fatigue Levels:**
    - 🟢 Normal: Alert and focused
    - 🟡 Moderate: Some signs of fatigue
    - 🔴 High: Significant fatigue detected
    """)

    return refresh_rate
