"""
charts.py
---------
All Plotly chart builders — premium dark theme, fully interactive.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Theme constants ───────────────────────────────────────────────────────────
_BG    = "#07111F"
_CARD  = "#111827"
_CARD2 = "#1a2332"
_GRID  = "rgba(255,255,255,0.05)"
_TEXT  = "#F8FAFC"
_MUTED = "#94A3B8"
_BLUE  = "#2563EB"
_PURP  = "#8B5CF6"
_GREEN = "#22C55E"
_YEL   = "#FACC15"
_ORAN  = "#F97316"
_RED   = "#EF4444"

_LC = {0: _GREEN, 1: _YEL, 2: _ORAN, 3: _RED}
_LN = {0: "Normal", 1: "Mild", 2: "Moderate", 3: "Severe"}

_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=_TEXT, size=11),
    margin=dict(l=8, r=8, t=32, b=8),
    xaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickfont=dict(color=_MUTED, size=10), linecolor=_GRID),
    yaxis=dict(gridcolor=_GRID, zerolinecolor=_GRID, tickfont=dict(color=_MUTED, size=10), linecolor=_GRID),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=_MUTED, size=10), orientation="h", y=-0.15),
    hoverlabel=dict(bgcolor=_CARD2, font_color=_TEXT, bordercolor=_GRID),
)

def _fig(height=260) -> go.Figure:
    f = go.Figure()
    f.update_layout(height=height, **_BASE)
    return f

def _empty(msg="Waiting for data…", height=240) -> go.Figure:
    f = _fig(height)
    f.add_annotation(text=msg, x=0.5, y=0.5, showarrow=False,
                     font=dict(color=_MUTED, size=13), xref="paper", yref="paper")
    return f


# ── 1. Fatigue trend ──────────────────────────────────────────────────────────
def fatigue_trend_chart(history: list) -> go.Figure:
    if not history:
        return _empty("Waiting for predictions…", 270)
    df = pd.DataFrame(history).sort_values("timestamp")
    df["col"] = df["level"].map(_LC).fillna(_MUTED)
    f = go.Figure()
    # Gradient fill
    f.add_trace(go.Scatter(
        x=df["timestamp"], y=df["level"],
        fill="tozeroy", fillcolor="rgba(37,99,235,0.07)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip",
    ))
    # Spline line
    f.add_trace(go.Scatter(
        x=df["timestamp"], y=df["level"],
        mode="lines+markers",
        line=dict(color=_BLUE, width=2.5, shape="spline", smoothing=1.2),
        marker=dict(color=df["col"].tolist(), size=9, line=dict(color=_CARD, width=2)),
        name="Fatigue Level",
        hovertemplate="<b>%{text}</b><br>%{x|%H:%M:%S}<extra></extra>",
        text=df["level"].map(_LN),
    ))
    # Confidence band if available
    if "confidence" in df.columns:
        f.add_trace(go.Scatter(
            x=df["timestamp"], y=df["confidence"],
            mode="lines", name="Confidence",
            line=dict(color=_PURP, width=1.5, dash="dot"),
            yaxis="y2",
            hovertemplate="Conf: %{y:.1%}<extra></extra>",
        ))
    f.update_layout(
        height=270,
        yaxis=dict(tickvals=[0,1,2], ticktext=["Normal","Moderate","High"],
                   range=[-0.25,2.4], gridcolor=_GRID, tickfont=dict(color=_MUTED,size=10)),
        yaxis2=dict(overlaying="y", side="right", range=[0,1.1],
                    tickformat=".0%", tickfont=dict(color=_PURP,size=9),
                    showgrid=False, title=""),
        xaxis=dict(gridcolor=_GRID, tickfont=dict(color=_MUTED,size=10)),
        title=dict(text="Live Fatigue Trend", font=dict(size=12,color=_MUTED), x=0),
        **{k:v for k,v in _BASE.items() if k not in ("xaxis","yaxis","margin")},
        margin=dict(l=8,r=8,t=36,b=8),
    )
    return f


# ── 2. Confidence gauge ───────────────────────────────────────────────────────
def confidence_gauge(confidence: float, level: int = 0) -> go.Figure:
    color = _LC.get(level, _BLUE)
    f = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(confidence * 100, 1),
        delta=dict(reference=75, valueformat=".1f", suffix="%",
                   increasing=dict(color=_GREEN), decreasing=dict(color=_RED)),
        number=dict(suffix="%", font=dict(size=30, color=color, family="Inter")),
        gauge=dict(
            axis=dict(range=[0,100], tickfont=dict(color=_MUTED,size=8), tickcolor=_MUTED,
                      tickwidth=1, ticklen=4),
            bar=dict(color=color, thickness=0.24),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[
                dict(range=[0,50],  color="rgba(255,255,255,0.03)"),
                dict(range=[50,75], color="rgba(255,255,255,0.05)"),
                dict(range=[75,100],color="rgba(255,255,255,0.07)"),
            ],
            threshold=dict(line=dict(color=color,width=3), thickness=0.8, value=confidence*100),
        ),
        title=dict(text=f"<b>{_LN.get(level,'Normal')}</b>", font=dict(size=11,color=_MUTED)),
    ))
    f.update_layout(height=210, paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter",color=_TEXT), margin=dict(l=16,r=16,t=24,b=8))
    return f


# ── 3. Probability donut ──────────────────────────────────────────────────────
def probability_donut(probs: dict) -> go.Figure:
    vals = [probs.get("normal",0), probs.get("moderate",0), probs.get("high",0)]
    if sum(vals) == 0:
        vals = [0.34, 0.33, 0.33]
    f = go.Figure(go.Pie(
        labels=["Normal","Moderate","High"], values=vals, hole=0.68,
        marker=dict(colors=[_GREEN,_ORAN,_RED], line=dict(color=_CARD,width=2)),
        textfont=dict(size=10,color=_TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        sort=False,
    ))
    f.update_layout(
        height=210, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=8,r=8,t=8,b=8),
        legend=dict(orientation="h", y=-0.08, font=dict(color=_MUTED,size=9)),
        annotations=[dict(text="Prob", x=0.5, y=0.5, font_size=11,
                          font_color=_MUTED, showarrow=False)],
    )
    return f


# ── 4. SHAP bar ───────────────────────────────────────────────────────────────
def shap_bar_chart(shap_vals: list, feature_names: list) -> go.Figure:
    if not shap_vals:
        return _empty("SHAP values unavailable", 300)
    pairs = sorted(zip(feature_names, shap_vals), key=lambda x: abs(x[1]), reverse=True)[:10]
    labels = [p[0].replace("_"," ").title() for p in pairs]
    values = [p[1] for p in pairs]
    colors = [_RED if v > 0 else _GREEN for v in values]
    f = go.Figure(go.Bar(
        x=values[::-1], y=labels[::-1], orientation="h",
        marker=dict(color=colors[::-1], opacity=0.88,
                    line=dict(color="rgba(255,255,255,0.08)",width=0.5)),
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:.5f}<extra></extra>",
    ))
    f.add_vline(x=0, line_color=_MUTED, line_width=1, line_dash="dot")
    f.update_layout(
        title=dict(text="SHAP Feature Contributions (Top 10)", font=dict(size=11,color=_MUTED), x=0),
        xaxis_title="Impact on Fatigue Score",
        height=310, **_BASE,
    )
    return f


# ── 5. Feature importance ─────────────────────────────────────────────────────
def feature_importance_chart(importances: dict) -> go.Figure:
    if not importances:
        return _empty("Feature importance unavailable", 320)
    items = sorted(importances.items(), key=lambda x: x[1])
    labels = [k.replace("_"," ").title() for k,_ in items]
    values = [v for _,v in items]
    mx = max(values) if values else 1
    colors = [f"rgba(37,99,235,{0.35 + 0.65*v/mx})" for v in values]
    f = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.06)",width=0.5)),
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="XGBoost Feature Importance", font=dict(size=11,color=_MUTED), x=0),
        height=320, **_BASE,
    )
    return f


# ── 6. Activity timeline ──────────────────────────────────────────────────────
def activity_timeline_chart(timeline: list) -> go.Figure:
    if not timeline:
        return _empty("Activity timeline will appear here", 240)
    df = pd.DataFrame(timeline).sort_values("timestamp")
    f = go.Figure()
    traces = [
        ("typing_speed",    "Typing Speed (WPM)", _BLUE),
        ("cursor_speed",    "Cursor Speed (px/s)", _PURP),
        ("key_press_count", "Key Presses",         _GREEN),
        ("mouse_click_count","Mouse Clicks",        _ORAN),
    ]
    for col, name, color in traces:
        if col in df.columns:
            f.add_trace(go.Scatter(
                x=df["timestamp"], y=df[col], name=name,
                mode="lines", line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<br>%{{x|%H:%M:%S}}<extra></extra>",
            ))
    f.update_layout(
        title=dict(text="Activity Timeline", font=dict(size=11,color=_MUTED), x=0),
        height=240, **_BASE,
    )
    return f


# ── 7. Keyboard bar ───────────────────────────────────────────────────────────
def keyboard_bar(features: dict) -> go.Figure:
    keys   = ["key_press_count","backspace_count","scroll_count","double_click"]
    labels = ["Key Presses","Backspaces","Scrolls","Double Clicks"]
    values = [features.get(k,0) for k in keys]
    colors = [_BLUE, _RED, _PURP, _YEL]
    f = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, opacity=0.85,
                    line=dict(color="rgba(255,255,255,0.08)",width=0.5)),
        hovertemplate="<b>%{x}</b>: %{y}<extra></extra>",
    ))
    f.update_layout(title=dict(text="Keyboard Activity", font=dict(size=11,color=_MUTED),x=0),
                    height=210, **_BASE)
    return f


# ── 8. Mouse bar ──────────────────────────────────────────────────────────────
def mouse_bar(features: dict) -> go.Figure:
    keys   = ["left_click","right_click","double_click","drag_count","scroll_count"]
    labels = ["Left Click","Right Click","Double Click","Drag","Scroll"]
    values = [features.get(k,0) for k in keys]
    colors = [_BLUE, _ORAN, _PURP, _GREEN, _YEL]
    f = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, opacity=0.85,
                    line=dict(color="rgba(255,255,255,0.08)",width=0.5)),
        hovertemplate="<b>%{x}</b>: %{y}<extra></extra>",
    ))
    f.update_layout(title=dict(text="Mouse Activity", font=dict(size=11,color=_MUTED),x=0),
                    height=210, **_BASE)
    return f


# ── 9. Analytics bar (daily/weekly/monthly) ───────────────────────────────────
def analytics_bar(records: list, period: str = "daily") -> go.Figure:
    if not records:
        return _empty("No data yet — start monitoring to populate analytics", 260)
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
            cmin=0, cmax=2, showscale=False,
            line=dict(color="rgba(255,255,255,0.06)",width=0.5),
        ),
        hovertemplate="<b>%{x}</b><br>Avg Fatigue: %{y:.2f}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text=f"{period.title()} Fatigue Average", font=dict(size=11,color=_MUTED),x=0),
        height=260, **_BASE,
    )
    return f


# ── 10. Prediction distribution ───────────────────────────────────────────────
def prediction_distribution(records: list) -> go.Figure:
    if not records:
        return _empty("No predictions yet", 240)
    df = pd.DataFrame(records)
    counts = df["fatigue_level"].value_counts().sort_index()
    labels = [_LN.get(int(i), str(i)) for i in counts.index]
    colors = [_LC.get(int(i), _MUTED) for i in counts.index]
    f = go.Figure(go.Pie(
        labels=labels, values=counts.values, hole=0.52,
        marker=dict(colors=colors, line=dict(color=_CARD,width=2)),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text="Prediction Distribution", font=dict(size=11,color=_MUTED),x=0),
        height=240, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=8,r=8,t=32,b=8),
        legend=dict(font=dict(color=_MUTED,size=10)),
    )
    return f


# ── 11. Hourly heatmap ────────────────────────────────────────────────────────
def hourly_heatmap(records: list) -> go.Figure:
    if not records:
        return _empty("No data for heatmap yet", 220)
    df = pd.DataFrame(records)
    df["ts"]   = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["ts"])
    df["hour"] = df["ts"].dt.hour
    df["day"]  = df["ts"].dt.day_name()
    pivot = df.pivot_table(values="fatigue_level", index="day", columns="hour", aggfunc="mean")
    f = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale=[[0,_GREEN],[0.5,_ORAN],[1,_RED]],
        zmin=0, zmax=2,
        hovertemplate="<b>%{y} %{x}:00</b><br>Avg Fatigue: %{z:.2f}<extra></extra>",
        colorbar=dict(tickfont=dict(color=_MUTED,size=9), len=0.8),
    ))
    f.update_layout(
        title=dict(text="Hourly Fatigue Heatmap", font=dict(size=11,color=_MUTED),x=0),
        height=220, **_BASE,
    )
    return f


# ── 12. Confusion matrix heatmap ──────────────────────────────────────────────
def confusion_matrix_chart(cm: list, labels: list) -> go.Figure:
    f = go.Figure(go.Heatmap(
        z=cm, x=labels, y=labels,
        colorscale=[[0,"rgba(37,99,235,0.1)"],[1,"rgba(37,99,235,0.9)"]],
        text=cm, texttemplate="%{text}", textfont=dict(size=14,color=_TEXT),
        hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Count: %{z}<extra></extra>",
        showscale=False,
    ))
    f.update_layout(
        title=dict(text="Confusion Matrix", font=dict(size=11,color=_MUTED),x=0),
        xaxis=dict(title="Predicted", tickfont=dict(color=_MUTED,size=10)),
        yaxis=dict(title="Actual",    tickfont=dict(color=_MUTED,size=10)),
        height=280, **{k:v for k,v in _BASE.items() if k not in ("xaxis","yaxis")},
    )
    return f


# ── 13. Radar chart (feature profile) ────────────────────────────────────────
def radar_chart(features: dict, baseline: dict) -> go.Figure:
    keys = ["typing_speed","key_press_count","cursor_speed",
            "mouse_click_count","scroll_count","idle_time"]
    labels = ["Typing Speed","Key Presses","Cursor Speed",
              "Mouse Clicks","Scrolls","Idle Time"]
    curr_vals = [features.get(k,0) for k in keys]
    base_vals = [baseline.get(k,0) for k in keys]
    # Normalize to 0-1
    mx = [max(c,b,1) for c,b in zip(curr_vals,base_vals)]
    curr_n = [v/m for v,m in zip(curr_vals,mx)]
    base_n = [v/m for v,m in zip(base_vals,mx)]
    f = go.Figure()
    f.add_trace(go.Scatterpolar(
        r=curr_n+[curr_n[0]], theta=labels+[labels[0]],
        fill="toself", fillcolor="rgba(37,99,235,0.15)",
        line=dict(color=_BLUE,width=2), name="Current",
    ))
    f.add_trace(go.Scatterpolar(
        r=base_n+[base_n[0]], theta=labels+[labels[0]],
        fill="toself", fillcolor="rgba(139,92,246,0.1)",
        line=dict(color=_PURP,width=2,dash="dot"), name="Baseline",
    ))
    f.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,1], tickfont=dict(color=_MUTED,size=8),
                            gridcolor=_GRID, linecolor=_GRID),
            angularaxis=dict(tickfont=dict(color=_MUTED,size=9), gridcolor=_GRID, linecolor=_GRID),
        ),
        title=dict(text="Behavior Profile vs Baseline", font=dict(size=11,color=_MUTED),x=0),
        height=280, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter",color=_TEXT),
        margin=dict(l=40,r=40,t=36,b=8),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color=_MUTED,size=10)),
    )
    return f


# ── 14. Typing speed sparkline ────────────────────────────────────────────────
def sparkline(timeline: list, col: str, color: str, title: str) -> go.Figure:
    if not timeline:
        return _empty(f"No {title} data", 120)
    df = pd.DataFrame(timeline).sort_values("timestamp")
    if col not in df.columns:
        return _empty(f"No {title} data", 120)
    f = go.Figure(go.Scatter(
        x=df["timestamp"], y=df[col],
        mode="lines", fill="tozeroy",
        fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.12)",
        line=dict(color=color, width=2, shape="spline"),
        hovertemplate=f"%{{y:.1f}}<br>%{{x|%H:%M:%S}}<extra></extra>",
    ))
    f.update_layout(
        title=dict(text=title, font=dict(size=10,color=_MUTED),x=0),
        height=120,
        xaxis=dict(showticklabels=False, gridcolor=_GRID, linecolor=_GRID),
        yaxis=dict(gridcolor=_GRID, tickfont=dict(color=_MUTED,size=9)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8,r=8,t=28,b=4),
        font=dict(family="Inter",color=_TEXT),
        showlegend=False,
    )
    return f
