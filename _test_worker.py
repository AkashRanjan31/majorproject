import subprocess, sys, time, json
from pathlib import Path

shared = Path('C:/Users/shrey/AppData/Local/Temp/neurosense/input_snapshot.json')
ready  = shared.with_suffix('.ready')
shared.unlink(missing_ok=True)
ready.unlink(missing_ok=True)

proc = subprocess.Popen(
    [sys.executable, 'input_worker.py', str(shared)],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)
print('Worker PID:', proc.pid)

for _ in range(50):
    if ready.exists():
        print('Worker ready after', _ * 0.1, 's')
        break
    time.sleep(0.1)
else:
    print('Worker NOT ready after 5s')

print('Waiting 6s for events...')
time.sleep(6)

if shared.exists():
    d = json.loads(shared.read_text())
    print('mouse_movements:', len(d['mouse_movements']))
    print('key_presses (window):', len(d['key_presses']))
    print('total_key_presses:', d.get('_total_key_presses', 0))
    print('scroll_count:', d['scroll_count'])
    print('left_clicks:', d['mouse_clicks']['left'])
    print('backspace_count:', d['backspace_count'])
else:
    print('NO SNAPSHOT FILE')

proc.terminate()
print('Done')
