"""
ui/pages/model.py
-----------------
Model page — ensemble info, metrics, confusion matrix, feature importance, pipeline.
"""

import streamlit as st
import joblib
import numpy as np
from pathlib import Path
from ui.charts import feature_importance, confusion_matrix_chart

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _load_eval_metrics():
    try:
        saved = joblib.load(str(PROJECT_ROOT / "models" / "xgboost_model.pkl"))
        if isinstance(saved, dict):
            return saved.get("metrics", None), saved.get("feature_names", [])
        return None, []
    except Exception:
        return None, []


def _load_all_model_metrics():
    """Load metrics from model pkl files; fall back to model_comparison.csv."""
    models_dir = PROJECT_ROOT / "models"
    # Try CSV first (has all columns after retrain)
    csv_path = models_dir / "model_comparison.csv"
    if csv_path.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            cols = ["Model", "Accuracy", "Balanced_Acc", "Macro_F1", "F1_Score", "Precision", "Recall"]
            present = [c for c in cols if c in df.columns]
            df = df[present].rename(columns={"Balanced_Acc": "Balanced Acc", "Macro_F1": "Macro F1", "F1_Score": "Weighted F1"})
            return df.to_dict("records")
        except Exception:
            pass
    # Fallback: read individual pkl files
    results = []
    for pkl in sorted(models_dir.glob("*.pkl")):
        try:
            saved = joblib.load(str(pkl))
            if not isinstance(saved, dict):
                continue
            m = saved.get("metrics", {})
            if not m:
                continue
            results.append({
                "Model":        pkl.stem,
                "Accuracy":     m.get("accuracy", 0),
                "Balanced Acc": m.get("balanced_accuracy", m.get("accuracy", 0)),
                "Macro F1":     m.get("macro_f1", m.get("f1", 0)),
                "Weighted F1":  m.get("weighted_f1", m.get("f1", 0)),
                "Precision":    m.get("precision", 0),
                "Recall":       m.get("recall", 0),
            })
        except Exception:
            continue
    return results


def _ensemble_section():
    """Show ensemble composition and per-model weights."""
    st.markdown('<div class="sec">🤝 Ensemble Composition</div>', unsafe_allow_html=True)
    _WEIGHTS = {"XGBoost": 0.50, "LightGBM": 0.30, "CatBoost": 0.20}
    _COLORS  = {"XGBoost": "#f59e0b", "LightGBM": "#22c55e", "CatBoost": "#6366f1"}
    html = '<div class="card" style="padding:.8rem 1rem;">'
    for name, w in _WEIGHTS.items():
        col  = _COLORS[name]
        path = PROJECT_ROOT / "models" / f"{name}.pkl"
        status = "✅ Loaded" if path.exists() else "❌ Missing"
        html += f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:.4rem 0;border-bottom:1px solid rgba(255,255,255,.05);">
          <span style="color:#F8FAFC;font-weight:600;font-size:.82rem;">{name}</span>
          <span style="color:{col};font-size:.8rem;">{int(w*100)}% weight</span>
          <span style="font-size:.75rem;color:#94A3B8;">{status}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_model_page(predictor):
    st.markdown('<div class="sec">🤖 Model Overview</div>', unsafe_allow_html=True)

    if not predictor:
        st.error("Model not loaded. Run `python src/train_model.py` first.")
        return

    info = predictor.get_model_info()
    _, feature_names = _load_eval_metrics()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="sec">⚙️ XGBoost Parameters</div>', unsafe_allow_html=True)
        st.markdown('<div class="card" style="padding:.8rem 1rem;">', unsafe_allow_html=True)
        for k, v in info.items():
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;
                        padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.04);
                        font-size:.8rem;">
              <span style="color:#94A3B8;">{k}</span>
              <span style="color:#60a5fa;font-weight:600;">{v}</span>
            </div>""", unsafe_allow_html=True)
        model = predictor.model
        if hasattr(model, "get_params"):
            for k, v in list(model.get_params().items())[:10]:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                            padding:.3rem 0;border-bottom:1px solid rgba(255,255,255,.04);
                            font-size:.8rem;">
                  <span style="color:#94A3B8;">{k}</span>
                  <span style="color:#a78bfa;font-weight:600;">{v}</span>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        _ensemble_section()

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Model Comparison Table ──
    all_metrics = _load_all_model_metrics()
    if all_metrics:
        import pandas as pd
        st.markdown('<div class="sec">📊 Model Comparison</div>', unsafe_allow_html=True)
        df = pd.DataFrame(all_metrics).sort_values("Balanced Acc", ascending=False)
        # Format as percentage strings for display
        for col in ["Accuracy", "Balanced Acc", "Macro F1", "Weighted F1", "Precision", "Recall"]:
            df[col] = df[col].apply(lambda x: f"{x:.1%}" if isinstance(x, float) else x)
        st.dataframe(
            df.set_index("Model"),
            use_container_width=True,
        )
    else:
        st.markdown("""
        <div class="card" style="padding:.8rem 1rem;">
          <div style="font-size:.78rem;color:#64748B;">
            Run <code style="color:#60a5fa;">python main.py</code> to train all models
            and populate the comparison table.
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Feature Importance ──
    model = predictor.model
    fn    = feature_names or []
    if hasattr(model, "feature_importances_") and not fn:
        from src.feature_extraction import FEATURE_ORDER
        fn = FEATURE_ORDER
    if hasattr(model, "feature_importances_") and fn:
        st.markdown('<div class="sec">📈 Feature Importance</div>', unsafe_allow_html=True)
        imp = dict(zip(fn, model.feature_importances_))
        st.plotly_chart(feature_importance(imp), use_container_width=True,
                        config={"displayModeBar": False})

    cm_path = PROJECT_ROOT / "confusion_matrix.png"
    fi_path = PROJECT_ROOT / "feature_importance.png"
    if cm_path.exists() or fi_path.exists():
        c1, c2 = st.columns(2)
        if cm_path.exists():
            with c1:
                st.image(str(cm_path), caption="Confusion Matrix", use_container_width=True)
        if fi_path.exists():
            with c2:
                st.image(str(fi_path), caption="Feature Importance", use_container_width=True)

    # ── Pipeline ──
    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec">🔄 Real-Time Pipeline</div>', unsafe_allow_html=True)
    steps = [
        ("🚀","Application Starts"),("⌨️","Keyboard Listener"),("🖱️","Mouse Listener"),
        ("📥","Collect Events"),("⚙️","Extract Features"),("⏳","Temporal Buffer"),
        ("📊","Feature Vector"),("🤝","Ensemble Predict"),("🎯","Confidence Score"),
        ("🔍","SHAP Values"),("👤","Baseline Compare"),("💡","Recommendation"),
        ("🗄️","Store to DB"),("🖥️","Update Dashboard"),("🔄","Repeat Forever ↺"),
    ]
    html = '<div class="pipe">'
    for icon, step in steps:
        html += f'<div class="pstep">{icon} {step}</div>'
        if step != "Repeat Forever ↺":
            html += '<div class="parr">↓</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
