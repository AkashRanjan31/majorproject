"""
ui/pages/analytics.py
---------------------
Analytics page — daily/weekly/monthly fatigue, heatmap, distributions.
"""

import streamlit as st
from ui.charts import analytics_bar, hourly_heatmap, prediction_distribution


def render_analytics_page(records: list, default_tab: str = "daily"):
    st.markdown('<div class="sec">📊 Analytics</div>', unsafe_allow_html=True)

    if not records:
        st.info("📊 No data yet. Start monitoring to populate analytics.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Daily", "📆 Weekly", "🗓️ Monthly", "🔥 Heatmap"
    ])

    with tab1:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.plotly_chart(analytics_bar(records, "daily"),
                            use_container_width=True,
                            config={"displayModeBar": False})
        with col2:
            st.plotly_chart(prediction_distribution(records),
                            use_container_width=True,
                            config={"displayModeBar": False})

    with tab2:
        st.plotly_chart(analytics_bar(records, "weekly"),
                        use_container_width=True,
                        config={"displayModeBar": False})

    with tab3:
        st.plotly_chart(analytics_bar(records, "monthly"),
                        use_container_width=True,
                        config={"displayModeBar": False})

    with tab4:
        st.plotly_chart(hourly_heatmap(records),
                        use_container_width=True,
                        config={"displayModeBar": False})

    # Summary stats
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec">📈 Summary</div>', unsafe_allow_html=True)
    total = len(records)
    if total:
        import pandas as pd
        df = pd.DataFrame(records)
        avg_f = df["fatigue_level"].mean()
        max_f = df["fatigue_level"].max()
        avg_c = df["confidence"].mean() if "confidence" in df.columns else 0
        dist  = df["fatigue_level"].value_counts().to_dict()

        c1, c2, c3, c4, c5 = st.columns(5)
        items = [
            ("Total Records",  str(total),          "#2563EB"),
            ("Avg Fatigue",    f"{avg_f:.2f}",       "#F97316"),
            ("Max Fatigue",    str(int(max_f)),      "#EF4444"),
            ("Avg Confidence", f"{avg_c:.1%}",       "#22C55E"),
            ("Normal %",       f"{dist.get(0,0)/total*100:.0f}%", "#22C55E"),
        ]
        for col_obj, (lbl, val, color) in zip([c1,c2,c3,c4,c5], items):
            with col_obj:
                st.markdown(f"""
                <div class="mtile" style="border-left-color:{color};">
                  <div class="mtile-lbl">{lbl}</div>
                  <div class="mtile-val" style="color:{color};">{val}</div>
                </div>""", unsafe_allow_html=True)
