"""Round-4 arcade art atlas -- per-machine printed artwork, not one motif x16.

Round 3's `a2kit._art_atlas()` painted a 4x4 grid of 16 tiles in which twelve
were THE SAME drawing in different hues and four were sine-wash "marquees" with
rectangles standing in for letters.  Its critic counted sixteen of one machine.

This module replaces it.  The four art agents' modules
(`art/art_g0.py` .. `art_g3.py`) each expose

    PANELS : {"<slug>.<panel>": paint(px, ox, oy, tile)}

where `paint` writes a `tile` x `tile` square block into the row-major pixel
list `px` at (ox, oy).  Here they are merged, packed into one PNG per wall run,
and exposed as a key -> (u0, v0, u1, v1) lookup with the same half-texel inset
`a2kit.uvr()` had, so every `uvq`/`sweep` call site takes a rect and nothing
about the call sites changes.

THREE THINGS WORTH KNOWING BEFORE CHANGING ANYTHING HERE.

1.  ONE ATLAS PER WALL RUN, not one for the room.  `glb.py` shares an image by
    byte identity *inside one file*, but Cabinets East / North / South are three
    separate GLBs, so a single room-wide atlas is paid for three times.  Sixteen
    machines x 4 panels at 256 px is ~1.2 MB of PNG; x3 it is 3.6 MB against a
    1.5 MB room.  Per-run atlases carry only the machines standing on that wall.

2.  PANEL SIZES ARE PER PANEL CLASS.  A marquee is the identity of a machine and
    gets the pixels; a flank is mostly hidden by its neighbour and a deck is seen
    at a grazing angle from eye level, so they get fewer.  `SIZE` below is the
    only dial that matters for payload.

3.  EVERY PANEL IS SUPERSAMPLED.  Panels are painted at `SS` x the target size
    and box-averaged down.  Two reasons: `art_g2` always paints into a fixed
    256 px buffer and point-samples on the way out, which shreds letterforms at
    any smaller tile; and averaging a 4x4-Bayer-dithered image is exactly the
    reconstruction the dither was designed for, so the small tiles come out
    smoother than they would if painted at size.

Run it standalone to write the three PNGs and report their bytes:

    $PY scratchpad/arc4/atlas4.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_TOOLS = os.path.abspath(os.path.join(_HERE, "..", "..", "tools"))
for _p in (_TOOLS, os.path.join(_HERE, "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from roomkit.glb import png_rgb                              # noqa: E402

import art_g0                                                # noqa: E402
import art_g1                                                # noqa: E402
import art_g2                                                # noqa: E402
import art_g3                                                # noqa: E402

_MODULES = (art_g0, art_g1, art_g2, art_g3)

PANELS = {}
for _m in _MODULES:
    for _k, _fn in _m.PANELS.items():
        if _k in PANELS:
            raise KeyError("two art modules both claim %r" % _k)
        PANELS[_k] = _fn


# --------------------------------------------------------------- panel sizes
# px per panel class.  Payload scales with the sum of these squared, so this
# table IS the budget.  Measured bytes for the three runs are printed by
# __main__ -- re-run it after touching anything here.
SIZE = {
    "marquee": 120,     # the identity of a machine; the round-4 hero surface
    "front":    96,     # the second identifying surface on most machines
    "side":     64,     # mostly occluded by the next machine in the run
    "deck":     48,     # seen at a grazing angle from any eye-level camera
    "bezel":    48,     # a dark surround; carries identity on Golden Tee only
    "speaker":  48,     # Time Crisis' twin-hole head panel
    "riser":    64,
}

# Two flanks ARE the machine, so they are not on the run-of-the-mill side
# budget: Star Wars is a black art panel of TIE fighters and an X-wing on a
# yellow carcase, and the north-wall multicade's whole identity is its pale
# line-work wrap.  Both stand at the end of their run where the flank is not
# occluded by the next cabinet.
SIZE_KEY = {
    "star-wars-atari.side": 96,
    "north-1-graffiti-multicade.side": 96,
}
SS = 2                  # supersample factor; see note 3 above
DEFAULT_SIZE = 96

# Post-quantisation step, in levels.  The art modules all quantise to multiples
# of 8 and then rely on a fixed 4x4 Bayer pattern, which zlib matches cheaply.
# Box-averaging the supersampled panel destroys BOTH -- it produces every value
# in between -- and that alone cost 0.86 bytes/px against the modules' own
# 0.13-0.47.  Re-quantising the averaged result puts the compressor back where
# it was.  MEASURED, same panel sizes, all three runs: 243.2 KB at 8 levels,
# 209.2 at 12, 181.6 at 16, 146.8 at 24.  16 is what ships -- these are flat
# printed vinyl graphics, not photographs, and no banding is visible at panel
# scale in the sheets or in the render.  Re-applying the Bayer dither at
# quantise time to hide banding was tried and costs 40 KB for no visible gain,
# because a fixed 4x4 pattern is only cheap when it is the ONLY variation.
QUANT = 16


def size_of(key):
    if key in SIZE_KEY:
        return SIZE_KEY[key]
    return SIZE.get(key.split(".")[-1], DEFAULT_SIZE)


# ------------------------------------------------------------------- render
_CACHE = {}


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


def render(key, n):
    """One panel as an n x n list of (r, g, b) rows, supersampled."""
    ck = (key, n)
    if ck in _CACHE:
        return _CACHE[ck]
    big = n * SS
    buf = [[(0, 0, 0)] * big for _ in range(big)]
    PANELS[key](buf, 0, 0, big)
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
    _CACHE[ck] = out
    return out


# -------------------------------------------------------------------- atlas
class Atlas(object):
    """A packed art atlas plus the key -> UV rect lookup.

    `uv(key)` is the drop-in replacement for `a2kit.uvr(i)`: it returns
    (u0, v0, u1, v1) with a half-texel inset, so bilinear filtering never
    bleeds a neighbouring panel across a cabinet's edge.
    """

    def __init__(self, keys, inset=0.5):
        keys = list(dict.fromkeys(keys))
        for k in keys:
            if k not in PANELS:
                raise KeyError("no art module paints %r" % k)
        # shelf-pack, tallest first, into the narrowest power-of-two width that
        # keeps the sheet roughly square
        items = sorted(keys, key=lambda k: (-size_of(k), k))
        area = sum(size_of(k) ** 2 for k in items)
        width = 128
        while width * width < area * 1.30:
            width *= 2
        while True:
            placed, x, y, shelf = {}, 0, 0, 0
            for k in items:
                n = size_of(k)
                if x + n > width:
                    x, y, shelf = 0, y + shelf, 0
                placed[k] = (x, y, n)
                x += n
                shelf = max(shelf, n)
            height = y + shelf
            if height <= width * 2:
                break
            width *= 2
        height = max(1, height)

        px = [[(0, 0, 0)] * width for _ in range(height)]
        for k, (ox, oy, n) in placed.items():
            tile = render(k, n)
            for row in range(n):
                px[oy + row][ox:ox + n] = tile[row]

        self.w, self.h = width, height
        self.png = png_rgb(px)
        self.rects = {}
        for k, (ox, oy, n) in placed.items():
            self.rects[k] = ((ox + inset) / width, (oy + inset) / height,
                             (ox + n - inset) / width,
                             (oy + n - inset) / height)
        self.keys = list(placed)

    def uv(self, key):
        return self.rects[key]

    def __contains__(self, key):
        return key in self.rects

    def __repr__(self):
        return "<Atlas %dx%d, %d panels, %.1f KB>" % (
            self.w, self.h, len(self.rects), len(self.png) / 1024.0)


# ------------------------------------------------- what each wall run needs
# Derived from the canonical roster.  Order matches ar2.py's run tables.
EAST_SLUGS = ["star-wars-atari", "marvel-super-heroes", "marvel-vs-capcom",
              "mortal-kombat", "nba-jam", "tmnt-turtles-in-time",
              "east-7-no-machine"]
SOUTH_SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
               "time-crisis", "terminator-2", "ridge-racer"]
NORTH_SLUGS = ["north-1-graffiti-multicade", "pac-man", "nfl-blitz",
               "golden-tee-3d-golf"]

# Every machine needs these four.  EXTRA is the short list of extra surfaces
# the geometry actually uses: `art_g3` painted a bezel for all four of its
# machines but said itself that three of them "carry no identity -- dark frames
# with a small wordmark", so only Golden Tee's is kept (its lit yellow
# three-panel instruction strip is a real, and genuinely emissive, feature of
# that machine).  The other fifteen bezels are a plain untextured dark material,
# which is what `art_g0` recommended and what keeps NBA Jam's flaming ball from
# being smeared round its monitor.  `time-crisis.speaker` is the maroon band and
# twin-hole tan panel under its marquee -- the most distinctive thing on that
# head -- but the cabinet has no separate speaker quad, so it is not packed.
CORE = ("marquee", "side", "front", "deck")
EXTRA_KEYS = ("golden-tee-3d-golf.bezel",)


def keys_for(slugs):
    out = []
    for s in slugs:
        for p in CORE:
            k = "%s.%s" % (s, p)
            if k not in PANELS:
                raise KeyError("no %s panel for %s" % (p, s))
            out.append(k)
    for k in EXTRA_KEYS:
        if k.split(".")[0] in slugs:
            out.append(k)
    return out


def east():
    return Atlas(keys_for(EAST_SLUGS))


def south():
    return Atlas(keys_for(SOUTH_SLUGS))


def north():
    return Atlas(keys_for(NORTH_SLUGS))


if __name__ == "__main__":
    tot = 0
    for name, fn in (("east", east), ("south", south), ("north", north)):
        a = fn()
        tot += len(a.png)
        p = os.path.join(_HERE, "atlas4_%s.png" % name)
        with open(p, "wb") as f:
            f.write(a.png)
        print("%-6s %s  -> %s" % (name, a, os.path.basename(p)))
    print("all three atlases: %.1f KB" % (tot / 1024.0))
