"""
_test_full.py — full pipeline test
Press keys and move mouse during the 8-second wait.
"""
import sys, time, json
sys.path.insert(0, '.')

from src.monitor import ActivityMonitor
from src.feature_extraction import FeatureExtractor
from src.realtime_predict import FatiguePredictor

print("=== FULL PIPELINE TEST ===")

m = ActivityMonitor(window_size=30)
m.start()
print(f"Backend: {'subprocess' if m._use_subprocess else 'direct'}")
print(f"Worker alive: {m.is_alive()}")
print("Waiting 8 seconds — please type and move your mouse...")

for i in range(8):
    time.sleep(1)
    raw  = m.get_raw_data()
    kp   = len(raw["key_presses"])
    mv   = len(raw["mouse_movements"])
    sc   = raw["scroll_count"]
    lc   = raw["mouse_clicks"]["left"]
    sess = round(raw["session_duration"], 1)
    print(f"  t={i+1}s  keys={kp}  mouse_moves={mv}  scrolls={sc}  clicks={lc}  session={sess}s")

print("\n--- Feature Extraction ---")
raw = m.get_raw_data()
feats, vec = FeatureExtractor.extract_features(raw, window_size=30)
for k in ["key_press_count", "typing_speed", "backspace_count",
          "cursor_speed", "mouse_velocity", "cursor_distance",
          "scroll_count", "left_click", "idle_time"]:
    print(f"  {k}: {feats.get(k, 0):.3f}")

print("\n--- Prediction ---")
try:
    p = FatiguePredictor()
    result = p.predict(vec)
    print(f"  Level: {result['name']}")
    print(f"  Score: {result['fatigue_score']}%")
    print(f"  Confidence: {result['confidence']}%")
except Exception as e:
    print(f"  Prediction error: {e}")

print("\n--- Stats ---")
stats = m.get_stats()
for k, v in stats.items():
    print(f"  {k}: {v}")

m.stop()
print("\nDone.")
