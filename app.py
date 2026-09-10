"""
app.py
------
Premium AI glassmorphism dashboard for Mental Health Fatigue Detection.
"""

import streamlit as st
from src.predict import predict_fatigue

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Fatigue Detection",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 30%, #f5f3ff 60%, #e0f2fe 100%);
    min-height: 100vh;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80vw 60vh at 10% 10%, rgba(139,92,246,.18) 0%, transparent 60%),
        radial-gradient(ellipse 60vw 50vh at 90% 20%, rgba(99,102,241,.15) 0%, transparent 55%),
        radial-gradient(ellipse 70vw 55vh at 50% 90%, rgba(6,182,212,.12) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

/* Hide Streamlit chrome */
#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 2rem 3rem 4rem !important; max-width: 1400px !important; }

/* ── Navbar ── */
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(255,255,255,.72);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,.6);
    border-radius: 20px;
    padding: 1rem 2rem;
    margin-bottom: 3rem;
    box-shadow: 0 8px 32px rgba(99,102,241,.10);
}
.navbar-brand { font-size: 1.15rem; font-weight: 700; color: #6366f1; display:flex; align-items:center; gap:.5rem; }
.navbar-links { display:flex; gap:2rem; }
.navbar-links a { color:#374151; font-size:.9rem; font-weight:500; text-decoration:none; transition:color .2s; }
.navbar-links a:hover { color:#6366f1; }

/* ── Hero ── */
.hero { text-align:center; padding: 3rem 1rem 2rem; }
.hero-badge {
    display:inline-flex; align-items:center; gap:.4rem;
    background: rgba(99,102,241,.1); border:1px solid rgba(99,102,241,.25);
    border-radius:999px; padding:.35rem 1rem; font-size:.82rem; font-weight:600;
    color:#6366f1; margin-bottom:1.5rem;
}
.hero h1 { font-size: clamp(2rem,5vw,3.2rem); font-weight:800; line-height:1.15; color:#111827; margin-bottom:.5rem; }
.hero h1 span {
    background: linear-gradient(135deg,#6366f1,#8b5cf6,#06b6d4);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.hero p { color:#6b7280; font-size:1.05rem; max-width:600px; margin:0 auto 2rem; line-height:1.7; }

/* ── Pill buttons ── */
.pill-btn {
    display:inline-flex; align-items:center; gap:.5rem;
    padding:.65rem 1.6rem; border-radius:999px; font-size:.9rem; font-weight:600;
    cursor:pointer; border:none; transition: all .25s ease;
    text-decoration:none;
}
.pill-primary {
    background: linear-gradient(135deg,#6366f1,#8b5cf6);
    color:#fff; box-shadow:0 4px 20px rgba(99,102,241,.35);
}
.pill-primary:hover { transform:translateY(-2px); box-shadow:0 8px 28px rgba(99,102,241,.45); }
.pill-secondary {
    background:rgba(255,255,255,.8); color:#374151;
    border:1px solid rgba(99,102,241,.2);
    box-shadow:0 2px 12px rgba(0,0,0,.06);
}
.pill-secondary:hover { transform:translateY(-2px); background:#fff; }

/* ── Glass card ── */
.glass-card {
    background: rgba(255,255,255,.75);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,.7);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(99,102,241,.08), 0 2px 8px rgba(0,0,0,.04);
    transition: transform .25s ease, box-shadow .25s ease;
    height: 100%;
}
.glass-card:hover { transform:translateY(-3px); box-shadow:0 16px 48px rgba(99,102,241,.14); }
.card-title { font-size:1.1rem; font-weight:700; color:#111827; margin-bottom:1.5rem; display:flex; align-items:center; gap:.5rem; }

/* ── Feature row ── */
.feature-row { margin-bottom:1.1rem; }
.feature-label { font-size:.82rem; font-weight:600; color:#374151; margin-bottom:.2rem; display:flex; justify-content:space-between; }
.feature-desc { font-size:.73rem; color:#9ca3af; margin-bottom:.4rem; }

/* ── Predict button ── */
.predict-wrap { text-align:center; margin: 2.5rem 0; }
.predict-btn {
    display:inline-flex; align-items:center; gap:.6rem;
    background: linear-gradient(135deg,#8b5cf6,#6366f1,#06b6d4);
    color:#fff; font-size:1.1rem; font-weight:700;
    padding:1rem 3rem; border-radius:999px; border:none; cursor:pointer;
    box-shadow: 0 8px 32px rgba(99,102,241,.4), 0 0 0 0 rgba(99,102,241,.3);
    transition: all .3s ease;
    animation: pulse-glow 3s infinite;
}
.predict-btn:hover { transform:translateY(-4px) scale(1.03); box-shadow:0 16px 48px rgba(99,102,241,.55); }
@keyframes pulse-glow {
    0%,100% { box-shadow:0 8px 32px rgba(99,102,241,.4), 0 0 0 0 rgba(99,102,241,.2); }
    50%      { box-shadow:0 8px 32px rgba(99,102,241,.4), 0 0 0 12px rgba(99,102,241,.0); }
}

/* ── Result card ── */
.result-card {
    background: rgba(255,255,255,.82);
    backdrop-filter:blur(24px); -webkit-backdrop-filter:blur(24px);
    border:1px solid rgba(255,255,255,.75);
    border-radius:24px; padding:2.5rem;
    box-shadow:0 12px 48px rgba(99,102,241,.12);
    text-align:center; margin:0 auto; max-width:700px;
    animation: fadeUp .5s ease;
}
@keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
.result-emoji { font-size:3.5rem; margin-bottom:.5rem; }
.result-label { font-size:1.8rem; font-weight:800; margin-bottom:.4rem; }
.result-desc { color:#6b7280; font-size:.95rem; margin-bottom:1.5rem; }
.confidence-bar-wrap { background:rgba(0,0,0,.06); border-radius:999px; height:10px; overflow:hidden; margin:.4rem 0; }
.confidence-bar { height:100%; border-radius:999px; transition:width .8s ease; }

/* ── Summary metric cards ── */
.metric-card {
    background:rgba(255,255,255,.75);
    backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
    border:1px solid rgba(255,255,255,.7);
    border-radius:20px; padding:1.5rem;
    box-shadow:0 4px 20px rgba(99,102,241,.07);
    transition:transform .25s, box-shadow .25s;
    text-align:center;
}
.metric-card:hover { transform:translateY(-4px); box-shadow:0 12px 36px rgba(99,102,241,.14); }
.metric-icon {
    width:52px; height:52px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:1.4rem; margin:0 auto .8rem;
}
.metric-value { font-size:1.7rem; font-weight:800; color:#111827; }
.metric-label { font-size:.78rem; color:#9ca3af; font-weight:500; margin-top:.2rem; }

/* ── Footer ── */
.footer {
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;
    padding:1.5rem 2rem;
    background:rgba(255,255,255,.6);
    backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
    border:1px solid rgba(255,255,255,.6);
    border-radius:20px; margin-top:3rem;
    font-size:.82rem; color:#9ca3af;
}
.footer a { color:#6366f1; text-decoration:none; font-weight:500; margin-left:1rem; }
.footer a:hover { text-decoration:underline; }

/* ── Streamlit widget overrides ── */
[data-testid="stNumberInput"] input,
[data-testid="stSlider"] { border-radius:12px !important; }
div[data-testid="stHorizontalBlock"] { gap:1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "features" not in st.session_state:
    st.session_state.features = {}

SAMPLE = dict(
    key_press_count=120, key_hold_time=0.20, typing_speed=45,
    error_rate=0.08, backspace_count=15, idle_time=8,
    mouse_click_count=25, left_click=20, right_click=5,
    double_click=2, scroll_count=10, cursor_speed=220,
    cursor_distance=1500, drag_count=2, movement_speed=200, idle_mouse_time=6,
)

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
  <div class="navbar-brand">🧠 AI Fatigue Detection</div>
  <div class="navbar-links">
    <a href="#">Home</a>
    <a href="#">About</a>
    <a href="#">How it Works</a>
    <a href="https://github.com" target="_blank">GitHub</a>
  </div>
  <div style="color:#9ca3af;font-size:.85rem;font-weight:500;">✨ Powered by XGBoost</div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">✨ AI Powered Insight</div>
  <h1>AI-Based Mental Health<br><span>Fatigue Detection</span></h1>
  <p>Predict cognitive fatigue using keyboard and mouse interaction behaviour using Machine Learning.</p>
</div>
""", unsafe_allow_html=True)

# Sample / Reset buttons
c1, c2, c3 = st.columns([3, 1, 1])
with c2:
    fill_sample = st.button("📂 Fill Sample Data", use_container_width=True)
with c3:
    reset_all = st.button("🔄 Reset All", use_container_width=True)

if fill_sample:
    for k, v in SAMPLE.items():
        st.session_state[f"feat_{k}"] = v
if reset_all:
    for k in SAMPLE:
        st.session_state[f"feat_{k}"] = 0.0
    st.session_state.result = None

st.markdown("<div style='margin-bottom:2rem'></div>", unsafe_allow_html=True)

# ── Feature cards ─────────────────────────────────────────────────────────────
KEYBOARD_FEATURES = [
    ("key_press_count",  "⌨️", "Key Press Count",   "Total keys pressed",          1.0,   0,   500,  "count"),
    ("key_hold_time",    "⏱️", "Key Hold Time",      "Avg key hold duration",       0.01,  0.0, 2.0,  "sec"),
    ("typing_speed",     "🚀", "Typing Speed",       "Words per minute",            1.0,   0,   200,  "WPM"),
    ("error_rate",       "❌", "Error Rate",         "Errors per keystroke",        0.01,  0.0, 1.0,  "%"),
    ("backspace_count",  "⬅️", "Backspace Count",    "Backspace key presses",       1.0,   0,   100,  "count"),
    ("idle_time",        "💤", "Idle Time",          "Keyboard inactivity (sec)",   1.0,   0,   300,  "sec"),
]
MOUSE_FEATURES = [
    ("mouse_click_count","🖱️", "Mouse Click Count",  "Total mouse clicks",          1.0,   0,   300,  "count"),
    ("left_click",       "👆", "Left Click",         "Left button clicks",          1.0,   0,   300,  "count"),
    ("right_click",      "👉", "Right Click",        "Right button clicks",         1.0,   0,   100,  "count"),
    ("double_click",     "⚡", "Double Click",       "Double click events",         1.0,   0,   50,   "count"),
    ("cursor_speed",     "💨", "Cursor Speed",       "Pixels per second",           1.0,   0,   2000, "px/s"),
    ("cursor_distance",  "📏", "Cursor Distance",    "Total pixels moved",          10.0,  0,   10000,"px"),
    ("drag_count",       "🤚", "Drag Count",         "Click-and-drag events",       1.0,   0,   50,   "count"),
    ("movement_speed",   "🏃", "Movement Speed",     "Avg movement speed",          1.0,   0,   2000, "px/s"),
    ("idle_mouse_time",  "🕐", "Idle Mouse Time",    "Mouse inactivity (sec)",      1.0,   0,   300,  "sec"),
]

def feature_inputs(features_def):
    vals = {}
    for key, icon, label, desc, step, mn, mx, unit in features_def:
        default = float(st.session_state.get(f"feat_{key}", SAMPLE.get(key, 0)))
        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.markdown(f"""
            <div class="feature-label">{icon} {label} <span style="color:#9ca3af;font-weight:400">{unit}</span></div>
            <div class="feature-desc">{desc}</div>
            """, unsafe_allow_html=True)
            slider_val = st.slider(f"_s_{key}", min_value=float(mn), max_value=float(mx),
                                   value=min(default, float(mx)), step=float(step),
                                   label_visibility="collapsed", key=f"sl_{key}")
        with col_r:
            num_val = st.number_input(f"_n_{key}", min_value=float(mn), max_value=float(mx),
                                      value=slider_val, step=float(step),
                                      label_visibility="collapsed", key=f"ni_{key}")
        vals[key] = num_val
    return vals

left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">⌨️ Keyboard Features</div>', unsafe_allow_html=True)
    kb_vals = feature_inputs(KEYBOARD_FEATURES)
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🖱️ Mouse Features</div>', unsafe_allow_html=True)
    ms_vals = feature_inputs(MOUSE_FEATURES)
    st.markdown('</div>', unsafe_allow_html=True)

features = {**kb_vals, **ms_vals}

# ── Predict button ────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:2.5rem'></div>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    predict_clicked = st.button("✨ Predict Fatigue", use_container_width=True, type="primary")

if predict_clicked:
    with st.spinner("Analysing behaviour patterns…"):
        try:
            label, confidence = predict_fatigue(features)
            st.session_state.result = (label, confidence)
            st.session_state.features = features
        except FileNotFoundError as e:
            st.error(str(e))
            st.info("Train the model first: `python src/train_model.py`")

# ── Result ────────────────────────────────────────────────────────────────────
if st.session_state.result:
    label, confidence = st.session_state.result
    feats = st.session_state.features

    CONFIG = {
        "Normal":           ("🟢", "#22c55e", "Everything looks normal.", "Keep maintaining healthy work habits."),
        "Moderate Fatigue": ("🟡", "#f59e0b", "Moderate fatigue detected.", "Consider taking a short break."),
        "High Fatigue":     ("🔴", "#ef4444", "High fatigue detected.", "Please rest and step away from the screen."),
    }
    emoji, color, line1, line2 = CONFIG.get(label, ("🔵", "#6366f1", "", ""))

    # Probability bars (approximate from confidence)
    if label == "Normal":
        probs = {"Normal": confidence, "Moderate Fatigue": (1-confidence)*0.6, "High Fatigue": (1-confidence)*0.4}
    elif label == "Moderate Fatigue":
        probs = {"Normal": (1-confidence)*0.5, "Moderate Fatigue": confidence, "High Fatigue": (1-confidence)*0.5}
    else:
        probs = {"Normal": (1-confidence)*0.3, "Moderate Fatigue": (1-confidence)*0.7, "High Fatigue": confidence}

    bar_colors = {"Normal": "#22c55e", "Moderate Fatigue": "#f59e0b", "High Fatigue": "#ef4444"}

    prob_bars = "".join([
        f"""<div style="display:flex;align-items:center;gap:.8rem;margin:.4rem 0">
              <span style="width:130px;font-size:.8rem;color:#374151;font-weight:500">{k}</span>
              <div class="confidence-bar-wrap" style="flex:1">
                <div class="confidence-bar" style="width:{v*100:.1f}%;background:{bar_colors[k]}"></div>
              </div>
              <span style="width:42px;font-size:.8rem;color:#6b7280;text-align:right">{v*100:.1f}%</span>
            </div>"""
        for k, v in probs.items()
    ])

    st.markdown(f"""
    <div class="result-card" style="border-top:4px solid {color}">
      <div class="result-emoji">{emoji}</div>
      <div class="result-label" style="color:{color}">{label}</div>
      <div class="result-desc">{line1}<br>{line2}</div>
      <div style="margin:1.2rem 0">
        <div style="font-size:.82rem;font-weight:600;color:#374151;margin-bottom:.6rem">
          Confidence Score: <span style="color:{color}">{confidence:.1%}</span>
        </div>
        <div class="confidence-bar-wrap">
          <div class="confidence-bar" style="width:{confidence*100:.1f}%;background:linear-gradient(90deg,{color},{color}88)"></div>
        </div>
      </div>
      <div style="margin-top:1.2rem">
        <div style="font-size:.82rem;font-weight:600;color:#374151;margin-bottom:.6rem">Probability Distribution</div>
        {prob_bars}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary metric cards ──────────────────────────────────────────────────
    st.markdown("<div style='margin-top:2.5rem'></div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4, gap="medium")

    typing_spd = feats.get("typing_speed", 0)
    clicks     = feats.get("mouse_click_count", 0)
    idle       = feats.get("idle_time", 0)
    activity   = "Low" if idle > 60 else ("Normal" if idle < 20 else "Moderate")

    cards = [
        (m1, "⌨️", "linear-gradient(135deg,#6366f1,#8b5cf6)", f"{typing_spd:.0f} WPM", "Typing Speed"),
        (m2, "🖱️", "linear-gradient(135deg,#06b6d4,#6366f1)", f"{clicks:.0f} Total",   "Mouse Clicks"),
        (m3, "⚡", "linear-gradient(135deg,#f59e0b,#ef4444)", activity,                 "Activity Level"),
        (m4, "🧠", f"linear-gradient(135deg,{color},{color}88)", label.split()[0],      "Fatigue Level"),
    ]
    for col, icon, grad, val, lbl in cards:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-icon" style="background:{grad}">{icon}</div>
              <div class="metric-value">{val}</div>
              <div class="metric-label">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
  <span>© 2026 AI-Based Mental Health Fatigue Detection</span>
  <div>
    <a href="https://github.com" target="_blank">GitHub</a>
    <a href="https://twitter.com" target="_blank">Twitter</a>
    <a href="https://linkedin.com" target="_blank">LinkedIn</a>
    <a href="#top">↑ Back to Top</a>
  </div>
</div>
""", unsafe_allow_html=True)
