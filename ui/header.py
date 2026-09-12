"""
ui/header.py
------------
Premium dashboard header with live status, time, session info.
"""

import streamlit as st
from datetime import datetime


def render_header(session_start: datetime, prediction_count: int, is_monitoring: bool):
    now = datetime.now().strftime("%H:%M:%S")
    dur = datetime.now() - session_start
    h = int(dur.total_seconds() // 3600)
    m = int((dur.total_seconds() % 3600) // 60)
    s = int(dur.total_seconds() % 60)
    dur_str = f"{h:02d}:{m:02d}:{s:02d}"

    live_badge = (
        '<span class="badge b-live"><span class="dot dot-g" style="margin-right:5px;"></span>LIVE</span>'
        if is_monitoring else
        '<span class="badge b-red">STOPPED</span>'
    )

    st.markdown(f"""
    <div class="hdr">
      <div>
        <div class="hdr-title">🧠 Mental Fatigue Detection System</div>
        <div class="hdr-sub">Real-Time Keyboard &amp; Mouse Monitoring &nbsp;·&nbsp;
          XGBoost Classifier &nbsp;·&nbsp; SHAP Explainability &nbsp;·&nbsp; SQLite</div>
      </div>
      <div class="hdr-right">
        {live_badge}
        <div class="hdr-stat">
          <div class="hdr-stat-lbl">Session</div>
          <div class="hdr-stat-val">{dur_str}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-lbl">Time</div>
          <div class="hdr-stat-val">{now}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-lbl">Predictions</div>
          <div class="hdr-stat-val">{prediction_count}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-lbl">User</div>
          <div class="hdr-stat-val">Local</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
