"""
floating_widget.py
------------------
Always-on-top floating fatigue monitor for NeuroSense AI.
Reads latest prediction from SQLite (written by realtime_app.py).
Launch: python floating_widget.py
"""

import json
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH      = PROJECT_ROOT / "database" / "fatigue_data.db"
POLL_INTERVAL_MS = 3000   # poll DB every 3 seconds
DASHBOARD_URL    = "http://localhost:8501"

# ── Fatigue config (mirrors realtime_predict.py + styles.py) ─────────────────
_FATIGUE = {
    0: {"name": "Normal",           "short": "Normal",   "color": "#22C55E", "rec": "Keep working — you are focused."},
    1: {"name": "Low Fatigue",      "short": "Low",      "color": "#FACC15", "rec": "Stay hydrated, take a short break."},
    2: {"name": "Moderate Fatigue", "short": "Moderate", "color": "#F97316", "rec": "Take a 5-minute break."},
    3: {"name": "High Fatigue",     "short": "High",     "color": "#EF4444", "rec": "Take a 15-minute walk."},
    4: {"name": "Critical Fatigue", "short": "Critical", "color": "#7C3AED", "rec": "Stop working. Rest immediately."},
}

# Dark theme palette (matches NeuroSense --bg / --card)
BG_PILL     = "#0d1b2e"
BG_CARD     = "#07111F"
BG_EXPANDED = "#0d1b2e"
TEXT_MAIN   = "#F8FAFC"
TEXT_MUTED  = "#94A3B8"
BORDER_CLR  = "#1e293b"


# ── DB helper ─────────────────────────────────────────────────────────────────
def _fetch_latest() -> dict | None:
    """Return the most recent prediction row from SQLite, or None."""
    if not DB_PATH.exists():
        return None
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=2, check_same_thread=False)
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        con.close()
        if row:
            d = dict(row)
            try:
                d["features"] = json.loads(d.get("features_json") or "{}")
            except Exception:
                d["features"] = {}
            return d
    except Exception:
        pass
    return None


def _compute_trend(limit: int = 6) -> str:
    """↑ / → / ↓ based on last N fatigue levels."""
    if not DB_PATH.exists():
        return "→"
    try:
        con = sqlite3.connect(str(DB_PATH), timeout=2, check_same_thread=False)
        rows = con.execute(
            "SELECT fatigue_level FROM predictions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        con.close()
        levels = [r[0] for r in rows]
        if len(levels) < 2:
            return "→"
        avg_recent = sum(levels[:3]) / min(3, len(levels))
        avg_older  = sum(levels[3:]) / max(1, len(levels) - 3)
        if avg_recent > avg_older + 0.3:
            return "↑"
        if avg_recent < avg_older - 0.3:
            return "↓"
        return "→"
    except Exception:
        return "→"


# ── Widget ────────────────────────────────────────────────────────────────────
class FloatingWidget:
    def __init__(self):
        self.root = tk.Tk()
        self._expanded   = False
        self._drag_x     = 0
        self._drag_y     = 0
        self._last_data  = None
        self._last_level = 0

        self._build_window()
        self._build_pill()
        self._build_expanded_card()
        self._show_pill()
        self._poll()

    # ── Window setup ──────────────────────────────────────────────────────────
    def _build_window(self):
        r = self.root
        r.overrideredirect(True)          # no title bar
        r.attributes("-topmost", True)    # always on top
        r.attributes("-alpha", 0.96)
        r.configure(bg=BG_PILL)
        r.resizable(False, False)

        # Start bottom-right
        sw = r.winfo_screenwidth()
        sh = r.winfo_screenheight()
        r.geometry(f"+{sw - 260}+{sh - 120}")

        # Drag bindings on root
        r.bind("<ButtonPress-1>",   self._drag_start)
        r.bind("<B1-Motion>",       self._drag_motion)

    # ── Pill (collapsed) ──────────────────────────────────────────────────────
    def _build_pill(self):
        self.pill = tk.Frame(self.root, bg=BG_PILL, cursor="fleur")
        self.pill.bind("<ButtonPress-1>",  self._drag_start)
        self.pill.bind("<B1-Motion>",      self._drag_motion)
        self.pill.bind("<ButtonRelease-1>", self._on_pill_click)

        # Brain icon
        tk.Label(
            self.pill, text="🧠", font=("Segoe UI Emoji", 14),
            bg=BG_PILL, fg=TEXT_MAIN, cursor="fleur",
        ).pack(side="left", padx=(10, 4), pady=6)

        # Score
        self.lbl_score = tk.Label(
            self.pill, text="--", font=("Segoe UI", 13, "bold"),
            bg=BG_PILL, fg=TEXT_MAIN, width=3, anchor="e", cursor="fleur",
        )
        self.lbl_score.pack(side="left", pady=6)

        # Separator dot
        tk.Label(
            self.pill, text=" •", font=("Segoe UI", 11),
            bg=BG_PILL, fg=TEXT_MUTED, cursor="fleur",
        ).pack(side="left")

        # Level name
        self.lbl_level = tk.Label(
            self.pill, text="Loading…", font=("Segoe UI", 10, "bold"),
            bg=BG_PILL, fg=TEXT_MUTED, width=10, anchor="w", cursor="fleur",
        )
        self.lbl_level.pack(side="left", padx=(2, 8), pady=6)

        # Status dot
        self.dot = tk.Label(
            self.pill, text="●", font=("Segoe UI", 8),
            bg=BG_PILL, fg="#22C55E", cursor="fleur",
        )
        self.dot.pack(side="left", padx=(0, 10), pady=6)

    # ── Expanded card ─────────────────────────────────────────────────────────
    def _build_expanded_card(self):
        self.card = tk.Frame(self.root, bg=BG_EXPANDED, padx=0, pady=0)

        # ── Header row ────────────────────────────────────────────────────────
        hdr = tk.Frame(self.card, bg=BG_EXPANDED)
        hdr.pack(fill="x", padx=14, pady=(12, 0))

        tk.Label(
            hdr, text="🧠 NeuroSense AI", font=("Segoe UI", 10, "bold"),
            bg=BG_EXPANDED, fg=TEXT_MAIN,
        ).pack(side="left")

        tk.Button(
            hdr, text="×", font=("Segoe UI", 12, "bold"),
            bg=BG_EXPANDED, fg=TEXT_MUTED, bd=0, relief="flat",
            activebackground=BG_EXPANDED, activeforeground=TEXT_MAIN,
            cursor="hand2", command=self._collapse,
        ).pack(side="right")

        # Divider
        tk.Frame(self.card, bg=BORDER_CLR, height=1).pack(fill="x", padx=14, pady=(8, 0))

        # ── Score + level ─────────────────────────────────────────────────────
        score_frame = tk.Frame(self.card, bg=BG_EXPANDED)
        score_frame.pack(pady=(14, 2))

        self.exp_score = tk.Label(
            score_frame, text="--", font=("Segoe UI", 36, "bold"),
            bg=BG_EXPANDED, fg=TEXT_MAIN,
        )
        self.exp_score.pack()

        self.exp_level = tk.Label(
            score_frame, text="LOADING", font=("Segoe UI", 10, "bold"),
            bg=BG_EXPANDED, fg=TEXT_MUTED, letter_spacing=2,
        )
        self.exp_level.pack()

        # ── Trend + recommendation ────────────────────────────────────────────
        self.exp_trend = tk.Label(
            self.card, text="→ Stable", font=("Segoe UI", 9),
            bg=BG_EXPANDED, fg=TEXT_MUTED,
        )
        self.exp_trend.pack(pady=(6, 0))

        self.exp_rec = tk.Label(
            self.card, text="", font=("Segoe UI", 9),
            bg=BG_EXPANDED, fg="#F97316", wraplength=200, justify="center",
        )
        self.exp_rec.pack(pady=(2, 8))

        # Divider
        tk.Frame(self.card, bg=BORDER_CLR, height=1).pack(fill="x", padx=14)

        # ── Metrics ───────────────────────────────────────────────────────────
        metrics_frame = tk.Frame(self.card, bg=BG_EXPANDED)
        metrics_frame.pack(fill="x", padx=14, pady=10)

        self.exp_typing  = self._metric_row(metrics_frame, "⌨  Typing Speed",   "--  WPM")
        self.exp_mouse   = self._metric_row(metrics_frame, "🖱  Mouse Activity", "--  px/s")
        self.exp_idle    = self._metric_row(metrics_frame, "💤  Idle Time",      "--  s")

        # Divider
        tk.Frame(self.card, bg=BORDER_CLR, height=1).pack(fill="x", padx=14)

        # ── Dashboard button ──────────────────────────────────────────────────
        tk.Button(
            self.card,
            text="View Dashboard ↗",
            font=("Segoe UI", 9, "bold"),
            bg="#1d4ed8", fg="#ffffff",
            activebackground="#2563eb", activeforeground="#ffffff",
            bd=0, relief="flat", cursor="hand2",
            padx=16, pady=7,
            command=self._open_dashboard,
        ).pack(pady=12)

    def _metric_row(self, parent, label: str, default: str):
        """Create a label-value row and return the value Label."""
        row = tk.Frame(parent, bg=BG_EXPANDED)
        row.pack(fill="x", pady=2)
        tk.Label(
            row, text=label, font=("Segoe UI", 9),
            bg=BG_EXPANDED, fg=TEXT_MUTED, anchor="w",
        ).pack(side="left")
        val = tk.Label(
            row, text=default, font=("Segoe UI", 9, "bold"),
            bg=BG_EXPANDED, fg=TEXT_MAIN, anchor="e",
        )
        val.pack(side="right")
        return val

    # ── Show / hide ───────────────────────────────────────────────────────────
    def _show_pill(self):
        self.card.pack_forget()
        self.pill.pack(fill="x")
        self.root.update_idletasks()
        self.root.geometry(f"{self.pill.winfo_reqwidth()}x{self.pill.winfo_reqheight()}"
                           f"+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def _show_card(self):
        self.pill.pack_forget()
        self.card.pack(fill="both", expand=True)
        self.root.update_idletasks()
        w = max(self.card.winfo_reqwidth(), 230)
        h = self.card.winfo_reqheight()
        self.root.geometry(f"{w}x{h}+{self.root.winfo_x()}+{self.root.winfo_y()}")

    def _collapse(self):
        self._expanded = False
        self._show_pill()

    # ── Click to expand ───────────────────────────────────────────────────────
    def _on_pill_click(self, event):
        # Only expand if the mouse didn't move (not a drag)
        if abs(event.x_root - self._drag_x) < 5 and abs(event.y_root - self._drag_y) < 5:
            self._expanded = not self._expanded
            if self._expanded:
                self._show_card()
            else:
                self._show_pill()

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root
        self._drag_y = event.y_root
        self._win_x  = self.root.winfo_x()
        self._win_y  = self.root.winfo_y()

    def _drag_motion(self, event):
        dx = event.x_root - self._drag_x
        dy = event.y_root - self._drag_y
        nx = self._win_x + dx
        ny = self._win_y + dy
        # Clamp to screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        nx = max(0, min(nx, sw - self.root.winfo_width()))
        ny = max(0, min(ny, sh - 40))
        self.root.geometry(f"+{nx}+{ny}")

    # ── Dashboard button ──────────────────────────────────────────────────────
    def _open_dashboard(self):
        import webbrowser
        webbrowser.open(DASHBOARD_URL)

    # ── Update UI from data ───────────────────────────────────────────────────
    def _apply(self, data: dict | None):
        if data is None:
            self.lbl_score.config(text="--")
            self.lbl_level.config(text="No data", fg=TEXT_MUTED)
            self.dot.config(fg=TEXT_MUTED)
            return

        level   = int(data.get("fatigue_level", 0))
        name    = data.get("fatigue_name", "") or _FATIGUE.get(level, {}).get("name", "Normal")
        conf    = float(data.get("confidence", 0))
        score   = int(round(conf))
        meta    = _FATIGUE.get(level, _FATIGUE[0])
        color   = meta["color"]
        short   = meta["short"]
        rec     = meta["rec"]

        # Pill
        self.lbl_score.config(text=str(score), fg=color)
        self.lbl_level.config(text=short, fg=color)
        self.dot.config(fg=color)
        self.root.configure(bg=BG_PILL)
        self.pill.configure(bg=BG_PILL)

        # Expanded
        self.exp_score.config(text=str(score), fg=color)
        self.exp_level.config(text=short.upper(), fg=color)
        self.exp_rec.config(text=f"⚠  {rec}", fg=color)

        # Trend
        trend = _compute_trend()
        trend_labels = {"↑": "↑ Fatigue Increasing", "↓": "↓ Fatigue Decreasing", "→": "→ Stable"}
        trend_colors = {"↑": "#EF4444", "↓": "#22C55E", "→": TEXT_MUTED}
        self.exp_trend.config(text=trend_labels.get(trend, "→ Stable"),
                              fg=trend_colors.get(trend, TEXT_MUTED))

        # Metrics from features_json
        feats = data.get("features", {})
        typing = feats.get("typing_speed", feats.get("typing_speed_wpm", None))
        mouse  = feats.get("cursor_speed", feats.get("mouse_speed", None))
        idle   = feats.get("idle_time", feats.get("idle_time_keyboard", None))

        self.exp_typing.config(text=f"{typing:.0f}  WPM"  if typing is not None else "--  WPM")
        self.exp_mouse.config( text=f"{mouse:.0f}  px/s"  if mouse  is not None else "--  px/s")
        self.exp_idle.config(  text=f"{idle:.0f}  s"      if idle   is not None else "--  s")

        self._last_level = level

    # ── Polling ───────────────────────────────────────────────────────────────
    def _poll(self):
        try:
            data = _fetch_latest()
            self._apply(data)
        except Exception:
            pass
        self.root.after(POLL_INTERVAL_MS, self._poll)

    # ── Run ───────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    FloatingWidget().run()
