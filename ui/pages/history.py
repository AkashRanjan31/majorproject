"""
ui/pages/history.py
-------------------
Enterprise-grade Prediction History page.

Features
--------
- 7 summary KPI cards (total, avg fatigue, avg confidence, high-fatigue
  count, today, this week, this month)
- Search bar (fatigue name, recommendation, session ID)
- Filter by date range, fatigue level, session ID, risk level
- Sort by any column (asc / desc)
- Pagination (configurable page size)
- Export: CSV, Excel, PDF
- 9 analytics charts across two tabs (Overview / Activity)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.history import calculate_statistics, export_history
from ui.styles import fc, fb
from ui.charts import (
    history_fatigue_trend,
    history_confidence_trend,
    history_risk_distribution,
    history_session_timeline,
    history_keyboard_trend,
    history_mouse_trend,
    history_hourly_graph,
    history_daily_graph,
    history_weekly_graph,
    history_pred_distribution,
)

# ── constants ─────────────────────────────────────────────────────────────────
_LEVEL_LABELS: dict[int, str] = {
    0: "Normal",
    1: "Mild Fatigue",
    2: "Moderate Fatigue",
    3: "High Fatigue",
}
_RISK_COLORS: dict[str, str] = {
    "Low": "#22C55E",
    "Medium": "#FACC15",
    "High": "#F97316",
    "Critical": "#EF4444",
}
_PAGE_SIZES = [10, 25, 50, 100]

# Display columns shown in the data table (subset of full schema)
_TABLE_COLS = [
    "prediction_id", "session_id", "timestamp",
    "fatigue_level", "fatigue_name", "confidence",
    "risk_level", "typing_speed_wpm", "key_press_count",
    "mouse_click_count", "mouse_speed",
    "low_probability", "moderate_probability", "high_probability",
    "recommendation", "break_duration", "next_recommended_break",
    "cpu_usage", "ram_usage",
]


# ── helpers ───────────────────────────────────────────────────────────────────
def _safe_num(df: pd.DataFrame, col: str) -> pd.Series:
    """Return a numeric Series, filling missing with 0."""
    if col not in df.columns:
        return pd.Series([0.0] * len(df))
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def _summary_cards(stats: dict[str, object]) -> None:
    """Render 7 KPI summary cards."""
    cards = [
        ("📊 Total Predictions",  str(stats["total"]),                    "#2563EB", "All time"),
        ("😴 Avg Fatigue Score",  f"{stats['avg_fatigue']:.2f} / 3.00",   "#F97316", "Lower is better"),
        ("🎯 Avg Confidence",     f"{stats['avg_confidence']:.1%}",        "#8B5CF6", "Model certainty"),
        ("🚨 High Fatigue Count", str(stats["high_count"]),                "#EF4444", "Level ≥ 2"),
        ("📅 Today",              str(stats["today_count"]),               "#22C55E", "Predictions today"),
        ("📆 This Week",          str(stats["week_count"]),                "#FACC15", "Current week"),
        ("🗓️ This Month",         str(stats["month_count"]),               "#06b6d4", "Current month"),
    ]
    cols = st.columns(7)
    for col_obj, (label, value, color, sub) in zip(cols, cards):
        with col_obj:
            st.markdown(f"""
            <div class="kpi" style="border-top:3px solid {color};padding:.85rem 1rem;">
              <div class="kpi-lbl">{label}</div>
              <div class="kpi-val anim" style="color:{color};font-size:1.35rem;">{value}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)


def _distribution_mini(stats: dict[str, object]) -> None:
    """Render a compact 3-column distribution bar."""
    total = max(stats["total"], 1)
    items = [
        ("🟢 Normal",   stats["normal_pct"],   "#22C55E"),
        ("🟡 Mild",     stats["moderate_pct"], "#FACC15"),
        ("🔴 High+",    stats["high_pct"],      "#EF4444"),
    ]
    cols = st.columns(3)
    for col_obj, (label, pct, color) in zip(cols, items):
        with col_obj:
            st.markdown(f"""
            <div class="mtile" style="border-left-color:{color};text-align:center;">
              <div class="mtile-lbl">{label}</div>
              <div class="mtile-val" style="color:{color};">{pct:.1f}%</div>
              <div style="background:#1a2332;border-radius:4px;height:4px;margin-top:.3rem;">
                <div style="background:{color};width:{min(pct,100):.1f}%;
                            height:4px;border-radius:4px;"></div>
              </div>
            </div>""", unsafe_allow_html=True)


def _filter_controls(
    df: pd.DataFrame,
    current_session_id: str,
) -> tuple[pd.DataFrame, int, int]:
    """
    Render all filter / sort / pagination controls and return
    (filtered_df, page_index, page_size).
    """
    st.markdown('<div class="sec">🔍 Search &amp; Filters</div>', unsafe_allow_html=True)

    # ── Row 1: search + level + risk ──────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    with c1:
        search = st.text_input(
            "Search",
            placeholder="Search fatigue name, session ID, recommendation…",
            label_visibility="collapsed",
            key="hist_search",
        )
    with c2:
        level_opts = ["All Levels"] + [_LEVEL_LABELS[i] for i in range(4)]
        level_filter = st.selectbox(
            "Fatigue Level", level_opts,
            label_visibility="collapsed", key="hist_level",
        )
    with c3:
        risk_opts = ["All Risks", "Low", "Medium", "High", "Critical"]
        risk_filter = st.selectbox(
            "Risk Level", risk_opts,
            label_visibility="collapsed", key="hist_risk",
        )
    with c4:
        session_opts = ["All Sessions", "Current Session"] + sorted(
            df["session_id"].dropna().unique().tolist()
        )
        session_filter = st.selectbox(
            "Session", session_opts,
            label_visibility="collapsed", key="hist_session",
        )

    # ── Row 2: date range + sort ──────────────────────────────────────────────
    d1, d2, s1, s2, ps = st.columns([2, 2, 2, 2, 1])
    with d1:
        date_from = st.date_input(
            "From", value=None, key="hist_date_from",
            label_visibility="collapsed",
        )
    with d2:
        date_to = st.date_input(
            "To", value=None, key="hist_date_to",
            label_visibility="collapsed",
        )
    with s1:
        sort_col_opts = [
            "timestamp", "fatigue_level", "confidence",
            "typing_speed_wpm", "mouse_speed", "risk_level",
        ]
        sort_col = st.selectbox(
            "Sort by", sort_col_opts,
            label_visibility="collapsed", key="hist_sort_col",
        )
    with s2:
        sort_dir = st.selectbox(
            "Order", ["Descending", "Ascending"],
            label_visibility="collapsed", key="hist_sort_dir",
        )
    with ps:
        page_size = st.selectbox(
            "Rows", _PAGE_SIZES, index=1,
            label_visibility="collapsed", key="hist_page_size",
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = df.copy()

    if search:
        mask = (
            filtered["fatigue_name"].str.contains(search, case=False, na=False)
            | filtered["recommendation"].str.contains(search, case=False, na=False)
            | filtered["session_id"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    if level_filter != "All Levels":
        target = {v: k for k, v in _LEVEL_LABELS.items()}.get(level_filter)
        if target is not None:
            filtered = filtered[_safe_num(filtered, "fatigue_level") == target]

    if risk_filter != "All Risks" and "risk_level" in filtered.columns:
        filtered = filtered[filtered["risk_level"] == risk_filter]

    if session_filter == "Current Session":
        filtered = filtered[filtered["session_id"] == current_session_id]
    elif session_filter not in ("All Sessions", "Current Session"):
        filtered = filtered[filtered["session_id"] == session_filter]

    if date_from:
        filtered = filtered[
            pd.to_datetime(filtered["timestamp"], errors="coerce")
            >= pd.Timestamp(date_from)
        ]
    if date_to:
        filtered = filtered[
            pd.to_datetime(filtered["timestamp"], errors="coerce")
            <= pd.Timestamp(date_to) + timedelta(days=1)
        ]

    # ── Sort ──────────────────────────────────────────────────────────────────
    ascending = sort_dir == "Ascending"
    if sort_col in filtered.columns:
        try:
            filtered = filtered.sort_values(sort_col, ascending=ascending)
        except Exception:
            pass

    # ── Pagination state ──────────────────────────────────────────────────────
    total_rows = len(filtered)
    total_pages = max(1, math.ceil(total_rows / page_size))

    if "hist_page" not in st.session_state:
        st.session_state.hist_page = 0
    # Reset page when filters change
    filter_key = f"{search}|{level_filter}|{risk_filter}|{session_filter}|{date_from}|{date_to}"
    if st.session_state.get("_hist_filter_key") != filter_key:
        st.session_state.hist_page = 0
        st.session_state["_hist_filter_key"] = filter_key

    page_idx = st.session_state.hist_page

    return filtered, page_idx, page_size, total_pages


def _export_row(df: pd.DataFrame) -> None:
    """Render CSV / Excel / PDF export buttons in one row."""
    st.markdown('<div class="sec">📥 Export</div>', unsafe_allow_html=True)
    c1, c2, c3, c_space = st.columns([1, 1, 1, 4])

    with c1:
        try:
            csv_bytes = export_history(df, "csv")
            st.download_button(
                "⬇️ CSV",
                csv_bytes,
                file_name=f"fatigue_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="hist_dl_csv",
            )
        except Exception as e:
            st.caption(f"CSV error: {e}")

    with c2:
        try:
            xl_bytes = export_history(df, "excel")
            st.download_button(
                "⬇️ Excel",
                xl_bytes,
                file_name=f"fatigue_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="hist_dl_excel",
            )
        except Exception as e:
            st.caption(f"Excel error: {e}")

    with c3:
        try:
            pdf_bytes = export_history(df, "pdf")
            mime = (
                "application/pdf"
                if pdf_bytes[:4] == b"%PDF"
                else "text/csv"
            )
            ext = "pdf" if mime == "application/pdf" else "csv"
            st.download_button(
                "⬇️ PDF",
                pdf_bytes,
                file_name=f"fatigue_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                mime=mime,
                use_container_width=True,
                key="hist_dl_pdf",
            )
        except Exception as e:
            st.caption(f"PDF error: {e}")


def _pagination_controls(page_idx: int, total_pages: int, total_rows: int) -> int:
    """Render prev / page-info / next controls. Returns updated page index."""
    pc1, pc2, pc3 = st.columns([1, 3, 1])
    with pc1:
        if st.button("◀ Prev", key="hist_prev", use_container_width=True,
                     disabled=(page_idx == 0)):
            st.session_state.hist_page = max(0, page_idx - 1)
            st.rerun()
    with pc2:
        st.markdown(
            f"""<div style="text-align:center;font-size:.75rem;color:#94A3B8;
                            padding:.45rem 0;">
              Page <b style="color:#F8FAFC;">{page_idx + 1}</b> of
              <b style="color:#F8FAFC;">{total_pages}</b>
              &nbsp;·&nbsp; {total_rows} records
            </div>""",
            unsafe_allow_html=True,
        )
    with pc3:
        if st.button("Next ▶", key="hist_next", use_container_width=True,
                     disabled=(page_idx >= total_pages - 1)):
            st.session_state.hist_page = min(total_pages - 1, page_idx + 1)
            st.rerun()
    return st.session_state.hist_page


def _data_table(page_df: pd.DataFrame) -> None:
    """Render the styled data table for the current page."""
    if page_df.empty:
        st.info("No records match the current filters.")
        return

    # Keep only columns that exist
    display_cols = [c for c in _TABLE_COLS if c in page_df.columns]
    view = page_df[display_cols].copy()

    # Format columns for display
    if "confidence" in view.columns:
        view["confidence"] = pd.to_numeric(view["confidence"], errors="coerce").apply(
            lambda x: f"{x:.1%}" if pd.notna(x) else "—"
        )
    for prob_col in ["low_probability", "moderate_probability", "high_probability"]:
        if prob_col in view.columns:
            view[prob_col] = pd.to_numeric(view[prob_col], errors="coerce").apply(
                lambda x: f"{x:.3f}" if pd.notna(x) else "—"
            )
    for num_col in ["typing_speed_wpm", "mouse_speed", "cpu_usage", "ram_usage"]:
        if num_col in view.columns:
            view[num_col] = pd.to_numeric(view[num_col], errors="coerce").apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "—"
            )

    st.dataframe(
        view,
        use_container_width=True,
        height=min(420, 60 + len(view) * 35),
        column_config={
            "prediction_id":    st.column_config.TextColumn("Pred ID",    width="small"),
            "session_id":       st.column_config.TextColumn("Session",    width="medium"),
            "timestamp":        st.column_config.TextColumn("Timestamp",  width="medium"),
            "fatigue_level":    st.column_config.NumberColumn("Level",    format="%d", width="small"),
            "fatigue_name":     st.column_config.TextColumn("Fatigue",    width="medium"),
            "confidence":       st.column_config.TextColumn("Confidence", width="small"),
            "risk_level":       st.column_config.TextColumn("Risk",       width="small"),
            "typing_speed_wpm": st.column_config.TextColumn("WPM",        width="small"),
            "key_press_count":  st.column_config.NumberColumn("Keys",     format="%d", width="small"),
            "mouse_click_count":st.column_config.NumberColumn("Clicks",   format="%d", width="small"),
            "mouse_speed":      st.column_config.TextColumn("Cursor px/s",width="small"),
            "low_probability":  st.column_config.TextColumn("P(Low)",     width="small"),
            "moderate_probability": st.column_config.TextColumn("P(Mod)", width="small"),
            "high_probability": st.column_config.TextColumn("P(High)",    width="small"),
            "recommendation":   st.column_config.TextColumn("Recommendation", width="large"),
            "break_duration":   st.column_config.NumberColumn("Break(min)", format="%d", width="small"),
            "next_recommended_break": st.column_config.TextColumn("Next Break", width="small"),
            "cpu_usage":        st.column_config.TextColumn("CPU %",      width="small"),
            "ram_usage":        st.column_config.TextColumn("RAM %",      width="small"),
        },
    )


def _analytics_tabs(df: pd.DataFrame) -> None:
    """Render all 9 analytics charts across two tabs."""
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec">📊 Analytics</div>', unsafe_allow_html=True)

    tab_overview, tab_activity = st.tabs(["📈 Overview", "⌨️ Activity"])

    _cfg = {"displayModeBar": False}

    with tab_overview:
        # Row 1: fatigue trend (full width)
        st.plotly_chart(history_fatigue_trend(df),
                        use_container_width=True, config=_cfg)

        # Row 2: confidence trend | risk distribution
        r2a, r2b = st.columns([3, 2])
        with r2a:
            st.plotly_chart(history_confidence_trend(df),
                            use_container_width=True, config=_cfg)
        with r2b:
            st.plotly_chart(history_risk_distribution(df),
                            use_container_width=True, config=_cfg)

        # Row 3: prediction distribution | session timeline
        r3a, r3b = st.columns([2, 3])
        with r3a:
            st.plotly_chart(history_pred_distribution(df),
                            use_container_width=True, config=_cfg)
        with r3b:
            st.plotly_chart(history_session_timeline(df),
                            use_container_width=True, config=_cfg)

        # Row 4: hourly | daily | weekly
        r4a, r4b, r4c = st.columns(3)
        with r4a:
            st.plotly_chart(history_hourly_graph(df),
                            use_container_width=True, config=_cfg)
        with r4b:
            st.plotly_chart(history_daily_graph(df),
                            use_container_width=True, config=_cfg)
        with r4c:
            st.plotly_chart(history_weekly_graph(df),
                            use_container_width=True, config=_cfg)

    with tab_activity:
        # Row 1: keyboard trend | mouse trend
        ka, ma = st.columns(2)
        with ka:
            st.plotly_chart(history_keyboard_trend(df),
                            use_container_width=True, config=_cfg)
        with ma:
            st.plotly_chart(history_mouse_trend(df),
                            use_container_width=True, config=_cfg)

        # Row 2: feature breakdown table
        st.markdown('<div class="sec">⚙️ Feature Averages</div>', unsafe_allow_html=True)
        feat_cols = [
            "key_press_count", "typing_speed_wpm", "key_hold_time_ms",
            "typing_accuracy", "backspace_count", "error_rate",
            "mouse_click_count", "left_clicks", "right_clicks",
            "double_clicks", "mouse_speed", "mouse_distance",
            "scroll_count", "drag_events",
        ]
        avail = [c for c in feat_cols if c in df.columns]
        if avail:
            avg_row = {
                c: round(float(pd.to_numeric(df[c], errors="coerce").mean()), 3)
                for c in avail
            }
            avg_df = pd.DataFrame([avg_row])
            st.dataframe(avg_df, use_container_width=True, height=80)


# ── main render ───────────────────────────────────────────────────────────────
def render_history_page(
    df: pd.DataFrame,
    current_session_id: str = "",
) -> None:
    """
    Render the complete enterprise Prediction History page.

    Args:
        df: Full history DataFrame from load_prediction_history().
        current_session_id: Active session ID for the "Current Session" filter.
    """
    st.markdown('<div class="sec">📋 Prediction History</div>', unsafe_allow_html=True)

    # ── Empty state ───────────────────────────────────────────────────────────
    if df is None or df.empty:
        st.markdown("""
        <div class="card card-top-blue" style="text-align:center;padding:2.5rem;">
          <div style="font-size:2.5rem;margin-bottom:.75rem;">📭</div>
          <div style="font-size:1rem;font-weight:700;color:#F8FAFC;margin-bottom:.4rem;">
            No Prediction History Yet
          </div>
          <div style="font-size:.8rem;color:#64748B;">
            Start monitoring to generate predictions.<br>
            History is saved automatically to
            <code style="color:#60a5fa;">history/prediction_history.csv</code>
          </div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Ensure numeric types for stats ───────────────────────────────────────
    df = df.copy()
    df["fatigue_level"] = pd.to_numeric(df["fatigue_level"], errors="coerce").fillna(0)
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0)

    # ── Summary cards ─────────────────────────────────────────────────────────
    stats = calculate_statistics(df)
    _summary_cards(stats)
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    _distribution_mini(stats)
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── Session info badge ────────────────────────────────────────────────────
    if current_session_id:
        st.markdown(
            f'<div style="font-size:.7rem;color:#64748B;margin-bottom:.5rem;">'
            f'Current session: <span class="badge b-blue">{current_session_id}</span>'
            f'&nbsp;·&nbsp; {stats["session_count"]} total session(s) in history'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Filters ───────────────────────────────────────────────────────────────
    filtered, page_idx, page_size, total_pages = _filter_controls(df, current_session_id)

    st.markdown(
        f'<div style="font-size:.7rem;color:#64748B;margin:.3rem 0 .5rem;">'
        f'Showing <b style="color:#F8FAFC;">{len(filtered)}</b> of '
        f'<b style="color:#F8FAFC;">{len(df)}</b> records</div>',
        unsafe_allow_html=True,
    )

    # ── Export ────────────────────────────────────────────────────────────────
    _export_row(filtered)
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    # ── Data table ────────────────────────────────────────────────────────────
    st.markdown('<div class="sec">📄 Prediction Records</div>', unsafe_allow_html=True)
    start = page_idx * page_size
    end = start + page_size
    page_df = filtered.iloc[start:end]
    _data_table(page_df)

    # ── Pagination ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
    _pagination_controls(page_idx, total_pages, len(filtered))

    # ── Analytics charts (use full filtered set, not just current page) ───────
    st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
    _analytics_tabs(filtered)
