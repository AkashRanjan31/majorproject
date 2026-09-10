"""
history.py
----------
Enterprise-grade prediction history management.
Handles saving, loading, ID generation, export, statistics,
and validation for all fatigue predictions.
"""

from __future__ import annotations

import io
import os
import platform
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psutil

from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ── Column schema (exact order written to CSV) ────────────────────────────────
HISTORY_COLUMNS: list[str] = [
    # identifiers
    "id", "session_id", "prediction_id",
    # timing
    "timestamp", "prediction_time_ms",
    # model metadata
    "model_name", "model_version",
    # keyboard features
    "key_press_count", "typing_speed_wpm", "key_hold_time_ms",
    "typing_accuracy", "backspace_count", "error_rate",
    "typing_rhythm", "idle_time_keyboard", "keystroke_interval_ms",
    # mouse features
    "mouse_click_count", "left_clicks", "right_clicks", "double_clicks",
    "mouse_speed", "mouse_distance", "mouse_jitter",
    "scroll_count", "drag_events", "idle_time_mouse",
    # prediction details
    "fatigue_level", "fatigue_name", "fatigue_score",
    "low_probability", "moderate_probability", "high_probability",
    "confidence", "risk_level",
    # recommendation
    "recommendation", "break_duration", "next_recommended_break",
    # system
    "cpu_usage", "ram_usage", "prediction_latency", "device_type", "os_name",
]

# ── Risk level mapping ────────────────────────────────────────────────────────
_RISK: dict[int, str] = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
_BREAK_DURATION: dict[int, int] = {0: 0, 1: 5, 2: 10, 3: 20}  # minutes


# ── Dataclass ─────────────────────────────────────────────────────────────────
@dataclass
class PredictionRecord:
    """One fully-enriched prediction row."""

    # identifiers
    id: int = 0
    session_id: str = ""
    prediction_id: str = ""

    # timing
    timestamp: str = ""
    prediction_time_ms: float = 0.0

    # model metadata
    model_name: str = ""
    model_version: str = ""

    # keyboard
    key_press_count: float = 0.0
    typing_speed_wpm: float = 0.0
    key_hold_time_ms: float = 0.0
    typing_accuracy: float = 0.0
    backspace_count: float = 0.0
    error_rate: float = 0.0
    typing_rhythm: float = 0.0
    idle_time_keyboard: float = 0.0
    keystroke_interval_ms: float = 0.0

    # mouse
    mouse_click_count: float = 0.0
    left_clicks: float = 0.0
    right_clicks: float = 0.0
    double_clicks: float = 0.0
    mouse_speed: float = 0.0
    mouse_distance: float = 0.0
    mouse_jitter: float = 0.0
    scroll_count: float = 0.0
    drag_events: float = 0.0
    idle_time_mouse: float = 0.0

    # prediction
    fatigue_level: int = 0
    fatigue_name: str = ""
    fatigue_score: float = 0.0
    low_probability: float = 0.0
    moderate_probability: float = 0.0
    high_probability: float = 0.0
    confidence: float = 0.0
    risk_level: str = "Low"

    # recommendation
    recommendation: str = ""
    break_duration: int = 0
    next_recommended_break: str = ""

    # system
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    prediction_latency: float = 0.0
    device_type: str = ""
    os_name: str = ""


# ── Session / prediction ID generators ───────────────────────────────────────
def generate_session_id() -> str:
    """
    Generate a unique session ID.

    Returns:
        str: e.g. ``SESSION_20260803_001``
    """
    date_str = datetime.now().strftime("%Y%m%d")
    suffix = str(uuid.uuid4().int)[:3].zfill(3)
    return f"SESSION_{date_str}_{suffix}"


def generate_prediction_id(sequence: int) -> str:
    """
    Generate a zero-padded prediction ID.

    Args:
        sequence: Monotonically increasing integer.

    Returns:
        str: e.g. ``PRED_000042``
    """
    return f"PRED_{sequence:06d}"


# ── Path helpers ──────────────────────────────────────────────────────────────
def _history_path() -> Path:
    config = get_config()
    return Path(config.HISTORY_DIR) / config.HISTORY_FILE


def _ensure_history_dir() -> None:
    """Create history directory if it does not exist."""
    _history_path().parent.mkdir(parents=True, exist_ok=True)


# ── System info (cached per process) ─────────────────────────────────────────
_OS_NAME: str = platform.system()
_DEVICE_TYPE: str = "Desktop" if not any(
    k in platform.node().lower() for k in ("laptop", "book", "mobile")
) else "Laptop"


def _system_snapshot() -> tuple[float, float]:
    """Return (cpu_percent, ram_percent) without blocking."""
    try:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        return float(cpu), float(ram)
    except Exception:
        return 0.0, 0.0


# ── Feature → record mapping ──────────────────────────────────────────────────
def _map_features(features: dict[str, Any]) -> dict[str, float]:
    """
    Map raw feature dict (from FeatureExtractor) to PredictionRecord fields.
    Converts key_hold_time (seconds) → ms, typing_speed → wpm alias, etc.
    """
    kp = float(features.get("key_press_count", 0))
    bs = float(features.get("backspace_count", 0))
    er = float(features.get("error_rate", 0))
    kht = float(features.get("key_hold_time", 0)) * 1000  # s → ms
    ts = float(features.get("typing_speed", 0))
    idle_kb = float(features.get("idle_time", 0))

    # Typing accuracy = 1 - error_rate, clamped [0, 1]
    accuracy = max(0.0, min(1.0, 1.0 - er))

    # Typing rhythm: std-dev of inter-key intervals is not available at this
    # stage (raw timestamps already aggregated), so we use a proxy:
    # rhythm ≈ key_hold_time_ms / max(typing_speed, 1)
    rhythm = kht / max(ts, 1.0)

    # Keystroke interval: average gap between presses ≈ 60 000 / (wpm * 5)
    keystroke_interval = (60_000.0 / max(ts * 5, 1.0)) if ts > 0 else 0.0

    mc = float(features.get("mouse_click_count", 0))
    lc = float(features.get("left_click", 0))
    rc = float(features.get("right_click", 0))
    dc = float(features.get("double_click", 0))
    spd = float(features.get("cursor_speed", 0))
    dist = float(features.get("cursor_distance", 0))
    sc = float(features.get("scroll_count", 0))
    drag = float(features.get("drag_count", 0))
    idle_ms = float(features.get("idle_mouse_time", 0))
    mv_spd = float(features.get("movement_speed", 0))

    # Mouse jitter: difference between cursor_speed and movement_speed
    jitter = abs(spd - mv_spd)

    return {
        "key_press_count": kp,
        "typing_speed_wpm": ts,
        "key_hold_time_ms": kht,
        "typing_accuracy": accuracy,
        "backspace_count": bs,
        "error_rate": er,
        "typing_rhythm": rhythm,
        "idle_time_keyboard": idle_kb,
        "keystroke_interval_ms": keystroke_interval,
        "mouse_click_count": mc,
        "left_clicks": lc,
        "right_clicks": rc,
        "double_clicks": dc,
        "mouse_speed": spd,
        "mouse_distance": dist,
        "mouse_jitter": jitter,
        "scroll_count": sc,
        "drag_events": drag,
        "idle_time_mouse": idle_ms,
    }


# ── Validation ────────────────────────────────────────────────────────────────
def validate_prediction(record: PredictionRecord) -> bool:
    """
    Validate a PredictionRecord before persisting.

    Args:
        record: The record to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If any required field is missing or out of range.
    """
    if not record.session_id:
        raise ValueError("session_id is required")
    if not record.prediction_id:
        raise ValueError("prediction_id is required")
    if record.fatigue_level not in (0, 1, 2, 3, 4):
        raise ValueError(f"fatigue_level must be 0-4, got {record.fatigue_level}")
    total_prob = record.low_probability + record.moderate_probability + record.high_probability
    if total_prob > 0 and not (0.98 <= total_prob <= 1.02):
        logger.warning("Probabilities sum to %.4f (expected ~1.0)", total_prob)
    return True


# ── Core save / load ──────────────────────────────────────────────────────────
def save_prediction(record: PredictionRecord) -> bool:
    """
    Append one PredictionRecord to the CSV history file.

    Creates the file with headers if it does not exist.
    Skips duplicate prediction_ids.

    Args:
        record: Fully populated PredictionRecord.

    Returns:
        bool: True on success.
    """
    try:
        validate_prediction(record)
        _ensure_history_dir()
        path = _history_path()

        row = {col: getattr(record, col, "") for col in HISTORY_COLUMNS}
        df_new = pd.DataFrame([row])

        if path.exists():
            # Duplicate guard
            try:
                existing = pd.read_csv(path, usecols=["prediction_id"], dtype=str)
                if record.prediction_id in existing["prediction_id"].values:
                    logger.warning("Duplicate prediction_id %s — skipped", record.prediction_id)
                    return False
            except Exception:
                pass  # file may be empty or malformed — proceed

            df_new.to_csv(path, mode="a", header=False, index=False)
        else:
            df_new.to_csv(path, mode="w", header=True, index=False)

        logger.debug("Saved prediction %s to %s", record.prediction_id, path)
        return True

    except Exception as exc:
        logger.error("save_prediction failed: %s", exc)
        return False


def load_prediction_history(
    limit: int = 500,
    session_id: str | None = None,
    fatigue_level: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
) -> pd.DataFrame:
    """
    Load prediction history from CSV with optional filters.

    Args:
        limit: Maximum rows to return (most recent first).
        session_id: Filter to a specific session.
        fatigue_level: Filter to a specific level (0-3).
        date_from: Inclusive start datetime.
        date_to: Inclusive end datetime.
        search: Case-insensitive substring match on fatigue_name / recommendation.

    Returns:
        pd.DataFrame: Filtered history, newest first.
    """
    path = _history_path()
    if not path.exists():
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    try:
        df = pd.read_csv(path, dtype=str)

        # Drop legacy unnamed index column if present
        df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]

        # Ensure all expected columns exist
        for col in HISTORY_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        df = df[HISTORY_COLUMNS].copy()

        # Type coercions
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for num_col in [
            "fatigue_level", "id",
            "key_press_count", "typing_speed_wpm", "confidence",
            "low_probability", "moderate_probability", "high_probability",
            "fatigue_score", "cpu_usage", "ram_usage",
        ]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0)

        # Filters
        if session_id:
            df = df[df["session_id"] == session_id]
        if fatigue_level is not None:
            df = df[df["fatigue_level"] == fatigue_level]
        if date_from:
            df = df[df["timestamp"] >= pd.Timestamp(date_from)]
        if date_to:
            df = df[df["timestamp"] <= pd.Timestamp(date_to)]
        if search:
            mask = (
                df["fatigue_name"].str.contains(search, case=False, na=False)
                | df["recommendation"].str.contains(search, case=False, na=False)
                | df["session_id"].str.contains(search, case=False, na=False)
            )
            df = df[mask]

        df = df.sort_values("timestamp", ascending=False).head(limit)
        return df.reset_index(drop=True)

    except Exception as exc:
        logger.error("load_prediction_history failed: %s", exc)
        return pd.DataFrame(columns=HISTORY_COLUMNS)


# ── Statistics ────────────────────────────────────────────────────────────────
def calculate_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute summary statistics from a history DataFrame.

    Args:
        df: Output of load_prediction_history().

    Returns:
        dict with keys: total, avg_fatigue, avg_confidence, high_count,
        today_count, week_count, month_count, session_count,
        normal_pct, moderate_pct, high_pct.
    """
    if df.empty:
        return {
            "total": 0, "avg_fatigue": 0.0, "avg_confidence": 0.0,
            "high_count": 0, "today_count": 0, "week_count": 0,
            "month_count": 0, "session_count": 0,
            "normal_pct": 0.0, "moderate_pct": 0.0, "high_pct": 0.0,
        }

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    fl = pd.to_numeric(df["fatigue_level"], errors="coerce").fillna(0)
    conf = pd.to_numeric(df["confidence"], errors="coerce").fillna(0)

    total = len(df)
    return {
        "total": total,
        "avg_fatigue": float(fl.mean()),
        "avg_confidence": float(conf.mean()),
        "high_count": int((fl >= 2).sum()),
        "today_count": int((ts >= today_start).sum()),
        "week_count": int((ts >= week_start).sum()),
        "month_count": int((ts >= month_start).sum()),
        "session_count": int(df["session_id"].nunique()),
        "normal_pct": float((fl == 0).sum() / total * 100),
        "moderate_pct": float((fl == 1).sum() / total * 100),
        "high_pct": float((fl >= 2).sum() / total * 100),
    }


# ── Export ────────────────────────────────────────────────────────────────────
def export_history(df: pd.DataFrame, fmt: str = "csv") -> bytes:
    """
    Serialise history DataFrame to bytes for download.

    Args:
        df: History DataFrame.
        fmt: ``"csv"``, ``"excel"``, or ``"pdf"``.

    Returns:
        bytes: File content ready for st.download_button.
    """
    if fmt == "csv":
        return df.to_csv(index=False).encode("utf-8")

    if fmt == "excel":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Predictions")
            # Summary sheet
            stats = calculate_statistics(df)
            pd.DataFrame([stats]).to_excel(writer, index=False, sheet_name="Summary")
        return buf.getvalue()

    if fmt == "pdf":
        return _export_pdf(df)

    raise ValueError(f"Unknown export format: {fmt!r}")


def _export_pdf(df: pd.DataFrame) -> bytes:
    """Generate a simple PDF report using fpdf2."""
    try:
        from fpdf import FPDF  # type: ignore

        stats = calculate_statistics(df)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NeuroSense AI — Fatigue Prediction Report", ln=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
        pdf.ln(4)

        # Summary
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Summary Statistics", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for k, v in stats.items():
            label = k.replace("_", " ").title()
            val = f"{v:.2f}" if isinstance(v, float) else str(v)
            pdf.cell(0, 6, f"  {label}: {val}", ln=True)
        pdf.ln(4)

        # Table header
        pdf.set_font("Helvetica", "B", 8)
        cols = ["timestamp", "fatigue_level", "fatigue_name", "confidence",
                "risk_level", "recommendation"]
        widths = [38, 18, 30, 22, 22, 60]
        for col, w in zip(cols, widths):
            pdf.cell(w, 7, col.replace("_", " ").title(), border=1)
        pdf.ln()

        # Table rows (max 200)
        pdf.set_font("Helvetica", "", 7)
        for _, row in df.head(200).iterrows():
            for col, w in zip(cols, widths):
                val = str(row.get(col, ""))[:30]
                pdf.cell(w, 6, val, border=1)
            pdf.ln()

        return bytes(pdf.output())
    except ImportError:
        logger.warning("fpdf2 not installed — returning CSV fallback for PDF export")
        return df.to_csv(index=False).encode("utf-8")


# ── Main public builder ───────────────────────────────────────────────────────
def build_prediction_record(
    *,
    session_id: str,
    prediction_id: str,
    row_id: int,
    prediction: dict[str, Any],
    features: dict[str, Any],
    prediction_start_time: float,
) -> PredictionRecord:
    """
    Construct a fully-enriched PredictionRecord from live prediction data.

    Args:
        session_id: Current session identifier.
        prediction_id: Unique prediction identifier.
        row_id: Auto-increment integer for the ``id`` column.
        prediction: Output dict from FatiguePredictor.predict().
        features: Feature dict from FeatureExtractor.extract_features().
        prediction_start_time: time.time() captured before predict() was called.

    Returns:
        PredictionRecord: Ready to pass to save_prediction().
    """
    config = get_config()
    now = datetime.now()
    elapsed_ms = (time.time() - prediction_start_time) * 1000
    cpu, ram = _system_snapshot()

    probs = prediction.get("probabilities", {})
    # Keys are full class names e.g. "Normal", "Low Fatigue", "Moderate Fatigue"
    low_p  = float(probs.get("Normal", 0.0))
    mod_p  = float(probs.get("Moderate Fatigue", 0.0))
    high_p = float(probs.get("High Fatigue", 0.0))

    lvl = int(prediction.get("level", 0))
    conf = float(prediction.get("confidence", 0.0))

    # fatigue_score: weighted sum (0=0, 1=0.33, 2=0.67, 3=1.0)
    fatigue_score = round(lvl / 3.0, 4)

    # next recommended break: now + break_duration minutes
    break_min = _BREAK_DURATION.get(lvl, 0)
    next_break = (
        (now + timedelta(minutes=break_min)).strftime("%H:%M")
        if break_min > 0 else "—"
    )

    feat = _map_features(features)

    return PredictionRecord(
        id=row_id,
        session_id=session_id,
        prediction_id=prediction_id,
        timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
        prediction_time_ms=round(elapsed_ms, 2),
        model_name=config.MODEL_NAME,
        model_version=config.MODEL_VERSION,
        # keyboard
        key_press_count=feat["key_press_count"],
        typing_speed_wpm=feat["typing_speed_wpm"],
        key_hold_time_ms=feat["key_hold_time_ms"],
        typing_accuracy=feat["typing_accuracy"],
        backspace_count=feat["backspace_count"],
        error_rate=feat["error_rate"],
        typing_rhythm=feat["typing_rhythm"],
        idle_time_keyboard=feat["idle_time_keyboard"],
        keystroke_interval_ms=feat["keystroke_interval_ms"],
        # mouse
        mouse_click_count=feat["mouse_click_count"],
        left_clicks=feat["left_clicks"],
        right_clicks=feat["right_clicks"],
        double_clicks=feat["double_clicks"],
        mouse_speed=feat["mouse_speed"],
        mouse_distance=feat["mouse_distance"],
        mouse_jitter=feat["mouse_jitter"],
        scroll_count=feat["scroll_count"],
        drag_events=feat["drag_events"],
        idle_time_mouse=feat["idle_time_mouse"],
        # prediction
        fatigue_level=lvl,
        fatigue_name=prediction.get("name", ""),
        fatigue_score=fatigue_score,
        low_probability=round(low_p, 4),
        moderate_probability=round(mod_p, 4),
        high_probability=round(high_p, 4),
        confidence=round(conf, 4),
        risk_level=_RISK.get(lvl, "Low"),
        # recommendation
        recommendation=prediction.get("recommendation", ""),
        break_duration=break_min,
        next_recommended_break=next_break,
        # system
        cpu_usage=cpu,
        ram_usage=ram,
        prediction_latency=round(elapsed_ms, 2),
        device_type=_DEVICE_TYPE,
        os_name=_OS_NAME,
    )
