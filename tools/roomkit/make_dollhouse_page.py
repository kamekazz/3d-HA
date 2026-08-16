"""Build the whole-house dollhouse gallery page.

    python -m roomkit.make_dollhouse_page
"""

import base64
import html
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SHOTS = os.path.join(ROOT, "scratchpad", "dollhouse")
OUT = os.path.join(HERE, "dollhouse.html")


def uri(name, max_w=1500, q=84):
    from PIL import Image
    path = os.path.join(SHOTS, name)
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


PLATES = [
    ("house_sw.png", "The whole house",
     "Every floor at once with the exterior shell hidden — the view the app does not otherwise have. "
     "House mode shows only the shell; single-floor mode shows one storey. This forces the third."),
    ("house_low.png", "Lower angle, both storeys",
     "Dropped to 18&deg; so the cutaway reads into the first floor as well as the second."),
    ("floor_L2.png", "Second floor",
     "Master suite with its vaulted ceiling, bath and walk-in closet; guest room, hallway and stairs, "
     "Rios Room with its birdcage and ladder shelf."),
    ("floor_L1.png", "First floor",
     "Living room with the stone chimney breast on the chamfer, kitchen and island, dining under its "
     "chandelier, office, laundry, pantry, bath, the staircase &mdash; and a garage with workbench, "
     "shelving, water heater, freezer and a car, which was the emptiest rectangle in the house."),
    ("floor_L0.png", "Basement",
     "Movie room and arcade. Both were derived by thresholding the basement floor plan into a grid and "
     "cross-checking it against the staircase, since there is only one photograph of each."),
    ("house_ne.png", "From the other side",
     "The same house from the north-east. Walls nearest the camera are culled, so which rooms you see "
     "depends on the quadrant you orbit to."),
]


def build():
    plates = []
    for fn, title, cap in PLATES:
        u = uri(fn)
        if not u:
            continue
        plates.append(f"""
  <figure>
    <img src="{u}" alt="{html.escape(title)}">
    <figcaption><b>{html.escape(title)}</b><span>{cap}</span></figcaption>
  </figure>""")

    doc = f"""<title>The house as a dollhouse</title>
<style>
:root {{
  --bg:#f1f2f3; --fg:#14171a; --muted:#6e757c; --card:#fff; --rule:#d9dcdf;
  --accent:#dd4f31;
  --shadow:0 1px 2px rgba(20,23,26,.06), 0 10px 30px -18px rgba(20,23,26,.4);
  --display:ui-sans-serif,"Segoe UI",system-ui,-apple-system,sans-serif;
  --mono:ui-monospace,"Cascadia Mono",Consolas,"SF Mono",monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0e1013; --fg:#e7e9ea; --muted:#939aa1; --card:#16191d; --rule:#282d33;
    --accent:#ef6d4e; --shadow:0 1px 2px rgba(0,0,0,.5), 0 12px 34px -20px #000;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0e1013; --fg:#e7e9ea; --muted:#939aa1; --card:#16191d; --rule:#282d33;
  --accent:#ef6d4e; --shadow:0 1px 2px rgba(0,0,0,.5), 0 12px 34px -20px #000;
}}
body {{ background:var(--bg); color:var(--fg); font-family:var(--display);
  font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:56px 22px 96px;
  display:flex; flex-direction:column; gap:44px; }}
.eyebrow {{ font-family:var(--mono); font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--muted); margin:0; }}
h1 {{ font-size:clamp(30px,5vw,46px); line-height:1.05; letter-spacing:-.028em;
  font-weight:640; margin:.3em 0 0; text-wrap:balance; }}
h1 em {{ font-style:normal; color:var(--accent); }}
.lede {{ margin:14px 0 0; max-width:66ch; color:var(--muted); font-size:17px; }}
figure {{ margin:0; display:flex; flex-direction:column; gap:12px; }}
figure img {{ display:block; width:100%; height:auto; border-radius:5px;
  background:var(--card); box-shadow:var(--shadow); }}
figcaption {{ display:flex; flex-direction:column; gap:4px; max-width:80ch; }}
figcaption b {{ font-size:15px; font-weight:600; letter-spacing:-.01em; }}
figcaption span {{ font-family:var(--mono); font-size:12.5px; line-height:1.5;
  color:var(--muted); }}
footer {{ font-family:var(--mono); font-size:12px; color:var(--muted);
  border-top:1px solid var(--rule); padding-top:16px; }}
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">3D Home Assistant &middot; dollhouse view</p>
    <h1>The house, <em>walls down</em></h1>
    <p class="lede">Rendered from the running app at 127.0.0.1:5000 &mdash; the same Three.js scene the
      Home Assistant dashboard draws, with device markers hidden. Room walls are single-sided with
      inward normals, so the two nearest the camera cull away on their own; that is what makes the
      cutaway, and it is why each orbit quadrant shows a different pair of rooms.</p>
  </header>
{''.join(plates)}
  <footer>Geometry traced from the floor plans; rooms furnished against the photographs of each
    actual room, and metered against them rather than eyeballed. Where no photograph exists &mdash; the
    garage interior, the pantry &mdash; the contents are inferred and labelled as such.</footer>
</div>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    build()
