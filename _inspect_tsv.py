"""
_inspect_tsv.py
---------------
Full inspection of dataset/Data TSV files. Read-only, no modifications.
"""
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import pandas as pd
import numpy as np

DATA = Path("dataset/Data")
SEP = "=" * 60

for uid, user_dir in enumerate(sorted(DATA.iterdir()), 1):
    print(f"\n{SEP}")
    print(f"USER {uid}: {user_dir.name}")
    print(SEP)

    # ── usercondition (ground truth) ──────────────────────────────────
    uc = pd.read_csv(user_dir/"usercondition.tsv", sep="\t", encoding="utf-8", on_bad_lines="skip")
    uc.columns = uc.columns.str.strip()
    uc["Time"] = pd.to_datetime(uc["Time"], errors="coerce")
    print(f"\n[usercondition.tsv]  {len(uc)} label events")
    print(f"  Columns      : {list(uc.columns)}")
    print(f"  Fatigue_Val  : {uc['Fatigue_Val'].value_counts().to_dict()}")
    print(f"  PAM_Val      : min={uc['PAM_Val'].min()}  max={uc['PAM_Val'].max()}")
    print(f"  Stress_Val   : {sorted(uc['Stress_Val'].dropna().unique().tolist())}")
    print(f"  Energy_Val   : {sorted(uc['Energy_Val'].dropna().unique().tolist())}")
    print(f"  Pleasant_Val : {sorted(uc['Pleasant_Val'].dropna().unique().tolist())}")
    print(f"  Daylight     : {sorted(uc['Daylight'].dropna().unique().tolist())}")
    print(f"  Date range   : {uc['Time'].min()}  ->  {uc['Time'].max()}")
    session_dates = sorted(set(uc["Time"].dt.date.astype(str).tolist()))
    print(f"  Session dates: {session_dates}  ({len(session_dates)} days)")
    # label interval
    uc_sorted = uc.sort_values("Time")
    intervals = uc_sorted["Time"].diff().dt.total_seconds().dropna()
    print(f"  Label interval (s): mean={intervals.mean():.0f}  min={intervals.min():.0f}  max={intervals.max():.0f}")
    print(f"  Missing Time : {uc['Time'].isnull().sum()}")

    # ── keystrokes ────────────────────────────────────────────────────
    ks = pd.read_csv(user_dir/"keystrokes.tsv", sep="\t", encoding="utf-8", on_bad_lines="skip")
    ks.columns = ks.columns.str.strip()
    ks["Press_Time"]  = pd.to_datetime(ks["Press_Time"],  errors="coerce")
    ks["Relase_Time"] = pd.to_datetime(ks["Relase_Time"], errors="coerce")
    ks["dwell_ms"] = (ks["Relase_Time"] - ks["Press_Time"]).dt.total_seconds() * 1000
    print(f"\n[keystrokes.tsv]  {len(ks)} events")
    print(f"  Columns      : {list(ks.columns)}")
    print(f"  Key types (top 10): {ks['Key'].value_counts().head(10).to_dict()}")
    print(f"  Dwell (ms)   : mean={ks['dwell_ms'].mean():.1f}  std={ks['dwell_ms'].std():.1f}  min={ks['dwell_ms'].min():.1f}  max={ks['dwell_ms'].max():.1f}")
    print(f"  Time range   : {ks['Press_Time'].min()}  ->  {ks['Press_Time'].max()}")
    print(f"  Missing Press_Time  : {ks['Press_Time'].isnull().sum()}")
    print(f"  Missing Relase_Time : {ks['Relase_Time'].isnull().sum()}")
    print(f"  Negative dwell      : {(ks['dwell_ms'] < 0).sum()}")
    print(f"  Dwell > 2000ms      : {(ks['dwell_ms'] > 2000).sum()}")
    print(f"  Daylight counts     : {ks['Daylight'].value_counts().to_dict()}")

    # ── mousedata ─────────────────────────────────────────────────────
    # Read only first 300k rows to avoid memory issues
    md = pd.read_csv(user_dir/"mousedata.tsv", sep="\t", encoding="utf-8",
                     on_bad_lines="skip", nrows=300000)
    md.columns = md.columns.str.strip()
    md["Time"] = pd.to_datetime(md["Time"], errors="coerce")
    print(f"\n[mousedata.tsv]  (first 300k rows sampled)")
    print(f"  Columns      : {list(md.columns)}")
    print(f"  Event_Type   : {md['Event_Type'].value_counts().to_dict()}")
    print(f"  X range      : {md['X'].min()} - {md['X'].max()}")
    print(f"  Y range      : {md['Y'].min()} - {md['Y'].max()}")
    print(f"  Time range   : {md['Time'].min()}  ->  {md['Time'].max()}")
    print(f"  Missing Time : {md['Time'].isnull().sum()}")

    # ── mouse_mov_speeds ──────────────────────────────────────────────
    ms = pd.read_csv(user_dir/"mouse_mov_speeds.tsv", sep="\t", encoding="utf-8", on_bad_lines="skip")
    ms.columns = ms.columns.str.strip()
    speed_col = [c for c in ms.columns if "speed" in c.lower()][0]
    print(f"\n[mouse_mov_speeds.tsv]  {len(ms)} rows")
    print(f"  Columns      : {list(ms.columns)}")
    print(f"  {speed_col}: mean={ms[speed_col].mean():.4f}  std={ms[speed_col].std():.4f}  min={ms[speed_col].min():.4f}  max={ms[speed_col].max():.4f}")

    # ── inactivity ────────────────────────────────────────────────────
    ia = pd.read_csv(user_dir/"inactivity.tsv", sep="\t", encoding="utf-8", on_bad_lines="skip")
    ia.columns = ia.columns.str.strip()
    dur_col = [c for c in ia.columns if "dur" in c.lower()][0]
    print(f"\n[inactivity.tsv]  {len(ia)} events")
    print(f"  Columns      : {list(ia.columns)}")
    print(f"  Type counts  : {ia['Type'].value_counts().to_dict()}")
    print(f"  {dur_col}: mean={ia[dur_col].mean():.2f}  min={ia[dur_col].min():.2f}  max={ia[dur_col].max():.2f}")

    # ── activewindows ─────────────────────────────────────────────────
    aw = pd.read_csv(user_dir/"activewindows.tsv", sep="\t", encoding="utf-8", on_bad_lines="skip")
    aw.columns = aw.columns.str.strip()
    print(f"\n[activewindows.tsv]  {len(aw)} events")
    print(f"  Columns      : {list(aw.columns)}")
    print(f"  App_Name (top 10): {aw['App_Name'].value_counts().head(10).to_dict()}")

    # ── label-to-window alignment check ──────────────────────────────
    print(f"\n[LABEL ALIGNMENT CHECK]")
    print(f"  Label events : {len(uc)}")
    print(f"  Keystroke events : {len(ks)}")
    # How many keystrokes fall within 30-min windows around each label?
    ks_times = ks["Press_Time"].dropna().sort_values()
    uc_times = uc["Time"].dropna().sort_values()
    window_s = 1800  # 30 minutes
    windows_with_data = 0
    for t in uc_times:
        lo = t - pd.Timedelta(seconds=window_s)
        hi = t
        n = ((ks_times >= lo) & (ks_times <= hi)).sum()
        if n > 0:
            windows_with_data += 1
    print(f"  Label windows with >=1 keystroke (30-min lookback): {windows_with_data}/{len(uc_times)}")

print(f"\n{SEP}")
print("SUMMARY")
print(SEP)
print("""
Participants : 2
Files/user   : 6 (keystrokes, mousedata, mouse_mov_speeds, inactivity, activewindows, usercondition)
Ground truth : usercondition.tsv  (Fatigue_Val column)
Label type   : Ordinal self-report (No, Below_Avg, Avg, Above_Avg, Low, V_High)
Label timing : Approximately every 30 minutes
Session span : Multiple days in September 2021
""")
