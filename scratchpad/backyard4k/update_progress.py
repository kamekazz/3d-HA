import argparse, json
from pathlib import Path
from datetime import datetime, timezone
p=argparse.ArgumentParser()
p.add_argument('piece')
p.add_argument('status')
p.add_argument('gap', nargs='?', default='')
a=p.parse_args()
f=Path(__file__).with_name('progress.json')
d=json.loads(f.read_text(encoding='utf-8-sig'))
d.setdefault('pieces',{})[a.piece]={'status':a.status,'gap':a.gap}
d['notes']=[f"{name}: {v['status']}"+(f" — {v['gap']}" if v.get('gap') else '') for name,v in d['pieces'].items()]
d['notes']+=['No piece has passed until its independent blind verdict is recorded.',
             'Comparisons use native photo resolution; 4K renders are linked above.']
d['updated']=datetime.now(timezone.utc).isoformat()
f.write_text(json.dumps(d,indent=2),encoding='utf-8')
