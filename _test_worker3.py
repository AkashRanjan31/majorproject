import subprocess, sys, time, json
from pathlib import Path

shared = Path('C:/Users/shrey/AppData/Local/Temp/neurosense/input_snapshot.json')
ready  = shared.with_suffix('.ready')
shared.unlink(missing_ok=True)
ready.unlink(missing_ok=True)

# Launch with CREATE_NEW_CONSOLE so we can see the worker's print output
proc = subprocess.Popen(
    [sys.executable, 'input_worker.py', str(shared)],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)
print('Worker PID:', proc.pid)

for i in range(60):
    if ready.exists():
        print(f'Worker ready after {i*0.1:.1f}s')
        break
    time.sleep(0.1)
else:
    print('Worker NOT ready')

print('Waiting 8s — type and move mouse...')
time.sleep(8)

d = json.loads(shared.read_text())
print('key_presses (window):', len(d['key_presses']))
print('total_key_presses:', d.get('_total_key_presses', 0))
print('backspace_count:', d['backspace_count'])
print('mouse_movements:', len(d['mouse_movements']))
print('scroll_count:', d['scroll_count'])
print('left_clicks:', d['mouse_clicks']['left'])

proc.terminate()
print('Done')
