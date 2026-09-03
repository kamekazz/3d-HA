"""Render the gauntlet progress page from status.json (rerun every round)."""
import base64, io, json, os, sys, datetime, html
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'gauntlet.html')

def uri(path, w=640, q=78):
    im = Image.open(path).convert('RGB')
    im.thumbnail((w, w * 2))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=q)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

st = json.load(open(os.path.join(HERE, 'status.json'), encoding='utf-8'))
photo = uri(os.path.join(ROOT, 'demo', 'exterior_night.jpg'))
current = uri(os.path.join(ROOT, st['current_render']))
e = html.escape
rows = []
for p in st['pieces']:
    cls = {'building': 'b', 'critic': 'c', 'fail': 'f', 'pass': 'p', 'queued': 'q'}[p['state']]
    hist = ''.join(f'<li><span class="r">R{h["round"]}</span> <span class="v {"win" if h.get("win") else "lose"}">{e(h["verdict"])}</span> — {e(h["gap"])}</li>' for h in p.get('history', []))
    rows.append(f'''<section class="piece">
  <header><h3>{e(p['name'])}</h3><span class="pill {cls}">{e(p['state'])}</span><span class="round">round {p['round']}</span></header>
  <p class="now">{e(p['now'])}</p>
  {'<ol class="hist">'+hist+'</ol>' if hist else ''}
</section>''')
timeline = ''.join(f'<li><time>{e(t["t"])}</time>{e(t["what"])}</li>' for t in st['log'][::-1])
page = f'''<title>Driveway at Night</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
:root{{--bg:#0b0c0f;--panel:#14161b;--line:rgba(255,255,255,.09);--ink:#e9e6df;--mute:#8d919a;--led:#f3c67c;--blue:#4c78ff;--ok:#5cc489;--bad:#e06c5a;--warn:#e0b04a}}
body{{background:var(--bg);color:var(--ink);font:15px/1.5 "IBM Plex Sans",system-ui,sans-serif;margin:0}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 24px 60px}}
h1{{font-size:26px;font-weight:600;margin:0 0 4px;text-wrap:balance}}
.sub{{color:var(--mute);margin:0 0 22px}}
.sub b{{color:var(--led);font-weight:600}}
.cmp{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:26px}}
.cmp figure{{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.cmp img{{display:block;width:100%;height:auto}}
.cmp figcaption{{padding:8px 12px;font:12px/1.4 "IBM Plex Mono",monospace;color:var(--mute);letter-spacing:.04em;text-transform:uppercase}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
.piece{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.piece header{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.piece h3{{font-size:16px;margin:0;flex:1}}
.pill{{font:11px/1 "IBM Plex Mono",monospace;letter-spacing:.06em;text-transform:uppercase;padding:5px 8px;border-radius:999px;border:1px solid var(--line)}}
.pill.b{{color:var(--led);border-color:var(--led)}}.pill.c{{color:var(--blue);border-color:var(--blue)}}.pill.f{{color:var(--bad);border-color:var(--bad)}}.pill.p{{color:var(--ok);border-color:var(--ok)}}.pill.q{{color:var(--mute)}}
.round{{font:12px "IBM Plex Mono",monospace;color:var(--mute)}}
.now{{margin:0 0 8px;color:var(--ink)}}
.hist{{margin:0;padding:0 0 0 2px;list-style:none;border-top:1px solid var(--line)}}
.hist li{{padding:7px 0;border-bottom:1px solid var(--line);font-size:13px;color:var(--mute)}}
.r{{font:12px "IBM Plex Mono",monospace;color:var(--ink);margin-right:6px}}
.v{{font-weight:600}}.v.win{{color:var(--ok)}}.v.lose{{color:var(--bad)}}
h2{{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute);margin:30px 0 10px;font-weight:600}}
.log{{list-style:none;margin:0;padding:0;font-size:13px}}
.log li{{display:grid;grid-template-columns:150px 1fr;gap:12px;padding:6px 0;border-bottom:1px solid var(--line)}}
.log time{{font:12px "IBM Plex Mono",monospace;color:var(--mute);font-variant-numeric:tabular-nums}}
@media (max-width:640px){{.cmp{{grid-template-columns:1fr}}.log li{{grid-template-columns:1fr}}}}
</style>
<div class="wrap">
<h1>Driveway at Night</h1>
<p class="sub">Render vs. the real photograph, from the same spot on the driveway. Updated <b>{e(st['updated'])}</b> · {e(st['headline'])}</p>
<div class="cmp">
<figure><img src="{photo}" alt="The photograph"><figcaption>Photograph · the bar</figcaption></figure>
<figure><img src="{current}" alt="Current render"><figcaption>Render · {e(st['current_label'])}</figcaption></figure>
</div>
<div class="grid">{''.join(rows)}</div>
<h2>Log</h2><ul class="log">{timeline}</ul>
</div>'''
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, len(page)//1024, 'KB')
