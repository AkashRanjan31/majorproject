"""
monitor.py
----------
Real-time keyboard and mouse activity monitoring.

Root cause & fix
----------------
Windows WH_KEYBOARD_LL / WH_MOUSE_LL hooks only deliver events to the thread
that installed them AND is actively pumping Windows messages.  When any Python
process is launched as a child of cmd.exe (which is what Streamlit does), the
process inherits a console session that does NOT deliver global hook events.

Fix: launch input_worker.py via ShellExecuteW, which creates a true top-level
process with its own desktop session.  The worker creates a hidden Win32
message-only window, registers Raw Input for keyboard (works without admin),
installs WH_MOUSE_LL for mouse, and runs GetMessage on the main thread.
It writes a JSON snapshot every 250 ms to a shared temp file.
ActivityMonitor reads that file every 250 ms.

Fallback: direct pynput (Linux / macOS, or Windows when already top-level).
"""

import json
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parents[1]
WORKER_SCRIPT = PROJECT_ROOT / "input_worker.py"


# ---------------------------------------------------------------------------
# CircularBuffer — kept for API compatibility with other modules
# ---------------------------------------------------------------------------
class CircularBuffer:
    """Thread-safe circular buffer."""

    def __init__(self, maxsize: int = 1000):
        from collections import deque
        self._buf  = deque(maxlen=maxsize)
        self._lock = threading.Lock()

    def append(self, item) -> None:
        with self._lock:
            self._buf.append(item)

    def get_all(self) -> list:
        with self._lock:
            return list(self._buf)

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buf)


# ---------------------------------------------------------------------------
# ActivityMonitor
# ---------------------------------------------------------------------------
class ActivityMonitor:
    """
    Captures keyboard and mouse events.

    On Windows  → launches input_worker.py via ShellExecuteW (top-level
                  process) and reads its JSON snapshot file.
    Fallback    → direct pynput listeners (Linux / macOS).
    """

    def __init__(self, window_size: int = 60):
        self.window_size      = window_size
        self.is_monitoring    = False
        self._session_start   = time.time()
        self._lock            = threading.Lock()

        # ── Shared-file IPC ───────────────────────────────────────────
        self._shared_dir  = Path(tempfile.gettempdir()) / "neurosense"
        self._shared_dir.mkdir(parents=True, exist_ok=True)
        self._shared_file = self._shared_dir / "input_snapshot.json"
        self._ready_file  = self._shared_dir / "input_snapshot.ready"

        # ── Backend selection ─────────────────────────────────────────
        self._use_subprocess = sys.platform == "win32"

        # ── Direct pynput fallback state ──────────────────────────────
        self._kb_listener  = None
        self._ms_listener  = None
        self._direct_state = self._empty_state()

        # ── Snapshot cache ────────────────────────────────────────────
        self._last_snapshot: dict = {}
        self._snap_lock = threading.Lock()

        # ── Reader thread ─────────────────────────────────────────────
        self._reader_thread: threading.Thread | None = None

        logger.info("ActivityMonitor init (window=%ds subprocess=%s)",
                    window_size, self._use_subprocess)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _empty_state() -> dict:
        return {
            "key_presses": [], "key_releases": [],
            "backspace_count": 0,
            "mouse_clicks": {"left": 0, "right": 0, "double": 0},
            "scroll_count": 0, "mouse_movements": [],
            "keyboard_idle": 0.0, "mouse_idle": 0.0,
            "session_duration": 0.0, "drag_count": 0,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self.is_monitoring:
            logger.warning("ActivityMonitor already running")
            return
        self.is_monitoring  = True
        self._session_start = time.time()

        if self._use_subprocess:
            self._start_subprocess()
        else:
            self._start_direct()

        self._reader_thread = threading.Thread(
            target=self._reader_loop, name="monitor-reader", daemon=True
        )
        self._reader_thread.start()
        logger.info("ActivityMonitor started")

    def stop(self) -> None:
        self.is_monitoring = False
        # Kill worker if we have a handle (Popen fallback path)
        if hasattr(self, "_worker_proc") and self._worker_proc:
            try:
                self._worker_proc.terminate()
                self._worker_proc.wait(timeout=3)
            except Exception:
                pass
            self._worker_proc = None
        # Stop direct listeners
        for attr in ("_kb_listener", "_ms_listener"):
            lst = getattr(self, attr, None)
            if lst:
                try:
                    lst.stop()
                except Exception:
                    pass
        # Remove shared files so a new session starts clean
        for f in (self._shared_file, self._ready_file):
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        logger.info("ActivityMonitor stopped")

    def is_alive(self) -> bool:
        """True if the worker is running and writing fresh snapshots."""
        if self._use_subprocess:
            # Primary check: snapshot file freshness
            if self._shared_file.exists():
                try:
                    return (time.time() - self._shared_file.stat().st_mtime) < 3.0
                except Exception:
                    pass
            # Secondary: process still running
            if hasattr(self, '_worker_proc') and self._worker_proc:
                return self._worker_proc.poll() is None
            return self._ready_file.exists()
        kb = getattr(self, "_kb_listener", None)
        ms = getattr(self, "_ms_listener", None)
        if kb and ms:
            return kb.is_alive() and ms.is_alive()
        return self.is_monitoring

    # ------------------------------------------------------------------
    # Subprocess backend  (Windows)
    # ------------------------------------------------------------------
    def _start_subprocess(self) -> None:
        """
        Launch input_worker.py with CREATE_NEW_CONSOLE.

        CREATE_NEW_CONSOLE gives the worker its own console window and
        desktop session, which is required for Windows global input hooks
        (WH_KEYBOARD_LL via Raw Input, WH_MOUSE_LL) to receive events.
        SW_HIDE / DETACHED_PROCESS do NOT work because they deprive the
        process of a proper interactive desktop session.
        """
        python_exe = sys.executable
        # pythonw.exe suppresses the console window on Windows
        pythonw = Path(python_exe).parent / "pythonw.exe"
        exe     = str(pythonw) if pythonw.exists() else python_exe

        self._ready_file.unlink(missing_ok=True)
        self._shared_file.unlink(missing_ok=True)

        try:
            self._worker_proc = subprocess.Popen(
                [exe, str(WORKER_SCRIPT), str(self._shared_file)],
                # CREATE_NEW_CONSOLE: worker gets its own console + desktop
                # session so Windows delivers hook events to it.
                # Do NOT pipe stdout/stderr — that can interfere with the
                # console allocation on some Windows versions.
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=str(PROJECT_ROOT),
            )
            logger.info("input_worker launched (pid=%d)", self._worker_proc.pid)

            # Wait up to 5 s for the ready marker
            deadline = time.time() + 5.0
            while time.time() < deadline:
                if self._ready_file.exists():
                    logger.info("input_worker signalled ready")
                    return
                time.sleep(0.1)

            logger.warning("input_worker not ready after 5 s — falling back")
            self._use_subprocess = False
            self._start_direct()

        except Exception as exc:
            logger.error("Subprocess launch failed (%s) — falling back", exc)
            self._use_subprocess = False
            self._start_direct()

    # ------------------------------------------------------------------
    # Direct pynput backend  (fallback)
    # ------------------------------------------------------------------
    def _start_direct(self) -> None:
        try:
            from pynput import keyboard
            self._kb_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release,
                daemon=True,
            )
            self._kb_listener.start()
            logger.info("Direct KB listener started (tid=%s)", self._kb_listener.ident)
        except Exception as exc:
            logger.error("Direct KB listener failed: %s", exc)

        try:
            from pynput import mouse
            self._ms_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll,
                daemon=True,
            )
            self._ms_listener.start()
            logger.info("Direct MS listener started (tid=%s)", self._ms_listener.ident)
        except Exception as exc:
            logger.error("Direct MS listener failed: %s", exc)

    # ------------------------------------------------------------------
    # Direct pynput callbacks
    # ------------------------------------------------------------------
    def _on_key_press(self, key) -> None:
        if not self.is_monitoring:
            return
        t = time.time()
        with self._lock:
            self._direct_state["key_presses"].append(t)

    def _on_key_release(self, key) -> None:
        if not self.is_monitoring:
            return
        t = time.time()
        with self._lock:
            self._direct_state["key_releases"].append(t)
            try:
                from pynput.keyboard import Key
                if key == Key.backspace:
                    self._direct_state["backspace_count"] += 1
            except Exception:
                pass

    def _on_mouse_move(self, x, y) -> None:
        if not self.is_monitoring:
            return
        import math
        t = time.time()
        with self._lock:
            st = self._direct_state
            lp = st.get("_last_pos")
            if lp:
                lx, ly, lt = lp
                dist = math.sqrt((x - lx) ** 2 + (y - ly) ** 2)
                dt   = t - lt
                if dist > 0 and dt > 0:
                    st["mouse_movements"].append(
                        {"time": t, "x": x, "y": y, "distance": dist, "time_diff": dt}
                    )
            st["_last_pos"] = (x, y, t)

    def _on_mouse_click(self, x, y, button, pressed) -> None:
        if not self.is_monitoring:
            return
        with self._lock:
            try:
                from pynput.mouse import Button
                if button == Button.left and pressed:
                    self._direct_state["mouse_clicks"]["left"] += 1
                elif button == Button.right and pressed:
                    self._direct_state["mouse_clicks"]["right"] += 1
            except Exception:
                pass

    def _on_mouse_scroll(self, x, y, dx, dy) -> None:
        if not self.is_monitoring:
            return
        with self._lock:
            self._direct_state["scroll_count"] += 1

    # ------------------------------------------------------------------
    # Snapshot reader thread
    # ------------------------------------------------------------------
    def _reader_loop(self) -> None:
        while self.is_monitoring:
            if self._use_subprocess:
                self._read_file_snapshot()
            else:
                self._sync_direct_snapshot()
            time.sleep(0.25)

    def _read_file_snapshot(self) -> None:
        if not self._shared_file.exists():
            return
        try:
            text = self._shared_file.read_text(encoding="utf-8")
            data = json.loads(text)
            # Trim events to the current window (worker keeps cumulative deques)
            cutoff = time.time() - self.window_size
            data["key_presses"]     = [t for t in data.get("key_presses", [])     if t >= cutoff]
            data["key_releases"]    = [t for t in data.get("key_releases", [])    if t >= cutoff]
            data["mouse_movements"] = [m for m in data.get("mouse_movements", []) if m.get("time", 0) >= cutoff]
            with self._snap_lock:
                self._last_snapshot = data
        except Exception:
            pass   # file may be mid-write (atomic rename handles most cases)

    def _sync_direct_snapshot(self) -> None:
        t      = time.time()
        cutoff = t - self.window_size
        with self._lock:
            st = self._direct_state
            snap = {
                "key_presses":     [ts for ts in st["key_presses"]   if ts >= cutoff],
                "key_releases":    [ts for ts in st["key_releases"]  if ts >= cutoff],
                "backspace_count": st["backspace_count"],
                "mouse_clicks":    dict(st["mouse_clicks"]),
                "scroll_count":    st["scroll_count"],
                "mouse_movements": [m for m in st["mouse_movements"] if m["time"] >= cutoff],
                "keyboard_idle":   t - (st["key_presses"][-1] if st["key_presses"] else self._session_start),
                "mouse_idle":      0.0,
                "session_duration": t - self._session_start,
                "drag_count":      0,
                "timestamp":       t,
            }
        with self._snap_lock:
            self._last_snapshot = snap

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------
    def get_raw_data(self) -> dict:
        """Return the latest monitoring snapshot."""
        with self._snap_lock:
            if self._last_snapshot:
                snap = dict(self._last_snapshot)
                snap["session_duration"] = time.time() - self._session_start
                return snap
        return {
            "key_presses": [], "key_releases": [],
            "backspace_count": 0,
            "mouse_clicks": {"left": 0, "right": 0, "double": 0},
            "scroll_count": 0, "mouse_movements": [],
            "keyboard_idle": 0.0, "mouse_idle": 0.0,
            "session_duration": time.time() - self._session_start,
            "drag_count": 0, "timestamp": time.time(),
        }

    def reset_window(self) -> None:
        """No-op: the worker maintains its own rolling window."""
        pass

    def get_stats(self) -> dict:
        """Return monitoring statistics (used by the debug panel)."""
        with self._snap_lock:
            snap = dict(self._last_snapshot)

        alive = self.is_alive()
        return {
            "is_monitoring":        self.is_monitoring,
            "kb_alive":             alive,
            "ms_alive":             alive,
            "backend":              "subprocess" if self._use_subprocess else "direct",
            "session_duration":     time.time() - self._session_start,
            "key_presses_buffered": len(snap.get("key_presses", [])),
            "mouse_moves_buffered": len(snap.get("mouse_movements", [])),
            "backspace_count":      snap.get("backspace_count", 0),
            "left_clicks":          snap.get("mouse_clicks", {}).get("left", 0),
            "right_clicks":         snap.get("mouse_clicks", {}).get("right", 0),
            "scroll_count":         snap.get("scroll_count", 0),
            "drag_count":           snap.get("drag_count", 0),
            # Legacy keys used by live_monitor.py
            "key_events":           len(snap.get("key_presses", [])),
            "mouse_events":         len(snap.get("mouse_movements", [])),
        }
