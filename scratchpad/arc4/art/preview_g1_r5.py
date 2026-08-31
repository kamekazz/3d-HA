"""Round-5 self-check sheet for art_g1.

Renders every panel at the EXACT size and quantisation atlas4.py will ship
(supersample 2x, box-average, re-quantise to 16 levels), then assembles each
machine as a front elevation and a flank at real feet, so the question the
critics actually asked -- "does this still read as a dark slab with a label on
it?" -- can be answered by looking.

    $PY scratchpad/arc4/art/preview_g1_r5.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from PIL import Image, ImageDraw                              # noqa: E402
import art_g1                                                 # noqa: E402

SIZE = {"marquee": 120, "front": 96, "side": 64, "deck": 48, "bezel": 48}
SS, QUANT = 2, 16

# ar2.py's own numbers for these four machines: (bw, top, dy, mqh, plinth)
GEO = {
    "marvel-super-heroes": (2.10, 5.86, 2.44, 0.55, 0.10),
    "marvel-vs-capcom":    (2.42, 6.34, 2.60, 0.76, 0.00),
    "mortal-kombat":       (2.16, 5.98, 2.48, 0.58, 0.14),
    "nfl-blitz":           (2.18, 6.02, 2.44, 0.56, 0.00),
}
ORDER = ["marvel-super-heroes", "marvel-vs-capcom", "mortal-kombat",
         "nfl-blitz"]
PXFT = 108


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


RECT = os.environ.get("G1_SQUARE") != "1"


def tile(key):
    """The panel exactly as it will ship: isotropic rect tiles from
    art_g1.PANEL_PX by default, or the old square tile with G1_SQUARE=1."""
    if RECT:
        w, h = art_g1.PANEL_PX[key]
        buf = [[(0, 0, 0)] * (w * SS) for _ in range(h * SS)]
        art_g1.PANELS[key].rect(buf, 0, 0, w * SS, h * SS)
    else:
        w = h = SIZE[key.split(".")[-1]]
        buf = [[(0, 0, 0)] * (w * SS) for _ in range(h * SS)]
        art_g1.PANELS[key](buf, 0, 0, w * SS)
    im = Image.new("RGB", (w, h))
    px = im.load()
    inv = 1.0 / (SS * SS)
    for y in range(h):
        rows = buf[y * SS:(y + 1) * SS]
        for x in range(w):
            r = g = b = 0
            for sr in rows:
                for c in sr[x * SS:(x + 1) * SS]:
                    r += c[0]
                    g += c[1]
                    b += c[2]
            px[x, y] = (_q(r * inv), _q(g * inv), _q(b * inv))
    return im


def stats(im):
    px = list(im.getdata())
    lum = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in px]
    mean = sum(lum) / len(lum)
    sd = (sum((v - mean) ** 2 for v in lum) / len(lum)) ** 0.5
    w, h = im.size
    d = 0.0
    n = 0
    for y in range(h):
        for x in range(w - 1):
            d += abs(lum[y * w + x] - lum[y * w + x + 1])
            n += 1
    return mean, sd, d / max(1, n)


def main():
    T = {}
    for s in ORDER:
        for p in ("marquee", "front", "side", "deck", "bezel"):
            if s + "." + p in art_g1.PANELS:
                T[s + "." + p] = tile(s + "." + p)

    rows = []
    for s in ORDER:
        bw, top, dy, mqh, pl = GEO[s]
        H = int(top * PXFT) + 6
        # ---- front elevation, real feet
        fw = int(bw * PXFT)
        el = Image.new("RGB", (fw, H), (26, 26, 30))
        dr = ImageDraw.Draw(el)

        def put(key, x0, y0, x1, y1):
            w, h = max(1, int(x1 - x0)), max(1, int(y1 - y0))
            el.paste(T[key].resize((w, h), Image.NEAREST), (int(x0), int(y0)))

        def yy(ft):                     # feet from the floor -> pixel row
            return H - 6 - ft * PXFT
        mq_hi, mq_lo = top - 0.18 + pl, top - mqh - 0.18 + pl
        put(s + ".marquee", 0.06 * PXFT, yy(mq_hi), (bw - 0.06) * PXFT,
            yy(mq_lo))
        bk = s + ".bezel"
        if bk in art_g1.PANELS:
            put(bk, 0.05 * PXFT, yy(mq_lo - 0.10), (bw - 0.05) * PXFT,
                yy(dy + pl + 0.30))
        else:
            dr.rectangle([0.05 * PXFT, yy(mq_lo - 0.10), (bw - 0.05) * PXFT,
                          yy(dy + pl + 0.30)], fill=(21, 21, 26))
        dr.rectangle([0.17 * PXFT, yy(mq_lo - 0.26), (bw - 0.17) * PXFT,
                      yy(dy + pl + 0.46)], fill=(10, 12, 16))
        put(s + ".deck", 0.06 * PXFT, yy(dy + pl + 0.014),
            (bw - 0.06) * PXFT, yy(dy + pl + 0.014) + 0.92 * PXFT * 0.34)
        put(s + ".front", 0.08 * PXFT, yy(dy + pl - 0.62),
            (bw - 0.08) * PXFT, yy(pl + 0.16))
        if pl:
            dr.rectangle([0, yy(pl), fw, yy(0)], fill=(16, 16, 20))
        # ---- flank, real feet (2.95 ft of profile bbox)
        sw = int(2.95 * PXFT)
        fl = T[s + ".side"].resize((sw, H - 6), Image.NEAREST)
        # ---- deck in plan, real feet
        dk = T[s + ".deck"].resize((int((bw - 0.12) * PXFT),
                                    int(0.92 * PXFT)), Image.NEAREST)
        # ---- marquee big
        mq = T[s + ".marquee"].resize(
            (int(2.4 * PXFT), int(2.4 * PXFT / art_g1.ASPECT[s + ".marquee"])),
            Image.NEAREST)
        rows.append((s, el, fl, dk, mq))

    gap, pad, lab = 26, 22, 30
    rw = max(e.width + f.width + max(d.width, m.width) + gap * 3
             for (_, e, f, d, m) in rows)
    rh = max(e.height for (_, e, _f, _d, _m) in rows) + lab
    W = rw + pad * 2
    Hh = rh * len(rows) + pad * 2
    sheet = Image.new("RGB", (W, Hh), (14, 14, 16))
    d = ImageDraw.Draw(sheet)
    for i, (s, el, fl, dk, mq) in enumerate(rows):
        y = pad + i * rh
        d.text((pad, y + 6), "%s   front elevation / flank / deck (plan) / "
                             "marquee   [all at ship resolution]"
               % s.upper(), fill=(210, 214, 224))
        y += lab
        x = pad
        sheet.paste(el, (x, y))
        x += el.width + gap
        sheet.paste(fl, (x, y))
        x += fl.width + gap
        sheet.paste(mq, (x, y))
        sheet.paste(dk, (x, y + mq.height + 18))
    out = os.path.join(_HERE, "wrap_g1.png")
    sheet.save(out)
    print("wrote", out, sheet.size)
    print()
    print("%-34s %7s %7s %7s" % ("panel", "mean", "sd", "mean|d1|"))
    for s in ORDER:
        for p in ("marquee", "front", "side", "deck"):
            k = s + "." + p
            m, sd, d1 = stats(T[k])
            print("%-34s %7.1f %7.1f %7.2f" % (k, m, sd, d1))


if __name__ == "__main__":
    main()
