"""
styles.py
---------
Complete premium dark-theme CSS + icon fonts for the enterprise dashboard.
"""

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

/* ── Design tokens ── */
:root {
  --bg:       #07111F;
  --card:     #111827;
  --card2:    #1a2332;
  --card3:    #0f1c2e;
  --border:   rgba(255,255,255,0.07);
  --border2:  rgba(255,255,255,0.12);
  --blue:     #2563EB;
  --blue2:    #3b82f6;
  --purple:   #8B5CF6;
  --green:    #22C55E;
  --yellow:   #FACC15;
  --orange:   #F97316;
  --red:      #EF4444;
  --text:     #F8FAFC;
  --muted:    #94A3B8;
  --muted2:   #64748B;
  --radius:   16px;
  --radius-sm:10px;
  --shadow:   0 8px 32px rgba(0,0,0,0.45);
  --shadow-lg:0 20px 60px rgba(0,0,0,0.6);
}

/* ── Global reset ── */
*, *::before, *::after { box-sizing: border-box; }
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main .block-container {
  background-color: var(--bg) !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  color: var(--text) !important;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0a1628 0%, #07111F 60%, #050e18 100%) !important;
  border-right: 1px solid var(--border) !important;
  min-width: 220px !important;
}
[data-testid="stSidebarContent"] { padding: .75rem .6rem !important; }
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; visibility: hidden !important; }
.block-container { padding: .75rem 1.25rem 2rem !important; max-width: 100% !important; }
section[data-testid="stSidebar"] > div { width: 230px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,.2); }

/* ══════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════ */
.sb-logo {
  display: flex; align-items: center; gap: .65rem;
  padding: .6rem .4rem 1rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: .75rem;
}
.sb-logo-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: linear-gradient(135deg, var(--blue), var(--purple));
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(37,99,235,.4);
}
.sb-logo-text { font-size: .88rem; font-weight: 800; line-height: 1.15; }
.sb-logo-sub  { font-size: .6rem; color: var(--muted); font-weight: 500; letter-spacing: .04em; }

.sb-section {
  font-size: .58rem; font-weight: 700; letter-spacing: .12em;
  text-transform: uppercase; color: var(--muted2);
  padding: .5rem .4rem .25rem; margin-top: .25rem;
}
.sb-nav-btn {
  display: flex; align-items: center; gap: .55rem;
  padding: .55rem .75rem; border-radius: var(--radius-sm);
  font-size: .82rem; font-weight: 500; color: var(--muted);
  cursor: pointer; transition: all .18s; margin-bottom: .15rem;
  border: 1px solid transparent; width: 100%;
  background: transparent; text-align: left;
}
.sb-nav-btn:hover { background: rgba(37,99,235,.12); color: var(--blue2); border-color: rgba(37,99,235,.2); }
.sb-nav-btn.active {
  background: rgba(37,99,235,.18); color: #93c5fd;
  border-color: rgba(37,99,235,.35);
  border-left: 3px solid var(--blue);
}
.sb-footer {
  font-size: .68rem; color: var(--muted2); padding: .5rem .4rem;
  border-top: 1px solid var(--border); margin-top: .5rem;
  line-height: 1.8;
}
.sb-footer b { color: var(--muted); }

/* ══════════════════════════════════════════
   HEADER
══════════════════════════════════════════ */
.app-header {
  background: linear-gradient(135deg, rgba(37,99,235,.1) 0%, rgba(139,92,246,.07) 100%);
  border: 1px solid rgba(37,99,235,.22);
  border-radius: var(--radius);
  padding: .9rem 1.4rem;
  margin-bottom: 1rem;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: .75rem;
  position: relative; overflow: hidden;
}
.app-header::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--blue), var(--purple), var(--blue));
  background-size: 200% 100%; animation: gradMove 4s linear infinite;
}
@keyframes gradMove { 0%{background-position:0% 0%} 100%{background-position:200% 0%} }
.app-title {
  font-size: 1.2rem; font-weight: 900; letter-spacing: -.02em;
  background: linear-gradient(135deg, #93c5fd, #c4b5fd);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.app-subtitle { font-size: .72rem; color: var(--muted); margin-top: .1rem; letter-spacing: .02em; }
.hdr-right { display: flex; gap: 1.25rem; align-items: center; flex-wrap: wrap; }
.hdr-stat { text-align: right; }
.hdr-stat-label { font-size: .6rem; color: var(--muted2); text-transform: uppercase; letter-spacing: .08em; }
.hdr-stat-value { font-size: .88rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: var(--text); }

/* ══════════════════════════════════════════
   BADGES & PILLS
══════════════════════════════════════════ */
.badge {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .2rem .65rem; border-radius: 999px;
  font-size: .65rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
}
.badge-live   { background: rgba(34,197,94,.15);  color: var(--green);  border: 1px solid rgba(34,197,94,.3); }
.badge-green  { background: rgba(34,197,94,.15);  color: var(--green);  border: 1px solid rgba(34,197,94,.3); }
.badge-yellow { background: rgba(250,204,21,.15); color: var(--yellow); border: 1px solid rgba(250,204,21,.3); }
.badge-orange { background: rgba(249,115,22,.15); color: var(--orange); border: 1px solid rgba(249,115,22,.3); }
.badge-red    { background: rgba(239,68,68,.15);  color: var(--red);    border: 1px solid rgba(239,68,68,.3); }
.badge-blue   { background: rgba(37,99,235,.15);  color: #93c5fd;       border: 1px solid rgba(37,99,235,.3); }
.badge-purple { background: rgba(139,92,246,.15); color: #c4b5fd;       border: 1px solid rgba(139,92,246,.3); }
.badge-gray   { background: rgba(148,163,184,.1); color: var(--muted);  border: 1px solid rgba(148,163,184,.2); }

/* ══════════════════════════════════════════
   PULSE ANIMATIONS
══════════════════════════════════════════ */
.pulse-dot {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px;
}
.pulse-green  { background: var(--green);  animation: pulseG 2s infinite; }
.pulse-yellow { background: var(--yellow); animation: pulseY 2s infinite; }
.pulse-orange { background: var(--orange); animation: pulseO 2s infinite; }
.pulse-red    { background: var(--red);    animation: pulseR 2s infinite; }
@keyframes pulseG { 0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.5)}  50%{box-shadow:0 0 0 6px rgba(34,197,94,0)} }
@keyframes pulseY { 0%,100%{box-shadow:0 0 0 0 rgba(250,204,21,.5)} 50%{box-shadow:0 0 0 6px rgba(250,204,21,0)} }
@keyframes pulseO { 0%,100%{box-shadow:0 0 0 0 rgba(249,115,22,.5)} 50%{box-shadow:0 0 0 6px rgba(249,115,22,0)} }
@keyframes pulseR { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5)}  50%{box-shadow:0 0 0 6px rgba(239,68,68,0)} }

/* ══════════════════════════════════════════
   KPI CARDS
══════════════════════════════════════════ */
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: .75rem; margin-bottom: .75rem; }
.kpi-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.1rem 1.25rem;
  box-shadow: var(--shadow); transition: all .22s;
  position: relative; overflow: hidden;
}
.kpi-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); border-color: var(--border2); }
.kpi-card::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.06), transparent);
}
.kpi-label {
  font-size: .62rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted); margin-bottom: .4rem;
  display: flex; align-items: center; gap: .35rem;
}
.kpi-value {
  font-size: 1.65rem; font-weight: 900; line-height: 1.05;
  margin-bottom: .2rem; letter-spacing: -.02em;
}
.kpi-sub { font-size: .72rem; color: var(--muted); }
.kpi-sub b { color: var(--text); }
.kpi-icon {
  position: absolute; top: .9rem; right: 1rem;
  font-size: 1.8rem; opacity: .1; pointer-events: none;
}
.kpi-trend {
  position: absolute; bottom: .75rem; right: 1rem;
  font-size: .65rem; font-weight: 700;
}

/* ══════════════════════════════════════════
   SECTION TITLES
══════════════════════════════════════════ */
.sec-title {
  font-size: .62rem; font-weight: 800; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted);
  margin-bottom: .6rem; display: flex; align-items: center; gap: .5rem;
}
.sec-title::after {
  content: ''; flex: 1; height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,.07), transparent);
}

/* ══════════════════════════════════════════
   METRIC TILES (keyboard / mouse)
══════════════════════════════════════════ */
.metric-tile {
  background: var(--card2); border-radius: var(--radius-sm);
  padding: .65rem .9rem; border-left: 3px solid transparent;
  transition: all .18s; margin-bottom: .4rem;
}
.metric-tile:hover { background: #1e2d42; transform: translateX(2px); }
.metric-tile-label { font-size: .6rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.metric-tile-value { font-size: 1.05rem; font-weight: 700; margin-top: .1rem; }

/* ══════════════════════════════════════════
   CARDS
══════════════════════════════════════════ */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 1.1rem 1.25rem;
  box-shadow: var(--shadow); position: relative; overflow: hidden;
}
.card-glass {
  background: rgba(17,24,39,.8); backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,.09);
  border-radius: var(--radius); padding: 1.1rem 1.25rem;
  box-shadow: var(--shadow);
}
.card-accent-top::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--blue), var(--purple));
}

/* ══════════════════════════════════════════
   RECOMMENDATION CARD
══════════════════════════════════════════ */
.rec-card {
  border-radius: var(--radius); padding: 1.75rem 1.5rem;
  text-align: center; position: relative; overflow: hidden;
  transition: all .25s;
}
.rec-card:hover { transform: scale(1.01); }
.rec-card-green  { background: linear-gradient(135deg,rgba(34,197,94,.14),rgba(34,197,94,.04));  border:1px solid rgba(34,197,94,.3); }
.rec-card-yellow { background: linear-gradient(135deg,rgba(250,204,21,.14),rgba(250,204,21,.04)); border:1px solid rgba(250,204,21,.3); }
.rec-card-orange { background: linear-gradient(135deg,rgba(249,115,22,.14),rgba(249,115,22,.04)); border:1px solid rgba(249,115,22,.3); }
.rec-card-red    { background: linear-gradient(135deg,rgba(239,68,68,.14), rgba(239,68,68,.04));  border:1px solid rgba(239,68,68,.3); }
.rec-icon  { font-size: 3rem; margin-bottom: .6rem; display: block; }
.rec-title { font-size: 1.25rem; font-weight: 900; margin-bottom: .35rem; letter-spacing: -.01em; }
.rec-sub   { font-size: .8rem; color: var(--muted); line-height: 1.5; }

/* ══════════════════════════════════════════
   SYSTEM HEALTH
══════════════════════════════════════════ */
.health-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: .5rem 0; border-bottom: 1px solid var(--border); font-size: .8rem;
}
.health-row:last-child { border-bottom: none; }
.health-name { display: flex; align-items: center; gap: .5rem; color: var(--text); }
.health-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.h-ok   { background: var(--green);  box-shadow: 0 0 5px var(--green); }
.h-warn { background: var(--yellow); box-shadow: 0 0 5px var(--yellow); }
.h-err  { background: var(--red);    box-shadow: 0 0 5px var(--red); }
.health-status { font-size: .68rem; font-weight: 700; letter-spacing: .05em; }

/* ══════════════════════════════════════════
   BASELINE TABLE
══════════════════════════════════════════ */
.bl-table { width: 100%; border-collapse: collapse; font-size: .8rem; }
.bl-table th {
  font-size: .6rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted2);
  padding: .4rem .5rem; border-bottom: 1px solid var(--border);
  text-align: left;
}
.bl-table td { padding: .45rem .5rem; border-bottom: 1px solid rgba(255,255,255,.04); }
.bl-table tr:last-child td { border-bottom: none; }
.bl-table tr:hover td { background: rgba(37,99,235,.05); }
.delta-up   { color: var(--red);    font-weight: 700; }
.delta-down { color: var(--green);  font-weight: 700; }
.delta-flat { color: var(--muted);  font-weight: 600; }

/* ══════════════════════════════════════════
   LIVE EVENT TABLE
══════════════════════════════════════════ */
.evt-table { width: 100%; border-collapse: collapse; font-size: .76rem; }
.evt-table th {
  font-size: .58rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted2);
  padding: .35rem .5rem; border-bottom: 1px solid var(--border);
  text-align: left; white-space: nowrap;
}
.evt-table td { padding: .38rem .5rem; border-bottom: 1px solid rgba(255,255,255,.03); white-space: nowrap; }
.evt-table tr:hover td { background: rgba(37,99,235,.06); }
.evt-time { color: var(--muted); font-family: monospace; font-size: .72rem; }

/* ══════════════════════════════════════════
   PRIVACY PANEL
══════════════════════════════════════════ */
.priv-item {
  display: flex; align-items: center; gap: .6rem;
  padding: .55rem 0; border-bottom: 1px solid var(--border);
  font-size: .82rem; color: var(--text);
}
.priv-item:last-child { border-bottom: none; }
.priv-check { color: var(--green); font-size: .95rem; flex-shrink: 0; }

/* ══════════════════════════════════════════
   PIPELINE FLOW
══════════════════════════════════════════ */
.pipeline-wrap { display: flex; flex-direction: column; align-items: center; gap: 0; }
.pipeline-step {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--radius-sm); padding: .55rem 1.5rem;
  font-size: .78rem; font-weight: 600; color: var(--text);
  text-align: center; width: 260px; position: relative;
  transition: all .2s;
}
.pipeline-step:hover { background: rgba(37,99,235,.15); border-color: rgba(37,99,235,.4); }
.pipeline-step.active { background: rgba(37,99,235,.2); border-color: var(--blue); color: #93c5fd; }
.pipeline-arrow {
  color: var(--muted2); font-size: .9rem; line-height: 1;
  padding: .1rem 0; user-select: none;
}

/* ══════════════════════════════════════════
   SKELETON LOADER
══════════════════════════════════════════ */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position:  400px 0; }
}
.skeleton {
  background: linear-gradient(90deg, var(--card) 25%, var(--card2) 50%, var(--card) 75%);
  background-size: 400px 100%; animation: shimmer 1.6s infinite;
  border-radius: 6px;
}

/* ══════════════════════════════════════════
   ANIMATED VALUE
══════════════════════════════════════════ */
@keyframes fadeUp { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
.anim-val { animation: fadeUp .35s ease-out; }

/* ══════════════════════════════════════════
   STREAMLIT OVERRIDES
══════════════════════════════════════════ */
/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--card) !important; border-radius: 12px !important;
  padding: 3px !important; gap: 3px !important; border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--muted) !important;
  border-radius: 9px !important; font-weight: 600 !important;
  font-size: .78rem !important; padding: .4rem .9rem !important;
  transition: all .18s !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--blue), var(--purple)) !important;
  color: white !important; box-shadow: 0 2px 8px rgba(37,99,235,.4) !important;
}
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding-top: .75rem !important; }

/* Metrics */
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight: 800 !important; font-size: 1.4rem !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: .68rem !important; text-transform: uppercase !important; letter-spacing: .08em !important; }
[data-testid="stMetricDelta"] { font-size: .72rem !important; }
[data-testid="metric-container"] {
  background: var(--card) !important; border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important; padding: .75rem 1rem !important;
}

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--blue), var(--purple)) !important;
  color: white !important; border: none !important; border-radius: var(--radius-sm) !important;
  font-weight: 700 !important; font-size: .8rem !important;
  padding: .5rem 1.1rem !important; transition: all .2s !important;
  letter-spacing: .02em !important;
}
.stButton > button:hover {
  opacity: .88 !important; transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(37,99,235,.45) !important;
}

/* Inputs */
.stTextInput input, .stSelectbox select, .stNumberInput input {
  background: var(--card2) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; border-radius: var(--radius-sm) !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
  border-color: var(--blue) !important; box-shadow: 0 0 0 2px rgba(37,99,235,.2) !important;
}
.stSelectbox label, .stSlider label, .stToggle label, .stTextInput label {
  color: var(--muted) !important; font-size: .68rem !important;
  font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: .08em !important;
}

/* DataFrame */
[data-testid="stDataFrame"] { background: var(--card) !important; border-radius: var(--radius) !important; }
.stDataFrame thead tr th {
  background: var(--card2) !important; color: var(--muted) !important;
  font-size: .65rem !important; text-transform: uppercase !important; letter-spacing: .08em !important;
  font-weight: 700 !important;
}
.stDataFrame tbody tr:hover td { background: rgba(37,99,235,.07) !important; }

/* Alerts */
.stAlert { border-radius: var(--radius-sm) !important; }
.stSuccess { background: rgba(34,197,94,.1) !important; border-color: rgba(34,197,94,.3) !important; }
.stInfo    { background: rgba(37,99,235,.1) !important; border-color: rgba(37,99,235,.3) !important; }
.stWarning { background: rgba(250,204,21,.1) !important; border-color: rgba(250,204,21,.3) !important; }
.stError   { background: rgba(239,68,68,.1) !important; border-color: rgba(239,68,68,.3) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: .6rem 0 !important; }

/* Download button */
.stDownloadButton > button {
  background: rgba(37,99,235,.15) !important; color: #93c5fd !important;
  border: 1px solid rgba(37,99,235,.35) !important; border-radius: var(--radius-sm) !important;
  font-weight: 600 !important; font-size: .78rem !important;
}
.stDownloadButton > button:hover {
  background: rgba(37,99,235,.25) !important; transform: translateY(-1px) !important;
}

/* Toggle */
.stToggle > label { color: var(--muted) !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--blue) !important; }

/* Expander */
.streamlit-expanderHeader {
  background: var(--card2) !important; border-radius: var(--radius-sm) !important;
  color: var(--text) !important; font-weight: 600 !important;
}
</style>
"""


# ── Color helpers ─────────────────────────────────────────────────────────────
def fatigue_color(level: int) -> str:
    return {0: "#22C55E", 1: "#FACC15", 2: "#F97316", 3: "#EF4444"}.get(level, "#94A3B8")

def fatigue_badge(level: int) -> str:
    return {0: "badge-green", 1: "badge-yellow", 2: "badge-orange", 3: "badge-red"}.get(level, "badge-gray")

def fatigue_pulse(level: int) -> str:
    return {0: "pulse-green", 1: "pulse-yellow", 2: "pulse-orange", 3: "pulse-red"}.get(level, "pulse-green")

def rec_card_cls(level: int) -> str:
    return {0: "rec-card-green", 1: "rec-card-yellow", 2: "rec-card-orange", 3: "rec-card-red"}.get(level, "rec-card-green")
