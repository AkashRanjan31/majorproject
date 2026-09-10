"""
db.py
-----
SQLite persistence layer: stores predictions, features, and session data.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from src.logger import setup_logger

logger = setup_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "fatigue_data.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    """Create tables if they don't exist."""
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS predictions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            fatigue_level INTEGER,
            fatigue_name  TEXT,
            confidence    REAL,
            recommendation TEXT,
            features_json TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time  TEXT,
            end_time    TEXT,
            total_predictions INTEGER DEFAULT 0,
            avg_fatigue REAL,
            max_fatigue INTEGER
        );
        """)
    logger.info("Database initialised at %s", DB_PATH)


def insert_prediction(prediction: dict, features: dict, recommendation: str) -> None:
    """Persist one prediction row."""
    try:
        with _conn() as con:
            con.execute(
                """INSERT INTO predictions
                   (timestamp, fatigue_level, fatigue_name, confidence, recommendation, features_json)
                   VALUES (?,?,?,?,?,?)""",
                (
                    prediction.get("timestamp", datetime.now()).isoformat()
                    if hasattr(prediction.get("timestamp"), "isoformat")
                    else str(prediction.get("timestamp", "")),
                    prediction.get("level", 0),
                    prediction.get("name", ""),
                    prediction.get("confidence", 0.0),
                    recommendation,
                    json.dumps({k: round(float(v), 4) for k, v in features.items()}),
                ),
            )
    except Exception as e:
        logger.warning("DB insert failed: %s", e)


def fetch_predictions(limit: int = 200, search: str = "") -> list[dict]:
    """Return recent predictions as list of dicts."""
    try:
        with _conn() as con:
            if search:
                rows = con.execute(
                    "SELECT * FROM predictions WHERE fatigue_name LIKE ? ORDER BY id DESC LIMIT ?",
                    (f"%{search}%", limit),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning("DB fetch failed: %s", e)
        return []


def fetch_stats() -> dict:
    """Aggregate session statistics from DB."""
    try:
        with _conn() as con:
            row = con.execute(
                """SELECT COUNT(*) as total,
                          AVG(fatigue_level) as avg_f,
                          MAX(fatigue_level) as max_f,
                          AVG(confidence)    as avg_c
                   FROM predictions"""
            ).fetchone()
        return dict(row) if row else {}
    except Exception as e:
        logger.warning("DB stats failed: %s", e)
        return {}
