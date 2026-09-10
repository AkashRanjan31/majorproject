"""
input_worker.py
---------------
Standalone input capture worker.  Launch as a separate process:

    python input_worker.py <shared_json_path>

How it works
------------
1. Creates a hidden Win32 message-only window (HWND_MESSAGE parent).
   This gives us a valid HWND required for RegisterRawInputDevices.

2. Registers for Raw Input keyboard events (WM_INPUT) using that HWND.
   Raw Input works without admin and without UIAccess on all Windows versions.

3. Installs WH_MOUSE_LL hook for mouse events (works without admin).

4. Runs GetMessage loop on the main thread — required for both Raw Input
   and low-level mouse hooks to receive events.

5. A background thread writes a JSON snapshot every 250 ms.
"""

import ctypes
import ctypes.wintypes as wt
import json
import math
import sys
import threading
import time
from collections import deque
from pathlib import Path

# ── Args ──────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print("Usage: python input_worker.py <shared_file_path>", flush=True)
    sys.exit(1)

SHARED_FILE = Path(sys.argv[1])
SHARED_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Win32 constants ───────────────────────────────────────────────────────────
WH_MOUSE_LL    = 14
HC_ACTION      = 0
PM_REMOVE      = 0x0001
HWND_MESSAGE   = ctypes.cast(ctypes.c_void_p(-3), wt.HWND)

WM_DESTROY     = 0x0002
WM_INPUT       = 0x00FF
WM_MOUSEMOVE   = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_MOUSEWHEEL  = 0x020A

VK_BACK        = 0x08

# Raw Input
RIDEV_INPUTSINK    = 0x00000100
RIM_TYPEKEYBOARD   = 1
RIM_TYPEMOUSE      = 0
RIDI_DEVICEINFO    = 0x2000000B
RID_INPUT          = 0x10000003

RI_KEY_MAKE        = 0x00   # key down
RI_KEY_BREAK       = 0x01   # key up

# ── Structs ───────────────────────────────────────────────────────────────────
class POINT(ctypes.Structure):
    _fields_ = [("x", wt.LONG), ("y", wt.LONG)]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt",          POINT),
        ("mouseData",   wt.DWORD),
        ("flags",       wt.DWORD),
        ("time",        wt.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wt.ULONG)),
    ]

class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wt.USHORT),
        ("usUsage",     wt.USHORT),
        ("dwFlags",     wt.DWORD),
        ("hwndTarget",  wt.HWND),
    ]

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType",  wt.DWORD),
        ("dwSize",  wt.DWORD),
        ("hDevice", wt.HANDLE),
        ("wParam",  wt.WPARAM),
    ]

class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode",         wt.USHORT),
        ("Flags",            wt.USHORT),
        ("Reserved",         wt.USHORT),
        ("VKey",             wt.USHORT),
        ("Message",          wt.UINT),
        ("ExtraInformation", wt.ULONG),
    ]

class RAWINPUT_UNION(ctypes.Union):
    _fields_ = [("keyboard", RAWKEYBOARD)]

class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data",   RAWINPUT_UNION),
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wt.WPARAM, wt.LPARAM)
WNDPROC  = ctypes.WINFUNCTYPE(ctypes.c_long, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

# ── Shared state ──────────────────────────────────────────────────────────────
_lock = threading.Lock()

_key_presses:  deque = deque(maxlen=5000)
_key_releases: deque = deque(maxlen=5000)
_backspace_times: deque = deque(maxlen=1000)  # timestamps of backspace presses
_last_key_time:   float | None = None
_kb_last_active:  float = time.time()

_mouse_movements: deque = deque(maxlen=10000)
_click_times: deque = deque(maxlen=2000)   # (time, button) tuples
_scroll_times: deque = deque(maxlen=2000)  # timestamps
_drag_count:     int = 0
_last_mouse_pos: tuple | None = None
_is_left_pressed:     bool = False
_moved_while_pressed: bool = False
_last_left_release_t: float | None = None
_ms_last_active: float = time.time()

_session_start: float = time.time()
_running: bool = True

# ── Raw keyboard event handler ────────────────────────────────────────────────
def _handle_raw_keyboard(vkey: int, flags: int) -> None:
    global _last_key_time, _kb_last_active
    t = time.time()
    is_up = bool(flags & RI_KEY_BREAK)
    with _lock:
        if not is_up:
            _key_presses.append(t)
            _last_key_time = t
            _kb_last_active = t
            if vkey == VK_BACK:
                _backspace_times.append(t)
        else:
            _key_releases.append(t)

# ── Window procedure ──────────────────────────────────────────────────────────
def _wnd_proc(hwnd: int, msg: int, wparam: int, lparam: int) -> int:
    if msg == WM_INPUT:
        # Get size of RAWINPUT struct
        size = wt.UINT(0)
        ctypes.windll.user32.GetRawInputData(
            ctypes.cast(lparam, wt.HANDLE),
            RID_INPUT, None, ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )
        if size.value > 0:
            buf = (ctypes.c_byte * size.value)()
            ctypes.windll.user32.GetRawInputData(
                ctypes.cast(lparam, wt.HANDLE),
                RID_INPUT, buf, ctypes.byref(size),
                ctypes.sizeof(RAWINPUTHEADER),
            )
            ri = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
            if ri.header.dwType == RIM_TYPEKEYBOARD:
                _handle_raw_keyboard(
                    ri.data.keyboard.VKey,
                    ri.data.keyboard.Flags,
                )
        return 0

    if msg == WM_DESTROY:
        ctypes.windll.user32.PostQuitMessage(0)
        return 0

    return ctypes.windll.user32.DefWindowProcW(
        hwnd, msg, wparam, ctypes.c_ssize_t(lparam)
    )

# ── Mouse hook callback ───────────────────────────────────────────────────────
def _ms_proc(nCode: int, wParam: int, lParam: int) -> int:
    global _drag_count, _last_mouse_pos, _is_left_pressed
    global _moved_while_pressed, _last_left_release_t, _ms_last_active

    if nCode == HC_ACTION:
        t = time.time()
        ms = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
        x, y = ms.pt.x, ms.pt.y

        with _lock:
            if wParam == WM_MOUSEMOVE:
                if _last_mouse_pos is not None:
                    lx, ly, lt = _last_mouse_pos
                    dist = math.sqrt((x - lx) ** 2 + (y - ly) ** 2)
                    dt = t - lt
                    if dist > 0 and dt > 0:
                        _mouse_movements.append({
                            "time": t, "x": x, "y": y,
                            "distance": dist, "time_diff": dt,
                        })
                        _ms_last_active = t
                        if _is_left_pressed:
                            _moved_while_pressed = True
                _last_mouse_pos = (x, y, t)

            elif wParam == WM_LBUTTONDOWN:
                _click_times.append((t, "left"))
                _is_left_pressed = True
                _moved_while_pressed = False
                if _last_left_release_t and t - _last_left_release_t < 0.3:
                    _click_times.append((t, "double"))
                _ms_last_active = t

            elif wParam == WM_LBUTTONUP:
                _is_left_pressed = False
                _last_left_release_t = t
                if _moved_while_pressed:
                    _drag_count += 1
                    _moved_while_pressed = False

            elif wParam == WM_RBUTTONDOWN:
                _click_times.append((t, "right"))
                _ms_last_active = t

            elif wParam == WM_MOUSEWHEEL:
                _scroll_times.append(t)
                _ms_last_active = t

    return ctypes.windll.user32.CallNextHookEx(
        None, nCode, wParam, ctypes.c_ssize_t(lParam)
    )

# ── Snapshot writer ───────────────────────────────────────────────────────────
def _writer_loop() -> None:
    _write_count = 0
    while _running:
        try:
            t      = time.time()
            cutoff = t - 60.0   # rolling 60-second window
            with _lock:
                # Trim all deques to window
                while _key_presses    and _key_presses[0]  < cutoff:
                    _key_presses.popleft()
                while _key_releases   and _key_releases[0] < cutoff:
                    _key_releases.popleft()
                while _backspace_times and _backspace_times[0] < cutoff:
                    _backspace_times.popleft()
                while _mouse_movements and _mouse_movements[0].get("time", 0) < cutoff:
                    _mouse_movements.popleft()
                while _click_times    and _click_times[0][0] < cutoff:
                    _click_times.popleft()
                while _scroll_times   and _scroll_times[0]  < cutoff:
                    _scroll_times.popleft()

                kp  = list(_key_presses)
                kr  = list(_key_releases)
                mv  = list(_mouse_movements)
                bs  = len(_backspace_times)
                lc  = sum(1 for ts, btn in _click_times if btn == "left")
                rc  = sum(1 for ts, btn in _click_times if btn == "right")
                dc  = sum(1 for ts, btn in _click_times if btn == "double")
                sc  = len(_scroll_times)
                drg = _drag_count
                lkt = _last_key_time
                msa = _ms_last_active

            snap = {
                "key_presses":     kp,
                "key_releases":    kr,
                "backspace_count": bs,
                "mouse_clicks":    {"left": lc, "right": rc, "double": dc},
                "scroll_count":    sc,
                "mouse_movements": mv,
                "keyboard_idle":   max(0.0, t - (lkt or _session_start)),
                "mouse_idle":      max(0.0, t - msa),
                "session_duration": t - _session_start,
                "drag_count":      drg,
                "timestamp":       t,
                "_total_key_presses": len(kp),
                "_total_mouse_moves": len(mv),
            }

            _write_count += 1
            if _write_count % 20 == 0:  # every 5 s
                print(f"[worker] snap kp={len(kp)} mv={len(mv)} sc={sc} lc={lc} bs={bs}",
                      flush=True)

            tmp = SHARED_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(snap), encoding="utf-8")
            tmp.replace(SHARED_FILE)

        except Exception as e:
            print(f"[worker] writer error: {e}", flush=True)

        time.sleep(0.25)

# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    global _running

    user32   = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    # ── 1. Register window class ──────────────────────────────────────────────
    wnd_proc_cb = WNDPROC(_wnd_proc)   # keep strong reference

    class WNDCLASSEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize",        wt.UINT),
            ("style",         wt.UINT),
            ("lpfnWndProc",   WNDPROC),
            ("cbClsExtra",    ctypes.c_int),
            ("cbWndExtra",    ctypes.c_int),
            ("hInstance",     wt.HINSTANCE),
            ("hIcon",         wt.HICON),
            ("hCursor",       wt.HANDLE),
            ("hbrBackground", wt.HBRUSH),
            ("lpszMenuName",  wt.LPCWSTR),
            ("lpszClassName", wt.LPCWSTR),
            ("hIconSm",       wt.HICON),
        ]

    hinstance = kernel32.GetModuleHandleW(None)
    class_name = "NeurosenseWorker"

    wc = WNDCLASSEXW()
    wc.cbSize       = ctypes.sizeof(WNDCLASSEXW)
    wc.lpfnWndProc  = wnd_proc_cb
    wc.hInstance    = hinstance
    wc.lpszClassName = class_name

    atom = user32.RegisterClassExW(ctypes.byref(wc))
    if not atom:
        err = ctypes.GetLastError()
        if err != 1410:   # 1410 = class already registered
            print(f"[worker] RegisterClassEx failed err={err}", flush=True)

    # ── 2. Create hidden message-only window ──────────────────────────────────
    hwnd = user32.CreateWindowExW(
        0, class_name, "NeurosenseWorker",
        0, 0, 0, 0, 0,
        HWND_MESSAGE,   # message-only window — no visible UI
        None, hinstance, None,
    )
    if not hwnd:
        print(f"[worker] CreateWindowEx failed err={ctypes.GetLastError()}", flush=True)
        sys.exit(1)

    print(f"[worker] Hidden window created hwnd={hwnd}", flush=True)

    # ── 3. Register Raw Input for keyboard ───────────────────────────────────
    rid = RAWINPUTDEVICE(
        usUsagePage=1,
        usUsage=6,                  # keyboard
        dwFlags=RIDEV_INPUTSINK,    # receive input even when not foreground
        hwndTarget=hwnd,
    )
    ok = user32.RegisterRawInputDevices(
        ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE)
    )
    if not ok:
        print(f"[worker] RegisterRawInputDevices failed err={ctypes.GetLastError()}", flush=True)
    else:
        print("[worker] Raw keyboard input registered", flush=True)

    # ── 4. Install WH_MOUSE_LL hook ───────────────────────────────────────────
    ms_cb = HOOKPROC(_ms_proc)   # strong reference
    # Pass NULL for hModule — required for global low-level hooks
    ms_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, ms_cb, None, 0)
    if not ms_hook:
        print(f"[worker] Mouse hook failed err={ctypes.GetLastError()}", flush=True)
    else:
        print(f"[worker] Mouse hook installed handle={ms_hook}", flush=True)

    # ── 5. Signal ready ───────────────────────────────────────────────────────
    SHARED_FILE.with_suffix(".ready").write_text("1", encoding="utf-8")

    # ── 6. Start snapshot writer thread ──────────────────────────────────────
    writer = threading.Thread(target=_writer_loop, daemon=True)
    writer.start()

    pid = kernel32.GetCurrentProcessId()
    print(f"[worker] Message pump running. PID={pid}", flush=True)

    # ── 7. Main thread message pump ───────────────────────────────────────────
    # Both WM_INPUT (raw keyboard) and WH_MOUSE_LL callbacks are delivered
    # to this thread because it owns the window and installed the hook.
    msg = wt.MSG()
    try:
        while _running:
            r = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if r == 0 or r == -1:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        if ms_hook:
            user32.UnhookWindowsHookEx(ms_hook)
        user32.DestroyWindow(hwnd)
        print("[worker] Exiting.", flush=True)


if __name__ == "__main__":
    main()
