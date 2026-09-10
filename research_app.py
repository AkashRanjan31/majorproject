"""
research_app.py
---------------
Research-grade Streamlit dashboard: live monitoring, model comparison,
explainability, personalization, and smart recommendations.
"""

import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()

MODELS_DIR  = Path(config.MODELS_DIR)
PLOTS_DIR   = PROJECT_ROOT / "plots"
CLASS_NAMES = config.CLASS_NAMES
CLASS_COLORS = config.CLASS_COLORS
CLASS_EMOJIS = config.CLASS_EMOJIS

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Mental Fatigue Detection — Research Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background: #0f172a; }
  .glass {
    background: rgba(255,255,255,.07);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.12);
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
  }
  .metric-card {
    background: linear-gradient(135deg,rgba(99,102,241,.25),rgba(139,92,246,.15));
    border-radius: 16px;
    padding: 1rem;
    text-align: center;
    border: 1px solid rgba(99,102,241,.3);
  }
  .fatigue-badge {
    font-size: 2rem; font-weight: 800;
    padding: .4rem 1.2rem;
    border-radius: 50px;
    display: inline-block;
  }
  h1,h2,h3 { color: #e2e8f0 !important; }
  .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; }
  .stTabs [aria-selected="true"] { color: #6366f1 !important; border-bottom: 2px solid #6366f1; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "monitor": None, "predictor": None, "monitoring": False,
        "history": [], "timeline": [], "baseline": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_comparison() -> pd.DataFrame | None:
    p = MODELS_DIR / "model_comparison.csv"
    return pd.read_csv(p) if p.exists() else None


def _load_plot(name: str):
    p = PLOTS_DIR / name
    return str(p) if p.exists() else None


def _fatigue_gauge(score: int, level_name: str, color: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": level_name, "font": {"size": 18, "color": "#e2e8f0"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar": {"color": color},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 20],  "color": "rgba(34,197,94,.15)"},
                {"range": [20, 40], "color": "rgba(132,204,22,.15)"},
                {"range": [40, 60], "color": "rgba(245,158,11,.15)"},
                {"range": [60, 80], "color": "rgba(239,68,68,.15)"},
                {"range": [80, 100],"color": "rgba(124,58,237,.15)"},
            ],
            "threshold": {"line": {"color": color, "width": 4}, "value": score},
        },
        number={"font": {"color": color, "size": 40}, "suffix": "%"},
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=280, margin=dict(t=40, b=10))
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Mental Fatigue Detection")
    st.markdown("*Research Dashboard — B.Tech CSE Major Project*")
    st.divider()

    page = st.radio("Navigation", [
        "🏠 Live Monitor",
        "📊 Model Comparison",
        "🔍 Explainability",
        "👤 Personalization",
        "📈 Analytics",
        "ℹ️ Research Info",
    ])

    st.divider()
    if st.session_state.monitoring:
        st.success("🟢 Monitoring Active")
    else:
        st.warning("🔴 Monitoring Stopped")

    st.caption(f"Models dir: `{MODELS_DIR.name}/`")
    st.caption(f"Plots dir: `{PLOTS_DIR.name}/`")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Live Monitor
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Live Monitor":
    st.markdown("# 🧠 Real-Time Mental Fatigue Monitor")
    st.markdown("*Keyboard & Mouse Behavioral Biometrics — No EEG, No Wearables*")

    col_start, col_stop, col_reset = st.columns([1, 1, 2])
    with col_start:
        if st.button("▶ Start Monitoring", type="primary", use_container_width=True):
            if not st.session_state.monitoring:
                try:
                    from src.monitor import ActivityMonitor
                    from src.realtime_predict import FatiguePredictor
                    st.session_state.monitor   = ActivityMonitor(window_size=config.WINDOW_SIZE)
                    st.session_state.predictor = FatiguePredictor()
                    st.session_state.monitor.start()
                    st.session_state.monitoring = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start: {e}")
    with col_stop:
        if st.button("⏹ Stop", use_container_width=True):
            if st.session_state.monitor:
                st.session_state.monitor.stop()
            if st.session_state.predictor:
                st.session_state.predictor.save_baseline()
            st.session_state.monitoring = False
            st.rerun()

    st.divider()

    # ── Live prediction ───────────────────────────────────────────────────────
    if st.session_state.monitoring and st.session_state.monitor:
        monitor   = st.session_state.monitor
        predictor = st.session_state.predictor

        from src.feature_extraction import FeatureExtractor
        raw = monitor.get_raw_data()
        features, vector = FeatureExtractor.extract_features(raw, config.WINDOW_SIZE)

        try:
            result = predictor.predict(vector)
        except Exception as e:
            st.error(f"Prediction error: {e}")
            result = None

        if result:
            level = result["level"]
            color = result["color"]
            score = result["fatigue_score"]

            # ── Top metrics row ───────────────────────────────────────────
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Fatigue Level", f"{result['emoji']} {result['name']}")
            c2.metric("Fatigue Score", f"{score}%")
            c3.metric("Confidence",    f"{result['confidence']}%")
            c4.metric("Typing Speed",  f"{features.get('typing_speed', 0):.0f} WPM")
            c5.metric("Mouse Velocity",f"{features.get('mouse_velocity', 0):.0f} px/s")

            # ── Gauge + Probabilities ─────────────────────────────────────
            g1, g2 = st.columns([1, 1])
            with g1:
                st.plotly_chart(_fatigue_gauge(score, result["name"], color),
                                use_container_width=True)
            with g2:
                proba_df = pd.DataFrame({
                    "Class": list(result["probabilities"].keys()),
                    "Probability": list(result["probabilities"].values()),
                })
                fig_bar = px.bar(proba_df, x="Class", y="Probability",
                                 color="Class",
                                 color_discrete_sequence=CLASS_COLORS,
                                 title="Class Probabilities (%)")
                fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)",
                                      font_color="#e2e8f0", showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            # ── Recommendations ───────────────────────────────────────────
            if result["recommendations"]:
                st.markdown("### 💡 Smart Recommendations")
                cols = st.columns(len(result["recommendations"]))
                for col, rec in zip(cols, result["recommendations"]):
                    col.info(rec)

            # ── Feature snapshot ──────────────────────────────────────────
            with st.expander("📋 Current Feature Values"):
                feat_df = pd.DataFrame(
                    {"Feature": list(features.keys()), "Value": list(features.values())}
                )
                st.dataframe(feat_df, use_container_width=True, height=300)

            # ── History timeline ──────────────────────────────────────────
            st.session_state.history.append({
                "time": pd.Timestamp.now().strftime("%H:%M:%S"),
                "score": score, "level": result["name"],
            })
            if len(st.session_state.history) > config.MAX_HISTORY_SIZE:
                st.session_state.history.pop(0)

            if len(st.session_state.history) > 1:
                hist_df = pd.DataFrame(st.session_state.history)
                fig_line = px.line(hist_df, x="time", y="score",
                                   title="Fatigue Score Timeline",
                                   color_discrete_sequence=["#6366f1"])
                fig_line.add_hrect(y0=60, y1=100, fillcolor="red", opacity=0.08)
                fig_line.add_hrect(y0=40, y1=60, fillcolor="orange", opacity=0.08)
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                       plot_bgcolor="rgba(0,0,0,0)",
                                       font_color="#e2e8f0")
                st.plotly_chart(fig_line, use_container_width=True)

        # Auto-refresh every 30 seconds
        time.sleep(0.5)
        st.rerun()

    else:
        st.info("Click **▶ Start Monitoring** to begin real-time fatigue detection.")
        st.markdown("""
        **How it works:**
        1. The system captures keyboard and mouse events in the background
        2. Every 30 seconds, 40+ behavioral features are extracted
        3. The best ML model predicts your fatigue level (5 classes)
        4. SHAP explains WHY the prediction was made
        5. Smart recommendations are shown when fatigue is detected
        """)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Model Comparison
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Model Comparison":
    st.markdown("# 📊 Model Comparison — All 14 Classifiers")

    df = _load_comparison()
    if df is None:
        st.warning("No comparison data found. Run `python src/multi_train.py` first.")
    else:
        # ── Leaderboard ───────────────────────────────────────────────────
        st.markdown("### 🏆 Model Leaderboard")
        display_cols = ["Rank", "Model", "Accuracy", "F1_Score", "ROC_AUC",
                        "CV_Accuracy", "Train_Time_s", "Model_Size_KB"]
        st.dataframe(
            df[display_cols].style
              .background_gradient(subset=["Accuracy", "F1_Score", "ROC_AUC"], cmap="YlOrRd")
              .format({"Accuracy": "{:.4f}", "F1_Score": "{:.4f}", "ROC_AUC": "{:.4f}",
                       "CV_Accuracy": "{:.4f}", "Train_Time_s": "{:.3f}"}),
            use_container_width=True,
        )

        # ── Metric comparison charts ──────────────────────────────────────
        st.markdown("### 📈 Metric Comparison")
        metric = st.selectbox("Select Metric", ["Accuracy", "F1_Score", "ROC_AUC",
                                                 "CV_Accuracy", "Precision", "Recall"])
        fig = px.bar(df.sort_values(metric, ascending=True),
                     x=metric, y="Model", orientation="h",
                     color=metric, color_continuous_scale="viridis",
                     title=f"{metric} — All Models")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#e2e8f0", height=500)
        st.plotly_chart(fig, use_container_width=True)

        # ── Scatter: Time vs Accuracy ─────────────────────────────────────
        st.markdown("### ⏱️ Training Time vs Accuracy")
        fig2 = px.scatter(df, x="Train_Time_s", y="Accuracy", text="Model",
                          size="Model_Size_KB", color="F1_Score",
                          color_continuous_scale="plasma",
                          title="Training Time vs Accuracy (bubble = model size)")
        fig2.update_traces(textposition="top center")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#e2e8f0")
        st.plotly_chart(fig2, use_container_width=True)

        # ── Radar chart ───────────────────────────────────────────────────
        st.markdown("### 🕸️ Radar Chart — Top 5 Models")
        top5 = df.head(5)
        metrics = ["Accuracy", "Precision", "Recall", "F1_Score", "ROC_AUC"]
        fig3 = go.Figure()
        for _, row in top5.iterrows():
            vals = [row[m] for m in metrics] + [row[metrics[0]]]
            fig3.add_trace(go.Scatterpolar(
                r=vals, theta=metrics + [metrics[0]],
                fill="toself", name=row["Model"], opacity=0.7,
            ))
        fig3.update_layout(polar=dict(radialaxis=dict(range=[0, 1])),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
                           title="Top-5 Models Radar")
        st.plotly_chart(fig3, use_container_width=True)

        # ── Saved plots ───────────────────────────────────────────────────
        st.markdown("### 🖼️ Generated Plots")
        plot_files = [
            ("model_comparison_bar.png", "Model Comparison Bar"),
            ("metrics_heatmap.png",      "Metrics Heatmap"),
            ("all_confusion_matrices.png","Confusion Matrices"),
            ("roc_curves_multiclass.png", "ROC Curves"),
            ("pr_curves.png",             "Precision-Recall Curves"),
            ("cv_boxplot.png",            "CV Boxplot"),
            ("model_leaderboard.png",     "Leaderboard Table"),
        ]
        for fname, label in plot_files:
            p = _load_plot(fname)
            if p:
                with st.expander(f"📊 {label}"):
                    st.image(p, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Explainability
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Explainability":
    st.markdown("# 🔍 Explainable AI — SHAP Analysis")
    st.markdown("*Why did the model predict this fatigue level?*")

    # Show saved SHAP plots
    shap_plots = [
        ("shap_summary.png",       "SHAP Summary (Global)"),
        ("shap_bar.png",           "Mean |SHAP| Bar Chart"),
        ("shap_local_sample0.png", "Local Explanation — Sample 0"),
        ("permutation_importance.png", "Permutation Importance"),
        ("feature_importance_comparison.png", "Feature Importance Comparison"),
    ]
    for fname, label in shap_plots:
        p = _load_plot(fname)
        if p:
            st.markdown(f"### {label}")
            st.image(p, use_container_width=True)
        else:
            st.info(f"Run `python src/explainability.py` to generate: {fname}")

    # ── Manual prediction explanation ─────────────────────────────────────
    st.divider()
    st.markdown("### 🔬 Explain a Custom Prediction")
    st.markdown("Enter feature values to get a SHAP-based explanation:")

    from src.feature_extraction import FEATURE_ORDER
    with st.form("explain_form"):
        cols = st.columns(4)
        values = {}
        for i, feat in enumerate(FEATURE_ORDER):
            with cols[i % 4]:
                values[feat] = st.number_input(feat, value=0.0, format="%.3f", key=f"f_{feat}")
        submitted = st.form_submit_button("🔍 Explain Prediction")

    if submitted:
        try:
            from src.explainability import explain_prediction
            vector = [values[f] for f in FEATURE_ORDER]
            result = explain_prediction(vector, FEATURE_ORDER)

            st.markdown(f"### Prediction: {result['fatigue_name']} "
                        f"({result['fatigue_score']}% fatigue)")
            st.markdown(f"**Confidence:** {result['confidence']}%")

            if result["reasons"]:
                st.markdown("#### Top Contributing Features:")
                for r in result["reasons"]:
                    direction_color = "🔴" if r["shap"] > 0 else "🟢"
                    st.markdown(
                        f"{direction_color} **{r['feature']}** = `{r['value']}` "
                        f"→ SHAP: `{r['shap']:+.4f}` ({r['direction']})"
                    )
        except Exception as e:
            st.error(f"Explanation failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Personalization
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👤 Personalization":
    st.markdown("# 👤 Personal Baseline & Adaptive Scoring")
    st.markdown("*The system learns YOUR normal behaviour and compares against it.*")

    try:
        from src.personalization import UserBaseline
        baseline = UserBaseline.load()

        c1, c2, c3 = st.columns(3)
        c1.metric("Calibrated", "✅ Yes" if baseline.is_calibrated else "⏳ Collecting...")
        c2.metric("Windows Collected", baseline._calibration_count)
        c3.metric("Windows Needed", config.BASELINE_WINDOW_COUNT)

        if baseline.is_calibrated:
            st.success("✅ Personal baseline is active. Fatigue scores are personalised.")
            if baseline.baseline_mean is not None:
                from src.feature_extraction import FEATURE_ORDER
                baseline_df = pd.DataFrame({
                    "Feature": FEATURE_ORDER[:len(baseline.baseline_mean)],
                    "Your Baseline Mean": baseline.baseline_mean,
                    "Your Baseline Std":  baseline.baseline_std,
                })
                st.dataframe(baseline_df, use_container_width=True)
        else:
            remaining = config.BASELINE_WINDOW_COUNT - baseline._calibration_count
            st.info(f"⏳ Collecting baseline... {remaining} more windows needed "
                    f"({config.WINDOW_SIZE}s each).")
            st.progress(baseline._calibration_count / config.BASELINE_WINDOW_COUNT)

        if st.button("🗑️ Reset Baseline"):
            from src.config import get_config
            Path(config.BASELINE_PATH).unlink(missing_ok=True)
            st.success("Baseline reset. Restart monitoring to recalibrate.")
    except Exception as e:
        st.error(f"Personalization error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Analytics
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.markdown("# 📈 Analytics & Trends")

    hist_path = Path(config.HISTORY_DIR) / config.HISTORY_FILE
    if hist_path.exists():
        hist_df = pd.read_csv(hist_path)
        if not hist_df.empty:
            st.markdown("### Daily Fatigue Trend")
            fig = px.line(hist_df.tail(100), y="fatigue_score",
                          title="Fatigue Score Over Time",
                          color_discrete_sequence=["#6366f1"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#e2e8f0")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Fatigue Level Distribution")
            if "fatigue_level" in hist_df.columns:
                dist = hist_df["fatigue_level"].value_counts().reset_index()
                dist.columns = ["Level", "Count"]
                fig2 = px.pie(dist, names="Level", values="Count",
                              color_discrete_sequence=CLASS_COLORS)
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No history data yet. Start monitoring to collect data.")

    # Show dataset distribution
    st.markdown("### Dataset Class Distribution")
    try:
        from src.load_data import load_dataset
        ds = load_dataset()
        if "fatigue_level" in ds.columns:
            dist = ds["fatigue_level"].value_counts().sort_index().reset_index()
            dist.columns = ["Level", "Count"]
            dist["Class"] = dist["Level"].map(
                {i: n for i, n in enumerate(CLASS_NAMES)}
            )
            fig3 = px.bar(dist, x="Class", y="Count",
                          color="Class", color_discrete_sequence=CLASS_COLORS,
                          title="Training Dataset Class Distribution")
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#e2e8f0", showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load dataset: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: Research Info
# ══════════════════════════════════════════════════════════════════════════════
elif page == "ℹ️ Research Info":
    st.markdown("# ℹ️ Research Contributions")

    st.markdown("""
    ## Project Title
    **Real-Time Explainable Mental Fatigue Detection Using Keyboard and Mouse Dynamics
    with Comparative Machine Learning Models**

    ## Inspired By
    > Arroyo-Morales et al., *"Monitoring Mental Fatigue through the Analysis of
    > Keyboard and Mouse Interaction Patterns"*, HAIS 2013.
    > Original paper used only **k-NN**.

    ## Our Improvements Over HAIS 2013

    | Aspect | HAIS 2013 | This Work |
    |---|---|---|
    | ML Models | k-NN only | 14 models compared |
    | Fatigue Classes | 2 (Fatigued / Not) | 5 (Normal → Critical) |
    | Features | ~8 | 40+ |
    | Explainability | None | SHAP + Permutation |
    | Real-time | No | Yes (30s windows) |
    | Personalization | No | Per-user baseline |
    | Auto model selection | No | Yes (rank score) |
    | Dashboard | No | Professional Streamlit |

    ## 14 Models Compared
    KNN · Decision Tree · Random Forest · XGBoost · LightGBM · CatBoost ·
    Extra Trees · AdaBoost · Gradient Boosting · HistGradientBoosting ·
    Logistic Regression · SVM · Naive Bayes · MLP

    ## 40+ Features Extracted
    **Keyboard:** Key press count, hold time, typing speed (WPM), error rate,
    backspace count, idle time, inter-key delay, flight time, burst duration,
    correction delay, pause duration, keystrokes/min

    **Mouse:** Velocity, acceleration, jerk, smoothness, idle time, click rate,
    double-click speed, drag distance/speed, scroll speed/frequency, path curvature,
    entropy, precision, direction changes, click accuracy, cursor distance,
    straight-line ratio, turning angles, reaction time

    **Productivity:** App switch frequency, session lengths, break duration

    ## Evaluation Metrics
    Accuracy · Precision · Recall · F1 Score · ROC AUC · Confusion Matrix ·
    Cross-Validation · Training Time · Inference Speed · Memory Usage · Model Size

    ## Tech Stack
    Python 3.10+ · XGBoost · LightGBM · CatBoost · Scikit-learn · SHAP ·
    Streamlit · Plotly · Pynput · Pandas · NumPy · Joblib
    """)

    st.markdown("---")
    st.markdown("*B.Tech CSE Final Year Major Project — Research-Grade Implementation*")
