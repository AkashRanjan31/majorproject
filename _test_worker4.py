import subprocess, sys, time, json
from pathlib import Path

shared = Path('C:/Users/shrey/AppData/Local/Temp/neurosense/input_snapshot.json')
ready  = shared.with_suffix('.ready')
shared.unlink(missing_ok=True)
ready.unlink(missing_ok=True)

# Capture stdout this time to see worker messages
proc = subprocess.Popen(
    [sys.executable, 'input_worker.py', str(shared)],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True,
)
print('Worker PID:', proc.pid)

for i in range(60):
    if ready.exists():
        print(f'Worker ready after {i*0.1:.1f}s')
        break
    time.sleep(0.1)
else:
    print('Worker NOT ready')

print('Waiting 6s...')
time.sleep(6)

d = json.loads(shared.read_text())
print('total_kp:', d.get('_total_key_presses', 0))
print('kp_list:', len(d['key_presses']))
print('bs:', d['backspace_count'])
print('mv:', len(d['mouse_movements']))
print('sc:', d['scroll_count'])
print('lc:', d['mouse_clicks']['left'])

proc.terminate()
out, _ = proc.communicate(timeout=3)
print('=== Worker stdout ===')
print(out)
