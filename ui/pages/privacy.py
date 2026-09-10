"""
ui/pages/privacy.py
-------------------
Privacy & Security page.
"""

import streamlit as st


def render_privacy_page():
    st.markdown('<div class="sec">🔒 Privacy &amp; Security</div>', unsafe_allow_html=True)

    items = [
        ("No Webcam or Camera Access",   "Camera data is never captured or accessed."),
        ("No Microphone Recording",      "Audio input is completely disabled."),
        ("No Screenshot Capture",        "Screen content is never recorded."),
        ("No Password or Text Storage",  "Keystrokes are counted, never logged as text."),
        ("No Cloud Data Transmission",   "All data stays on your local machine only."),
        ("Behavior Statistics Only",     "Only numeric aggregates are stored in SQLite."),
        ("All Data Stored Locally",      "SQLite database on your device — no external servers."),
        ("Open Source & Auditable",      "All code is transparent and inspectable."),
    ]

    col1, col2 = st.columns(2)
    for i, (title, desc) in enumerate(items):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="card" style="margin-bottom:.5rem;padding:.8rem 1rem;">
              <div class="priv">
                <span class="priv-chk">✅</span>
                <div>
                  <div style="font-weight:700;font-size:.82rem;">{title}</div>
                  <div style="font-size:.7rem;color:#64748B;margin-top:.1rem;">{desc}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card card-top-green" style="text-align:center;padding:1.2rem;">
      <div style="font-size:1.5rem;margin-bottom:.4rem;">🛡️</div>
      <div style="font-weight:800;font-size:.95rem;color:#22C55E;">
        100% Privacy-Preserving
      </div>
      <div style="font-size:.75rem;color:#94A3B8;margin-top:.3rem;">
        This system monitors only behavioral patterns — never content.
        No personal data leaves your device.
      </div>
    </div>""", unsafe_allow_html=True)
