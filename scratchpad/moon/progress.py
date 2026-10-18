"""Build progress.html from rounds.json (list of rounds, each with piece, round,
shot, verdict, gap, notes, meter). Images are embedded downscaled so the page
is one file.  python progress.py"""
import json, base64, io, html
from PIL import Image
rounds = json.load(open('rounds.json'))
def img64(path, w=720):
    im = Image.open(path).convert('RGB'); r = w / im.width
    im = im.resize((w, int(im.height * r)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=78)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
ref = img64('ref/sims4_ea_moon_street_800.png')
cards = []
for r in rounds:
    pick = r.get('verdict', 'pending')
    cls = {'ours': 'win', 'bar': 'lose', 'skipped': 'pend'}.get(pick, 'pend')
    cards.append(f'''
<section class="round {cls}">
  <header><span class="piece">{html.escape(r["piece"])}</span><span class="n">round {r["round"]}</span>
    <span class="pill">{html.escape({"ours":"critic picked ours","bar":"critic picked the bar","skipped":"not judged"}.get(pick,"awaiting critic"))}</span></header>
  <div class="pair"><figure><img src="{img64(r["shot"])}" alt=""><figcaption>ours · {html.escape(r.get("pose",""))}</figcaption></figure></div>
  <dl>
    <dt>What changed</dt><dd>{html.escape(r.get("notes",""))}</dd>
    <dt>Biggest remaining gap</dt><dd>{html.escape(r.get("gap","—"))}</dd>
    <dt>Meter</dt><dd class="mono">{html.escape(json.dumps(r.get("meter",{})))}</dd>
  </dl>
</section>''')
page = f'''<title>Moon Gauntlet</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* layout: one column of round cards under a pinned reference strip; dark-first because the subject is a night sky */
:root {{ --bg:#0b0f1c; --fg:#e4e8f4; --mute:#8a93ad; --card:#121830; --line:rgba(190,205,255,.12); --win:#5ad48a; --lose:#f06c6c; --pend:#c9a24b;
  --display:"Fraunces", Georgia, serif; --body:"IBM Plex Sans", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, monospace; color-scheme: dark; }}
@media (prefers-color-scheme: light) {{ :root:not([data-theme="dark"]) {{ --bg:#f4f5fa; --fg:#151a2c; --mute:#5c6480; --card:#ffffff; --line:rgba(20,30,80,.12); color-scheme: light; }} }}
:root[data-theme="light"] {{ --bg:#f4f5fa; --fg:#151a2c; --mute:#5c6480; --card:#ffffff; --line:rgba(20,30,80,.12); color-scheme: light; }}
body {{ background:var(--bg); color:var(--fg); font-family:var(--body); padding-left:max(16px, env(safe-area-inset-left,0px)); padding-right:max(16px, env(safe-area-inset-right,0px)); padding-block:24px; }}
main {{ max-width:900px; margin:0 auto; display:grid; gap:24px; }}
h1 {{ font-family:var(--display); font-weight:400; font-size:2rem; text-wrap:balance; margin:0; }}
.sub {{ color:var(--mute); max-width:65ch; }}
.bar {{ display:grid; gap:8px; }}
.bar img {{ width:100%; max-width:100%; border-radius:6px; }}
.bar figcaption, figcaption {{ color:var(--mute); font-size:.85rem; }}
.round {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px; display:grid; gap:12px; }}
.round header {{ display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; }}
.piece {{ font-family:var(--display); font-size:1.25rem; }}
.n {{ color:var(--mute); }}
.pill {{ margin-left:auto; font-size:.8rem; letter-spacing:.04em; text-transform:uppercase; padding:3px 10px; border-radius:999px; border:1px solid currentColor; }}
.win .pill {{ color:var(--win); }} .lose .pill {{ color:var(--lose); }} .pend .pill {{ color:var(--pend); }}
.pair img {{ width:100%; max-width:100%; border-radius:6px; }}
dl {{ display:grid; grid-template-columns:max-content 1fr; gap:6px 16px; margin:0; min-width:0; }}
dt {{ color:var(--mute); font-size:.85rem; text-transform:uppercase; letter-spacing:.04em; }}
dd {{ margin:0; min-width:0; }}
.mono {{ font-family:var(--mono); font-size:.8rem; overflow-x:auto; }}
@media (max-width:520px) {{ dl {{ grid-template-columns:1fr; }} }}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono&display=swap">
<main>
<h1>Moon Gauntlet</h1>
<p class="sub">The house's night exterior, judged blind against The Sims 4's own full-moon screenshot until a fresh critic picks ours. Newest round first. Pieces: sky &amp; moon, moonlight on the house, the lot under moonlight, the night optics.</p>
<figure class="bar"><img src="{ref}" alt=""><figcaption>The bar: EA's lunar-cycle screenshot (Willow Creek street at night, moon up). Sky zenith (21,25,45), cloud band (40,47,78), moonlit white siding (57,72,102), moon disc L 160.</figcaption></figure>
{''.join(reversed(cards))}
</main>
'''
open('progress.html', 'w', encoding='utf-8').write(page)
print('progress.html', len(page) // 1024, 'KB')
