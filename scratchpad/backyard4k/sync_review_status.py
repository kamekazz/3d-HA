"""Refresh derived progress notes without overwriting newer worker statuses."""
import json
from pathlib import Path
from datetime import datetime, timezone
p = Path(__file__).with_name('progress.json')
d = json.loads(p.read_text(encoding='utf-8-sig'))
d['notes'] = [f"{name}: {v['status']} — {v.get('gap', '')}" for name, v in d.get('pieces', {}).items()]
d['notes'] += ['No piece has passed its independent blind review.', 'Comparisons use native photo resolution; full 4K renders are linked above.']
d['updated'] = datetime.now(timezone.utc).isoformat()
p.write_text(json.dumps(d, indent=2), encoding='utf-8')
