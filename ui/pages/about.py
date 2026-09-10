"""
ui/pages/about.py
-----------------
About page — project info, tech stack, team.
"""

import streamlit as st


def render_about_page():
    st.markdown('<div class="sec">ℹ️ About NeuroSense AI</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("""
        <div class="card card-top-blue" style="margin-bottom:.75rem;">
          <div style="font-size:1.1rem;font-weight:800;margin-bottom:.5rem;
                      background:linear-gradient(135deg,#93c5fd,#c4b5fd);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            AI-Based Mental Fatigue Detection System
          </div>
          <div style="font-size:.8rem;color:#94A3B8;line-height:1.8;">
            A privacy-preserving, real-time cognitive fatigue monitoring system
            that uses only keyboard and mouse behavioral signals — no webcam,
            EEG, wearables, or microphone required.<br><br>
            The system passively monitors your interaction patterns and uses
            a trained XGBoost classifier to predict your current fatigue level,
            providing actionable break recommendations.
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="card" style="margin-bottom:.75rem;">
          <div style="font-weight:700;font-size:.85rem;margin-bottom:.6rem;color:#F8FAFC;">
            🎯 Fatigue Classes
          </div>
          <div style="font-size:.8rem;line-height:2.2;">
            <span style="color:#22C55E;font-weight:700;">🟢 Normal (0)</span>
            — Alert and focused, optimal productivity<br>
            <span style="color:#FACC15;font-weight:700;">🟡 Mild Fatigue (1)</span>
            — Early signs, consider a short break<br>
            <span style="color:#F97316;font-weight:700;">🟠 Moderate Fatigue (2)</span>
            — Noticeable fatigue, take a 10-min break<br>
            <span style="color:#EF4444;font-weight:700;">🔴 High Fatigue (3)</span>
            — Severe fatigue, rest immediately
          </div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card" style="margin-bottom:.75rem;">
          <div style="font-weight:700;font-size:.85rem;margin-bottom:.6rem;color:#F8FAFC;">
            🛠️ Tech Stack
          </div>
          <div style="font-size:.78rem;line-height:2.2;color:#94A3B8;">
            <b style="color:#60a5fa;">ML Model</b> — XGBoost Classifier<br>
            <b style="color:#a78bfa;">Explainability</b> — SHAP<br>
            <b style="color:#22C55E;">Frontend</b> — Streamlit + Plotly<br>
            <b style="color:#FACC15;">Monitoring</b> — pynput<br>
            <b style="color:#F97316;">Database</b> — SQLite<br>
            <b style="color:#EF4444;">Language</b> — Python 3.10+<br>
            <b style="color:#94A3B8;">Config</b> — python-dotenv
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
          <div style="font-weight:700;font-size:.85rem;margin-bottom:.6rem;color:#F8FAFC;">
            📊 Features Tracked
          </div>
          <div style="font-size:.75rem;color:#94A3B8;line-height:1.9;">
            <b style="color:#60a5fa;">Keyboard:</b> Key presses, hold time,
            typing speed, error rate, backspaces, idle time<br>
            <b style="color:#a78bfa;">Mouse:</b> Clicks (L/R/double), scroll,
            cursor speed, distance, drag, idle time
          </div>
        </div>""", unsafe_allow_html=True)

    # Commands
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec">🚀 Quick Start</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card" style="padding:.8rem 1.2rem;">
      <div style="font-size:.78rem;color:#94A3B8;line-height:2.4;font-family:monospace;">
        <span style="color:#64748B;"># Train the model</span><br>
        <span style="color:#22C55E;">python src/train_model.py</span><br>
        <span style="color:#64748B;"># Evaluate</span><br>
        <span style="color:#22C55E;">python src/evaluate.py</span><br>
        <span style="color:#64748B;"># Launch enterprise dashboard</span><br>
        <span style="color:#60a5fa;">streamlit run enterprise_app.py</span>
      </div>
    </div>""", unsafe_allow_html=True)
