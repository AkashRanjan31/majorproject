"""
ui/pages/settings.py
--------------------
Settings page — prediction window, refresh rate, toggles.
"""

import streamlit as st


def render_settings_page():
    st.markdown('<div class="sec">⚙️ Settings</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card card-top-blue" style="margin-bottom:.75rem;">', unsafe_allow_html=True)
        st.markdown("**Monitoring Configuration**")

        window = st.selectbox(
            "Prediction Window",
            [30, 60, 120],
            index=[30,60,120].index(st.session_state.get("window_size", 60)),
            key="cfg_window",
        )
        st.session_state.window_size = window

        refresh = st.selectbox(
            "Refresh Rate (seconds)",
            [3, 5, 10, 15, 30],
            index=[3,5,10,15,30].index(st.session_state.get("refresh_rate", 5)),
            key="cfg_refresh",
        )
        st.session_state.refresh_rate = refresh

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card card-top-blue" style="margin-bottom:.75rem;">', unsafe_allow_html=True)
        st.markdown("**Notifications**")
        st.toggle("Break Reminders", value=True, key="cfg_breaks")
        st.toggle("Sound Alerts",    value=False, key="cfg_sound")
        st.toggle("Desktop Notifications", value=False, key="cfg_notif")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card" style="margin-top:.5rem;">', unsafe_allow_html=True)
    st.markdown("**Current Configuration**")
    st.markdown(f"""
    <div style="font-size:.8rem;color:#94A3B8;line-height:2;">
      Prediction Window: <b style="color:#60a5fa;">{st.session_state.get('window_size',60)}s</b><br>
      Refresh Rate: <b style="color:#60a5fa;">{st.session_state.get('refresh_rate',5)}s</b><br>
      Model: <b style="color:#a78bfa;">XGBoost Classifier</b><br>
      Database: <b style="color:#22C55E;">SQLite (Local)</b>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
