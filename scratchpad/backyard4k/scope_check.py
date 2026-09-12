"""Check the protected front builder/shared helpers against the captured baseline."""
from pathlib import Path
import re, hashlib, json
HERE = Path(__file__).resolve().parent
current = (HERE.parents[1]/'frontend/js/environment.js').read_text(encoding='utf-8')
before = (HERE/'environment-baseline.js').read_text(encoding='utf-8')
def section(s, begin, end):
    return s[s.index(begin):s.index(end, s.index(begin))]
checks = {}
for name, begin, end in [
    ('front_builder', 'function addFrontYard(', 'function addBackYard('),
    ('shared_landmarks', 'function landmarks(', '// Grass over the shell'),
    ('global_grass_weather', 'const GRASS_BASE', '// ------------------------------------------------------- front yard detail'),
]:
    a, b = section(before, begin, end), section(current, begin, end)
    # Rear helper blocks may be inserted between front and back functions.
    if name == 'front_builder':
        a = a[:a.rfind('\n}')+2]
        b = b[:len(a)]
    checks[name] = {'unchanged': a == b, 'baseline_sha256':hashlib.sha256(a.encode()).hexdigest()}
print(json.dumps(checks, indent=2))
if not all(x['unchanged'] for x in checks.values()):
    raise SystemExit(1)
