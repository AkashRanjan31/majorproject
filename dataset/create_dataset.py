"""
create_dataset.py
-----------------
Generates a 5-class, 40-feature synthetic dataset for research-grade
Mental Fatigue Detection. Classes: 0=Normal, 1=Low, 2=Moderate, 3=High, 4=Critical.
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)
N = 500  # samples per class
OUT = Path(__file__).resolve().parent / "dataset.csv"
NOISE = 0.40  # fraction of std-dev noise added to create realistic class overlap


def _rng(lo, hi, n, dtype="float"):
    """Sample uniformly then add Gaussian noise for realistic class overlap."""
    if dtype == "int":
        base = np.random.randint(lo, hi + 1, n).astype(float)
        noise = np.random.normal(0, (hi - lo) * NOISE, n)
        return np.clip(np.round(base + noise), lo * 0.5, hi * 1.5).astype(int)
    base = np.random.uniform(lo, hi, n)
    noise = np.random.normal(0, (hi - lo) * NOISE, n)
    return np.clip(base + noise, lo * 0.5, hi * 1.5)


def generate_samples(n: int, level: int) -> pd.DataFrame:
    """
    Generate n rows for a given fatigue level.
    Higher level → slower typing, more errors, erratic mouse, more idle time.
    Fatigue levels: 0=Normal, 1=Low, 2=Moderate, 3=High, 4=Critical
    """
    # ── Fatigue-level parameter table ──────────────────────────────────────
    #   (key_press_lo, key_press_hi,
    #    hold_lo, hold_hi,
    #    wpm_lo, wpm_hi,
    #    error_lo, error_hi,
    #    bs_lo, bs_hi,
    #    idle_lo, idle_hi,
    #    inter_key_lo, inter_key_hi,
    #    flight_lo, flight_hi,
    #    burst_lo, burst_hi,
    #    corr_delay_lo, corr_delay_hi,
    #    pause_lo, pause_hi,
    #    kpm_lo, kpm_hi,
    #    vel_lo, vel_hi,
    #    accel_lo, accel_hi,
    #    jerk_lo, jerk_hi,
    #    smooth_lo, smooth_hi,
    #    m_idle_lo, m_idle_hi,
    #    click_rate_lo, click_rate_hi,
    #    dc_speed_lo, dc_speed_hi,
    #    drag_dist_lo, drag_dist_hi,
    #    drag_spd_lo, drag_spd_hi,
    #    scroll_spd_lo, scroll_spd_hi,
    #    scroll_freq_lo, scroll_freq_hi,
    #    curvature_lo, curvature_hi,
    #    entropy_lo, entropy_hi,
    #    precision_lo, precision_hi,
    #    dir_changes_lo, dir_changes_hi,
    #    click_acc_lo, click_acc_hi,
    #    cursor_dist_lo, cursor_dist_hi,
    #    sl_ratio_lo, sl_ratio_hi,
    #    turn_angle_lo, turn_angle_hi,
    #    abs_turn_lo, abs_turn_hi,
    #    reaction_lo, reaction_hi,
    #    app_switch_lo, app_switch_hi,
    #    typing_sess_lo, typing_sess_hi,
    #    mouse_sess_lo, mouse_sess_hi,
    #    break_dur_lo, break_dur_hi)

    params = {
        0: dict(  # Normal
            kp=(250, 450), hold=(0.07, 0.13), wpm=(65, 110), err=(0.01, 0.04),
            bs=(1, 8), idle=(0.5, 4), ik=(0.08, 0.15), fl=(0.05, 0.12),
            burst=(8, 20), cd=(0.1, 0.3), pause=(0.5, 2), kpm=(200, 400),
            vel=(350, 650), accel=(80, 180), jerk=(10, 40), smooth=(0.75, 0.95),
            m_idle=(0.3, 2), cr=(0.8, 2.0), dc=(0.15, 0.28), dd=(300, 800),
            ds=(200, 500), ss=(80, 200), sf=(15, 50), curv=(0.02, 0.12),
            ent=(2.5, 4.5), prec=(0.85, 0.98), dc_ch=(5, 20), ca=(0.88, 0.99),
            cd2=(3000, 7000), slr=(0.75, 0.95), ta=(5, 25), ata=(10, 40),
            rt=(0.15, 0.35), apps=(1, 5), ts=(20, 60), ms=(15, 50), bd=(0, 2)
        ),
        1: dict(  # Low Fatigue
            kp=(180, 280), hold=(0.11, 0.18), wpm=(50, 70), err=(0.03, 0.07),
            bs=(6, 15), idle=(3, 8), ik=(0.13, 0.22), fl=(0.10, 0.18),
            burst=(5, 14), cd=(0.25, 0.5), pause=(1.5, 5), kpm=(140, 220),
            vel=(250, 400), accel=(50, 110), jerk=(30, 80), smooth=(0.60, 0.80),
            m_idle=(1.5, 5), cr=(0.5, 1.2), dc=(0.22, 0.38), dd=(180, 450),
            ds=(130, 300), ss=(50, 120), sf=(8, 25), curv=(0.10, 0.25),
            ent=(2.0, 3.5), prec=(0.75, 0.90), dc_ch=(12, 35), ca=(0.78, 0.92),
            cd2=(1800, 4000), slr=(0.60, 0.80), ta=(15, 40), ata=(25, 60),
            rt=(0.28, 0.55), apps=(3, 8), ts=(12, 35), ms=(10, 35), bd=(1, 5)
        ),
        2: dict(  # Moderate Fatigue
            kp=(100, 200), hold=(0.16, 0.26), wpm=(32, 55), err=(0.06, 0.13),
            bs=(12, 28), idle=(7, 18), ik=(0.20, 0.35), fl=(0.16, 0.28),
            burst=(3, 10), cd=(0.45, 0.9), pause=(4, 12), kpm=(80, 160),
            vel=(140, 280), accel=(25, 70), jerk=(60, 140), smooth=(0.42, 0.65),
            m_idle=(4, 12), cr=(0.25, 0.75), dc=(0.30, 0.50), dd=(80, 250),
            ds=(60, 180), ss=(25, 80), sf=(3, 15), curv=(0.20, 0.45),
            ent=(1.5, 2.8), prec=(0.60, 0.78), dc_ch=(25, 60), ca=(0.65, 0.82),
            cd2=(700, 2200), slr=(0.45, 0.68), ta=(30, 65), ata=(45, 90),
            rt=(0.45, 0.85), apps=(5, 12), ts=(6, 20), ms=(5, 20), bd=(3, 10)
        ),
        3: dict(  # High Fatigue
            kp=(40, 110), hold=(0.24, 0.40), wpm=(15, 35), err=(0.12, 0.22),
            bs=(25, 55), idle=(16, 35), ik=(0.32, 0.55), fl=(0.25, 0.45),
            burst=(1, 6), cd=(0.8, 1.5), pause=(10, 25), kpm=(30, 90),
            vel=(55, 160), accel=(8, 35), jerk=(110, 250), smooth=(0.22, 0.48),
            m_idle=(10, 25), cr=(0.08, 0.35), dc=(0.42, 0.65), dd=(20, 100),
            ds=(15, 80), ss=(8, 35), sf=(1, 8), curv=(0.40, 0.75),
            ent=(0.8, 1.8), prec=(0.42, 0.65), dc_ch=(45, 100), ca=(0.48, 0.70),
            cd2=(150, 800), slr=(0.28, 0.52), ta=(55, 100), ata=(75, 130),
            rt=(0.75, 1.40), apps=(8, 18), ts=(2, 10), ms=(2, 10), bd=(8, 20)
        ),
        4: dict(  # Critical Fatigue
            kp=(5, 45), hold=(0.38, 0.65), wpm=(3, 18), err=(0.20, 0.40),
            bs=(50, 100), idle=(30, 60), ik=(0.50, 0.90), fl=(0.40, 0.70),
            burst=(0, 3), cd=(1.3, 2.5), pause=(20, 50), kpm=(5, 35),
            vel=(10, 65), accel=(1, 15), jerk=(200, 450), smooth=(0.05, 0.28),
            m_idle=(20, 50), cr=(0.01, 0.12), dc=(0.55, 0.85), dd=(2, 30),
            ds=(2, 25), ss=(1, 12), sf=(0, 3), curv=(0.65, 0.95),
            ent=(0.1, 0.9), prec=(0.18, 0.48), dc_ch=(80, 180), ca=(0.22, 0.52),
            cd2=(10, 200), slr=(0.10, 0.32), ta=(85, 150), ata=(110, 180),
            rt=(1.20, 2.50), apps=(12, 25), ts=(0, 5), ms=(0, 5), bd=(15, 40)
        ),
    }
    p = params[level]

    df = pd.DataFrame({
        # ── Keyboard ──────────────────────────────────────────────────────
        "key_press_count":       _rng(*p["kp"], n, "int"),
        "key_hold_time":         _rng(*p["hold"], n),
        "typing_speed":          _rng(*p["wpm"], n),
        "error_rate":            _rng(*p["err"], n),
        "backspace_count":       _rng(*p["bs"], n, "int"),
        "idle_time":             _rng(*p["idle"], n),
        "inter_key_delay":       _rng(*p["ik"], n),
        "flight_time":           _rng(*p["fl"], n),
        "typing_burst_duration": _rng(*p["burst"], n),
        "correction_delay":      _rng(*p["cd"], n),
        "pause_duration":        _rng(*p["pause"], n),
        "keystrokes_per_minute": _rng(*p["kpm"], n),
        # ── Mouse ─────────────────────────────────────────────────────────
        "mouse_velocity":        _rng(*p["vel"], n),
        "mouse_acceleration":    _rng(*p["accel"], n),
        "mouse_jerk":            _rng(*p["jerk"], n),
        "movement_smoothness":   _rng(*p["smooth"], n),
        "idle_mouse_time":       _rng(*p["m_idle"], n),
        "mouse_click_rate":      _rng(*p["cr"], n),
        "double_click_speed":    _rng(*p["dc"], n),
        "drag_distance":         _rng(*p["dd"], n),
        "drag_speed":            _rng(*p["ds"], n),
        "scroll_speed":          _rng(*p["ss"], n),
        "scroll_frequency":      _rng(*p["sf"], n),
        "mouse_path_curvature":  _rng(*p["curv"], n),
        "mouse_entropy":         _rng(*p["ent"], n),
        "mouse_precision":       _rng(*p["prec"], n),
        "direction_changes":     _rng(*p["dc_ch"], n, "int"),
        "click_accuracy":        _rng(*p["ca"], n),
        "cursor_distance":       _rng(*p["cd2"], n),
        "straight_line_ratio":   _rng(*p["slr"], n),
        "avg_turning_angle":     _rng(*p["ta"], n),
        "abs_turning_angle":     _rng(*p["ata"], n),
        "reaction_time":         _rng(*p["rt"], n),
        # ── Productivity ──────────────────────────────────────────────────
        "app_switch_frequency":  _rng(*p["apps"], n, "int"),
        "typing_session_length": _rng(*p["ts"], n),
        "mouse_session_length":  _rng(*p["ms"], n),
        "break_duration":        _rng(*p["bd"], n),
        # ── Legacy compatibility ───────────────────────────────────────────
        "left_click":            (_rng(*p["kp"], n, "int") * 0.15).astype(int),
        "right_click":           (_rng(*p["kp"], n, "int") * 0.04).astype(int),
        "double_click":          (_rng(*p["kp"], n, "int") * 0.02).astype(int),
        "scroll_count":          _rng(*p["sf"], n, "int"),
        "cursor_speed":          _rng(*p["vel"], n),
        "drag_count":            _rng(0, max(1, p["dd"][1] // 200), n, "int"),
        "movement_speed":        _rng(*p["vel"], n),
        # ── Target ────────────────────────────────────────────────────────
        "fatigue_level":         np.full(n, level, dtype=int),
    })
    return df


frames = [generate_samples(N, lvl) for lvl in range(5)]
df = pd.concat(frames, ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv(OUT, index=False)

print(f"Dataset saved -> {OUT}")
print(f"Shape: {df.shape}")
print(df["fatigue_level"].value_counts().sort_index().to_string())
