"""
ui/pages/dashboard.py
---------------------
Main dashboard page — KPI cards, live analytics, trend, SHAP, baseline, health.
"""

import streamlit as st
from datetime import datetime
import plotly.graph_objects as go

from ui.styles import fc, fb, fd, rc, FATIGUE_META, REC_META
from ui.charts import (
    fatigue_trend, confidence_gauge, probability_donut,
    shap_bar, feature_importance, activity_timeline,
    keyboard_bar, mouse_bar, radar_chart,
)


def _kpi_cards(prediction, features, session_start):
    c1, c2, c3, c4 = st.columns(4)

    # Card 1 — Fatigue
    with c1:
        if prediction:
            lvl  = prediction.get("level", 0)
            col  = fc(lvl)
            meta = FATIGUE_META.get(lvl, FATIGUE_META[0])
            conf = prediction.get("confidence", 0)
            st.markdown(f"""
            <div class="kpi" style="border-top:3px solid {col};">
              <div class="kpi-lbl">Current Fatigue Level</div>
              <div class="kpi-val anim" style="color:{col};">{meta['emoji']} {meta['name']}</div>
              <div class="kpi-sub">Confidence: <b style="color:{col};">{conf:.1f}%</b></div>
              <div class="kpi-bg-icon">{meta['icon']}</div>
              <div class="kpi-badge"><span class="badge {fb(lvl)}">{meta['short']}</span></div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi" style="border-top:3px solid #1e3a5f;">
              <div class="kpi-lbl">Current Fatigue Level</div>
              <div class="skel" style="height:32px;margin:.5rem 0;"></div>
              <div class="kpi-sub" style="color:#475569;">Initializing…</div>
            </div>""", unsafe_allow_html=True)

    # Card 2 — Keyboard
    with c2:
        kp  = int(features.get("key_press_count", 0)) if features else 0
        wpm = features.get("typing_speed", 0.0) if features else 0.0
        er  = features.get("error_rate", 0.0) if features else 0.0
        st.markdown(f"""
        <div class="kpi" style="border-top:3px solid #2563EB;">
          <div class="kpi-lbl">⌨️ Keyboard Status</div>
          <div class="kpi-val anim" style="color:#60a5fa;">{kp}</div>
          <div class="kpi-sub">Keys &nbsp;·&nbsp; <b>{wpm:.1f} WPM</b> &nbsp;·&nbsp; Err {er:.1%}</div>
          <div class="kpi-bg-icon">⌨️</div>
          <div class="kpi-badge"><span class="badge b-blue">ACTIVE</span></div>
        </div>""", unsafe_allow_html=True)

    # Card 3 — Mouse
    with c3:
        mc   = int(features.get("mouse_click_count", 0)) if features else 0
        spd  = features.get("cursor_speed", 0.0) if features else 0.0
        dist = features.get("cursor_distance", 0.0) if features else 0.0
        st.markdown(f"""
        <div class="kpi" style="border-top:3px solid #8B5CF6;">
          <div class="kpi-lbl">🖱️ Mouse Status</div>
          <div class="kpi-val anim" style="color:#a78bfa;">{mc}</div>
          <div class="kpi-sub">Clicks &nbsp;·&nbsp; <b>{spd:.0f} px/s</b> &nbsp;·&nbsp; {dist:.0f}px</div>
          <div class="kpi-bg-icon">🖱️</div>
          <div class="kpi-badge"><span class="badge b-purp">ACTIVE</span></div>
        </div>""", unsafe_allow_html=True)

    # Card 4 — Session
    with c4:
        dur  = datetime.now() - session_start
        h    = int(dur.total_seconds() // 3600)
        m    = int((dur.total_seconds() % 3600) // 60)
        s    = int(dur.total_seconds() % 60)
        st.markdown(f"""
        <div class="kpi" style="border-top:3px solid #22C55E;">
          <div class="kpi-lbl">⏱️ Session Duration</div>
          <div class="kpi-val anim" style="color:#22C55E;">{h:02d}:{m:02d}:{s:02d}</div>
          <div class="kpi-sub">Active monitoring time</div>
          <div class="kpi-bg-icon">⏱️</div>
          <div class="kpi-badge"><span class="badge b-green">RUNNING</span></div>
        </div>""", unsafe_allow_html=True)


def _keyboard_panel(features):
    st.markdown('<div class="sec">⌨️ Live Keyboard Analytics</div>', unsafe_allow_html=True)
    if not features:
        st.markdown('<div class="skel" style="height:130px;border-radius:12px;"></div>',
                    unsafe_allow_html=True)
        return
    rows = [
        ("Typing Speed",  f"{features.get('typing_speed',0):.1f} WPM",     "#2563EB"),
        ("Key Presses",   f"{int(features.get('key_press_count',0))}",      "#8B5CF6"),
        ("Backspaces",    f"{int(features.get('backspace_count',0))}",      "#EF4444"),
        ("Error Rate",    f"{features.get('error_rate',0):.2%}",            "#F97316"),
        ("Hold Time",     f"{features.get('key_hold_time',0)*1000:.0f} ms", "#FACC15"),
        ("Idle Time",     f"{features.get('idle_time',0):.1f} s",           "#94A3B8"),
    ]
    cols = st.columns(3)
    for i, (lbl, val, color) in enumerate(rows):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="mtile" style="border-left-color:{color};">
              <div class="mtile-lbl">{lbl}</div>
              <div class="mtile-val anim" style="color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)


def _mouse_panel(features):
    st.markdown('<div class="sec">🖱️ Live Mouse Analytics</div>', unsafe_allow_html=True)
    if not features:
        st.markdown('<div class="skel" style="height:130px;border-radius:12px;"></div>',
                    unsafe_allow_html=True)
        return
    rows = [
        ("Cursor Speed",  f"{features.get('cursor_speed',0):.0f} px/s",  "#8B5CF6"),
        ("Distance",      f"{features.get('cursor_distance',0):.0f} px", "#2563EB"),
        ("Left Clicks",   f"{int(features.get('left_click',0))}",        "#22C55E"),
        ("Right Clicks",  f"{int(features.get('right_click',0))}",       "#F97316"),
        ("Double Clicks", f"{int(features.get('double_click',0))}",      "#FACC15"),
        ("Scroll Count",  f"{int(features.get('scroll_count',0))}",      "#94A3B8"),
        ("Drag Events",   f"{int(features.get('drag_count',0))}",        "#EF4444"),
        ("Mouse Idle",    f"{features.get('idle_mouse_time',0):.1f} s",  "#475569"),
    ]
    cols = st.columns(4)
    for i, (lbl, val, color) in enumerate(rows):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="mtile" style="border-left-color:{color};">
              <div class="mtile-lbl">{lbl}</div>
              <div class="mtile-val anim" style="color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)


def _recommendation(prediction):
    if not prediction:
        st.markdown('<div class="skel" style="height:120px;border-radius:16px;"></div>',
                    unsafe_allow_html=True)
        return
    lvl   = prediction.get("level", 0)
    col   = fc(lvl)
    cls   = rc(lvl)
    title, icon, desc = REC_META.get(lvl, REC_META[0])
    st.markdown(f"""
    <div class="rec {cls}">
      <span class="rec-icon">{icon}</span>
      <div class="rec-title" style="color:{col};">{title}</div>
      <div class="rec-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)


def _system_health(is_monitoring, model_loaded):
    st.markdown('<div class="sec">🔧 System Health</div>', unsafe_allow_html=True)
    services = [
        ("Keyboard Listener",  is_monitoring,                "Running"    if is_monitoring else "Stopped"),
        ("Mouse Listener",     is_monitoring,                "Running"    if is_monitoring else "Stopped"),
        ("Feature Extraction", is_monitoring,                "Active"     if is_monitoring else "Idle"),
        ("XGBoost Model",      model_loaded,                 "Loaded"     if model_loaded  else "Not Loaded"),
        ("SHAP Engine",        model_loaded,                 "Ready"      if model_loaded  else "Unavailable"),
        ("Prediction Engine",  is_monitoring and model_loaded,"Running"   if (is_monitoring and model_loaded) else "Idle"),
        ("Database",           True,                         "Healthy"),
    ]
    html = '<div class="card" style="padding:.7rem 1rem;">'
    for name, ok, status in services:
        dot = "hok" if ok else "herr"
        sc  = "#22C55E" if ok else "#EF4444"
        html += f"""
        <div class="hrow">
          <div class="hrow-name"><span class="hdot {dot}"></span>{name}</div>
          <span class="hstat" style="color:{sc};">{status}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _baseline_table(baseline_tracker, features):
    st.markdown('<div class="sec">👤 Personalized Baseline</div>', unsafe_allow_html=True)
    deltas  = baseline_tracker.get_deltas(features) if features else {}
    baseline = baseline_tracker.get_baseline()
    if not deltas:
        st.markdown("""
        <div class="card" style="padding:.7rem 1rem;color:#64748B;font-size:.8rem;">
          ⏳ Building baseline… needs a few more prediction windows.
        </div>""", unsafe_allow_html=True)
        return
    _LABELS = {
        "typing_speed":"Typing Speed","key_press_count":"Key Presses",
        "cursor_speed":"Cursor Speed","mouse_click_count":"Mouse Clicks",
        "idle_time":"Keyboard Idle","idle_mouse_time":"Mouse Idle",
        "backspace_count":"Backspaces",
    }
    rows = ""
    for key, delta in deltas.items():
        lbl  = _LABELS.get(key, key.replace("_"," ").title())
        curr = features.get(key, 0) if features else 0
        base = baseline.get(key, 0)
        if delta > 2:
            arrow, cls = "▲", "dup"
        elif delta < -2:
            arrow, cls = "▼", "ddown"
        else:
            arrow, cls = "●", "dflat"
        rows += f"""
        <tr>
          <td style="color:#F8FAFC;font-weight:500;">{lbl}</td>
          <td style="color:#60a5fa;font-weight:600;">{curr:.1f}</td>
          <td style="color:#94A3B8;">{base:.1f}</td>
          <td class="{cls}">{arrow} {delta:+.1f}%</td>
        </tr>"""
    st.markdown(f"""
    <div class="card" style="padding:.7rem 1rem;">
      <table class="bltbl">
        <thead><tr><th>Feature</th><th>Current</th><th>Baseline</th><th>Delta</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


def _session_stats(session_start, prediction_count, history, break_count):
    st.markdown('<div class="sec">📊 Session Statistics</div>', unsafe_allow_html=True)
    dur  = datetime.now() - session_start
    avg_f = sum(h.get("level",0) for h in history) / max(len(history),1)
    max_f = max((h.get("level",0) for h in history), default=0)
    avg_c = sum(h.get("confidence",0) for h in history) / max(len(history),1)
    prod  = max(0, 100 - int(avg_f * 30))
    stats = [
        ("⏱️ Monitoring",  f"{int(dur.total_seconds()//60)}m {int(dur.total_seconds()%60)}s"),
        ("🔮 Predictions", str(prediction_count)),
        ("📊 Avg Fatigue", f"{avg_f:.2f}"),
        ("📈 Max Fatigue", str(max_f)),
        ("🎯 Avg Conf",    f"{avg_c:.1f}%"),
        ("☕ Breaks",      str(break_count)),
        ("⚡ Productivity",f"{prod}%"),
    ]
    cols = st.columns(4)
    for i, (lbl, val) in enumerate(stats):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="mtile" style="border-left-color:#2563EB;">
              <div class="mtile-lbl">{lbl}</div>
              <div class="mtile-val">{val}</div>
            </div>""", unsafe_allow_html=True)


def _live_events(events):
    st.markdown('<div class="sec">📡 Live Event Monitor</div>', unsafe_allow_html=True)
    if not events:
        st.markdown('<div class="card" style="color:#64748B;font-size:.8rem;padding:.7rem 1rem;">Waiting for events…</div>',
                    unsafe_allow_html=True)
        return
    rows = ""
    for ev in reversed(events[-20:]):
        ts  = ev.get("timestamp","")
        ts  = ts.strftime("%H:%M:%S") if hasattr(ts,"strftime") else str(ts)
        kp  = int(ev.get("key_press_count",0))
        mc  = int(ev.get("mouse_click_count",0))
        spd = ev.get("cursor_speed",0)
        lvl = ev.get("level",0)
        col = fc(lvl)
        nm  = {0:"Normal",1:"Mild",2:"Moderate",3:"High"}.get(lvl,"—")
        rows += f"""
        <tr>
          <td class="etime">{ts}</td>
          <td style="color:#60a5fa;">{kp} keys</td>
          <td style="color:#a78bfa;">{mc} clicks</td>
          <td style="color:#94A3B8;">{spd:.0f} px/s</td>
          <td style="color:{col};font-weight:700;">{nm}</td>
        </tr>"""
    st.markdown(f"""
    <div class="card" style="padding:.7rem 1rem;max-height:220px;overflow-y:auto;">
      <table class="evttbl">
        <thead><tr><th>Time</th><th>Keyboard</th><th>Mouse</th><th>Speed</th><th>Fatigue</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


def _ensemble_indicator(prediction):
    """Show which models contributed to the current prediction."""
    if not prediction:
        return
    models_used = prediction.get("models_used")
    per_model   = prediction.get("per_model_proba")
    if not models_used or not per_model:
        return
    st.markdown('<div class="sec">🤝 Ensemble Breakdown</div>', unsafe_allow_html=True)
    _W = {"XGBoost": 0.50, "LightGBM": 0.30, "CatBoost": 0.20}
    _C = {"XGBoost": "#f59e0b", "LightGBM": "#22c55e", "CatBoost": "#6366f1"}
    html = '<div class="card" style="padding:.7rem 1rem;">'
    for name in models_used:
        w    = _W.get(name, 0.25)
        col  = _C.get(name, "#60a5fa")
        proba = per_model.get(name, [])
        top_p = max(proba) if proba else 0
        html += f"""
        <div style="margin-bottom:.5rem;">
          <div style="display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:.2rem;">
            <span style="color:#F8FAFC;font-weight:600;">{name}</span>
            <span style="color:{col};">{int(w*100)}% weight &nbsp;·&nbsp; top {top_p:.1f}%</span>
          </div>
          <div style="background:#1a2332;border-radius:4px;height:5px;">
            <div style="background:{col};width:{int(w*100)}%;height:5px;border-radius:4px;"></div>
          </div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _temporal_panel(temporal: dict):
    """Show temporal feature deltas (pct_change + trend) for key features."""
    if not temporal:
        return
    st.markdown('<div class="sec">⏳ Temporal Trends</div>', unsafe_allow_html=True)
    _LABELS = {
        "typing_speed":    "Typing Speed",
        "key_press_count": "Key Presses",
        "error_rate":      "Error Rate",
        "idle_time":       "Keyboard Idle",
        "mouse_velocity":  "Mouse Velocity",
        "cursor_distance": "Cursor Distance",
        "idle_mouse_time": "Mouse Idle",
        "mouse_click_rate":"Click Rate",
    }
    rows = ""
    for key, label in _LABELS.items():
        pct   = temporal.get(f"{key}_pct_change", 0.0)
        trend = temporal.get(f"{key}_trend", 0.0)
        mean  = temporal.get(f"{key}_roll_mean", 0.0)
        if pct > 5:
            arrow, cls = "▲", "dup"
        elif pct < -5:
            arrow, cls = "▼", "ddown"
        else:
            arrow, cls = "●", "dflat"
        rows += f"""
        <tr>
          <td style="color:#F8FAFC;font-weight:500;font-size:.75rem;">{label}</td>
          <td style="color:#60a5fa;font-size:.75rem;">{mean:.2f}</td>
          <td class="{cls}" style="font-size:.75rem;">{arrow} {pct:+.1f}%</td>
          <td style="color:#94A3B8;font-size:.75rem;">{trend:+.3f}/win</td>
        </tr>"""
    st.markdown(f"""
    <div class="card" style="padding:.7rem 1rem;">
      <table class="bltbl">
        <thead><tr><th>Feature</th><th>Avg</th><th>Change</th><th>Trend</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


def render_dashboard_page(
    prediction, features, history, timeline, events,
    shap_data, baseline_tracker, session_start,
    prediction_count, break_count, is_monitoring, model_loaded,
    temporal=None,
):
    # ── KPI Cards ──
    _kpi_cards(prediction, features, session_start)
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 1: Keyboard | Mouse ──
    col_kb, col_ms = st.columns(2)
    with col_kb:
        _keyboard_panel(features)
    with col_ms:
        _mouse_panel(features)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 2: Trend | Gauge + Donut ──
    col_trend, col_gauge = st.columns([3, 2])
    with col_trend:
        st.markdown('<div class="sec">📈 Live Fatigue Trend</div>', unsafe_allow_html=True)
        st.plotly_chart(fatigue_trend(history), use_container_width=True,
                        config={"displayModeBar": False})
    with col_gauge:
        st.markdown('<div class="sec">🎯 Prediction Confidence</div>', unsafe_allow_html=True)
        conf = prediction.get("confidence", 0) if prediction else 0
        lvl  = prediction.get("level", 0) if prediction else 0
        probs = prediction.get("probabilities", {}) if prediction else {}
        st.plotly_chart(confidence_gauge(conf, lvl), use_container_width=True,
                        config={"displayModeBar": False})
        st.plotly_chart(probability_donut(probs), use_container_width=True,
                        config={"displayModeBar": False})

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 3: SHAP | Recommendation ──
    col_shap, col_rec = st.columns([3, 2])
    with col_shap:
        st.markdown('<div class="sec">🔍 SHAP Explainability</div>', unsafe_allow_html=True)
        sv, sn = shap_data
        st.plotly_chart(shap_bar(sv, sn), use_container_width=True,
                        config={"displayModeBar": False})
    with col_rec:
        st.markdown('<div class="sec">💡 Break Recommendation</div>', unsafe_allow_html=True)
        _recommendation(prediction)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        _system_health(is_monitoring, model_loaded)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 4: Ensemble indicator + Temporal ──
    temporal = temporal or st.session_state.get("last_temporal", {})
    if prediction and prediction.get("models_used"):
        col_ens, col_tmp = st.columns([2, 3])
        with col_ens:
            _ensemble_indicator(prediction)
        with col_tmp:
            _temporal_panel(temporal)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 5: Baseline | Activity Timeline ──
    col_bl, col_tl = st.columns([2, 3])
    with col_bl:
        _baseline_table(baseline_tracker, features)
    with col_tl:
        st.markdown('<div class="sec">📉 Activity Timeline</div>', unsafe_allow_html=True)
        st.plotly_chart(activity_timeline(timeline), use_container_width=True,
                        config={"displayModeBar": False})

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 6: Session Stats | Live Events ──
    col_ss, col_ev = st.columns([2, 3])
    with col_ss:
        _session_stats(session_start, prediction_count, history, break_count)
    with col_ev:
        _live_events(events)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Row 7: Keyboard bar | Mouse bar | Radar ──
    if features:
        col_kb2, col_ms2, col_rd = st.columns(3)
        with col_kb2:
            st.plotly_chart(keyboard_bar(features), use_container_width=True,
                            config={"displayModeBar": False})
        with col_ms2:
            st.plotly_chart(mouse_bar(features), use_container_width=True,
                            config={"displayModeBar": False})
        with col_rd:
            baseline = baseline_tracker.get_baseline()
            if baseline:
                st.plotly_chart(radar_chart(features, baseline),
                                use_container_width=True,
                                config={"displayModeBar": False})
