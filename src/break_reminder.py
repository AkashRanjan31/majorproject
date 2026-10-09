"""
break_reminder.py
-----------------
Smart continuous-work break reminder engine.
Tracks active work time, detects meaningful breaks, and fires a
one-time 6-hour reminder per continuous-work cycle.
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from src.logger import setup_logger

logger = setup_logger(__name__)

# ── Configurable constants (overridden via AppConfig) ─────────────────────────
WORK_REMINDER_HOURS    = 6
BREAK_IDLE_MINUTES     = 10
DEFAULT_BREAK_MINUTES  = 10
EXTENDED_BREAK_MINUTES = 30
BREAK_SNOOZE_MINUTES   = 30
MAX_REMINDERS_PER_SESSION = 2

# Fatigue level at which AI triggers an early break recommendation
AI_BREAK_THRESHOLD = 3   # High Fatigue (level 3+)


class WorkState(Enum):
    WORKING          = auto()
    REMINDER_SHOWN   = auto()
    BREAK_IN_PROGRESS = auto()


@dataclass
class BreakReminderState:
    """All session-level state for the break reminder system."""
    work_cycle_start:       float = field(default_factory=time.time)
    continuous_work_seconds: float = 0.0
    last_activity_time:     float = field(default_factory=time.time)
    last_break_time:        float | None = None
    last_break_duration:    float = 0.0
    total_breaks:           int   = 0
    six_hour_reminder_shown: bool = False
    reminder_count:         int   = 0
    snooze_until:           float | None = None
    break_start_time:       float | None = None
    break_duration_target:  float = DEFAULT_BREAK_MINUTES * 60
    state:                  WorkState = WorkState.WORKING
    ai_break_recommended:   bool = False
    ai_break_level:         int  = 0


class BreakReminderEngine:
    """
    Tracks continuous active work time and fires a one-time 6-hour reminder.

    Call update() on every prediction cycle, passing the latest raw monitor
    snapshot and the XGBoost fatigue level.  Query should_show_reminder() and
    get_dashboard_data() from the UI layer.
    """

    def __init__(self, config=None):
        if config:
            self._reminder_secs  = getattr(config, "WORK_REMINDER_HOURS",    WORK_REMINDER_HOURS)    * 3600
            self._idle_threshold = getattr(config, "BREAK_IDLE_MINUTES",     BREAK_IDLE_MINUTES)     * 60
            self._snooze_secs    = getattr(config, "BREAK_SNOOZE_MINUTES",   BREAK_SNOOZE_MINUTES)   * 60
            self._max_reminders  = getattr(config, "MAX_REMINDERS_PER_SESSION", MAX_REMINDERS_PER_SESSION)
            self._default_break  = getattr(config, "DEFAULT_BREAK_MINUTES",  DEFAULT_BREAK_MINUTES)  * 60
            self._extended_break = getattr(config, "EXTENDED_BREAK_MINUTES", EXTENDED_BREAK_MINUTES) * 60
        else:
            self._reminder_secs  = WORK_REMINDER_HOURS    * 3600
            self._idle_threshold = BREAK_IDLE_MINUTES     * 60
            self._snooze_secs    = BREAK_SNOOZE_MINUTES   * 60
            self._max_reminders  = MAX_REMINDERS_PER_SESSION
            self._default_break  = DEFAULT_BREAK_MINUTES  * 60
            self._extended_break = EXTENDED_BREAK_MINUTES * 60

        self.s = BreakReminderState()
        logger.info(
            "BreakReminderEngine init (threshold=%.1fh idle=%.0fm)",
            self._reminder_secs / 3600, self._idle_threshold / 60,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, raw_data: dict, fatigue_level: int) -> None:
        """
        Call once per prediction cycle.
        raw_data: dict from ActivityMonitor.get_raw_data()
        fatigue_level: int 0-4 from XGBoost prediction
        """
        now = time.time()
        s   = self.s

        # ── Detect activity ───────────────────────────────────────────────────
        kb_idle   = float(raw_data.get("keyboard_idle", 9999))
        ms_idle   = float(raw_data.get("mouse_idle",    9999))
        idle_secs = min(kb_idle, ms_idle)
        is_active = idle_secs < self._idle_threshold

        if is_active:
            s.last_activity_time = now

        # ── Break detection ───────────────────────────────────────────────────
        time_since_activity = now - s.last_activity_time
        meaningful_break    = time_since_activity >= self._idle_threshold

        if meaningful_break and s.state == WorkState.WORKING:
            self._start_break(now)
        elif meaningful_break and s.state == WorkState.REMINDER_SHOWN:
            self._start_break(now)

        # ── Break completion ──────────────────────────────────────────────────
        if s.state == WorkState.BREAK_IN_PROGRESS and s.break_start_time:
            elapsed_break = now - s.break_start_time
            if elapsed_break >= self._idle_threshold:
                self._complete_break(now, elapsed_break)

        # ── Accumulate continuous work time ───────────────────────────────────
        if s.state == WorkState.WORKING and is_active:
            s.continuous_work_seconds = now - s.work_cycle_start

        # ── AI-based early break ──────────────────────────────────────────────
        if fatigue_level >= AI_BREAK_THRESHOLD and s.state == WorkState.WORKING:
            s.ai_break_recommended = True
            s.ai_break_level       = fatigue_level
        else:
            s.ai_break_recommended = False

    def should_show_reminder(self) -> tuple[bool, str]:
        """
        Returns (show: bool, reason: str).
        'reason' is 'six_hour' | 'ai_fatigue' | ''
        """
        s   = self.s
        now = time.time()

        # Respect snooze
        if s.snooze_until and now < s.snooze_until:
            return False, ""

        # 6-hour one-time trigger
        if (
            s.state == WorkState.WORKING
            and s.continuous_work_seconds >= self._reminder_secs
            and not s.six_hour_reminder_shown
            and s.reminder_count < self._max_reminders
        ):
            s.six_hour_reminder_shown = True
            s.reminder_count         += 1
            s.state                   = WorkState.REMINDER_SHOWN
            logger.info("6-hour break reminder triggered (count=%d)", s.reminder_count)
            return True, "six_hour"

        # AI-based early break
        if s.ai_break_recommended and s.state == WorkState.WORKING:
            return True, "ai_fatigue"

        return False, ""

    def snooze(self) -> None:
        """User clicked 'Later'."""
        self.s.snooze_until = time.time() + self._snooze_secs
        logger.info("Break snoozed for %.0f min", self._snooze_secs / 60)

    def start_break(self, extended: bool = False) -> None:
        """User clicked 'Start Break'."""
        now = time.time()
        self.s.break_start_time       = now
        self.s.break_duration_target  = self._extended_break if extended else self._default_break
        self.s.state                  = WorkState.BREAK_IN_PROGRESS
        logger.info("Break started (target=%.0f min)", self.s.break_duration_target / 60)

    def complete_break_manually(self) -> None:
        """User finished break countdown."""
        self._complete_break(time.time(), self.s.break_duration_target)

    def get_dashboard_data(self) -> dict:
        """Return all data needed by the UI layer."""
        s   = self.s
        now = time.time()

        cw  = s.continuous_work_seconds
        h   = int(cw // 3600)
        m   = int((cw % 3600) // 60)
        sec = int(cw % 60)

        remaining = max(0.0, self._reminder_secs - cw)
        rh = int(remaining // 3600)
        rm = int((remaining % 3600) // 60)
        rs = int(remaining % 60)

        break_elapsed = (now - s.break_start_time) if s.break_start_time else 0.0
        break_remaining = max(0.0, s.break_duration_target - break_elapsed)

        last_break_str = "—"
        if s.last_break_time:
            mins = int(s.last_break_duration // 60)
            last_break_str = f"{mins} min" if mins > 0 else f"{int(s.last_break_duration)}s"

        status = "Working"
        if s.state == WorkState.REMINDER_SHOWN:
            status = "⚠️ Break Overdue"
        elif s.state == WorkState.BREAK_IN_PROGRESS:
            status = "☕ On Break"
        elif cw >= self._reminder_secs * 0.75:
            status = "⏳ Long Working Session"

        return {
            "continuous_work_hms":   f"{h:02d}:{m:02d}:{sec:02d}",
            "continuous_work_secs":  cw,
            "reminder_threshold_secs": self._reminder_secs,
            "reminder_triggered":    s.six_hour_reminder_shown,
            "time_to_reminder_hms":  f"{rh:02d}:{rm:02d}:{rs:02d}",
            "last_break":            last_break_str,
            "total_breaks":          s.total_breaks,
            "state":                 s.state.name,
            "status":                status,
            "break_remaining_secs":  break_remaining,
            "ai_break_recommended":  s.ai_break_recommended,
            "ai_break_level":        s.ai_break_level,
            "reminder_count":        s.reminder_count,
        }

    def get_break_recommendation(self, fatigue_level: int) -> tuple[str, str, str]:
        """
        Returns (title, description, severity) based on fatigue + work duration.
        severity: 'info' | 'warning' | 'error'
        """
        s  = self.s
        cw = s.continuous_work_seconds

        if cw >= self._reminder_secs and fatigue_level >= 3:
            return ("🛑 Take an Extended Break",
                    "Very high fatigue + long session. Rest for 30+ minutes.",
                    "error")
        if cw >= self._reminder_secs:
            return ("⏰ Take a 10-Minute Break",
                    f"You've worked continuously for {int(cw/3600)}h {int((cw%3600)/60)}m. Step away.",
                    "warning")
        if fatigue_level >= 3:
            return ("🔴 Take a 10-Minute Break",
                    "High fatigue detected by AI. Rest your eyes and mind.",
                    "error")
        if fatigue_level == 2:
            return ("🟠 Consider a Short Break",
                    "Moderate fatigue detected. A 5-minute break can help.",
                    "warning")
        if fatigue_level == 1:
            return ("🟡 Stay Hydrated",
                    "Mild fatigue. Drink water and take a short breathing break.",
                    "info")
        return ("🟢 Keep Working",
                "You are alert and focused. No break needed.",
                "info")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _start_break(self, now: float) -> None:
        s = self.s
        if s.state != WorkState.BREAK_IN_PROGRESS:
            s.break_start_time = now
            s.state            = WorkState.BREAK_IN_PROGRESS
            logger.info("Break period started (idle threshold reached)")

    def _complete_break(self, now: float, duration: float) -> None:
        s = self.s
        s.last_break_time     = now
        s.last_break_duration = duration
        s.total_breaks       += 1
        # Reset work cycle
        s.work_cycle_start        = now
        s.continuous_work_seconds = 0.0
        s.six_hour_reminder_shown = False
        s.break_start_time        = None
        s.state                   = WorkState.WORKING
        s.snooze_until            = None
        logger.info(
            "Break completed (%.0f min). Work timer reset. Total breaks: %d",
            duration / 60, s.total_breaks,
        )
