"""
monitor.py (Production Version)
-------------------------------
Real-time keyboard and mouse activity monitoring with proper resource management.
Features: circular buffers, error handling, logging, cleanup, bounds checking.
"""

import threading
import time
from datetime import datetime
from collections import deque
from pynput import keyboard, mouse
import logging
from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)


class CircularBuffer:
    """Memory-efficient circular buffer with automatic cleanup."""

    def __init__(self, maxsize: int = 1000):
        """Initialize circular buffer."""
        self.buffer = deque(maxlen=maxsize)
        self.maxsize = maxsize
        self.lock = threading.Lock()

    def append(self, item):
        """Add item to buffer."""
        with self.lock:
            self.buffer.append(item)

    def get_all(self):
        """Get all items as list."""
        with self.lock:
            return list(self.buffer)

    def clear(self):
        """Clear buffer."""
        with self.lock:
            self.buffer.clear()

    def __len__(self):
        """Get buffer size."""
        with self.lock:
            return len(self.buffer)


class ActivityMonitor:
    """Monitor keyboard and mouse activity in real-time."""

    def __init__(self, window_size=60):
        """
        Initialize the activity monitor.

        Args:
            window_size: Time window in seconds for collecting features
        """
        config = get_config()
        self.window_size = window_size
        self.listener_keyboard = None
        self.listener_mouse = None
        self.is_monitoring = False
        self.lock = threading.Lock()

        # Use circular buffers with size limits to prevent memory leaks
        self.key_presses = CircularBuffer(config.MAX_KEY_EVENTS_PER_WINDOW)
        self.key_releases = CircularBuffer(config.MAX_KEY_EVENTS_PER_WINDOW)
        self.backspace_count = 0
        self.last_key_time = None

        self.mouse_clicks = {'left': 0, 'right': 0, 'double': 0}
        self.scroll_count = 0
        self.mouse_movements = CircularBuffer(config.MAX_MOUSE_MOVEMENTS_PER_WINDOW)
        self.last_mouse_pos = None
        self.drag_count = 0
        self.mouse_idle_start = time.time()

        # Double-click detection: store last left-click time
        self._last_left_click_time = None
        self._is_left_pressed = False
        self._moved_while_pressed = False
        self._last_left_release_time = None

        # Accumulated idle tracking (matches training: sum of idle durations)
        self._keyboard_idle_accumulated = 0.0
        self._mouse_idle_accumulated = 0.0
        self._keyboard_last_active = time.time()
        self._mouse_last_active = time.time()
        self._keyboard_idle_start = None
        self._mouse_idle_start = None
        self._idle_threshold = 0.5  # seconds of no activity = idle

        # Session and cleanup tracking
        self.session_start = time.time()
        self.last_cleanup = time.time()

        logger.info(f"ActivityMonitor initialized with window_size={window_size}s")

    def start(self):
        """Start monitoring keyboard and mouse with error handling."""
        if self.is_monitoring:
            logger.warning("Monitor already running")
            return

        try:
            self.is_monitoring = True
            self.session_start = time.time()

            # Reset idle accumulators
            self._keyboard_idle_accumulated = 0.0
            self._mouse_idle_accumulated = 0.0
            self._keyboard_last_active = time.time()
            self._mouse_last_active = time.time()
            self._keyboard_idle_start = None
            self._mouse_idle_start = None

            # Keyboard listener
            self.listener_keyboard = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.listener_keyboard.start()

            # Mouse listener
            self.listener_mouse = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click,
                on_scroll=self._on_mouse_scroll
            )
            self.listener_mouse.start()

            logger.info("Monitoring started successfully")
        except Exception as e:
            self.is_monitoring = False
            logger.error(f"Failed to start monitoring: {e}")
            raise

    def stop(self):
        """Stop monitoring and cleanup resources."""
        try:
            self.is_monitoring = False

            if self.listener_keyboard:
                self.listener_keyboard.stop()
                self.listener_keyboard = None

            if self.listener_mouse:
                self.listener_mouse.stop()
                self.listener_mouse = None

            self._cleanup()
            logger.info("Monitoring stopped and resources cleaned up")
        except Exception as e:
            logger.error(f"Error stopping monitor: {e}")

    def _cleanup(self):
        """Clean up old data and reset counters periodically."""
        try:
            with self.lock:
                current_time = time.time()

                # Only cleanup if enough time has passed (60 seconds)
                if current_time - self.last_cleanup < 60:
                    return

                self.key_presses.clear()
                self.key_releases.clear()
                self.mouse_movements.clear()
                self.backspace_count = 0
                self.mouse_clicks = {'left': 0, 'right': 0, 'double': 0}
                self.scroll_count = 0
                self.drag_count = 0

                self.last_cleanup = current_time
                logger.debug("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _track_idle_time(self, idle_type, current_time):
        """Track accumulated idle time for keyboard or mouse."""
        if idle_type == 'keyboard':
            self._keyboard_idle_accumulated = 0.0
            self._keyboard_last_active = current_time
            self._keyboard_idle_start = None
        elif idle_type == 'mouse':
            self._mouse_idle_accumulated = 0.0
            self._mouse_last_active = current_time
            self._mouse_idle_start = None

    def _on_key_press(self, key):
        """Handle key press event with error handling."""
        if not self.is_monitoring:
            return

        try:
            with self.lock:
                current_time = time.time()
                self.key_presses.append(current_time)
                self.last_key_time = current_time
                self._track_idle_time('keyboard', current_time)
        except Exception as e:
            logger.error(f"Error in key press handler: {e}")

    def _on_key_release(self, key):
        """Handle key release event with error handling."""
        if not self.is_monitoring:
            return

        try:
            with self.lock:
                current_time = time.time()
                self.key_releases.append(current_time)

                # Track backspace
                if key == keyboard.Key.backspace:
                    self.backspace_count += 1
        except Exception as e:
            logger.error(f"Error in key release handler: {e}")

    def _on_mouse_move(self, x, y):
        """Handle mouse movement with relaxed bounds checking."""
        if not self.is_monitoring:
            return

        try:
            with self.lock:
                current_time = time.time()

                # Relaxed bounds: allow any valid screen coordinate (including multi-monitor)
                # Only reject obviously invalid values (NaN/Inf)
                if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
                    logger.warning(f"Invalid mouse position type: ({x}, {y})")
                    return

                if self.last_mouse_pos is not None:
                    last_x, last_y, last_t = self.last_mouse_pos
                    distance = ((x - last_x)**2 + (y - last_y)**2) ** 0.5
                    time_diff = current_time - last_t

                    if distance > 0 and time_diff > 0:
                        self.mouse_movements.append({
                            'time': current_time,
                            'distance': distance,
                            'time_diff': time_diff
                        })
                        self._track_idle_time('mouse', current_time)

                        # Flag movement while left button pressed for drag detection
                        if self._is_left_pressed:
                            self._moved_while_pressed = True

                self.last_mouse_pos = (x, y, current_time)
        except Exception as e:
            logger.error(f"Error in mouse move handler: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click with double-click and drag detection."""
        if not self.is_monitoring:
            return

        try:
            with self.lock:
                current_time = time.time()

                if button == mouse.Button.left:
                    if pressed:
                        # Left button pressed
                        self.mouse_clicks['left'] += 1
                        self._is_left_pressed = True
                        self._moved_while_pressed = False

                        # Double-click detection: within 300ms of last release
                        if self._last_left_release_time is not None:
                            time_since_release = current_time - self._last_left_release_time
                            if time_since_release < 0.3:
                                self.mouse_clicks['double'] += 1

                        self._last_left_click_time = current_time
                    else:
                        # Left button released
                        self._is_left_pressed = False
                        self._last_left_release_time = current_time

                        # Drag detection: if mouse moved while pressed
                        if self._moved_while_pressed:
                            self.drag_count += 1
                            self._moved_while_pressed = False

                elif button == mouse.Button.right and pressed:
                    self.mouse_clicks['right'] += 1

                if pressed:
                    self._track_idle_time('mouse', current_time)
        except Exception as e:
            logger.error(f"Error in mouse click handler: {e}")

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll."""
        if not self.is_monitoring:
            return

        try:
            with self.lock:
                self.scroll_count += 1
                self._track_idle_time('mouse', time.time())
        except Exception as e:
            logger.error(f"Error in mouse scroll handler: {e}")

    def _update_accumulated_idle(self, current_time):
        """Update accumulated idle time since last activity."""
        with self.lock:
            # Keyboard idle: accumulate time since last keyboard activity
            time_since_keyboard = current_time - self._keyboard_last_active
            if time_since_keyboard > self._idle_threshold:
                self._keyboard_idle_accumulated += time_since_keyboard - self._idle_threshold
                self._keyboard_last_active = current_time

            # Mouse idle: accumulate time since last mouse activity
            time_since_mouse = current_time - self._mouse_last_active
            if time_since_mouse > self._idle_threshold:
                self._mouse_idle_accumulated += time_since_mouse - self._idle_threshold
                self._mouse_last_active = current_time

    def get_raw_data(self):
        """Get raw monitoring data for the current window with error handling."""
        try:
            with self.lock:
                current_time = time.time()
                cutoff_time = current_time - self.window_size

                # Filter data within window using CircularBuffer
                key_presses_window = [t for t in self.key_presses.get_all() if t >= cutoff_time]
                key_releases_window = [t for t in self.key_releases.get_all() if t >= cutoff_time]
                mouse_moves_window = [m for m in self.mouse_movements.get_all() if m['time'] >= cutoff_time]

                # Idle time calculations (current idle since last event)
                keyboard_idle = current_time - (self.last_key_time or self.session_start)
                mouse_idle = current_time - self.mouse_idle_start

                return {
                    'key_presses': key_presses_window,
                    'key_releases': key_releases_window,
                    'backspace_count': self.backspace_count,
                    'mouse_clicks': dict(self.mouse_clicks),
                    'scroll_count': self.scroll_count,
                    'mouse_movements': mouse_moves_window,
                    'keyboard_idle': keyboard_idle,
                    'mouse_idle': mouse_idle,
                    'session_duration': current_time - self.session_start,
                    'timestamp': current_time,
                    'drag_count': self.drag_count,
                }
        except Exception as e:
            logger.error(f"Error getting raw data: {e}")
            # Return safe default data on error
            return {
                'key_presses': [],
                'key_releases': [],
                'backspace_count': 0,
                'mouse_clicks': {},
                'scroll_count': 0,
                'mouse_movements': [],
                'keyboard_idle': 0,
                'mouse_idle': 0,
                'session_duration': 0,
                'timestamp': time.time(),
                'drag_count': 0,
            }

    def reset_window(self):
        """Reset counters for the next window."""
        try:
            with self.lock:
                self.key_presses.clear()
                self.key_releases.clear()
                self.backspace_count = 0
                self.mouse_clicks = {'left': 0, 'right': 0, 'double': 0}
                self.scroll_count = 0
                self.mouse_movements.clear()
                self.drag_count = 0
                logger.debug("Window reset completed")
        except Exception as e:
            logger.error(f"Error resetting window: {e}")

    def get_stats(self):
        """Get current monitoring statistics."""
        try:
            with self.lock:
                return {
                    'is_monitoring': self.is_monitoring,
                    'session_duration': time.time() - self.session_start,
                    'key_events': len(self.key_presses) + len(self.key_releases),
                    'mouse_events': len(self.mouse_movements),
                    'buffer_usage': {
                        'key_presses': len(self.key_presses),
                        'key_releases': len(self.key_releases),
                        'mouse_movements': len(self.mouse_movements)
                    }
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
