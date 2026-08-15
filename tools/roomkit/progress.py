"""Regenerate the live progress page.

Reads status.json, embeds the reference photo and the latest render as data URIs
(the Artifact CSP blocks every external request, so nothing can be linked), and
writes progress.html ready to publish.

    python -m roomkit.progress
"""

import base64
import html
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS = os.path.join(HERE, "status.json")
OUT = os.path.join(HERE, "progress.html")


def data_uri(path, max_w=760, quality=82):
    from PIL import Image
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
}


def piece_row(p):
    state = p.get("state", "pending")
    rounds = int(p.get("round", 0))
    pips = "".join(
        f'<i class="pip{" on" if i < rounds else ""}"></i>' for i in range(3))
    note = p.get("note", "")
    note_html = (f'<p class="verdict">{html.escape(note)}</p>' if note else "")
    return f"""
      <tr class="s-{state}">
        <th scope="row">
          <span class="name">{html.escape(p["name"])}</span>
          {note_html}
        </th>
        <td class="rounds"><span class="pips">{pips}</span><span class="rn">{rounds or "&mdash;"}</span></td>
        <td class="state"><span class="chip">{STATE_LABEL.get(state, state)}</span></td>
      </tr>"""


def build():
    with open(STATUS) as fh:
        st = json.load(fh)

    ref = data_uri(st["reference"])
    render = data_uri(st["render"])
    pieces = "".join(piece_row(p) for p in st["pieces"])

    passed = sum(1 for p in st["pieces"] if p.get("state") == "pass")
    total = len(st["pieces"])

    facts = "".join(
        f'<div class="fact"><dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd></div>'
        for k, v in st["facts"].items())

    doc = f"""<title>Master bedroom → 3D</title>
<style>
:root {{
  /* pulled off the room itself: charcoal casework, grey plank floor, warm-white
     wall, and the coral of the canvas over the bed as the only hot accent */
  --ink:      #14171a;
  --paper:    #f1f2f3;
  --surface:  #ffffff;
  --slate:    #6e757c;
  --line:     #d9dcdf;
  --coral:    #dd4f31;
  --sage:     #4f7d5e;
  --shadow:   0 1px 2px rgba(20,23,26,.06), 0 8px 24px -16px rgba(20,23,26,.35);

  --bg: var(--paper);
  --fg: var(--ink);
  --muted: var(--slate);
  --card: var(--surface);
  --rule: var(--line);

  --display: ui-sans-serif, "Segoe UI", system-ui, -apple-system, "Helvetica Neue", sans-serif;
  --mono: ui-monospace, "Cascadia Mono", Consolas, "SF Mono", "Liberation Mono", monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #101215; --fg: #e7e9ea; --muted: #939aa1;
    --card: #181b1f; --rule: #2a2f35;
    --coral: #ef6d4e; --sage: #79ad88;
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 30px -18px rgba(0,0,0,.9);
  }}
}}
:root[data-theme="dark"] {{
  --bg: #101215; --fg: #e7e9ea; --muted: #939aa1;
  --card: #181b1f; --rule: #2a2f35;
  --coral: #ef6d4e; --sage: #79ad88;
  --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 30px -18px rgba(0,0,0,.9);
}}
:root[data-theme="light"] {{
  --bg: var(--paper); --fg: var(--ink); --muted: var(--slate);
  --card: var(--surface); --rule: var(--line);
  --coral: #dd4f31; --sage: #4f7d5e;
  --shadow: 0 1px 2px rgba(20,23,26,.06), 0 8px 24px -16px rgba(20,23,26,.35);
}}

body {{
  background: var(--bg); color: var(--fg);
  font-family: var(--display);
  font-size: 16px; line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}}
.wrap {{
  max-width: 940px; margin: 0 auto; padding: 56px 24px 96px;
  display: flex; flex-direction: column; gap: 48px;
}}

/* ---- masthead ---- */
.mast {{ display: flex; flex-direction: column; gap: 14px; }}
.eyebrow {{
  font-family: var(--mono); font-size: 11px; letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted);
}}
h1 {{
  font-size: clamp(30px, 5vw, 46px); line-height: 1.04;
  letter-spacing: -.028em; font-weight: 640; margin: 0;
  text-wrap: balance;
}}
h1 em {{ font-style: normal; color: var(--coral); }}
.lede {{ margin: 0; max-width: 62ch; color: var(--muted); font-size: 17px; }}
.tally {{
  font-family: var(--mono); font-variant-numeric: tabular-nums;
  font-size: 13px; color: var(--muted);
  border-top: 2px solid var(--coral); padding-top: 10px; margin-top: 4px;
}}
.tally b {{ color: var(--fg); font-weight: 620; }}

/* ---- the A/B ---- */
.ab {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
@media (max-width: 640px) {{ .ab {{ grid-template-columns: 1fr; }} }}
figure {{ margin: 0; display: flex; flex-direction: column; gap: 10px; }}
figure img {{
  display: block; width: 100%; height: auto; border-radius: 3px;
  background: var(--card); box-shadow: var(--shadow);
}}
figcaption {{
  font-family: var(--mono); font-size: 11px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted);
  display: flex; justify-content: space-between; gap: 12px;
}}
figcaption .side {{ color: var(--fg); }}

/* ---- pieces ---- */
section h2 {{
  font-size: 12px; font-family: var(--mono); letter-spacing: .14em;
  text-transform: uppercase; color: var(--muted); font-weight: 500;
  margin: 0 0 16px; padding-bottom: 10px; border-bottom: 1px solid var(--rule);
}}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; vertical-align: top; padding: 15px 0; border-bottom: 1px solid var(--rule); }}
th {{ font-weight: 500; padding-right: 20px; }}
.name {{ font-size: 17px; letter-spacing: -.01em; font-weight: 560; }}
.verdict {{
  margin: 6px 0 0; font-family: var(--mono); font-size: 12.5px;
  line-height: 1.5; color: var(--muted); max-width: 58ch;
}}
td.rounds {{ width: 96px; white-space: nowrap; }}
.pips {{ display: inline-flex; gap: 3px; vertical-align: middle; }}
.pip {{ width: 6px; height: 6px; border-radius: 50%; background: var(--rule); display: block; }}
.pip.on {{ background: var(--muted); }}
.s-fail .pip.on {{ background: var(--coral); }}
.s-pass .pip.on {{ background: var(--sage); }}
.rn {{
  font-family: var(--mono); font-variant-numeric: tabular-nums;
  font-size: 12px; color: var(--muted); margin-left: 8px;
}}
td.state {{ width: 118px; text-align: right; }}
.chip {{
  display: inline-block; font-family: var(--mono); font-size: 11px;
  letter-spacing: .08em; text-transform: uppercase;
  padding: 4px 9px; border-radius: 2px;
  border: 1px solid var(--rule); color: var(--muted);
}}
.s-pass .chip {{ border-color: color-mix(in srgb, var(--sage) 45%, transparent); color: var(--sage); }}
.s-fail .chip {{ border-color: color-mix(in srgb, var(--coral) 45%, transparent); color: var(--coral); }}
.s-building .chip, .s-judging .chip {{ border-color: var(--fg); color: var(--fg); }}

/* ---- facts ---- */
dl.facts {{ margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 20px 28px; }}
.fact {{ display: flex; flex-direction: column; gap: 3px; }}
.fact dt {{
  font-family: var(--mono); font-size: 11px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted);
}}
.fact dd {{ margin: 0; font-family: var(--mono); font-size: 13px; font-variant-numeric: tabular-nums; }}

footer {{ font-family: var(--mono); font-size: 12px; color: var(--muted); }}
</style>

<div class="wrap">
  <header class="mast">
    <p class="eyebrow">Gauntlet loop &middot; room 14 &middot; Master Bed</p>
    <h1>The real bedroom, rebuilt in&nbsp;3D until a critic <em>stops telling them apart</em></h1>
    <p class="lede">{html.escape(st["lede"])}</p>
    <p class="tally"><b>{passed}</b> of <b>{total}</b> pieces past the critic &nbsp;·&nbsp; {html.escape(st["stamp"])}</p>
  </header>

  <div class="ab">
    <figure>
      <img src="{ref}" alt="Photograph of the real master bedroom">
      <figcaption><span class="side">The room</span><span>reference photo</span></figcaption>
    </figure>
    <figure>
      <img src="{render}" alt="Current 3D render of the bedroom from the same viewpoint">
      <figcaption><span class="side">The render</span><span>{html.escape(st["render_label"])}</span></figcaption>
    </figure>
  </div>

  <section>
    <h2>Pieces</h2>
    <table>
      <tbody>{pieces}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Ground truth</h2>
    <dl class="facts">{facts}</dl>
  </section>

  <footer>{html.escape(st["footer"])}</footer>
</div>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
