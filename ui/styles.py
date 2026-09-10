"""
ui/styles.py
------------
Complete premium dark-theme CSS injection for the enterprise dashboard.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

:root {
  --bg:      #07111F;
  --card:    #0d1b2e;
  --card2:   #111827;
  --card3:   #162032;
  --border:  rgba(255,255,255,0.06);
  --border2: rgba(255,255,255,0.12);
  --blue:    #2563EB;
  --blue2:   #3b82f6;
  --purple:  #8B5CF6;
  --green:   #22C55E;
  --yellow:  #FACC15;
  --orange:  #F97316;
  --red:     #EF4444;
  --text:    #F8FAFC;
  --muted:   #94A3B8;
  --muted2:  #64748B;
  --r:       18px;
  --r2:      12px;
  --sh:      0 4px 24px rgba(0,0,0,0.5);
  --sh2:     0 8px 40px rgba(0,0,0,0.65);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}

html,body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,.main .block-container{
  background:#07111F !important;
  font-family:'Inter',-apple-system,sans-serif !important;
  color:var(--text) !important;
}

/* Prevent Streamlit containers from creating clipping stacking contexts */
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.appview-container {
  overflow-x: visible !important;
  overflow-y: visible !important;
}

/* Hide Streamlit chrome */
#MainMenu,footer,header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"]{display:none !important;}

.block-container{
  padding:.5rem 1.5rem 3rem !important;
  max-width:100% !important;
  width:100% !important;
  min-width:0 !important;
  box-sizing:border-box !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.08);border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.16);}

/* ── HEADER ── */
.hdr{
  background:linear-gradient(135deg,rgba(37,99,235,.08),rgba(139,92,246,.05));
  border:1px solid rgba(37,99,235,.18);
  border-radius:var(--r);padding:.85rem 1.5rem;
  margin-bottom:1.1rem;
  display:flex;align-items:center;justify-content:space-between;
  flex-wrap:wrap;gap:.75rem;
  position:relative;overflow:hidden;
}
.hdr::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--blue),var(--purple),var(--blue));
  background-size:200%;animation:hdrLine 4s linear infinite;
}
@keyframes hdrLine{0%{background-position:0%}100%{background-position:200%}}
.hdr-title{
  font-size:1.15rem;font-weight:900;letter-spacing:-.02em;
  background:linear-gradient(135deg,#93c5fd,#c4b5fd);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}
.hdr-sub{font-size:.7rem;color:var(--muted);margin-top:.15rem;letter-spacing:.02em;}
.hdr-right{display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;}
.hdr-stat{text-align:right;}
.hdr-stat-lbl{font-size:.58rem;color:var(--muted2);text-transform:uppercase;letter-spacing:.1em;}
.hdr-stat-val{font-size:.88rem;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums;}

/* ── BADGES ── */
.badge{
  display:inline-flex;align-items:center;gap:.3rem;
  padding:.18rem .6rem;border-radius:999px;
  font-size:.62rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
}
.b-live  {background:rgba(34,197,94,.12); color:var(--green); border:1px solid rgba(34,197,94,.28);}
.b-green {background:rgba(34,197,94,.12); color:var(--green); border:1px solid rgba(34,197,94,.28);}
.b-yel   {background:rgba(250,204,21,.12);color:var(--yellow);border:1px solid rgba(250,204,21,.28);}
.b-oran  {background:rgba(249,115,22,.12);color:var(--orange);border:1px solid rgba(249,115,22,.28);}
.b-red   {background:rgba(239,68,68,.12); color:var(--red);   border:1px solid rgba(239,68,68,.28);}
.b-blue  {background:rgba(37,99,235,.12); color:#93c5fd;      border:1px solid rgba(37,99,235,.28);}
.b-purp  {background:rgba(139,92,246,.12);color:#c4b5fd;      border:1px solid rgba(139,92,246,.28);}
.b-gray  {background:rgba(148,163,184,.08);color:var(--muted);border:1px solid rgba(148,163,184,.18);}

/* ── PULSE ── */
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;}
.dot-g{background:var(--green); animation:pg 2s infinite;}
.dot-y{background:var(--yellow);animation:py 2s infinite;}
.dot-o{background:var(--orange);animation:po 2s infinite;}
.dot-r{background:var(--red);   animation:pr 2s infinite;}
@keyframes pg{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,.5)} 50%{box-shadow:0 0 0 5px rgba(34,197,94,0)}}
@keyframes py{0%,100%{box-shadow:0 0 0 0 rgba(250,204,21,.5)} 50%{box-shadow:0 0 0 5px rgba(250,204,21,0)}}
@keyframes po{0%,100%{box-shadow:0 0 0 0 rgba(249,115,22,.5)} 50%{box-shadow:0 0 0 5px rgba(249,115,22,0)}}
@keyframes pr{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5)}  50%{box-shadow:0 0 0 5px rgba(239,68,68,0)}}

/* ── KPI CARDS ── */
.kpi{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:1.1rem 1.2rem;
  box-shadow:var(--sh);transition:all .2s;
  position:relative;overflow:hidden;
}
.kpi:hover{transform:translateY(-3px);box-shadow:var(--sh2);border-color:var(--border2);}
.kpi::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.05),transparent);
}
.kpi-lbl{
  font-size:.6rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin-bottom:.45rem;
}
.kpi-val{
  font-size:1.6rem;font-weight:900;line-height:1;
  letter-spacing:-.02em;margin-bottom:.25rem;
}
.kpi-sub{font-size:.7rem;color:var(--muted);}
.kpi-sub b{color:var(--text);}
.kpi-bg-icon{
  position:absolute;top:.8rem;right:.9rem;
  font-size:2rem;opacity:.07;pointer-events:none;
}
.kpi-badge{position:absolute;bottom:.75rem;right:.9rem;}

/* ── SECTION HEADER ── */
.sec{
  font-size:.6rem;font-weight:800;letter-spacing:.15em;
  text-transform:uppercase;color:var(--muted);
  margin-bottom:.65rem;display:flex;align-items:center;gap:.5rem;
}
.sec::after{
  content:'';flex:1;height:1px;
  background:linear-gradient(90deg,rgba(255,255,255,.06),transparent);
}

/* ── CARD ── */
.card{
  background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);padding:1rem 1.2rem;
  box-shadow:var(--sh);position:relative;overflow:hidden;
}
.card-glass{
  background:rgba(13,27,46,.85);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,.08);
  border-radius:var(--r);padding:1rem 1.2rem;box-shadow:var(--sh);
}
.card-top-blue::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--blue),var(--purple));
}
.card-top-green::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--green),#16a34a);
}

/* ── METRIC TILE ── */
.mtile{
  background:var(--card2);border-radius:var(--r2);
  padding:.6rem .9rem;border-left:3px solid transparent;
  transition:all .15s;margin-bottom:.35rem;
}
.mtile:hover{background:var(--card3);transform:translateX(2px);}
.mtile-lbl{font-size:.58rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;}
.mtile-val{font-size:1rem;font-weight:700;margin-top:.08rem;}

/* ── RECOMMENDATION CARD ── */
.rec{
  border-radius:var(--r);padding:1.6rem 1.4rem;
  text-align:center;transition:all .2s;position:relative;overflow:hidden;
}
.rec:hover{transform:scale(1.01);}
.rec-g{background:linear-gradient(135deg,rgba(34,197,94,.12),rgba(34,197,94,.03)); border:1px solid rgba(34,197,94,.25);}
.rec-y{background:linear-gradient(135deg,rgba(250,204,21,.12),rgba(250,204,21,.03));border:1px solid rgba(250,204,21,.25);}
.rec-o{background:linear-gradient(135deg,rgba(249,115,22,.12),rgba(249,115,22,.03));border:1px solid rgba(249,115,22,.25);}
.rec-r{background:linear-gradient(135deg,rgba(239,68,68,.12), rgba(239,68,68,.03)); border:1px solid rgba(239,68,68,.25);}
.rec-icon{font-size:2.8rem;margin-bottom:.5rem;display:block;}
.rec-title{font-size:1.2rem;font-weight:900;margin-bottom:.3rem;}
.rec-desc{font-size:.78rem;color:var(--muted);line-height:1.55;}

/* ── HEALTH ROW ── */
.hrow{
  display:flex;align-items:center;justify-content:space-between;
  padding:.45rem 0;border-bottom:1px solid var(--border);font-size:.8rem;
}
.hrow:last-child{border-bottom:none;}
.hrow-name{display:flex;align-items:center;gap:.5rem;color:var(--text);}
.hdot{width:6px;height:6px;border-radius:50%;flex-shrink:0;}
.hok {background:var(--green); box-shadow:0 0 5px var(--green);}
.hwrn{background:var(--yellow);box-shadow:0 0 5px var(--yellow);}
.herr{background:var(--red);   box-shadow:0 0 5px var(--red);}
.hstat{font-size:.65rem;font-weight:700;letter-spacing:.05em;}

/* ── BASELINE TABLE ── */
.bltbl{width:100%;border-collapse:collapse;font-size:.78rem;}
.bltbl th{
  font-size:.58rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted2);
  padding:.38rem .5rem;border-bottom:1px solid var(--border);text-align:left;
}
.bltbl td{padding:.42rem .5rem;border-bottom:1px solid rgba(255,255,255,.03);}
.bltbl tr:last-child td{border-bottom:none;}
.bltbl tr:hover td{background:rgba(37,99,235,.04);}
.dup  {color:var(--red);  font-weight:700;}
.ddown{color:var(--green);font-weight:700;}
.dflat{color:var(--muted);font-weight:600;}

/* ── EVENT TABLE ── */
.evttbl{width:100%;border-collapse:collapse;font-size:.74rem;}
.evttbl th{
  font-size:.56rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted2);
  padding:.32rem .5rem;border-bottom:1px solid var(--border);
  text-align:left;white-space:nowrap;
}
.evttbl td{padding:.35rem .5rem;border-bottom:1px solid rgba(255,255,255,.025);white-space:nowrap;}
.evttbl tr:hover td{background:rgba(37,99,235,.05);}
.etime{color:var(--muted);font-family:monospace;font-size:.7rem;}

/* ── PRIVACY ── */
.priv{
  display:flex;align-items:center;gap:.6rem;
  padding:.5rem 0;border-bottom:1px solid var(--border);font-size:.8rem;
}
.priv:last-child{border-bottom:none;}
.priv-chk{color:var(--green);font-size:.9rem;flex-shrink:0;}

/* ── PIPELINE ── */
.pipe{display:flex;flex-direction:column;align-items:center;gap:0;}
.pstep{
  background:var(--card2);border:1px solid var(--border);
  border-radius:var(--r2);padding:.5rem 1.4rem;
  font-size:.76rem;font-weight:600;color:var(--text);
  text-align:center;width:250px;transition:all .18s;
}
.pstep:hover{background:rgba(37,99,235,.12);border-color:rgba(37,99,235,.35);}
.pstep.act{background:rgba(37,99,235,.18);border-color:var(--blue);color:#93c5fd;}
.parr{color:var(--muted2);font-size:.85rem;padding:.08rem 0;user-select:none;}

/* ── SKELETON ── */
@keyframes shimmer{0%{background-position:-400px 0}100%{background-position:400px 0}}
.skel{
  background:linear-gradient(90deg,var(--card) 25%,var(--card2) 50%,var(--card) 75%);
  background-size:400px 100%;animation:shimmer 1.5s infinite;border-radius:8px;
}

/* ── FADE UP ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.anim{animation:fadeUp .3s ease-out;}

/* ── STREAMLIT OVERRIDES ── */
.stTabs [data-baseweb="tab-list"]{
  background:var(--card) !important;border-radius:14px !important;
  padding:3px !important;gap:3px !important;border:1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"]{
  background:transparent !important;color:var(--muted) !important;
  border-radius:11px !important;font-weight:600 !important;
  font-size:.76rem !important;padding:.38rem .85rem !important;transition:all .15s !important;
}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,var(--blue),var(--purple)) !important;
  color:#fff !important;box-shadow:0 2px 10px rgba(37,99,235,.4) !important;
}
.stTabs [data-baseweb="tab-panel"]{background:transparent !important;padding-top:.75rem !important;}

[data-testid="stMetricValue"]{color:var(--text) !important;font-weight:800 !important;font-size:1.35rem !important;}
[data-testid="stMetricLabel"]{color:var(--muted) !important;font-size:.65rem !important;text-transform:uppercase !important;letter-spacing:.08em !important;}
[data-testid="metric-container"]{
  background:var(--card) !important;border:1px solid var(--border) !important;
  border-radius:var(--r2) !important;padding:.7rem 1rem !important;
}

.stButton>button{
  background:linear-gradient(135deg,var(--blue),var(--purple)) !important;
  color:#fff !important;border:none !important;border-radius:var(--r2) !important;
  font-weight:700 !important;font-size:.78rem !important;
  padding:.48rem 1rem !important;transition:all .18s !important;
}
.stButton>button:hover{
  opacity:.85 !important;transform:translateY(-1px) !important;
  box-shadow:0 6px 20px rgba(37,99,235,.4) !important;
}

.stTextInput input,.stSelectbox select,.stNumberInput input{
  background:var(--card2) !important;border:1px solid var(--border) !important;
  color:var(--text) !important;border-radius:var(--r2) !important;
}
.stSelectbox label,.stSlider label,.stToggle label,.stTextInput label,.stRadio label{
  color:var(--muted) !important;font-size:.65rem !important;
  font-weight:700 !important;text-transform:uppercase !important;letter-spacing:.08em !important;
}

[data-testid="stDataFrame"]{background:var(--card) !important;border-radius:var(--r) !important;}

.stAlert{border-radius:var(--r2) !important;}
.stSuccess{background:rgba(34,197,94,.08) !important;border-color:rgba(34,197,94,.25) !important;}
.stInfo   {background:rgba(37,99,235,.08) !important;border-color:rgba(37,99,235,.25) !important;}
.stWarning{background:rgba(250,204,21,.08)!important;border-color:rgba(250,204,21,.25)!important;}
.stError  {background:rgba(239,68,68,.08) !important;border-color:rgba(239,68,68,.25) !important;}

hr{border-color:var(--border) !important;margin:.5rem 0 !important;}

.stDownloadButton>button{
  background:rgba(37,99,235,.1) !important;color:#93c5fd !important;
  border:1px solid rgba(37,99,235,.3) !important;border-radius:var(--r2) !important;
  font-weight:600 !important;font-size:.76rem !important;
}
.stDownloadButton>button:hover{background:rgba(37,99,235,.2) !important;transform:translateY(-1px) !important;}

.stSpinner>div{border-top-color:var(--blue) !important;}
.streamlit-expanderHeader{
  background:var(--card2) !important;border-radius:var(--r2) !important;
  color:var(--text) !important;font-weight:600 !important;
}
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Color helpers ──────────────────────────────────────────────────────────────
def fc(level: int) -> str:
    """Fatigue color."""
    return {0:"#22C55E",1:"#FACC15",2:"#F97316",3:"#EF4444"}.get(level,"#94A3B8")

def fb(level: int) -> str:
    """Fatigue badge class."""
    return {0:"b-green",1:"b-yel",2:"b-oran",3:"b-red"}.get(level,"b-gray")

def fd(level: int) -> str:
    """Fatigue dot class."""
    return {0:"dot-g",1:"dot-y",2:"dot-o",3:"dot-r"}.get(level,"dot-g")

def rc(level: int) -> str:
    """Rec card class."""
    return {0:"rec-g",1:"rec-y",2:"rec-o",3:"rec-r"}.get(level,"rec-g")

FATIGUE_META = {
    0: {"name":"Normal",          "emoji":"🟢","icon":"✅","short":"Normal"},
    1: {"name":"Mild Fatigue",    "emoji":"🟡","icon":"⚠️", "short":"Mild"},
    2: {"name":"Moderate Fatigue","emoji":"🟠","icon":"🔶","short":"Moderate"},
    3: {"name":"High Fatigue",    "emoji":"🔴","icon":"🚨","short":"High"},
}
REC_META = {
    0: ("Keep Working",           "💪","You are alert and focused. Productivity is optimal."),
    1: ("Consider a Short Break", "☕","Mild fatigue detected. A 2–5 min break can help."),
    2: ("Take a 10-Minute Break", "🛑","Moderate fatigue. Rest your eyes and step away."),
    3: ("Take Immediate Rest",    "🚨","High fatigue detected. Stop and rest immediately."),
}
