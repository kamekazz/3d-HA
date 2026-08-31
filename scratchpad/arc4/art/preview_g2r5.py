"""Round-5 G2 preview sheet.

Renders each panel at the size atlas4 will actually pack it at, re-quantises
to 16 levels the same way atlas4 does, then stretches it to the panel's TRUE
aspect so what is on screen is what lands on the cabinet.  Also builds a
crude front elevation per machine (marquee / screen / deck / front stacked at
their real feet) so the four can be judged as machines, not as tiles.

    $PY scratchpad/arc4/art/preview_g2r5.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from PIL import Image, ImageDraw            # noqa: E402  (preview only)
import art_g2                               # noqa: E402

# atlas4 merges all four art modules and raises on a duplicate key.  Round 5
# reassigned the machines by wall run, so the other three modules still claim
# some of mine until the integrator merges.  Stub them out for this preview
# only -- SIZE / SS / QUANT then still come from atlas4 itself, so what is
# drawn here is byte-for-byte what the atlas will pack.
import types                                # noqa: E402
for _n in ("art_g0", "art_g1", "art_g3"):
    _s = types.ModuleType(_n)
    _s.PANELS = {}
    sys.modules[_n] = _s
import atlas4                               # noqa: E402

SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
LABEL = {"legends-ultimate": "LEGENDS ULTIMATE  (SOUTH_RUN[0], bw 2.95)",
         "street-fighter-2-champion-edition":
             "STREET FIGHTER II CHAMPION EDITION  (SOUTH_RUN[1], bw 2.42)",
         "time-crisis": "TIME CRISIS  (SOUTH_RUN[2], bw 2.52)",
         "terminator-2": "TERMINATOR 2  (SOUTH_RUN[3], bw 2.28)"}
PANELS = ["marquee", "side", "front", "deck", "screen"]
SIZE = dict(atlas4.SIZE)
SIZE["screen"] = art_g2.SCREEN_SIZE_PX


def render(key):
    n = SIZE[key.split(".")[-1]]
    rows = atlas4.render(key, n)          # supersampled + 16-level requantised
    im = Image.new("RGB", (n, n))
    im.putdata([c for r in rows for c in r])
    return im


def to_panel(im, aspect, h):
    return im.resize((max(1, int(h * aspect)), h), Image.NEAREST)


def sheet():
    H = 200
    pad, lab = 18, 26
    cells = []
    for s in SLUGS:
        row = []
        for p in PANELS:
            a = art_g2.A[s][p]
            row.append((p, to_panel(render("%s.%s" % (s, p)), a, H)))
        cells.append((s, row))
    w = pad + max(sum(im.width + pad for _, im in row) for _, row in cells)
    h = sum(lab + H + pad for _ in cells) + pad
    out = Image.new("RGB", (w, h), (24, 24, 28))
    d = ImageDraw.Draw(out)
    y = pad
    for s, row in cells:
        d.text((pad, y - 1), LABEL[s], fill=(230, 232, 238))
        y += lab
        x = pad
        for p, im in row:
            out.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                        outline=(90, 94, 104))
            d.text((x + 3, y + im.height + 2), "%s %dpx" % (p, SIZE[p]),
                   fill=(150, 154, 162))
            x += im.width + pad
        y += H + pad
    return out


# ------- crude front elevations, real feet, so the four read as machines
ROWS = {  # bw, top, dy, mqh, plinth  (straight off ar2.SOUTH_RUN)
    "legends-ultimate": (2.95, 6.36, 2.62, 0.80, 0.00),
    "street-fighter-2-champion-edition": (2.42, 6.02, 2.46, 0.58, 0.00),
    "time-crisis": (2.52, 6.24, 2.56, 0.68, 0.12),
    "terminator-2": (2.28, 5.92, 2.42, 0.60, 0.00),
}
PPF = 78.0          # px per foot


def elevation(s):
    bw, top, dy, mqh, pl = ROWS[s]
    top += pl
    dy += pl
    mq_lo, mq_hi = top - mqh - 0.18, top - 0.18
    fr = art_g2.FRONT_RECT[s]
    W, H = int(bw * PPF), int(top * PPF)
    im = Image.new("RGB", (W, H), (18, 18, 22))

    def put(key, x0, y0, x1, y1):
        w, h = max(1, int((x1 - x0) * PPF)), max(1, int((y1 - y0) * PPF))
        p = render(key).resize((w, h), Image.NEAREST)
        im.paste(p, (int(x0 * PPF), int((top - y1) * PPF)))

    put("%s.front" % s, fr["inset_ft"], fr["y0_ft"], bw - fr["inset_ft"],
        fr["y1_ft"])
    put("%s.deck" % s, 0.06, dy, bw - 0.06, dy + 0.92)     # laid flat, faked
    put("%s.screen" % s, 0.17, dy + 1.10, bw - 0.17, mq_lo - 0.26)
    put("%s.marquee" % s, 0.06, mq_lo, bw - 0.06, mq_hi)
    return im


def elevations():
    ims = [elevation(s) for s in SLUGS]
    pad = 26
    w = pad + sum(i.width + pad for i in ims)
    h = max(i.height for i in ims) + pad * 2 + 20
    out = Image.new("RGB", (w, h), (24, 24, 28))
    d = ImageDraw.Draw(out)
    x = pad
    for s, i in zip(SLUGS, ims):
        out.paste(i, (x, pad + (h - pad * 2 - 20 - i.height)))
        d.text((x, h - 18), s, fill=(200, 204, 212))
        x += i.width + pad
    return out


if __name__ == "__main__":
    a, b = sheet(), elevations()
    pad = 20
    out = Image.new("RGB", (max(a.width, b.width) + pad * 2,
                            a.height + b.height + pad * 3), (24, 24, 28))
    out.paste(a, (pad, pad))
    out.paste(b, (pad, a.height + pad * 2))
    p = os.path.join(HERE, "wrap_g2.png")
    out.save(p)
    print("wrote", p, out.size)
