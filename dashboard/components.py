"""
components.py
-------------
All reusable HTML/Streamlit UI components for the premium dashboard.
Every function renders one self-contained UI block.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from dashboard.styles import fatigue_color, fatigue_badge, fatigue_pulse, rec_card_cls

# ── Metadata maps ─────────────────────────────────────────────────────────────
_FM = {
    0: {"name": "Normal",           "emoji": "🟢", "icon": "✅", "short": "Normal"},
    1: {"name": "Mild Fatigue",     "emoji": "🟡", "icon": "⚠️",  "short": "Mild"},
    2: {"name": "Moderate Fatigue", "emoji": "🟠", "icon": "🔶", "short": "Moderate"},
    3: {"name": "High Fatigue",     "emoji": "🔴", "icon": "🚨", "short": "High"},
}
_RM = {
    0: ("Keep Working",           "💪", "You are alert and focused. Productivity is optimal."),
    1: ("Consider a Short Break", "☕", "Mild fatigue detected. A 2–5 min break can help."),
    2: ("Take a 10-Minute Break", "🛑", "Moderate fatigue. Rest your eyes and step away."),
    3: ("Take Immediate Rest",    "🚨", "High fatigue detected. Stop and rest immediately."),
}


# ── Header ────────────────────────────────────────────────────────────────────
def render_header(session_start: datetime, prediction_count: int, is_monitoring: bool) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    dur = datetime.now() - session_start
    h = int(dur.total_seconds() // 3600)
    m = int((dur.total_seconds() % 3600) // 60)
    s = int(dur.total_seconds() % 60)
    dur_str = f"{h:02d}:{m:02d}:{s:02d}"
    live_html = (
        '<span class="badge badge-live"><span class="pulse-dot pulse-green"></span>LIVE</span>'
        if is_monitoring else
        '<span class="badge badge-red">STOPPED</span>'
    )
    st.markdown(f"""
    <div class="app-header">
      <div>
        <div class="app-title">🧠 AI-Based Mental Fatigue Detection System</div>
        <div class="app-subtitle">Real-Time Keyboard &amp; Mouse Monitoring &nbsp;·&nbsp; XGBoost &nbsp;·&nbsp; SHAP Explainability &nbsp;·&nbsp; SQLite</div>
      </div>
      <div class="hdr-right">
        {live_html}
        <div class="hdr-stat">
          <div class="hdr-stat-label">Session</div>
          <div class="hdr-stat-value">{dur_str}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-label">Time</div>
          <div class="hdr-stat-value">{now}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-label">Predictions</div>
          <div class="hdr-stat-value">{prediction_count}</div>
        </div>
        <div class="hdr-stat">
          <div class="hdr-stat-label">User</div>
          <div class="hdr-stat-value">Local</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── KPI cards ─────────────────────────────────────────────────────────────────
def render_kpi_cards(prediction: dict | None, features: dict | None,
                     session_start: datetime) -> None:
    c1, c2, c3, c4 = st.columns(4)

    # Card 1 — Fatigue
    with c1:
        if prediction:
            lvl   = prediction.get("level", 0)
            col   = fatigue_color(lvl)
            meta  = _FM.get(lvl, _FM[0])
            conf  = prediction.get("confidence", 0)
            st.markdown(f"""
            <div class="kpi-card" style="border-top:3px solid {col};">
              <div class="kpi-label">Current Fatigue Level</div>
              <div class="kpi-value anim-val" style="color:{col};">{meta['emoji']} {meta['name']}</div>
              <div class="kpi-sub">Confidence: <b style="color:{col};">{conf:.1%}</b></div>
              <div class="kpi-icon">{meta['icon']}</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card" style="border-top:3px solid #334155;">
              <div class="kpi-label">Current Fatigue Level</div>
              <div class="skeleton" style="height:30px;margin:.5rem 0;"></div>
              <div class="kpi-sub" style="color:#475569;">Initializing…</div>
            </div>""", unsafe_allow_html=True)

    # Card 2 — Keyboard
    with c2:
        kp  = int(features.get("key_press_count", 0)) if features else 0
        wpm = features.get("typing_speed", 0.0) if features else 0.0
        er  = features.get("error_rate", 0.0) if features else 0.0
        st.markdown(f"""
        <div class="kpi-card" style="border-top:3px solid #2563EB;">
          <div class="kpi-label">⌨️ Keyboard Status</div>
          <div class="kpi-value anim-val" style="color:#60a5fa;">{kp}</div>
          <div class="kpi-sub">Keys &nbsp;·&nbsp; <b>{wpm:.1f} WPM</b> &nbsp;·&nbsp; Err: {er:.1%}</div>
          <div class="kpi-icon">⌨️</div>
          <div class="kpi-trend"><span class="badge badge-blue">ACTIVE</span></div>
        </div>""", unsafe_allow_html=True)

    # Card 3 — Mouse
    with c3:
        mc  = int(features.get("mouse_click_count", 0)) if features else 0
        spd = features.get("cursor_speed", 0.0) if features else 0.0
        dist= features.get("cursor_distance", 0.0) if features else 0.0
        st.markdown(f"""
        <div class="kpi-card" style="border-top:3px solid #8B5CF6;">
          <div class="kpi-label">🖱️ Mouse Status</div>
          <div class="kpi-value anim-val" style="color:#a78bfa;">{mc}</div>
          <div class="kpi-sub">Clicks &nbsp;·&nbsp; <b>{spd:.0f} px/s</b> &nbsp;·&nbsp; {dist:.0f}px</div>
          <div class="kpi-icon">🖱️</div>
          <div class="kpi-trend"><span class="badge badge-purple">ACTIVE</span></div>
        </div>""", unsafe_allow_html=True)

    # Card 4 — Session
    with c4:
        dur = datetime.now() - session_start
        mins = int(dur.total_seconds() // 60)
        secs = int(dur.total_seconds() % 60)
        hrs  = int(dur.total_seconds() // 3600)
        st.markdown(f"""
        <div class="kpi-card" style="border-top:3px solid #22C55E;">
          <div class="kpi-label">⏱️ Session Duration</div>
          <div class="kpi-value anim-val" style="color:#22C55E;">{hrs:02d}:{mins%60:02d}:{secs:02d}</div>
          <div class="kpi-sub">Active monitoring time</div>
          <div class="kpi-icon">⏱️</div>
          <div class="kpi-trend"><span class="badge badge-green">RUNNING</span></div>
        </div>""", unsafe_allow_html=True)


# ── Keyboard analytics ────────────────────────────────────────────────────────
def render_keyboard_analytics(features: dict | None) -> None:
    st.markdown('<div class="sec-title">⌨️ Live Keyboard Analytics</div>', unsafe_allow_html=True)
    if not features:
        st.markdown('<div class="skeleton" style="height:140px;border-radius:12px;"></div>', unsafe_allow_html=True)
        return
    rows = [
        ("Typing Speed",    f"{features.get('typing_speed',0):.1f} WPM",    "#2563EB"),
        ("Key Presses",     f"{int(features.get('key_press_count',0))}",     "#8B5CF6"),
        ("Backspaces",      f"{int(features.get('backspace_count',0))}",     "#EF4444"),
        ("Error Rate",      f"{features.get('error_rate',0):.2%}",           "#F97316"),
        ("Key Hold Time",   f"{features.get('key_hold_time',0)*1000:.0f} ms","#FACC15"),
        ("Idle Time",       f"{features.get('idle_time',0):.1f} s",          "#94A3B8"),
    ]
    cols = st.columns(3)
    for i, (label, value, color) in enumerate(rows):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="metric-tile" style="border-left-color:{color};">
              <div class="metric-tile-label">{label}</div>
              <div class="metric-tile-value anim-val" style="color:{color};">{value}</div>
            </div>""", unsafe_allow_html=True)


# ── Mouse analytics ───────────────────────────────────────────────────────────
def render_mouse_analytics(features: dict | None) -> None:
    st.markdown('<div class="sec-title">🖱️ Live Mouse Analytics</div>', unsafe_allow_html=True)
    if not features:
        st.markdown('<div class="skeleton" style="height:140px;border-radius:12px;"></div>', unsafe_allow_html=True)
        return
    rows = [
        ("Cursor Speed",   f"{features.get('cursor_speed',0):.0f} px/s",   "#8B5CF6"),
        ("Distance",       f"{features.get('cursor_distance',0):.0f} px",  "#2563EB"),
        ("Left Clicks",    f"{int(features.get('left_click',0))}",          "#22C55E"),
        ("Right Clicks",   f"{int(features.get('right_click',0))}",         "#F97316"),
        ("Double Clicks",  f"{int(features.get('double_click',0))}",        "#FACC15"),
        ("Scroll Count",   f"{int(features.get('scroll_count',0))}",        "#94A3B8"),
        ("Drag Events",    f"{int(features.get('drag_count',0))}",          "#EF4444"),
        ("Mouse Idle",     f"{features.get('idle_mouse_time',0):.1f} s",    "#475569"),
    ]
    cols = st.columns(4)
    for i, (label, value, color) in enumerate(rows):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-tile" style="border-left-color:{color};">
              <div class="metric-tile-label">{label}</div>
              <div class="metric-tile-value anim-val" style="color:{color};">{value}</div>
            </div>""", unsafe_allow_html=True)


# ── Break recommendation ──────────────────────────────────────────────────────
def render_break_recommendation(prediction: dict | None) -> None:
    if not prediction:
        st.markdown('<div class="skeleton" style="height:120px;border-radius:12px;"></div>', unsafe_allow_html=True)
        return
    lvl   = prediction.get("level", 0)
    col   = fatigue_color(lvl)
    cls   = rec_card_cls(lvl)
    title, icon, detail = _RM.get(lvl, _RM[0])
    st.markdown(f"""
    <div class="rec-card {cls}">
      <span class="rec-icon">{icon}</span>
      <div class="rec-title" style="color:{col};">{title}</div>
      <div class="rec-sub">{detail}</div>
    </div>""", unsafe_allow_html=True)


# ── System health ─────────────────────────────────────────────────────────────
def render_system_health(is_monitoring: bool, model_loaded: bool) -> None:
    st.markdown('<div class="sec-title">🔧 System Health</div>', unsafe_allow_html=True)
    services = [
        ("Keyboard Listener",  is_monitoring,               "Running"    if is_monitoring else "Stopped"),
        ("Mouse Listener",     is_monitoring,               "Running"    if is_monitoring else "Stopped"),
        ("Feature Extraction", is_monitoring,               "Active"     if is_monitoring else "Idle"),
        ("XGBoost Model",      model_loaded,                "Loaded"     if model_loaded  else "Not Loaded"),
        ("SHAP Engine",        model_loaded,                "Ready"      if model_loaded  else "Unavailable"),
        ("Prediction Engine",  is_monitoring and model_loaded, "Running" if (is_monitoring and model_loaded) else "Idle"),
        ("Database",           True,                        "Healthy"),
    ]
    html = '<div class="card" style="padding:.75rem 1rem;">'
    for name, ok, status in services:
        dot = "h-ok" if ok else "h-err"
        sc  = "#22C55E" if ok else "#EF4444"
        html += f"""
        <div class="health-row">
          <div class="health-name"><span class="health-dot {dot}"></span>{name}</div>
          <span class="health-status" style="color:{sc};">{status}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Privacy panel ─────────────────────────────────────────────────────────────
def render_privacy_panel() -> None:
    st.markdown('<div class="sec-title">🔒 Privacy &amp; Security</div>', unsafe_allow_html=True)
    items = [
        ("No Webcam or Camera Access",    "Camera data is never captured or accessed."),
        ("No Microphone Recording",       "Audio input is completely disabled."),
        ("No Screenshot Capture",         "Screen content is never recorded."),
        ("No Password or Text Storage",   "Keystrokes are counted, never logged."),
        ("No Cloud Data Transmission",    "All data stays on your local machine."),
        ("Behavior Statistics Only",      "Only numeric aggregates are stored."),
        ("All Data Stored Locally",       "SQLite database on your device only."),
    ]
    html = '<div class="card" style="padding:.75rem 1rem;">'
    for title, desc in items:
        html += f"""
        <div class="priv-item">
          <span class="priv-check">✅</span>
          <div>
            <div style="font-weight:600;font-size:.82rem;">{title}</div>
            <div style="font-size:.7rem;color:#64748B;">{desc}</div>
          </div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Baseline comparison table ─────────────────────────────────────────────────
def render_baseline_table(deltas: dict, features: dict, baseline: dict) -> None:
    st.markdown('<div class="sec-title">👤 Personalized Baseline Comparison</div>', unsafe_allow_html=True)
    if not deltas:
        st.markdown("""
        <div class="card" style="padding:.75rem 1rem;color:#64748B;font-size:.82rem;">
          ⏳ Building your personal baseline… needs a few more prediction windows.
        </div>""", unsafe_allow_html=True)
        return
    _LABELS = {
        "typing_speed":      "Typing Speed",
        "key_press_count":   "Key Presses",
        "cursor_speed":      "Cursor Speed",
        "mouse_click_count": "Mouse Clicks",
        "idle_time":         "Keyboard Idle",
        "idle_mouse_time":   "Mouse Idle",
        "backspace_count":   "Backspaces",
    }
    rows_html = ""
    for key, delta in deltas.items():
        label   = _LABELS.get(key, key.replace("_"," ").title())
        current = features.get(key, 0)
        base    = baseline.get(key, 0)
        if delta > 2:
            arrow, cls = "▲", "delta-up"
        elif delta < -2:
            arrow, cls = "▼", "delta-down"
        else:
            arrow, cls = "●", "delta-flat"
        rows_html += f"""
        <tr>
          <td style="color:#F8FAFC;font-weight:500;">{label}</td>
          <td style="color:#60a5fa;font-weight:600;">{current:.1f}</td>
          <td style="color:#94A3B8;">{base:.1f}</td>
          <td class="{cls}">{arrow} {delta:+.1f}%</td>
        </tr>"""
    st.markdown(f"""
    <div class="card" style="padding:.75rem 1rem;">
      <table class="bl-table">
        <thead><tr><th>Feature</th><th>Current</th><th>Baseline</th><th>Delta</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


# ── Session statistics ────────────────────────────────────────────────────────
def render_session_stats(session_start: datetime, prediction_count: int,
                         history: list, break_count: int = 0) -> None:
    st.markdown('<div class="sec-title">📊 Session Statistics</div>', unsafe_allow_html=True)
    dur  = datetime.now() - session_start
    avg_f = sum(h.get("level",0) for h in history) / max(len(history),1)
    max_f = max((h.get("level",0) for h in history), default=0)
    avg_c = sum(h.get("confidence",0) for h in history) / max(len(history),1)
    prod  = max(0, 100 - int(avg_f * 35))
    stats = [
        ("⏱️ Monitoring Time",  f"{int(dur.total_seconds()//60)}m {int(dur.total_seconds()%60)}s"),
        ("🔮 Predictions",      str(prediction_count)),
        ("📊 Avg Fatigue",      f"{avg_f:.2f}"),
        ("📈 Max Fatigue",      str(max_f)),
        ("🎯 Avg Confidence",   f"{avg_c:.1%}"),
        ("☕ Break Count",      str(break_count)),
        ("⚡ Productivity",     f"{prod}%"),
    ]
    cols = st.columns(4)
    for i, (label, value) in enumerate(stats):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-tile" style="border-left-color:#2563EB;">
              <div class="metric-tile-label">{label}</div>
              <div class="metric-tile-value">{value}</div>
            </div>""", unsafe_allow_html=True)


# ── Live event monitor ────────────────────────────────────────────────────────
def render_live_event_table(events: list) -> None:
    st.markdown('<div class="sec-title">📡 Live Event Monitor</div>', unsafe_allow_html=True)
    if not events:
        st.markdown('<div class="card" style="color:#64748B;font-size:.82rem;padding:.75rem 1rem;">Waiting for events…</div>', unsafe_allow_html=True)
        return
    rows_html = ""
    for ev in reversed(events[-25:]):
        ts  = ev.get("timestamp","")
        ts  = ts.strftime("%H:%M:%S") if hasattr(ts,"strftime") else str(ts)
        kp  = int(ev.get("key_press_count",0))
        mc  = int(ev.get("mouse_click_count",0))
        spd = ev.get("cursor_speed",0)
        lvl = ev.get("level",0)
        col = fatigue_color(lvl)
        nm  = {0:"Normal",1:"Moderate",2:"High"}.get(lvl,"—")
        rows_html += f"""
        <tr>
          <td class="evt-time">{ts}</td>
          <td style="color:#60a5fa;">{kp} keys</td>
          <td style="color:#a78bfa;">{mc} clicks</td>
          <td style="color:#94A3B8;">{spd:.0f} px/s</td>
          <td style="color:{col};font-weight:700;">{nm}</td>
        </tr>"""
    st.markdown(f"""
    <div class="card" style="padding:.75rem 1rem;max-height:230px;overflow-y:auto;">
      <table class="evt-table">
        <thead><tr><th>Time</th><th>Keyboard</th><th>Mouse</th><th>Speed</th><th>Fatigue</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


# ── History table ─────────────────────────────────────────────────────────────
def render_history_table(records: list) -> None:
    st.markdown('<div class="sec-title">📋 Fatigue History</div>', unsafe_allow_html=True)
    if not records:
        st.info("No history yet. Start monitoring to populate this table.")
        return
    df = pd.DataFrame(records)
    cols_needed = ["timestamp","fatigue_level","fatigue_name","confidence","recommendation"]
    for c in cols_needed:
        if c not in df.columns:
            df[c] = ""
    df = df[cols_needed].copy()
    df.columns = ["Timestamp","Level","Fatigue","Confidence","Recommendation"]
    df["Confidence"] = df["Confidence"].apply(lambda x: f"{float(x):.1%}" if x else "—")

    sc, se = st.columns([3,1])
    with sc:
        search = st.text_input("Search", placeholder="Filter by fatigue name…",
                               label_visibility="collapsed", key="hist_search")
    with se:
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ CSV", csv, "fatigue_history.csv", "text/csv",
                           use_container_width=True)
    if search:
        df = df[df["Fatigue"].str.contains(search, case=False, na=False)]
    st.dataframe(df, use_container_width=True, height=340,
                 column_config={"Level": st.column_config.NumberColumn(format="%d")})


# ── Reports panel ─────────────────────────────────────────────────────────────
def render_reports_panel(history: list, db_records: list) -> None:
    st.markdown('<div class="sec-title">📄 Reports &amp; Export</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    # Session history CSV
    with c1:
        if history:
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False).encode()
            st.download_button("⬇️ Session CSV", csv, "session_history.csv",
                               "text/csv", use_container_width=True)
        else:
            st.button("⬇️ Session CSV", disabled=True, use_container_width=True)
    # Full DB CSV
    with c2:
        if db_records:
            df2 = pd.DataFrame(db_records)
            csv2 = df2.to_csv(index=False).encode()
            st.download_button("⬇️ Full Report CSV", csv2, "fatigue_report.csv",
                               "text/csv", use_container_width=True)
        else:
            st.button("⬇️ Full Report CSV", disabled=True, use_container_width=True)
    # Excel
    with c3:
        try:
            import io
            if db_records:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    pd.DataFrame(db_records).to_excel(w, index=False, sheet_name="Predictions")
                st.download_button("⬇️ Export Excel", buf.getvalue(),
                                   "fatigue_report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            else:
                st.button("⬇️ Export Excel", disabled=True, use_container_width=True)
        except ImportError:
            st.caption("Install `openpyxl` for Excel export.")


# ── Pipeline flow diagram ─────────────────────────────────────────────────────
def render_pipeline_diagram(active_step: int = -1) -> None:
    steps = [
        "Application Starts",
        "Keyboard Listener Starts",
        "Mouse Listener Starts",
        "Collect Events",
        "Extract Features",
        "Generate Feature Vector",
        "Load XGBoost Model",
        "Predict Fatigue Level",
        "Calculate Confidence",
        "Generate SHAP Values",
        "Compare with Baseline",
        "Generate Recommendation",
        "Store to Database",
        "Update Dashboard",
        "Repeat Forever ↺",
    ]
    icons = ["🚀","⌨️","🖱️","📥","⚙️","📊","🤖","🔮","🎯","🔍","👤","💡","🗄️","🖥️","🔄"]
    html = '<div class="pipeline-wrap">'
    for i, (step, icon) in enumerate(zip(steps, icons)):
        cls = "pipeline-step active" if i == active_step else "pipeline-step"
        html += f'<div class="{cls}">{icon} {step}</div>'
        if i < len(steps) - 1:
            html += '<div class="pipeline-arrow">↓</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── Model info card ───────────────────────────────────────────────────────────
def render_model_info(predictor, eval_metrics: dict | None = None) -> None:
    st.markdown('<div class="sec-title">🤖 XGBoost Model Information</div>', unsafe_allow_html=True)
    if not predictor:
        st.info("Model not loaded yet.")
        return
    info = predictor.get_model_info()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card" style="padding:.75rem 1rem;">', unsafe_allow_html=True)
        st.markdown("**Model Parameters**")
        for k, v in info.items():
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:.3rem 0;'
                f'border-bottom:1px solid rgba(255,255,255,.04);font-size:.8rem;">'
                f'<span style="color:#94A3B8;">{k}</span>'
                f'<span style="color:#60a5fa;font-weight:600;">{v}</span></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        if eval_metrics:
            st.markdown('<div class="card" style="padding:.75rem 1rem;">', unsafe_allow_html=True)
            st.markdown("**Evaluation Metrics**")
            metrics = [
                ("Accuracy",  f"{eval_metrics.get('accuracy',0):.4f}"),
                ("Precision", f"{eval_metrics.get('precision',0):.4f}"),
                ("Recall",    f"{eval_metrics.get('recall',0):.4f}"),
                ("F1 Score",  f"{eval_metrics.get('f1',0):.4f}"),
            ]
            for label, val in metrics:
                st.markdown(
                    f'<div style="display:flex;justify-content:space-between;padding:.3rem 0;'
                    f'border-bottom:1px solid rgba(255,255,255,.04);font-size:.8rem;">'
                    f'<span style="color:#94A3B8;">{label}</span>'
                    f'<span style="color:#22C55E;font-weight:700;">{val}</span></div>',
                    unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="padding:.75rem 1rem;color:#64748B;font-size:.82rem;">
              Run <code>python src/evaluate.py</code> to generate evaluation metrics.
            </div>""", unsafe_allow_html=True)
