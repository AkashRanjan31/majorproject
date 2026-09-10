"""
ui/pages/reports.py
-------------------
Reports page — export CSV, Excel, session history.
"""

import streamlit as st
import pandas as pd
import io


def render_reports_page(history: list, db_records: list):
    st.markdown('<div class="sec">📄 Reports &amp; Export</div>', unsafe_allow_html=True)

    # Summary
    total = len(db_records)
    st.markdown(f"""
    <div class="card card-top-blue" style="margin-bottom:1rem;">
      <div style="font-size:.8rem;color:#94A3B8;">
        Total records in database: <b style="color:#60a5fa;">{total}</b>
        &nbsp;·&nbsp; Session predictions: <b style="color:#a78bfa;">{len(history)}</b>
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="sec">📥 Session Export</div>', unsafe_allow_html=True)
        if history:
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False).encode()
            st.download_button("⬇️ Session CSV", csv,
                               "session_history.csv", "text/csv",
                               use_container_width=True)
        else:
            st.button("⬇️ Session CSV", disabled=True, use_container_width=True)

    with c2:
        st.markdown('<div class="sec">📥 Full Report</div>', unsafe_allow_html=True)
        if db_records:
            df2 = pd.DataFrame(db_records)
            csv2 = df2.to_csv(index=False).encode()
            st.download_button("⬇️ Full Report CSV", csv2,
                               "fatigue_report.csv", "text/csv",
                               use_container_width=True)
        else:
            st.button("⬇️ Full Report CSV", disabled=True, use_container_width=True)

    with c3:
        st.markdown('<div class="sec">📥 Excel Export</div>', unsafe_allow_html=True)
        try:
            if db_records:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    pd.DataFrame(db_records).to_excel(
                        w, index=False, sheet_name="Predictions"
                    )
                st.download_button(
                    "⬇️ Export Excel", buf.getvalue(),
                    "fatigue_report.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            else:
                st.button("⬇️ Export Excel", disabled=True, use_container_width=True)
        except ImportError:
            st.caption("Install `openpyxl` for Excel export.")

    # Preview
    if db_records:
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec">👁️ Data Preview</div>', unsafe_allow_html=True)
        df_prev = pd.DataFrame(db_records[:50])
        if "features_json" in df_prev.columns:
            df_prev = df_prev.drop(columns=["features_json"])
        st.dataframe(df_prev, use_container_width=True, height=300)
