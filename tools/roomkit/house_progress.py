"""Regenerate the whole-house live progress page.

progress.py covers a single room (the master bedroom). This is the house-wide
view: one row per room, each with its reference photo beside the current render
and the critic's last verdict, plus the dollhouse hero shot.

Reads house_status.json, embeds every image as a data URI (the Artifact CSP
blocks all external requests, so nothing can be linked), writes
house_progress.html ready to publish.

    python -m roomkit.house_progress
"""

import base64
import html
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS = os.path.join(HERE, "house_status.json")
OUT = os.path.join(HERE, "house_progress.html")


def data_uri(path, max_w=560, quality=78):
    from PIL import Image
    if not path or not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


STATE_LABEL = {
    "pass": "Passed",
    "fail": "Rejected",
    "building": "Building",
    "judging": "With critic",
    "pending": "Queued",
    "nophoto": "No photo",
}


def room_block(r):
    state = r.get("state", "pending")
    rounds = int(r.get("round", 0))
    pips = "".join(f'<i class="pip{" on" if i < rounds else ""}"></i>'
                   for i in range(4))
    ref = data_uri(r.get("ref"))
    ren = data_uri(r.get("render"))

    def fig(uri, side, cap):
        if not uri:
            return (f'<figure class="empty"><div class="ph">not yet</div>'
                    f'<figcaption><span class="side">{side}</span></figcaption></figure>')
        return (f'<figure><img src="{uri}" alt="{html.escape(cap)}">'
                f'<figcaption><span class="side">{side}</span>'
                f'<span>{html.escape(cap)}</span></figcaption></figure>')

    note = r.get("note", "")
    return f"""
  <article class="room s-{state}" id="room-{r['id']}">
    <header>
      <h3>{html.escape(r['name'])}</h3>
      <div class="meta">
        <span class="pips">{pips}</span>
        <span class="chip">{STATE_LABEL.get(state, state)}</span>
      </div>
    </header>
    <div class="ab">
      {fig(ref, "Photo", r.get("ref_label", "reference"))}
      {fig(ren, "Render", r.get("render_label", "current"))}
    </div>
    {f'<p class="verdict">{html.escape(note)}</p>' if note else ''}
  </article>"""


def build():
    with open(STATUS, encoding="utf-8") as fh:
        st = json.load(fh)

    rooms = st["rooms"]
    judged = [r for r in rooms if r.get("state") != "nophoto"]
    passed = sum(1 for r in judged if r.get("state") == "pass")
    hero = data_uri(st.get("hero"), max_w=1100, quality=84)

    blocks = "".join(room_block(r) for r in rooms)
    facts = "".join(
        f'<div class="fact"><dt>{html.escape(k)}</dt><dd>{html.escape(str(v))}</dd></div>'
        for k, v in st.get("facts", {}).items())

    doc = f"""<title>The house, in 3D</title>
<style>
:root {{
  --ink:#14171a; --paper:#f1f2f3; --surface:#fff; --slate:#6e757c;
  --line:#d9dcdf; --coral:#dd4f31; --sage:#4f7d5e;
  --shadow: 0 1px 2px rgba(20,23,26,.06), 0 8px 24px -16px rgba(20,23,26,.35);
  --bg:var(--paper); --fg:var(--ink); --muted:var(--slate);
  --card:var(--surface); --rule:var(--line);
  --display: ui-sans-serif,"Segoe UI",system-ui,-apple-system,"Helvetica Neue",sans-serif;
  --mono: ui-monospace,"Cascadia Mono",Consolas,"SF Mono","Liberation Mono",monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#101215; --fg:#e7e9ea; --muted:#939aa1; --card:#181b1f; --rule:#2a2f35;
    --coral:#ef6d4e; --sage:#79ad88;
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 30px -18px rgba(0,0,0,.9);
  }}
}}
:root[data-theme="dark"] {{
  --bg:#101215; --fg:#e7e9ea; --muted:#939aa1; --card:#181b1f; --rule:#2a2f35;
  --coral:#ef6d4e; --sage:#79ad88;
  --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 30px -18px rgba(0,0,0,.9);
}}
body {{ background:var(--bg); color:var(--fg); font-family:var(--display);
  font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1040px; margin:0 auto; padding:56px 24px 96px;
  display:flex; flex-direction:column; gap:44px; }}
.eyebrow {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted); margin:0; }}
h1 {{ font-size:clamp(30px,5vw,46px); line-height:1.04; letter-spacing:-.028em;
  font-weight:640; margin:.35em 0 0; text-wrap:balance; }}
h1 em {{ font-style:normal; color:var(--coral); }}
.lede {{ margin:14px 0 0; max-width:64ch; color:var(--muted); font-size:17px; }}
.tally {{ font-family:var(--mono); font-variant-numeric:tabular-nums; font-size:13px;
  color:var(--muted); border-top:2px solid var(--coral); padding-top:10px; margin:18px 0 0; }}
.tally b {{ color:var(--fg); font-weight:620; }}
.hero img {{ display:block; width:100%; height:auto; border-radius:4px;
  box-shadow:var(--shadow); background:var(--card); }}
.hero figcaption {{ font-family:var(--mono); font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--muted); margin-top:10px; }}
h2 {{ font-size:12px; font-family:var(--mono); letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted); font-weight:500;
  margin:0 0 20px; padding-bottom:10px; border-bottom:1px solid var(--rule); }}
.rooms {{ display:flex; flex-direction:column; gap:34px; }}
.room header {{ display:flex; align-items:baseline; justify-content:space-between;
  gap:16px; margin-bottom:12px; }}
.room h3 {{ margin:0; font-size:19px; letter-spacing:-.012em; font-weight:580; }}
.meta {{ display:flex; align-items:center; gap:12px; flex:none; }}
.ab {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
@media (max-width:640px) {{ .ab {{ grid-template-columns:1fr; }} }}
figure {{ margin:0; display:flex; flex-direction:column; gap:8px; }}
figure img {{ display:block; width:100%; height:auto; border-radius:3px;
  background:var(--card); box-shadow:var(--shadow); }}
figure.empty .ph {{ aspect-ratio:4/3; border:1px dashed var(--rule); border-radius:3px;
  display:grid; place-items:center; font-family:var(--mono); font-size:12px;
  color:var(--muted); }}
figcaption {{ font-family:var(--mono); font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--muted);
  display:flex; justify-content:space-between; gap:12px; }}
figcaption .side {{ color:var(--fg); }}
.verdict {{ margin:12px 0 0; font-family:var(--mono); font-size:12.5px; line-height:1.5;
  color:var(--muted); max-width:78ch; }}
.pips {{ display:inline-flex; gap:3px; }}
.pip {{ width:6px; height:6px; border-radius:50%; background:var(--rule); display:block; }}
.pip.on {{ background:var(--muted); }}
.s-fail .pip.on {{ background:var(--coral); }}
.s-pass .pip.on {{ background:var(--sage); }}
.chip {{ display:inline-block; font-family:var(--mono); font-size:11px;
  letter-spacing:.08em; text-transform:uppercase; padding:4px 9px; border-radius:2px;
  border:1px solid var(--rule); color:var(--muted); }}
.s-pass .chip {{ border-color:color-mix(in srgb,var(--sage) 45%,transparent); color:var(--sage); }}
.s-fail .chip {{ border-color:color-mix(in srgb,var(--coral) 45%,transparent); color:var(--coral); }}
.s-building .chip, .s-judging .chip {{ border-color:var(--fg); color:var(--fg); }}
dl.facts {{ margin:0; display:grid;
  grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:20px 28px; }}
.fact {{ display:flex; flex-direction:column; gap:3px; }}
.fact dt {{ font-family:var(--mono); font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--muted); }}
.fact dd {{ margin:0; font-family:var(--mono); font-size:13px;
  font-variant-numeric:tabular-nums; }}
footer {{ font-family:var(--mono); font-size:12px; color:var(--muted); }}
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">Gauntlet loop &middot; whole house</p>
    <h1>{html.escape(st.get("headline", "The real house, rebuilt in 3D until a critic stops telling them apart"))}</h1>
    <p class="lede">{html.escape(st["lede"])}</p>
    <p class="tally"><b>{passed}</b> of <b>{len(judged)}</b> rooms past the critic
      &nbsp;·&nbsp; {html.escape(st["stamp"])}</p>
  </header>

  {f'<figure class="hero"><img src="{hero}" alt="Dollhouse view of the whole house"><figcaption>{html.escape(st.get("hero_label",""))}</figcaption></figure>' if hero else ''}

  <section>
    <h2>Rooms</h2>
    <div class="rooms">{blocks}
    </div>
  </section>

  {f'<section><h2>Ground truth</h2><dl class="facts">{facts}</dl></section>' if facts else ''}

  <footer>{html.escape(st.get("footer", ""))}</footer>
</div>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
