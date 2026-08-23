"""Build the round-V3 live progress page for room 17.

    python progress_v3.py r1_        # tag of the round's official shots

Reads shots/<tag><pose>.png, the six reference photos and state_v3.json, and
writes progress_v3.html with every image inlined, so the page is self-contained
and can be published as an Artifact.
"""
import base64
import io
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PHOTOS = os.path.join(ROOT, "docs", "v2 Hallway-jpg")
SHOTS = os.path.join(HERE, "shots")
STATE = os.path.join(HERE, "state_v3.json")
OUT = os.path.join(HERE, "progress_v3.html")

POSE_ORDER = ["p_runner", "p_stairs", "p_down", "p_up", "p_doors2", "p_doors1"]
PHOTO = {
    "p_stairs": "hallway_looking_towards_stairs.jpg",
    "p_runner": "hallway_with_white_runner_rug.jpg",
    "p_down": "staircase_looking_down.jpg",
    "p_up": "staircase_looking_up.jpg",
    "p_doors1": "two_closed_white_doors_1.jpg",
    "p_doors2": "two_closed_white_doors_2.jpg",
}
POSE_NAME = {
    "p_runner": "Looking south, runner",
    "p_stairs": "Looking north, knee wall",
    "p_down": "Down the flight",
    "p_up": "Up the flight",
    "p_doors2": "Alcove, three doors",
    "p_doors1": "Alcove, close",
}
CHIP = {"win": "good", "fail": "bad", "part": "warn"}


def jpg(path, width=460):
    if not os.path.exists(path):
        return ""
    im = Image.open(path).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build(tag):
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    verdicts = state.get("verdicts") or {}

    cards = []
    for pose in POSE_ORDER:
        ours = jpg(os.path.join(SHOTS, f"{tag}{pose}.png"))
        ref = jpg(os.path.join(PHOTOS, PHOTO[pose]))
        v = verdicts.get(pose) or {}
        cls = CHIP.get(v.get("state"), "idle")
        badge = v.get("badge", "not yet judged")
        gap = v.get("gap", "")
        gap_html = (f'<p class="gap"><b>Biggest gap</b> {esc(gap)}</p>') if gap else ""
        cards.append(f"""
        <figure class="shot">
          <figcaption>
            <span class="pose">{esc(POSE_NAME[pose])}</span>
            <span class="chip {cls}">{esc(badge)}</span>
          </figcaption>
          <div class="pair">
            <div class="half"><img alt="Our render, {esc(POSE_NAME[pose])}" src="{ours}"><span>ours</span></div>
            <div class="half"><img alt="Reference photograph" src="{ref}"><span>photo</span></div>
          </div>
          {gap_html}
        </figure>""")

    rows = []
    for p in state.get("pieces", []):
        rows.append(f"""
        <tr>
          <th scope="row">{esc(p.get('name', ''))}</th>
          <td><span class="chip {esc(p.get('cls', 'idle'))}">{esc(p.get('status', 'queued'))}</span></td>
          <td class="num">{esc(p.get('kb', '—'))}</td>
          <td class="note">{esc(p.get('note', ''))}</td>
        </tr>""")

    log = "".join(
        f'<li><span class="when">{esc(e.get("when", ""))}</span>{esc(e.get("what", ""))}</li>'
        for e in state.get("log", []))

    html = TEMPLATE.format(
        round_no=esc(state.get("round", "?")),
        headline=esc(state.get("headline", "")),
        cards="".join(cards), rows="".join(rows), log=log,
        stat_done=esc(state.get("stat_done", "—")),
        stat_open=esc(state.get("stat_open", "—")),
        stat_pieces=esc(state.get("stat_pieces", "—")),
    )
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(OUT, f"{os.path.getsize(OUT) / 1e6:.2f} MB")


TEMPLATE = """<title>Hallway Gauntlet</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  --ground:#e9eaeb; --panel:#fdfdfd; --panel-2:#f2f3f3;
  --ink:#17181a; --ink-2:#4a4d51; --ink-3:#7f858b;
  --line:rgba(23,24,26,.12);
  --runner:#a9865e;
  --good:#3f7d5a; --bad:#a8443a; --warn:#8f6d22; --idle:#7f858b;
  --r:10px;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#121315; --panel:#1a1c1f; --panel-2:#212429;
    --ink:#eceef0; --ink-2:#a8adb4; --ink-3:#767c84;
    --line:rgba(255,255,255,.11);
    --runner:#d8bb93;
    --good:#6fae86; --bad:#d9756a; --warn:#c9a24e; --idle:#767c84;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#121315; --panel:#1a1c1f; --panel-2:#212429;
  --ink:#eceef0; --ink-2:#a8adb4; --ink-3:#767c84;
  --line:rgba(255,255,255,.11);
  --runner:#d8bb93;
  --good:#6fae86; --bad:#d9756a; --warn:#c9a24e; --idle:#767c84;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:Archivo,"Helvetica Neue",Arial,sans-serif;
  font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:1120px; margin:0 auto; padding:40px 22px 80px;
  display:flex; flex-direction:column; gap:34px; }}
header h1 {{ font-size:clamp(29px,5vw,44px); font-weight:800; letter-spacing:-.025em;
  margin:0 0 8px; text-wrap:balance; line-height:1.1; }}
.eyebrow {{ font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11.5px;
  letter-spacing:.14em; text-transform:uppercase; color:var(--ink-3); margin:0 0 12px; }}
header p.lede {{ margin:0; color:var(--ink-2); max-width:64ch; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px; }}
.stat {{ flex:1 1 190px; background:var(--panel); border:1px solid var(--line);
  border-radius:var(--r); padding:14px 16px; }}
.stat b {{ display:block; font-size:26px; font-weight:800; letter-spacing:-.02em;
  font-variant-numeric:tabular-nums; }}
.stat span {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--ink-3); }}
h2 {{ font-size:12px; font-weight:500; letter-spacing:.14em; text-transform:uppercase;
  color:var(--ink-3); margin:0 0 14px; font-family:"IBM Plex Mono",monospace; }}
.shots {{ display:grid; gap:20px; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); }}
.shot {{ margin:0; background:var(--panel); border:1px solid var(--line);
  border-radius:var(--r); padding:12px; }}
.shot figcaption {{ display:flex; align-items:center; justify-content:space-between;
  gap:10px; margin-bottom:10px; }}
.pose {{ font-weight:600; font-size:14px; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; }}
.half {{ position:relative; }}
.half img {{ width:100%; display:block; border-radius:6px; background:var(--panel-2); }}
.half span {{ position:absolute; left:6px; bottom:6px;
  font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.1em;
  text-transform:uppercase; color:#fff; background:rgba(0,0,0,.62);
  padding:2px 6px; border-radius:4px; }}
.gap {{ margin:10px 2px 2px; font-size:13.5px; color:var(--ink-2); }}
.gap b {{ color:var(--ink); font-weight:600; }}
.chip {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.07em;
  text-transform:uppercase; padding:3px 8px; border-radius:999px;
  border:1px solid currentColor; white-space:nowrap; }}
.chip.good {{ color:var(--good); }} .chip.bad {{ color:var(--bad); }}
.chip.warn {{ color:var(--warn); }} .chip.idle {{ color:var(--idle); }}
.tablewrap {{ overflow-x:auto; background:var(--panel); border:1px solid var(--line);
  border-radius:var(--r); }}
table {{ width:100%; border-collapse:collapse; min-width:640px; }}
th,td {{ text-align:left; padding:11px 16px; border-bottom:1px solid var(--line);
  vertical-align:top; }}
tbody tr:last-child th, tbody tr:last-child td {{ border-bottom:0; }}
thead th {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.11em;
  text-transform:uppercase; color:var(--ink-3); font-weight:400; }}
tbody th {{ font-weight:600; white-space:nowrap; }}
.num {{ font-variant-numeric:tabular-nums; font-family:"IBM Plex Mono",monospace;
  font-size:13px; color:var(--ink-2); white-space:nowrap; }}
.note {{ color:var(--ink-2); font-size:13.5px; }}
ol.log {{ list-style:none; margin:0; padding:0; }}
ol.log li {{ display:flex; gap:14px; padding:11px 0; border-bottom:1px solid var(--line);
  color:var(--ink-2); font-size:14px; }}
ol.log li:last-child {{ border-bottom:0; }}
.when {{ flex:0 0 96px; font-family:"IBM Plex Mono",monospace; font-size:11px;
  letter-spacing:.05em; text-transform:uppercase; color:var(--runner); padding-top:3px; }}
footer {{ color:var(--ink-3); font-size:12.5px; font-family:"IBM Plex Mono",monospace;
  line-height:1.7; }}
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">Room 17 &middot; second floor &middot; round {round_no}</p>
    <h1>Grinding the hallway against its own photographs</h1>
    <p class="lede">{headline}</p>
  </header>

  <section class="stats">
    <div class="stat"><b>{stat_pieces}</b><span>pieces in flight</span></div>
    <div class="stat"><b>{stat_done}</b><span>views a critic can't split</span></div>
    <div class="stat"><b>{stat_open}</b><span>open failures</span></div>
  </section>

  <section>
    <h2>Render beside photograph</h2>
    <div class="shots">{cards}</div>
  </section>

  <section>
    <h2>Pieces</h2>
    <div class="tablewrap">
      <table>
        <thead><tr><th>Piece</th><th>Status</th><th>Size</th><th>Latest note</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2>What changed</h2>
    <ol class="log">{log}</ol>
  </section>

  <footer>
    The bar is docs/v2&nbsp;Hallway-jpg &mdash; the owner's own six photographs.<br>
    Critics judge blind: labels stripped, order shuffled per view, one subject each.
  </footer>
</div>
"""

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "a_")
