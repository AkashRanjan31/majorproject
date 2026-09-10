"""
ui/pages/live_monitor.py
------------------------
Live Monitor page — raw events, feature vector, prediction, latency.
"""

import streamlit as st
import time
from ui.styles import fc, FATIGUE_META


def render_live_monitor_page(prediction, features, events, monitor):
    st.markdown('<div class="sec">📡 Live Monitor</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    # ── Left: Current Prediction ──
    with col1:
        st.markdown('<div class="sec">🔮 Current Prediction</div>', unsafe_allow_html=True)
        if prediction:
            lvl  = prediction.get("level", 0)
            col  = fc(lvl)
            meta = FATIGUE_META.get(lvl, FATIGUE_META[0])
            conf = prediction.get("confidence", 0)
            ts   = prediction.get("timestamp","")
            ts_s = ts.strftime("%H:%M:%S") if hasattr(ts,"strftime") else str(ts)
            st.markdown(f"""
            <div class="card card-top-blue" style="text-align:center;padding:1.5rem;">
              <div style="font-size:3rem;margin-bottom:.5rem;">{meta['emoji']}</div>
              <div style="font-size:1.5rem;font-weight:900;color:{col};">{meta['name']}</div>
              <div style="font-size:.8rem;color:#94A3B8;margin-top:.3rem;">
                Confidence: <b style="color:{col};">{conf:.1f}%</b>
              </div>
              <div style="font-size:.7rem;color:#64748B;margin-top:.2rem;">@ {ts_s}</div>
            </div>""", unsafe_allow_html=True)

            # Probabilities
            probs = prediction.get("probabilities", {})
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec">📊 Class Probabilities</div>', unsafe_allow_html=True)
            for cls_name, cls_key, cls_col in [
                ("Normal",           "Normal",           "#22C55E"),
                ("Low Fatigue",      "Low Fatigue",      "#84cc16"),
                ("Moderate Fatigue", "Moderate Fatigue", "#F97316"),
                ("High Fatigue",     "High Fatigue",     "#EF4444"),
                ("Critical Fatigue", "Critical Fatigue", "#7c3aed"),
            ]:
                pct = probs.get(cls_key, 0)
                st.markdown(f"""
                <div style="margin-bottom:.4rem;">
                  <div style="display:flex;justify-content:space-between;
                              font-size:.75rem;margin-bottom:.2rem;">
                    <span style="color:#94A3B8;">{cls_name}</span>
                    <span style="color:{cls_col};font-weight:700;">{pct:.1f}%</span>
                  </div>
                  <div style="background:#1a2332;border-radius:4px;height:6px;">
                    <div style="background:{cls_col};width:{pct:.1f}%;height:6px;
                                border-radius:4px;transition:width .3s;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("⏳ Waiting for prediction…")

    # ── Right: Feature Vector ──
    with col2:
        st.markdown('<div class="sec">⚙️ Current Feature Vector</div>', unsafe_allow_html=True)
        if features:
            rows = ""
            for k, v in features.items():
                rows += f"""
                <tr>
                  <td style="color:#94A3B8;font-size:.75rem;">{k.replace('_',' ').title()}</td>
                  <td style="color:#60a5fa;font-weight:600;font-size:.75rem;
                             font-family:monospace;">{v:.4f}</td>
                </tr>"""
            st.markdown(f"""
            <div class="card" style="padding:.7rem 1rem;max-height:340px;overflow-y:auto;">
              <table style="width:100%;border-collapse:collapse;">
                <thead>
                  <tr>
                    <th style="font-size:.58rem;color:#64748B;text-transform:uppercase;
                               letter-spacing:.1em;padding:.3rem .4rem;
                               border-bottom:1px solid rgba(255,255,255,.06);text-align:left;">
                      Feature</th>
                    <th style="font-size:.58rem;color:#64748B;text-transform:uppercase;
                               letter-spacing:.1em;padding:.3rem .4rem;
                               border-bottom:1px solid rgba(255,255,255,.06);text-align:left;">
                      Value</th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="skel" style="height:200px;border-radius:12px;"></div>',
                        unsafe_allow_html=True)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Monitor Stats ──
    if monitor:
        stats = monitor.get_stats()
        st.markdown('<div class="sec">📈 Monitor Statistics</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        items = [
            ("Key Events",    stats.get("key_events", 0),    "#2563EB"),
            ("Mouse Events",  stats.get("mouse_events", 0),  "#8B5CF6"),
            ("Session (s)",   f"{stats.get('session_duration',0):.0f}", "#22C55E"),
            ("Monitoring",    "Active" if stats.get("is_monitoring") else "Stopped", "#FACC15"),
        ]
        for col_obj, (lbl, val, color) in zip([c1,c2,c3,c4], items):
            with col_obj:
                st.markdown(f"""
                <div class="mtile" style="border-left-color:{color};">
                  <div class="mtile-lbl">{lbl}</div>
                  <div class="mtile-val" style="color:{color};">{val}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)

    # ── Live Event Table ──
    st.markdown('<div class="sec">📋 Recent Events</div>', unsafe_allow_html=True)
    if events:
        rows = ""
        for ev in reversed(events[-30:]):
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
              <td style="color:#60a5fa;">{kp}</td>
              <td style="color:#a78bfa;">{mc}</td>
              <td style="color:#94A3B8;">{spd:.0f}</td>
              <td style="color:{col};font-weight:700;">{nm}</td>
            </tr>"""
        st.markdown(f"""
        <div class="card" style="padding:.7rem 1rem;max-height:280px;overflow-y:auto;">
          <table class="evttbl">
            <thead>
              <tr>
                <th>Time</th><th>Key Events</th><th>Mouse Events</th>
                <th>Speed (px/s)</th><th>Fatigue</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""", unsafe_allow_html=True)
    else:
        st.info("No events yet. Start typing or moving your mouse.")
