"""
web_app.py
----------
Premium AI Dashboard - serves the glassmorphism UI, real-time monitoring,
and prediction API. Uses Python's built-in HTTP server (no external deps).
"""

import os
import sys
import json
import time
import urllib.parse
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from copy import deepcopy

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.predict import predict_fatigue
from src.monitor import ActivityMonitor
from src.feature_extraction import FeatureExtractor, FEATURE_ORDER

# --- MIME Types ---
MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
    '.json': 'application/json',
}

# --- File paths ---
PROJECT_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
STATIC_DIR = PROJECT_ROOT / 'static'

# --- Global monitor state (thread-safe) ---
_monitor = None
_monitor_lock = threading.Lock()
_session_history = []
_session_history_lock = threading.Lock()
_session_start_time = None
_session_features = {}
_last_history_throttle = {'time': 0.0}  # throttle history additions


def get_monitor():
    """Get or create the global ActivityMonitor instance (thread-safe)."""
    global _monitor
    with _monitor_lock:
        if _monitor is None:
            _monitor = ActivityMonitor(window_size=60)
        return _monitor


def reset_session():
    """Reset session data (thread-safe)."""
    global _session_history, _session_start_time, _session_features
    with _monitor_lock:
        _session_history = []
        _session_start_time = None
        _session_features = {}


def add_prediction_to_history(features, label, confidence):
    """Add a prediction to the session history (thread-safe)."""
    global _session_history
    with _session_history_lock:
        _session_history.append({
            'timestamp': time.time(),
            'features': {k: float(v) for k, v in features.items()},
            'prediction': label,
            'confidence': float(confidence)
        })
        # Keep only last 200 entries
        if len(_session_history) > 200:
            _session_history = _session_history[-200:]


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler serving the premium dashboard UI and prediction API."""

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = parsed.query

        try:
            if path == '/' or path == '/index.html':
                self._serve_html()
            elif path.startswith('/static/'):
                self._serve_static(path)
            elif path == '/predict':
                self._handle_predict(query)
            elif path == '/api/monitor/status':
                self._handle_monitor_status()
            elif path == '/api/monitor/session-data':
                self._handle_session_data()
            elif path == '/api/monitor/report':
                self._handle_report()
            elif path == '/api/monitor/history':
                self._handle_history()
            else:
                self._send_json(404, {'error': 'Not found'})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def do_POST(self):
        """Handle POST requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == '/api/monitor/start':
                self._handle_monitor_start()
            elif path == '/api/monitor/stop':
                self._handle_monitor_stop()
            elif path == '/api/monitor/predict-now':
                self._handle_predict_now()
            else:
                self._send_json(404, {'error': 'Not found'})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _serve_html(self):
        """Serve the main dashboard HTML."""
        html_path = TEMPLATES_DIR / 'index.html'
        if not html_path.exists():
            self._send_error(404, 'Template not found')
            return
        try:
            content = html_path.read_text(encoding='utf-8')
            self._send_response(200, 'text/html; charset=utf-8', content.encode('utf-8'))
        except Exception as e:
            self._send_json(500, {'error': f'Error reading template: {str(e)}'})

    def _serve_static(self, path):
        """Serve static files (CSS, JS, images)."""
        rel_path = path[len('/static/'):]
        file_path = STATIC_DIR / rel_path

        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(STATIC_DIR.resolve())):
                self._send_json(403, {'error': 'Forbidden'})
                return
        except Exception:
            self._send_json(403, {'error': 'Forbidden'})
            return

        if not file_path.exists() or not file_path.is_file():
            self._send_json(404, {'error': 'File not found'})
            return

        ext = file_path.suffix.lower()
        mime = MIME_TYPES.get(ext, 'application/octet-stream')

        try:
            content = file_path.read_bytes()
            self._send_response(200, mime, content)
        except Exception as e:
            self._send_json(500, {'error': f'Error reading file: {str(e)}'})

    def _handle_predict(self, query_string):
        """Handle manual prediction requests."""
        try:
            params = urllib.parse.parse_qs(query_string)

            features = {
                'key_press_count': float(params.get('key_press_count', [120])[0]),
                'key_hold_time': float(params.get('key_hold_time', [0.20])[0]),
                'typing_speed': float(params.get('typing_speed', [45])[0]),
                'error_rate': float(params.get('error_rate', [0.08])[0]),
                'backspace_count': float(params.get('backspace_count', [15])[0]),
                'idle_time': float(params.get('idle_time', [8])[0]),
                'mouse_click_count': float(params.get('mouse_click_count', [25])[0]),
                'left_click': float(params.get('left_click', [20])[0]),
                'right_click': float(params.get('right_click', [3])[0]),
                'double_click': float(params.get('double_click', [1])[0]),
                'scroll_count': float(params.get('scroll_count', [50])[0]),
                'cursor_speed': float(params.get('cursor_speed', [100])[0]),
                'cursor_distance': float(params.get('cursor_distance', [50000])[0]),
                'drag_count': float(params.get('drag_count', [10])[0]),
                'movement_speed': float(params.get('movement_speed', [100])[0]),
                'idle_mouse_time': float(params.get('idle_mouse_time', [500])[0]),
            }

            label, confidence = predict_fatigue(features)

            if label.lower().find('low') != -1 or label.lower().find('normal') != -1:
                recommendation = 'Everything looks normal. Keep maintaining healthy work habits.'
            elif label.lower().find('moderate') != -1:
                recommendation = 'Signs of fatigue detected. Consider taking a short break and stretching.'
            else:
                recommendation = 'High fatigue levels detected. We strongly recommend resting.'

            response_data = {
                'prediction': label,
                'confidence': confidence,
                'recommendation': recommendation,
                'features': {
                    'typing_speed': features['typing_speed'],
                    'mouse_click_count': features['mouse_click_count'],
                }
            }

            self._send_json(200, response_data)

        except FileNotFoundError as e:
            self._send_json(503, {
                'error': 'Model not found. Please train the model first with: python src/train_model.py',
                'prediction': 'Model Unavailable',
                'confidence': 0,
                'recommendation': 'Model is not trained yet.'
            })
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    # ========== Monitoring API ==========

    def _handle_monitor_start(self):
        """Start real-time monitoring."""
        global _session_start_time
        try:
            monitor = get_monitor()
            if monitor.is_monitoring:
                self._send_json(200, {'status': 'already_running', 'message': 'Monitoring is already active.'})
                return

            reset_session()
            _session_start_time = time.time()
            monitor.start()

            self._send_json(200, {
                'status': 'started',
                'message': 'Monitoring started successfully.',
                'session_start': _session_start_time
            })
        except Exception as e:
            self._send_json(500, {'status': 'error', 'error': str(e)})

    def _handle_monitor_stop(self):
        """Stop monitoring, extract features, predict, and return session report."""
        global _session_features
        try:
            monitor = get_monitor()
            if not monitor.is_monitoring:
                self._send_json(400, {'status': 'not_running', 'message': 'Monitoring is not active.'})
                return

            monitor.stop()

            # Get final raw data
            raw_data = monitor.get_raw_data()
            features, _ = FeatureExtractor.extract_features(raw_data, window_size=60)
            _session_features = features

            # Get final prediction
            try:
                label, confidence = predict_fatigue(features)
            except FileNotFoundError:
                label, confidence = 'Model Unavailable', 0.0

            # Add final prediction to history
            add_prediction_to_history(features, label, confidence)

            # Build recommendation
            if label.lower().find('low') != -1 or label.lower().find('normal') != -1:
                recommendation = 'Everything looks normal. Keep maintaining healthy work habits.'
            elif label.lower().find('moderate') != -1:
                recommendation = 'Signs of fatigue detected. Consider taking a short break and stretching.'
            else:
                recommendation = 'High fatigue levels detected. We strongly recommend resting.'

            # Build activity summary
            activity_summary = {
                'key_press_count': int(features.get('key_press_count', 0)),
                'typing_speed': round(features.get('typing_speed', 0), 1),
                'mouse_click_count': int(features.get('mouse_click_count', 0)),
                'cursor_distance': int(features.get('cursor_distance', 0)),
                'backspace_count': int(features.get('backspace_count', 0)),
                'idle_time': round(features.get('idle_time', 0), 1),
                'error_rate': round(features.get('error_rate', 0) * 100, 1),
                'session_duration': round(time.time() - _session_start_time, 1) if _session_start_time else 0,
            }

            response_data = {
                'status': 'stopped',
                'message': 'Monitoring stopped successfully.',
                'prediction': label,
                'confidence': confidence,
                'recommendation': recommendation,
                'features': features,
                'activity_summary': activity_summary,
                'session_duration': activity_summary['session_duration'],
                'history_count': len(_session_history),
            }

            self._send_json(200, response_data)

        except Exception as e:
            self._send_json(500, {'status': 'error', 'error': str(e)})

    def _handle_monitor_status(self):
        """Get current monitoring status and live feature values."""
        try:
            monitor = get_monitor()
            raw_data = monitor.get_raw_data() if monitor.is_monitoring else {}
            features, _ = FeatureExtractor.extract_features(raw_data, window_size=60) if raw_data else ({}, [])

            # Get live prediction if monitoring AND enough baseline data exists
            prediction = None
            confidence = 0.0
            recommendation = ''
            is_baseline = True  # True until enough behavioral data is collected

            # Minimum threshold to avoid predicting on empty/near-empty windows
            MIN_KEY_EVENTS = 5
            MIN_MOUSE_EVENTS = 5

            if monitor.is_monitoring and features:
                key_events = len(raw_data.get('key_presses', [])) if raw_data else 0
                mouse_events = len(raw_data.get('mouse_movements', [])) if raw_data else 0

                if key_events >= MIN_KEY_EVENTS and mouse_events >= MIN_MOUSE_EVENTS:
                    is_baseline = False
                    try:
                        label, conf = predict_fatigue(features)
                        prediction = label
                        confidence = conf
                        # Throttle: only add to history every 30 seconds
                        _now = time.time()
                        if _now - _last_history_throttle['time'] >= 30:
                            add_prediction_to_history(features, label, conf)
                            _last_history_throttle['time'] = _now
                    except FileNotFoundError:
                        pass

            # Events count
            key_events = len(raw_data.get('key_presses', [])) if raw_data else 0
            mouse_events = len(raw_data.get('mouse_movements', [])) if raw_data else 0

            status_data = {
                'is_monitoring': monitor.is_monitoring,
                'session_duration': round(time.time() - _session_start_time, 1) if _session_start_time and monitor.is_monitoring else 0,
                'session_start': _session_start_time,
                'features': {k: float(v) for k, v in features.items()} if features else {},
                'key_events': key_events,
                'mouse_events': mouse_events,
                'current_prediction': prediction,
                'current_confidence': confidence,
                'is_baseline': is_baseline,
                'baseline_message': 'Collecting behavioral baseline...' if is_baseline else '',
                'history_count': len(_session_history),
            }

            self._send_json(200, status_data)

        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _handle_predict_now(self):
        """Force a prediction with current monitoring data."""
        try:
            monitor = get_monitor()
            if not monitor.is_monitoring:
                self._send_json(400, {'status': 'not_running', 'message': 'Monitoring is not active.'})
                return

            raw_data = monitor.get_raw_data()
            features, _ = FeatureExtractor.extract_features(raw_data, window_size=60)

            try:
                label, confidence = predict_fatigue(features)
            except FileNotFoundError:
                label, confidence = 'Model Unavailable', 0.0

            # Add to history
            add_prediction_to_history(features, label, confidence)

            if label.lower().find('low') != -1 or label.lower().find('normal') != -1:
                recommendation = 'Everything looks normal. Keep maintaining healthy work habits.'
            elif label.lower().find('moderate') != -1:
                recommendation = 'Signs of fatigue detected. Consider taking a short break.'
            else:
                recommendation = 'High fatigue levels detected. We strongly recommend resting.'

            self._send_json(200, {
                'prediction': label,
                'confidence': confidence,
                'recommendation': recommendation,
                'features': {k: float(v) for k, v in features.items()},
                'timestamp': time.time()
            })

        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _handle_session_data(self):
        """Get full session history data for chart rendering."""
        try:
            with _session_history_lock:
                history = deepcopy(_session_history)

            # Format for chart consumption
            timeline = []
            for entry in history:
                timeline.append({
                    't': entry['timestamp'],
                    'p': entry['prediction'],
                    'c': entry['confidence'],
                    'ts': entry['features'].get('typing_speed', 0),
                    'mc': entry['features'].get('mouse_click_count', 0),
                    'kp': entry['features'].get('key_press_count', 0),
                })

            self._send_json(200, {
                'timeline': timeline,
                'count': len(timeline),
                'features': _session_features
            })

        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _handle_history(self):
        """Get prediction history as JSON."""
        try:
            with _session_history_lock:
                history = deepcopy(_session_history)
            self._send_json(200, {'history': history, 'count': len(history)})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _handle_report(self):
        """Generate and return a comprehensive session report."""
        try:
            with _session_history_lock:
                history = deepcopy(_session_history)

            if not history:
                self._send_json(200, {'message': 'No session data available.', 'has_data': False})
                return

            # Get latest prediction
            latest = history[-1]
            features = latest.get('features', {})

            # Generate fatigue trend data
            fatigue_levels = {'Normal': 0, 'Moderate Fatigue': 1, 'High Fatigue': 2}
            trend_data = []
            for entry in history:
                pred = entry['prediction']
                num_val = fatigue_levels.get(pred, 0)
                trend_data.append({
                    'timestamp': entry['timestamp'],
                    'level': num_val,
                    'label': pred,
                    'confidence': entry['confidence'],
                    'typing_speed': entry['features'].get('typing_speed', 0),
                })

            # Count predictions
            pred_counts = {}
            for entry in history:
                p = entry['prediction']
                pred_counts[p] = pred_counts.get(p, 0) + 1
            dominant_prediction = max(pred_counts, key=pred_counts.get) if pred_counts else 'Unknown'

            # Activity summary
            activity_summary = {
                'total_key_presses': int(features.get('key_press_count', 0)),
                'typing_speed': round(features.get('typing_speed', 0), 1),
                'total_mouse_clicks': int(features.get('mouse_click_count', 0)),
                'cursor_distance': int(features.get('cursor_distance', 0)),
                'error_rate': round(features.get('error_rate', 0) * 100, 1),
                'backspace_count': int(features.get('backspace_count', 0)),
                'avg_key_hold_time': round(features.get('key_hold_time', 0), 3),
                'idle_time': round(features.get('idle_time', 0), 1),
            }

            session_duration = round(time.time() - _session_start_time, 1) if _session_start_time else 0
            if _session_start_time and history:
                session_duration = round(history[-1]['timestamp'] - history[0]['timestamp'], 1)

            report_data = {
                'has_data': True,
                'session_duration': session_duration,
                'total_predictions': len(history),
                'dominant_prediction': dominant_prediction,
                'final_prediction': latest['prediction'],
                'final_confidence': latest['confidence'],
                'prediction_distribution': pred_counts,
                'trend': trend_data,
                'activity_summary': activity_summary,
                'recommendation': 'Based on your session, ' + (
                    'your fatigue levels appear normal. Keep up healthy work habits.'
                    if dominant_prediction.lower().find('low') != -1 or dominant_prediction.lower().find('normal') != -1
                    else 'you showed signs of moderate fatigue. Take regular breaks.'
                    if dominant_prediction.lower().find('moderate') != -1
                    else 'high fatigue was detected. Please rest and consider consulting a professional.'
                ),
                'features': features,
            }

            self._send_json(200, report_data)

        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _send_response(self, status, content_type, content):
        """Send a raw HTTP response."""
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status, data):
        """Send a JSON response."""
        content = json.dumps(data).encode('utf-8')
        self._send_response(status, 'application/json', content)

    def _send_error(self, status, message):
        """Send a plain text error."""
        content = message.encode('utf-8')
        self._send_response(status, 'text/plain', content)

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port=8501):
    """Run the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)

    print()
    print('  \u001b[36m\u2500' * 50 + '\u001b[0m')
    print('  \u001b[1;36m\u2728  AI-Based Mental Health Fatigue Detection\u001b[0m')
    print('  \u001b[36m\u2500' * 50 + '\u001b[0m')
    print(f'  \u001b[32m\u2705  Server running at: http://localhost:{port}\u001b[0m')
    print('  \u001b[90m  Features: Real-time Monitoring | Live Dashboard | Session Reports\u001b[0m')
    print('  \u001b[90m  Press Ctrl+C to stop the server\u001b[0m')
    print('  \u001b[36m\u2500' * 50 + '\u001b[0m')
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n  \u001b[33m\u2705 Server stopped gracefully\u001b[0m')
        httpd.server_close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    run_server(port)
