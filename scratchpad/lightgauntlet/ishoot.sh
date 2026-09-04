#!/bin/sh
cd "C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet"
J="C:/Users/Manuel/Desktop/Pro/3d HA/scratchpad/lightgauntlet/shot.json"
ROOM=$1; LEVEL=$2; TAG=$3; shift 3
OUT="shots/r${ROOM}_${TAG}"
PYTHONPATH="C:/Users/Manuel/Desktop/Pro/3d HA/tools" ../../backend/.venv/Scripts/python.exe isoshot.py --room "$ROOM" --level "$LEVEL" --out "$OUT" "$@" > "$J" 2>&1
../../backend/.venv/Scripts/python.exe - "$J" <<'PY'
import json, sys
raw = open(sys.argv[1]).read(); i = raw.find('{')
try: d = json.loads(raw[i:])
except Exception as e: print('PARSE FAIL', e); print(raw[:3000]); raise SystemExit
print('delta', d['delta'], '| on', d['on']['meter'], '| off', d['off']['meter'])
for f in d['on']['fixtures']:
    print('  fx', f['objectId'], 'glow', f['glow'], 'emits', f['emits'], 'shown', f['shown'], 'pooled', f['pooled'])
print('  slots(on)', [(s['owner'], s['intensity']) for s in d['on']['slots']])
print('  slots(off)', [(s['owner'], s['intensity']) for s in d['off']['slots']])
print('  at', d['on']['at'], 'errors', d.get('page_errors'))
PY
