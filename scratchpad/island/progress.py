"""Build progress.html from rounds.json. Each round: piece, round, shot, verdict
('ours'|'bar'|'pending'), gap, notes, metrics{}. Images are embedded downscaled so
the page is one file.   python progress.py"""
import json, base64, io, html, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
data = json.load(open('rounds.json', encoding='utf-8'))
rounds = data['rounds']

def img64(path, w=760):
    im = Image.open(path).convert('RGB'); r = w / im.width
    im = im.resize((w, int(im.height * r)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=76)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

refs = [img64('ref/ref1_stone_island.jpg', 640), img64('ref/ref2_avondale.jpg', 640)]
e = html.escape

# scoreboard: latest verdict per piece
pieces = {}
for r in rounds:
    pieces[r['piece']] = r
board = ''.join(
    f'<li class="{ {"ours": "win", "bar": "lose"}.get(r.get("verdict"), "pend") }">'
    f'<span class="pn">{e(p)}</span><span class="pv">{e({"ours": "ours picked", "bar": "bar picked", "pending": "judging"}.get(r.get("verdict"), "judging"))}</span>'
    f'<span class="pr">round {r["round"]}</span></li>'
    for p, r in pieces.items())

cards = []
for r in reversed(rounds):
    v = r.get('verdict', 'pending')
    cls = {'ours': 'win', 'bar': 'lose'}.get(v, 'pend')
    shots = r['shot'] if isinstance(r['shot'], list) else [r['shot']]
    figs = ''.join(f'<figure><img src="{img64(s)}" alt="Our render, {e(r["piece"])} round {r["round"]}" loading="lazy"><figcaption>{e(os.path.basename(s))}</figcaption></figure>' for s in shots)
    met = r.get('metrics') or {}
    metrows = ''.join(f'<span><b>{e(str(k))}</b> {e(str(val))}</span>' for k, val in met.items())
    cards.append(f'''
<article class="round {cls}">
  <header><h3>{e(r["piece"])}</h3><span class="n">round {r["round"]}</span>
    <span class="pill">{e({"ours": "critic picked ours", "bar": "critic picked the bar", "pending": "awaiting critic"}.get(v, v))}</span></header>
  <div class="figs">{figs}</div>
  <dl>
    <dt>What changed</dt><dd>{e(r.get("notes", ""))}</dd>
    <dt>Biggest remaining gap</dt><dd>{e(r.get("gap", "—"))}</dd>
  </dl>
  {f'<div class="met">{metrows}</div>' if metrows else ''}
</article>''')

page = f'''<title>Island Gauntlet</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,700&family=Public+Sans:wght@400;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
/* layout: a pinned header (goal, bar, scoreboard) over a newest-first column of round cards; dark-first, the void navy of the references */
:root {{ --bg:#0a1424; --panel:#101d33; --fg:#e6ecf5; --mute:#8d9bb3; --line:rgba(180,200,240,.13); --soil:#8a6040; --win:#5fd08c; --lose:#ef7a6a; --pend:#d9b45a;
  --display:"Bricolage Grotesque", "Segoe UI", system-ui, sans-serif; --body:"Public Sans", system-ui, sans-serif; --mono:"JetBrains Mono", ui-monospace, monospace; color-scheme: dark; }}
@media (prefers-color-scheme: light) {{ :root:not([data-theme="dark"]) {{ --bg:#eef2f8; --panel:#ffffff; --fg:#14203a; --mute:#56637d; --line:rgba(20,40,90,.13); --soil:#7a5235; --win:#1f8a4c; --lose:#c0412f; --pend:#9a7417; color-scheme: light; }} }}
:root[data-theme="light"] {{ --bg:#eef2f8; --panel:#ffffff; --fg:#14203a; --mute:#56637d; --line:rgba(20,40,90,.13); --soil:#7a5235; --win:#1f8a4c; --lose:#c0412f; --pend:#9a7417; color-scheme: light; }}
body {{ background:var(--bg); color:var(--fg); font-family:var(--body); line-height:1.5; padding-left:max(16px, env(safe-area-inset-left,0px)); padding-right:max(16px, env(safe-area-inset-right,0px)); padding-block:28px 48px; }}
main {{ max-width:980px; margin:0 auto; display:grid; gap:28px; }}
h1 {{ font-family:var(--display); font-weight:700; font-size:clamp(2rem, 5vw, 3rem); letter-spacing:-.02em; margin:0; text-wrap:balance; }}
h2 {{ font-family:var(--display); font-weight:700; font-size:1.15rem; margin:0; }}
h3 {{ font-family:var(--display); font-weight:700; font-size:1.05rem; margin:0; }}
.lede {{ color:var(--mute); max-width:68ch; margin:6px 0 0; }}
.eyebrow {{ font-family:var(--mono); font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--soil); }}
.refs {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px; }}
.refs img, .figs img {{ width:100%; display:block; border-radius:10px; border:1px solid var(--line); }}
figure {{ margin:0; min-width:0; }}
figcaption {{ font-family:var(--mono); font-size:.72rem; color:var(--mute); margin-top:4px; }}
.board {{ list-style:none; padding:0; margin:0; display:grid; grid-template-columns:repeat(auto-fill, minmax(210px, 1fr)); gap:8px; }}
.board li {{ display:grid; grid-template-columns:1fr auto; gap:2px 8px; padding:10px 12px; border-radius:10px; background:var(--panel); border:1px solid var(--line); border-left:4px solid var(--pend); }}
.board li.win {{ border-left-color:var(--win); }} .board li.lose {{ border-left-color:var(--lose); }}
.pn {{ font-weight:600; }} .pv {{ font-family:var(--mono); font-size:.75rem; color:var(--mute); grid-column:1; }} .pr {{ font-family:var(--mono); font-size:.75rem; color:var(--mute); grid-row:1; grid-column:2; }}
.round {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px; display:grid; gap:12px; min-width:0; }}
.round header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:10px; }}
.n {{ font-family:var(--mono); font-size:.78rem; color:var(--mute); }}
.pill {{ margin-left:auto; font-family:var(--mono); font-size:.72rem; padding:3px 10px; border-radius:99px; border:1px solid currentColor; }}
.round.win .pill {{ color:var(--win); }} .round.lose .pill {{ color:var(--lose); }} .round.pend .pill {{ color:var(--pend); }}
.figs {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:10px; }}
dl {{ margin:0; display:grid; grid-template-columns:max-content 1fr; gap:6px 14px; }}
dt {{ color:var(--mute); font-size:.85rem; }} dd {{ margin:0; min-width:0; max-width:72ch; }}
@media (max-width:560px) {{ dl {{ grid-template-columns:1fr; }} dt {{ margin-top:6px; }} }}
.met {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-family:var(--mono); font-size:.75rem; color:var(--mute); font-variant-numeric:tabular-nums; }}
.met b {{ color:var(--fg); font-weight:400; }}
</style>
<main>
  <section>
    <div class="eyebrow">3D HA · outside of the house only</div>
    <h1>The house as a floating island</h1>
    <p class="lede">{e(data.get("goal", ""))}</p>
  </section>
  <section style="display:grid;gap:10px">
    <h2>The bar</h2>
    <div class="refs"><figure><img src="{refs[0]}" alt="Reference 1: stone house on an island in a navy void"><figcaption>reference 1</figcaption></figure>
      <figure><img src="{refs[1]}" alt="Reference 2: house on a tree-ringed lot plate"><figcaption>reference 2</figcaption></figure></div>
  </section>
  <section style="display:grid;gap:10px">
    <h2>Pieces</h2>
    <ul class="board">{board}</ul>
    <p class="lede">{e(data.get("status", ""))}</p>
  </section>
  <section style="display:grid;gap:14px">
    <h2>Rounds, newest first</h2>
    {"".join(cards)}
  </section>
</main>'''
open('progress.html', 'w', encoding='utf-8').write(page)
print('wrote progress.html', len(page) // 1024, 'KB')
