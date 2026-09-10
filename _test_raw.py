import ctypes
import ctypes.wintypes as wt

class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ('usUsagePage', wt.USHORT),
        ('usUsage',     wt.USHORT),
        ('dwFlags',     wt.DWORD),
        ('hwndTarget',  wt.HWND),
    ]

RIDEV_INPUTSINK = 0x00000100
rid = RAWINPUTDEVICE(usUsagePage=1, usUsage=6, dwFlags=RIDEV_INPUTSINK, hwndTarget=None)
res = ctypes.windll.user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE))
print('RegisterRawInputDevices:', res, 'err:', ctypes.GetLastError())
