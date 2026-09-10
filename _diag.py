"""
_diag.py — pynput diagnostic
"""
import threading
import time
import ctypes
import sys

sys.path.insert(0, ".")

print("=== PYNPUT DIAGNOSTIC ===")
print("Admin:", bool(ctypes.windll.shell32.IsUserAnAdmin()))
print("Python:", sys.version)

from pynput import keyboard, mouse

# ── Test 1: Direct (main thread) ──────────────────────────────────────────────
print("\n[TEST 1] Keyboard listener from MAIN thread")
kb_events_main = []
kb = keyboard.Listener(on_press=lambda k: kb_events_main.append(str(k)), daemon=True)
kb.start()
kb.wait()
print("  KB alive:", kb.is_alive(), "thread:", kb.ident)
time.sleep(2)
print("  KB events captured:", len(kb_events_main))
kb.stop()

# ── Test 2: Mouse listener from main thread ───────────────────────────────────
print("\n[TEST 2] Mouse listener from MAIN thread")
ms_events_main = []
ms = mouse.Listener(on_move=lambda x, y: ms_events_main.append((x, y)), daemon=True)
ms.start()
ms.wait()
print("  MS alive:", ms.is_alive(), "thread:", ms.ident)
time.sleep(2)
print("  MS events captured:", len(ms_events_main))
ms.stop()

# ── Test 3: Both from a background thread (Streamlit model) ──────────────────
print("\n[TEST 3] Both listeners from BACKGROUND thread (Streamlit model)")
results = {}

def run_from_bg_thread():
    kb_e = []
    ms_e = []
    kb2 = keyboard.Listener(on_press=lambda k: kb_e.append(str(k)), daemon=True)
    ms2 = mouse.Listener(on_move=lambda x, y: ms_e.append((x, y)), daemon=True)
    kb2.start()
    ms2.start()
    kb2.wait()
    ms2.wait()
    results["kb_alive"] = kb2.is_alive()
    results["ms_alive"] = ms2.is_alive()
    results["kb_thread"] = kb2.ident
    results["ms_thread"] = ms2.ident
    time.sleep(3)
    results["kb_events"] = len(kb_e)
    results["ms_events"] = len(ms_e)
    kb2.stop()
    ms2.stop()

t = threading.Thread(target=run_from_bg_thread, daemon=True)
t.start()
t.join(timeout=8)
print("  Results:", results)

# ── Test 4: ActivityMonitor ───────────────────────────────────────────────────
print("\n[TEST 4] ActivityMonitor full test")
from src.monitor import ActivityMonitor
m = ActivityMonitor(window_size=10)
m.start()
time.sleep(0.5)
print("  is_alive:", m.is_alive())
print("  stats:", m.get_stats())
time.sleep(3)
raw = m.get_raw_data()
print("  key_presses in window:", len(raw["key_presses"]))
print("  mouse_movements in window:", len(raw["mouse_movements"]))
print("  scroll_count:", raw["scroll_count"])
print("  left_clicks:", raw["mouse_clicks"]["left"])
m.stop()
print("  Stopped OK")
