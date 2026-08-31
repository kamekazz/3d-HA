"""What round 5's art_g1 costs the room, against round 4's same four machines.

Packs my four machines' panels into one test sheet at exactly atlas4.py's
sizes, supersample and 16-level re-quantisation, and prints the PNG bytes.
Then does the same for the round-4 versions of those machines, which lived in
art_g1 (backed up), art_g2 (Marvel vs Capcom, NFL Blitz) and art_g3 (Mortal
Kombat) -- so the delta this round adds to Cabinets East + Cabinets North is a
measured number and not an estimate.

    $PY scratchpad/arc4/art/bytes_g1_r5.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "tools"))
for _p in (_TOOLS, _HERE, os.path.join(_HERE, "_r5")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from roomkit.glb import png_rgb                               # noqa: E402

SIZE = {"marquee": 120, "front": 96, "side": 64, "deck": 48, "bezel": 48,
        "riser": 64, "speaker": 48}
SS, QUANT = 2, 16
MINE = ["marvel-super-heroes", "marvel-vs-capcom", "mortal-kombat",
        "nfl-blitz"]
CORE = ("marquee", "side", "front", "deck")


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


def render(fn, n):
    big = n * SS
    buf = [[(0, 0, 0)] * big for _ in range(big)]
    fn(buf, 0, 0, big)
    out = []
    inv = 1.0 / (SS * SS)
    for y in range(n):
        rows = buf[y * SS:(y + 1) * SS]
        row = []
        for x in range(n):
            r = g = b = 0
            for sr in rows:
                for c in sr[x * SS:(x + 1) * SS]:
                    r += c[0]
                    g += c[1]
                    b += c[2]
            row.append((_q(r * inv), _q(g * inv), _q(b * inv)))
        out.append(row)
    return out


def sheet(items):
    """`items` is [(key, paint_fn)]; shelf-pack them the way Atlas does."""
    items = sorted(items, key=lambda kv: (-SIZE[kv[0].split(".")[-1]], kv[0]))
    area = sum(SIZE[k.split(".")[-1]] ** 2 for k, _ in items)
    width = 128
    while width * width < area * 1.30:
        width *= 2
    placed, x, y, shelf = [], 0, 0, 0
    for k, fn in items:
        n = SIZE[k.split(".")[-1]]
        if x + n > width:
            x, y, shelf = 0, y + shelf, 0
        placed.append((k, fn, x, y, n))
        x += n
        shelf = max(shelf, n)
    height = y + shelf
    px = [[(0, 0, 0)] * width for _ in range(height)]
    per = {}
    for k, fn, ox, oy, n in placed:
        t = render(fn, n)
        per[k] = len(png_rgb(t)) / 1024.0
        for r in range(n):
            px[oy + r][ox:ox + n] = t[r]
    return len(png_rgb(px)) / 1024.0, per, (width, height)


def collect(mod, slugs, extra=()):
    out = []
    for s in slugs:
        for p in CORE:
            k = s + "." + p
            if k in mod.PANELS:
                out.append((k, mod.PANELS[k]))
    for k in extra:
        if k in mod.PANELS:
            out.append((k, mod.PANELS[k]))
    return out


def render_rect(fn, w, h):
    W, H = w * SS, h * SS
    buf = [[(0, 0, 0)] * W for _ in range(H)]
    fn.rect(buf, 0, 0, W, H)
    out = []
    inv = 1.0 / (SS * SS)
    for y in range(h):
        rows = buf[y * SS:(y + 1) * SS]
        row = []
        for x in range(w):
            r = g = b = 0
            for sr in rows:
                for c in sr[x * SS:(x + 1) * SS]:
                    r += c[0]
                    g += c[1]
                    b += c[2]
            row.append((_q(r * inv), _q(g * inv), _q(b * inv)))
        out.append(row)
    return out


def sheet_rect(items, pxmap):
    """Shelf-pack NON-SQUARE tiles, tallest first."""
    items = sorted(items, key=lambda kv: (-pxmap[kv[0]][1], kv[0]))
    area = sum(pxmap[k][0] * pxmap[k][1] for k, _ in items)
    width = 128
    while width * width < area * 1.30:
        width *= 2
    placed, x, y, shelf = [], 0, 0, 0
    for k, fn in items:
        w, h = pxmap[k]
        if x + w > width:
            x, y, shelf = 0, y + shelf, 0
        placed.append((k, fn, x, y, w, h))
        x += w
        shelf = max(shelf, h)
    height = y + shelf
    px = [[(0, 0, 0)] * width for _ in range(height)]
    per = {}
    for k, fn, ox, oy, w, h in placed:
        t = render_rect(fn, w, h)
        per[k] = len(png_rgb(t)) / 1024.0
        for r in range(h):
            px[oy + r][ox:ox + w] = t[r]
    return len(png_rgb(px)) / 1024.0, per, (width, height)


def main():
    import art_g1
    new = collect(art_g1, MINE, extra=("marvel-super-heroes.bezel",))
    kb, per, wh = sheet(new)
    print("ROUND 5  art_g1, SQUARE tiles as atlas4 packs them today")
    print("         (4 machines, %d panels, sheet %dx%d): %.1f KB"
          % (len(new), wh[0], wh[1], kb))
    for k in sorted(per):
        n = SIZE[k.split(".")[-1]]
        print("    %-34s %6.2f KB   %3dx%-3d" % (k, per[k], n, n))
    rkb, rper, rwh = sheet_rect(new, art_g1.PANEL_PX)
    print()
    print("ROUND 5  art_g1, ISOTROPIC RECT tiles (art_g1.PANEL_PX)")
    print("         (%d panels, sheet %dx%d): %.1f KB   [%+.1f KB]"
          % (len(new), rwh[0], rwh[1], rkb, rkb - kb))
    for k in sorted(rper):
        w, h = art_g1.PANEL_PX[k]
        n = SIZE[k.split(".")[-1]]
        print("    %-34s %6.2f KB   %3dx%-3d  (was %3dx%-3d, %+.2f KB)"
              % (k, rper[k], w, h, n, n, rper[k] - per[k]))

    old = []
    sys.path.insert(0, os.path.join(_HERE, "_r5"))
    try:
        import art_g1_r4_bak as g1b                            # noqa: F401
    except Exception:
        g1b = None
    if g1b is None:
        try:
            sys.modules.pop("art_g1", None)
            sys.path.insert(0, os.path.join(_HERE, "_r5"))
            import importlib.util
            sp = importlib.util.spec_from_file_location(
                "g1r4", os.path.join(_HERE, "_r5", "art_g1_r4.bak.py"))
            g1b = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(g1b)
        except Exception as e:
            print("  (round-4 art_g1 backup unreadable: %s)" % e)
            g1b = None
    if g1b is not None:
        old += collect(g1b, ["marvel-super-heroes"])
    for name, slugs in (("art_g2", ["marvel-vs-capcom", "nfl-blitz"]),
                        ("art_g3", ["mortal-kombat"])):
        try:
            m = __import__(name)
            old += collect(m, slugs)
        except Exception as e:
            print("  (%s unreadable right now: %s)" % (name, e))
    if old:
        okb, oper, owh = sheet(old)
        print("ROUND 4  same machines (%d panels, sheet %dx%d): %.1f KB"
              % (len(old), owh[0], owh[1], okb))
        for k in sorted(oper):
            print("    %-34s %6.2f KB" % (k, oper[k]))
        print()
        print("DELTA on the four machines: %+.1f KB of PNG" % (kb - okb))
        print("  east run carries 3 of mine of 7 machines, north 1 of 4;")
        print("  the per-panel figures above are what the integrator adds up.")


if __name__ == "__main__":
    main()
