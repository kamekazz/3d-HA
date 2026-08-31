"""My four cabinets beside the owner's photographs of the same four."""
import os
import sys
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import preview_g1_r5 as P                                     # noqa: E402

ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
CROPS = [
    ("marvel-super-heroes",
     "scratchpad/arc4/roster/rec/e_run3x.png", (100, 150, 570, 1010)),
    ("marvel-vs-capcom",
     "scratchpad/arc4/roster/rec/e_run3x.png", (430, 130, 830, 960)),
    ("mortal-kombat",
     "scratchpad/arc4/roster/rec/e_run3x.png", (770, 170, 1070, 840)),
    ("nfl-blitz",
     "scratchpad/arc4/art/ref/blitz_v47.png", (150, 130, 640, 1090)),
]
PXFT = P.PXFT


def elevation(s):
    bw, top, dy, mqh, pl = P.GEO[s]
    T = {}
    for p in ("marquee", "front", "side", "deck", "bezel"):
        k = s + "." + p
        if k in P.art_g1.PANELS:
            T[k] = P.tile(k)
    H = int(top * PXFT) + 6
    fw = int(bw * PXFT)
    el = Image.new("RGB", (fw, H), (26, 26, 30))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(el)

    def yy(ft):
        return H - 6 - ft * PXFT

    def put(k, x0, y0, x1, y1):
        el.paste(T[k].resize((max(1, int(x1 - x0)), max(1, int(y1 - y0))),
                             Image.LANCZOS), (int(x0), int(y0)))
    mq_hi, mq_lo = top - 0.18 + pl, top - mqh - 0.18 + pl
    put(s + ".marquee", 0.06 * PXFT, yy(mq_hi), (bw - 0.06) * PXFT, yy(mq_lo))
    bk = s + ".bezel"
    if bk in T:
        put(bk, 0.05 * PXFT, yy(mq_lo - 0.10), (bw - 0.05) * PXFT,
            yy(dy + pl + 0.30))
    else:
        dr.rectangle([0.05 * PXFT, yy(mq_lo - 0.10), (bw - 0.05) * PXFT,
                      yy(dy + pl + 0.30)], fill=(21, 21, 26))
    dr.rectangle([0.17 * PXFT, yy(mq_lo - 0.26), (bw - 0.17) * PXFT,
                  yy(dy + pl + 0.46)], fill=(10, 12, 16))
    put(s + ".deck", 0.06 * PXFT, yy(dy + pl + 0.014),
        (bw - 0.06) * PXFT, yy(dy + pl + 0.014) + 0.92 * PXFT * 0.34)
    put(s + ".front", 0.08 * PXFT, yy(dy + pl - 0.62), (bw - 0.08) * PXFT,
        yy(pl + 0.16))
    if pl:
        dr.rectangle([0, yy(pl), fw, yy(0)], fill=(16, 16, 20))
    return el


def main():
    cells = []
    for s, path, box in CROPS:
        ph = Image.open(os.path.join(ROOT, path)).convert("RGB").crop(box)
        el = elevation(s)
        h = 780
        ph = ph.resize((int(ph.width * h / ph.height), h), Image.LANCZOS)
        el = el.resize((int(el.width * h / el.height), h), Image.LANCZOS)
        cells.append((s, ph, el))
    gap = 18
    W = sum(p.width + e.width + gap * 2 for (_, p, e) in cells) + gap
    im = Image.new("RGB", (W, 780 + 34), (12, 12, 14))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im)
    x = gap
    for s, ph, el in cells:
        d.text((x, 8), "%s   PHOTO | RENDER" % s.upper(), fill=(214, 218, 228))
        im.paste(ph, (x, 30))
        im.paste(el, (x + ph.width + gap, 30))
        x += ph.width + el.width + gap * 2
    out = os.path.join(_HERE, "compare_g1_r5.png")
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    main()
