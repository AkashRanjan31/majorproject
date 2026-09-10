"""
ui/charts.py
------------
All Plotly chart builders — premium dark theme.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

_BG    = "rgba(0,0,0,0)"
_CARD  = "#0d1b2e"
_GRID  = "rgba(255,255,255,0.04)"
_TEXT  = "#F8FAFC"
_MUTED = "#94A3B8"
_BLUE  = "#2563EB"
_PURP  = "#8B5CF6"
_GREEN = "#22C55E"
_YEL   = "#FACC15"
_ORAN  = "#F97316"
_RED   = "#EF4444"

_LC = {0:_GREEN, 1:_YEL, 2:_ORAN, 3:_RED}
_LN = {0:"Normal", 1:"Mild", 2:"Moderate", 3:"High"}

_BASE = dict(
    paper_bgcolor=_BG, plot_bgcolor=_BG,
    font=dict(family="Inter,sans-serif", color=_TEXT, size=11),
    margin=dict(l=8, r=8, t=36, b=8),
    xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID,
               tickfont=dict(color=_MUTED, size=10), linecolor=_GRID),
    yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID,
               tickfont=dict(color=_MUTED, size=10), linecolor=_GRID),
    legend=dict(bgcolor=_BG, font=dict(color=_MUTED, size=10),
                orientation="h", y=-0.18),
    hoverlabel=dict(bgcolor="#162032", font_color=_TEXT,
                    bordercolor=_GRID, font_size=12),
)


def _empty(msg="Waiting for data…", h=240):
    f = go.Figure()
    f.update_layout(height=h, paper_bgcolor=_BG, plot_bgcolor=_BG,
                    margin=dict(l=8,r=8,t=8,b=8))
    f.add_annotation(text=msg, x=.5, y=.5, showarrow=False,
                     font=dict(color=_MUTED, size=13),
                     xref="paper", yref="paper")
    return f


# ── 1. Fatigue trend ──────────────────────────────────────────────────────────
def fatigue_trend(history: list) -> go.Figure:
    if not history:
        return _empty("Waiting for predictions…", 280)
    df = pd.DataFrame(history).sort_values("timestamp")
    df["col"] = df["level"].map(_LC).fillna(_MUTED)
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=df["timestamp"], y=df["level"],
        fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    f.add_trace(go.Scatter(
        x=df["timestamp"], y=df["level"],
        mode="lines+markers",
        line=dict(color=_BLUE, width=2.5, shape="spline", smoothing=1.2),
        marker=dict(color=df["col"].tolist(), size=9,
                    line=dict(color=_CARD, width=2)),
        name="Fatigue Level",
        hovertemplate="<b>%{text}</b><br>%{x|%H:%M:%S}<extra></extra>",
        text=df["level"].map(_LN),
    ))
    if "confidence" in df.columns:
        f.add_trace(go.Scatter(
            x=df["timestamp"], y=df["confidence"],
            mode="lines", name="Confidence",
            line=dict(color=_PURP, width=1.5, dash="dot"),
            yaxis="y2",
            hovertemplate="Conf: %{y:.1%}<extra></extra>",
        ))
    f.update_layout(
        height=280,
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3,3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        yaxis2=dict(overlaying="y", side="right", range=[0,110],
                    ticksuffix="%", tickfont=dict(color=_PURP, size=9),
                    showgrid=False),
        title=dict(text="Live Fatigue Trend", font=dict(size=12,color=_MUTED), x=0),
        **{k:v for k,v in _BASE.items() if k not in ("xaxis","yaxis","margin")},
        margin=dict(l=8,r=8,t=36,b=8),
    )
    return f


# ── 2. Confidence gauge ───────────────────────────────────────────────────────
def confidence_gauge(confidence: float, level: int = 0) -> go.Figure:
    # confidence is already 0-100 from realtime_predict.py
    color = _LC.get(level, _BLUE)
    f = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(confidence, 1),
        delta=dict(reference=75, valueformat=".1f", suffix="%",
                   increasing=dict(color=_GREEN),
                   decreasing=dict(color=_RED)),
        number=dict(suffix="%", font=dict(size=32, color=color, family="Inter")),
        gauge=dict(
            axis=dict(range=[0,100], tickfont=dict(color=_MUTED,size=8),
                      tickcolor=_MUTED, tickwidth=1, ticklen=4),
            bar=dict(color=color, thickness=0.22),
            bgcolor=_BG, borderwidth=0,
            steps=[
                dict(range=[0,50],  color="rgba(255,255,255,0.02)"),
                dict(range=[50,75], color="rgba(255,255,255,0.04)"),
                dict(range=[75,100],color="rgba(255,255,255,0.06)"),
            ],
            threshold=dict(line=dict(color=color,width=3),
                           thickness=0.8, value=confidence),
        ),
        title=dict(text=f"<b>{_LN.get(level,'Normal')}</b>",
                   font=dict(size=11, color=_MUTED)),
    ))
    f.update_layout(height=220, paper_bgcolor=_BG,
                    font=dict(family="Inter",color=_TEXT),
                    margin=dict(l=16,r=16,t=28,b=8))
    return f


# ── 3. Probability donut ──────────────────────────────────────────────────────
def probability_donut(probs: dict) -> go.Figure:
    # Keys are full class names from realtime_predict.py
    vals = [probs.get("Normal",0), probs.get("Moderate Fatigue",0), probs.get("High Fatigue",0)]
    if sum(vals) == 0:
        vals = [0.34, 0.33, 0.33]
    f = go.Figure(go.Pie(
        labels=["Normal","Moderate","High"], values=vals, hole=0.65,
        marker=dict(colors=[_GREEN,_ORAN,_RED],
                    line=dict(color=_CARD, width=2)),
        textfont=dict(size=10, color=_TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        sort=False,
    ))
    f.update_layout(
        height=220, paper_bgcolor=_BG,
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=8,r=8,t=8,b=8),
        legend=dict(orientation="h", y=-0.1,
                    font=dict(color=_MUTED, size=9)),
        annotations=[dict(text="Prob", x=.5, y=.5,
                          font_size=11, font_color=_MUTED, showarrow=False)],
    )
    return f


# ── 4. SHAP bar ───────────────────────────────────────────────────────────────
def shap_bar(shap_vals: list, feature_names: list) -> go.Figure:
    if not shap_vals:
        return _empty("SHAP values unavailable", 300)
    pairs = sorted(zip(feature_names, shap_vals),
                   key=lambda x: abs(x[1]), reverse=True)[:10]
    labels = [p[0].replace("_"," ").title() for p in pairs]
    values = [p[1] for p in pairs]
    colors = [_RED if v > 0 else _GREEN for v in values]
    f = go.Figure(go.Bar(
        x=values[::-1], y=labels[::-1], orientation="h",
        marker=dict(color=colors[::-1], opacity=.88,
                    line=dict(color="rgba(255,255,255,0.06)",width=.5)),
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:.5f}<extra></extra>",
    ))
    f.add_vline(x=0, line_color=_MUTED, line_width=1, line_dash="dot")
    f.update_layout(
        title=dict(text="SHAP Feature Contributions (Top 10)",
                   font=dict(size=11,color=_MUTED), x=0),
        xaxis_title="Impact on Fatigue Score",
        height=310, **_BASE,
    )
    return f


# ── 5. Feature importance ─────────────────────────────────────────────────────
def feature_importance(importances: dict) -> go.Figure:
    if not importances:
        return _empty("Feature importance unavailable", 320)
    items = sorted(importances.items(), key=lambda x: x[1])
    labels = [k.replace("_"," ").title() for k,_ in items]
    values = [v for _,v in items]
    mx = max(values) if values else 1
    colors = [f"rgba(37,99,235,{0.3+0.7*v/mx})" for v in values]
    f = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors,
                    line=dict(color="rgba(255,255,255,0.05)",width=.5)),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="XGBoost Feature Importance",
                   font=dict(size=11,color=_MUTED), x=0),
        height=320, **_BASE,
    )
    return f


# ── 6. Activity timeline ──────────────────────────────────────────────────────
def activity_timeline(timeline: list) -> go.Figure:
    if not timeline:
        return _empty("Activity timeline will appear here", 240)
    df = pd.DataFrame(timeline).sort_values("timestamp")
    f = go.Figure()
    traces = [
        ("typing_speed",     "Typing Speed (WPM)", _BLUE),
        ("cursor_speed",     "Cursor Speed (px/s)", _PURP),
        ("key_press_count",  "Key Presses",         _GREEN),
        ("mouse_click_count","Mouse Clicks",         _ORAN),
    ]
    for col, name, color in traces:
        if col in df.columns:
            f.add_trace(go.Scatter(
                x=df["timestamp"], y=df[col], name=name,
                mode="lines",
                line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<br>%{{x|%H:%M:%S}}<extra></extra>",
            ))
    f.update_layout(
        title=dict(text="Activity Timeline",
                   font=dict(size=11,color=_MUTED), x=0),
        height=240, **_BASE,
    )
    return f


# ── 7. Analytics bar ─────────────────────────────────────────────────────────
def analytics_bar(records: list, period: str = "daily") -> go.Figure:
    if not records:
        return _empty("No data yet — start monitoring", 260)
    df = pd.DataFrame(records)
    df["ts"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["ts"])
    freq = {"daily":"h","weekly":"D","monthly":"W"}.get(period,"h")
    df["bucket"] = df["ts"].dt.floor(freq)
    agg = df.groupby("bucket")["fatigue_level"].mean().reset_index()
    f = go.Figure(go.Bar(
        x=agg["bucket"], y=agg["fatigue_level"],
        marker=dict(
            color=agg["fatigue_level"],
            colorscale=[[0,_GREEN],[0.5,_ORAN],[1,_RED]],
            cmin=0, cmax=3, showscale=False,
            line=dict(color="rgba(255,255,255,0.05)",width=.5),
        ),
        hovertemplate="<b>%{x}</b><br>Avg Fatigue: %{y:.2f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text=f"{period.title()} Fatigue Average",
                   font=dict(size=11,color=_MUTED), x=0),
        height=260, **_BASE,
    )
    return f


# ── 8. Prediction distribution ────────────────────────────────────────────────
def prediction_distribution(records: list) -> go.Figure:
    if not records:
        return _empty("No predictions yet", 240)
    df = pd.DataFrame(records)
    counts = df["fatigue_level"].value_counts().sort_index()
    labels = [_LN.get(int(i), str(i)) for i in counts.index]
    colors = [_LC.get(int(i), _MUTED) for i in counts.index]
    f = go.Figure(go.Pie(
        labels=labels, values=counts.values, hole=0.55,
        marker=dict(colors=colors, line=dict(color=_CARD,width=2)),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Prediction Distribution",
                   font=dict(size=11,color=_MUTED), x=0),
        height=240, paper_bgcolor=_BG,
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=8,r=8,t=32,b=8),
        legend=dict(font=dict(color=_MUTED,size=10)),
    )
    return f


# ── 9. Hourly heatmap ─────────────────────────────────────────────────────────
def hourly_heatmap(records: list) -> go.Figure:
    if not records:
        return _empty("No data for heatmap yet", 220)
    df = pd.DataFrame(records)
    df["ts"]   = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["ts"])
    df["hour"] = df["ts"].dt.hour
    df["day"]  = df["ts"].dt.day_name()
    pivot = df.pivot_table(values="fatigue_level",
                           index="day", columns="hour", aggfunc="mean")
    f = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0,_GREEN],[0.5,_ORAN],[1,_RED]],
        zmin=0, zmax=3,
        hovertemplate="<b>%{y} %{x}:00</b><br>Avg Fatigue: %{z:.2f}<extra></extra>",
        colorbar=dict(tickfont=dict(color=_MUTED,size=9), len=0.8),
    ))
    f.update_layout(
        title=dict(text="Hourly Fatigue Heatmap",
                   font=dict(size=11,color=_MUTED), x=0),
        height=220, **_BASE,
    )
    return f


# ── 10. Radar chart ───────────────────────────────────────────────────────────
def radar_chart(features: dict, baseline: dict) -> go.Figure:
    keys   = ["typing_speed","key_press_count","cursor_speed",
              "mouse_click_count","scroll_count","idle_time"]
    labels = ["Typing Speed","Key Presses","Cursor Speed",
              "Mouse Clicks","Scrolls","Idle Time"]
    curr = [features.get(k,0) for k in keys]
    base = [baseline.get(k,0) for k in keys]
    mx   = [max(c,b,1) for c,b in zip(curr,base)]
    cn   = [v/m for v,m in zip(curr,mx)]
    bn   = [v/m for v,m in zip(base,mx)]
    f = go.Figure()
    f.add_trace(go.Scatterpolar(
        r=cn+[cn[0]], theta=labels+[labels[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.12)",
        line=dict(color=_BLUE,width=2), name="Current",
    ))
    f.add_trace(go.Scatterpolar(
        r=bn+[bn[0]], theta=labels+[labels[0]],
        fill="toself", fillcolor="rgba(139,92,246,0.08)",
        line=dict(color=_PURP,width=2,dash="dot"), name="Baseline",
    ))
    f.update_layout(
        polar=dict(
            bgcolor=_BG,
            radialaxis=dict(visible=True, range=[0,1],
                            tickfont=dict(color=_MUTED,size=8),
                            gridcolor=_GRID, linecolor=_GRID),
            angularaxis=dict(tickfont=dict(color=_MUTED,size=9),
                             gridcolor=_GRID, linecolor=_GRID),
        ),
        title=dict(text="Behavior Profile vs Baseline",
                   font=dict(size=11,color=_MUTED), x=0),
        height=280, paper_bgcolor=_BG,
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=40,r=40,t=36,b=8),
        legend=dict(bgcolor=_BG, font=dict(color=_MUTED,size=10)),
    )
    return f


# ── 11. Confusion matrix ──────────────────────────────────────────────────────
def confusion_matrix_chart(cm: list, labels: list) -> go.Figure:
    f = go.Figure(go.Heatmap(
        z=cm, x=labels, y=labels,
        colorscale=[[0,"rgba(37,99,235,0.08)"],[1,"rgba(37,99,235,0.9)"]],
        text=cm, texttemplate="%{text}",
        textfont=dict(size=14,color=_TEXT),
        hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
        showscale=False,
    ))
    f.update_layout(
        title=dict(text="Confusion Matrix",
                   font=dict(size=11,color=_MUTED), x=0),
        xaxis=dict(title="Predicted", tickfont=dict(color=_MUTED,size=10)),
        yaxis=dict(title="Actual",    tickfont=dict(color=_MUTED,size=10)),
        height=280,
        **{k:v for k,v in _BASE.items() if k not in ("xaxis","yaxis")},
    )
    return f


# ── 12. History: fatigue trend from CSV DataFrame ────────────────────────────
def history_fatigue_trend(df: pd.DataFrame) -> go.Figure:
    """Fatigue level over time from the full history DataFrame."""
    if df.empty:
        return _empty("No history data yet", 260)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce")
    d["confidence"] = pd.to_numeric(d["confidence"], errors="coerce")
    d = d.dropna(subset=["timestamp", "fatigue_level"]).sort_values("timestamp")
    colors = d["fatigue_level"].map(_LC).fillna(_MUTED).tolist()
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=d["timestamp"], y=d["fatigue_level"],
        fill="tozeroy", fillcolor="rgba(37,99,235,0.05)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    f.add_trace(go.Scatter(
        x=d["timestamp"], y=d["fatigue_level"],
        mode="lines+markers", name="Fatigue Level",
        line=dict(color=_BLUE, width=2.5, shape="spline", smoothing=1.1),
        marker=dict(color=colors, size=8, line=dict(color=_CARD, width=2)),
        hovertemplate="<b>%{text}</b><br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
        text=d["fatigue_level"].map(_LN),
    ))
    f.add_trace(go.Scatter(
        x=d["timestamp"], y=d["confidence"],
        mode="lines", name="Confidence",
        line=dict(color=_PURP, width=1.5, dash="dot"),
        yaxis="y2",
        hovertemplate="Conf: %{y:.1%}<extra></extra>",
    ))
    f.update_layout(
        height=260,
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3, 3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        yaxis2=dict(overlaying="y", side="right", range=[0, 1.1],
                    tickformat=".0%", tickfont=dict(color=_PURP, size=9),
                    showgrid=False),
        title=dict(text="Fatigue Trend", font=dict(size=11, color=_MUTED), x=0),
        **{k: v for k, v in _BASE.items() if k not in ("xaxis", "yaxis", "margin")},
        margin=dict(l=8, r=8, t=36, b=8),
    )
    return f


# ── 13. History: confidence trend ─────────────────────────────────────────────
def history_confidence_trend(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No confidence data yet", 220)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["confidence"] = pd.to_numeric(d["confidence"], errors="coerce")
    d = d.dropna(subset=["timestamp", "confidence"]).sort_values("timestamp")
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=d["timestamp"], y=d["confidence"],
        mode="lines", name="Confidence %",
        fill="tozeroy", fillcolor="rgba(139,92,246,0.07)",
        line=dict(color=_PURP, width=2.5, shape="spline"),
        hovertemplate="Confidence: %{y:.1f}%<br>%{x|%H:%M:%S}<extra></extra>",
    ))
    f.add_hline(y=75, line_color=_GREEN, line_dash="dot", line_width=1,
                annotation_text="75% threshold",
                annotation_font=dict(color=_GREEN, size=9))
    f.update_layout(
        title=dict(text="Confidence Trend", font=dict(size=11, color=_MUTED), x=0),
        yaxis=dict(range=[0, 105], ticksuffix="%",
                   gridcolor=_GRID, tickfont=dict(color=_MUTED, size=10)),
        height=220, **_BASE,
    )
    return f


# ── 14. History: risk level distribution ──────────────────────────────────────
def history_risk_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No risk data yet", 220)
    d = df.copy()
    d["risk_level"] = d["risk_level"].fillna("Low")
    order = ["Low", "Medium", "High", "Critical"]
    colors_map = {"Low": _GREEN, "Medium": _YEL, "High": _ORAN, "Critical": _RED}
    counts = d["risk_level"].value_counts()
    labels = [r for r in order if r in counts.index]
    values = [counts[r] for r in labels]
    clrs = [colors_map[r] for r in labels]
    f = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=clrs, line=dict(color=_CARD, width=2)),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        sort=False,
    ))
    f.update_layout(
        title=dict(text="Risk Level Distribution", font=dict(size=11, color=_MUTED), x=0),
        height=220, paper_bgcolor=_BG,
        font=dict(family="Inter", color=_TEXT),
        margin=dict(l=8, r=8, t=32, b=8),
        legend=dict(font=dict(color=_MUTED, size=10)),
    )
    return f


# ── 15. History: session timeline ─────────────────────────────────────────────
def history_session_timeline(df: pd.DataFrame) -> go.Figure:
    if df.empty or "session_id" not in df.columns:
        return _empty("No session data yet", 220)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce")
    d = d.dropna(subset=["timestamp", "fatigue_level"])
    sessions = d["session_id"].unique()[:8]  # cap at 8 for readability
    palette = [_BLUE, _PURP, _GREEN, _ORAN, _RED, _YEL, "#06b6d4", "#ec4899"]
    f = go.Figure()
    for i, sid in enumerate(sessions):
        sd = d[d["session_id"] == sid].sort_values("timestamp")
        short = sid[-10:] if len(sid) > 10 else sid
        f.add_trace(go.Scatter(
            x=sd["timestamp"], y=sd["fatigue_level"],
            mode="lines+markers", name=short,
            line=dict(color=palette[i % len(palette)], width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{short}</b><br>Level: %{{y}}<br>%{{x|%H:%M:%S}}<extra></extra>",
        ))
    f.update_layout(
        title=dict(text="Session Timeline", font=dict(size=11, color=_MUTED), x=0),
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3, 3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        height=240, **_BASE,
    )
    return f


# ── 16. History: keyboard activity trend ──────────────────────────────────────
def history_keyboard_trend(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No keyboard data yet", 230)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    for c in ["key_press_count", "typing_speed_wpm", "backspace_count", "error_rate"]:
        d[c] = pd.to_numeric(d.get(c, 0), errors="coerce").fillna(0)
    d = d.dropna(subset=["timestamp"]).sort_values("timestamp")
    f = go.Figure()
    traces = [
        ("key_press_count",  "Key Presses",    _BLUE),
        ("typing_speed_wpm", "Typing Speed WPM", _GREEN),
        ("backspace_count",  "Backspaces",      _RED),
    ]
    for col, name, color in traces:
        if col in d.columns:
            f.add_trace(go.Scatter(
                x=d["timestamp"], y=d[col], name=name,
                mode="lines", line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<br>%{{x|%H:%M}}<extra></extra>",
            ))
    f.update_layout(
        title=dict(text="Keyboard Activity Trend", font=dict(size=11, color=_MUTED), x=0),
        height=230, **_BASE,
    )
    return f


# ── 17. History: mouse activity trend ─────────────────────────────────────────
def history_mouse_trend(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No mouse data yet", 230)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    for c in ["mouse_click_count", "mouse_speed", "scroll_count", "drag_events"]:
        d[c] = pd.to_numeric(d.get(c, 0), errors="coerce").fillna(0)
    d = d.dropna(subset=["timestamp"]).sort_values("timestamp")
    f = go.Figure()
    traces = [
        ("mouse_click_count", "Mouse Clicks",   _PURP),
        ("mouse_speed",       "Cursor Speed",    _BLUE),
        ("scroll_count",      "Scroll Events",   _ORAN),
    ]
    for col, name, color in traces:
        if col in d.columns:
            f.add_trace(go.Scatter(
                x=d["timestamp"], y=d[col], name=name,
                mode="lines", line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<br>%{{x|%H:%M}}<extra></extra>",
            ))
    f.update_layout(
        title=dict(text="Mouse Activity Trend", font=dict(size=11, color=_MUTED), x=0),
        height=230, **_BASE,
    )
    return f


# ── 18. History: hourly prediction graph ──────────────────────────────────────
def history_hourly_graph(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No hourly data yet", 230)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce")
    d = d.dropna(subset=["timestamp", "fatigue_level"])
    d["hour"] = d["timestamp"].dt.hour
    agg = d.groupby("hour").agg(
        avg_fatigue=("fatigue_level", "mean"),
        count=("fatigue_level", "count"),
    ).reset_index()
    f = go.Figure()
    f.add_trace(go.Bar(
        x=agg["hour"], y=agg["count"],
        name="Predictions", yaxis="y2",
        marker=dict(color="rgba(37,99,235,0.18)",
                    line=dict(color="rgba(37,99,235,0.4)", width=1)),
        hovertemplate="Hour %{x}:00 — %{y} predictions<extra></extra>",
    ))
    f.add_trace(go.Scatter(
        x=agg["hour"], y=agg["avg_fatigue"],
        mode="lines+markers", name="Avg Fatigue",
        line=dict(color=_ORAN, width=2.5),
        marker=dict(size=8, color=_ORAN, line=dict(color=_CARD, width=2)),
        hovertemplate="Hour %{x}:00 — Avg Fatigue: %{y:.2f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Hourly Prediction Graph", font=dict(size=11, color=_MUTED), x=0),
        xaxis=dict(tickvals=list(range(0, 24, 2)),
                   ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)],
                   gridcolor=_GRID, tickfont=dict(color=_MUTED, size=9)),
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3, 3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont=dict(color="rgba(37,99,235,0.6)", size=9)),
        height=230,
        **{k: v for k, v in _BASE.items() if k not in ("xaxis", "yaxis", "margin")},
        margin=dict(l=8, r=8, t=36, b=8),
    )
    return f


# ── 19. History: daily prediction graph ───────────────────────────────────────
def history_daily_graph(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No daily data yet", 230)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce")
    d = d.dropna(subset=["timestamp", "fatigue_level"])
    d["date"] = d["timestamp"].dt.date
    agg = d.groupby("date").agg(
        avg_fatigue=("fatigue_level", "mean"),
        count=("fatigue_level", "count"),
        max_fatigue=("fatigue_level", "max"),
    ).reset_index()
    f = go.Figure()
    f.add_trace(go.Bar(
        x=agg["date"], y=agg["count"],
        name="Predictions", yaxis="y2",
        marker=dict(color="rgba(139,92,246,0.18)",
                    line=dict(color="rgba(139,92,246,0.4)", width=1)),
        hovertemplate="%{x} — %{y} predictions<extra></extra>",
    ))
    f.add_trace(go.Scatter(
        x=agg["date"], y=agg["avg_fatigue"],
        mode="lines+markers", name="Avg Fatigue",
        line=dict(color=_BLUE, width=2.5, shape="spline"),
        marker=dict(size=8, color=_BLUE, line=dict(color=_CARD, width=2)),
        hovertemplate="%{x}<br>Avg: %{y:.2f}<extra></extra>",
    ))
    f.add_trace(go.Scatter(
        x=agg["date"], y=agg["max_fatigue"],
        mode="lines", name="Max Fatigue",
        line=dict(color=_RED, width=1.5, dash="dot"),
        hovertemplate="%{x}<br>Max: %{y}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Daily Prediction Graph", font=dict(size=11, color=_MUTED), x=0),
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3, 3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont=dict(color="rgba(139,92,246,0.6)", size=9)),
        height=230,
        **{k: v for k, v in _BASE.items() if k not in ("xaxis", "yaxis", "margin")},
        margin=dict(l=8, r=8, t=36, b=8),
    )
    return f


# ── 20. History: weekly prediction graph ──────────────────────────────────────
def history_weekly_graph(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No weekly data yet", 230)
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce")
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce")
    d = d.dropna(subset=["timestamp", "fatigue_level"])
    d["week"] = d["timestamp"].dt.to_period("W").dt.start_time
    agg = d.groupby("week").agg(
        avg_fatigue=("fatigue_level", "mean"),
        count=("fatigue_level", "count"),
    ).reset_index()
    f = go.Figure()
    f.add_trace(go.Bar(
        x=agg["week"], y=agg["count"],
        name="Predictions", yaxis="y2",
        marker=dict(color="rgba(34,197,94,0.15)",
                    line=dict(color="rgba(34,197,94,0.35)", width=1)),
        hovertemplate="Week of %{x|%b %d} — %{y} predictions<extra></extra>",
    ))
    f.add_trace(go.Scatter(
        x=agg["week"], y=agg["avg_fatigue"],
        mode="lines+markers", name="Avg Fatigue",
        line=dict(color=_GREEN, width=2.5, shape="spline"),
        marker=dict(size=8, color=_GREEN, line=dict(color=_CARD, width=2)),
        hovertemplate="Week of %{x|%b %d}<br>Avg: %{y:.2f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Weekly Prediction Graph", font=dict(size=11, color=_MUTED), x=0),
        yaxis=dict(tickvals=[0,1,2,3],
                   ticktext=["Normal","Mild","Moderate","High"],
                   range=[-0.3, 3.3], gridcolor=_GRID,
                   tickfont=dict(color=_MUTED, size=10)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    tickfont=dict(color="rgba(34,197,94,0.6)", size=9)),
        height=230,
        **{k: v for k, v in _BASE.items() if k not in ("xaxis", "yaxis", "margin")},
        margin=dict(l=8, r=8, t=36, b=8),
    )
    return f


# ── 21. History: prediction distribution (from DataFrame) ─────────────────────
def history_pred_distribution(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No distribution data yet", 220)
    d = df.copy()
    d["fatigue_level"] = pd.to_numeric(d["fatigue_level"], errors="coerce").fillna(0).astype(int)
    counts = d["fatigue_level"].value_counts().sort_index()
    labels = [_LN.get(i, str(i)) for i in counts.index]
    clrs = [_LC.get(i, _MUTED) for i in counts.index]
    f = go.Figure(go.Pie(
        labels=labels, values=counts.values, hole=0.55,
        marker=dict(colors=clrs, line=dict(color=_CARD, width=2)),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Prediction Distribution", font=dict(size=11, color=_MUTED), x=0),
        height=220, paper_bgcolor=_BG,
        font=dict(family="Inter", color=_TEXT),
        margin=dict(l=8, r=8, t=32, b=8),
        legend=dict(font=dict(color=_MUTED, size=10)),
    )
    return f


# ── 22. Keyboard / Mouse bar ──────────────────────────────────────────────────
def keyboard_bar(features: dict) -> go.Figure:
    keys   = ["key_press_count","backspace_count","scroll_count","double_click"]
    labels = ["Key Presses","Backspaces","Scrolls","Double Clicks"]
    values = [features.get(k,0) for k in keys]
    f = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=[_BLUE,_RED,_PURP,_YEL], opacity=.85,
                    line=dict(color="rgba(255,255,255,0.06)",width=.5)),
        hovertemplate="<b>%{x}</b>: %{y}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Keyboard Activity",
                   font=dict(size=11,color=_MUTED), x=0),
        height=210, **_BASE,
    )
    return f


def mouse_bar(features: dict) -> go.Figure:
    keys   = ["left_click","right_click","double_click","drag_count","scroll_count"]
    labels = ["Left Click","Right Click","Double Click","Drag","Scroll"]
    values = [features.get(k,0) for k in keys]
    f = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=[_BLUE,_ORAN,_PURP,_GREEN,_YEL], opacity=.85,
                    line=dict(color="rgba(255,255,255,0.06)",width=.5)),
        hovertemplate="<b>%{x}</b>: %{y}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Mouse Activity",
                   font=dict(size=11,color=_MUTED), x=0),
        height=210, **_BASE,
    )
    return f
