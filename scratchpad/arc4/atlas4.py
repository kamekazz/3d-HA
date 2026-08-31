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

2.  PANEL SIZES ARE PER PANEL CLASS, AND SINCE ROUND 5 THEY ARE ISOTROPIC.
    A marquee is the identity of a machine and gets the pixels; a flank is
    mostly hidden by its neighbour and a deck is seen at a grazing angle from
    eye level, so they get fewer.  `SIZE[cls]` is no longer a tile edge but a
    scale: a panel of world aspect A packs at S*sqrt(A) x S/sqrt(A), so a 3.4:1
    marquee stops spending 120 rows on a 0.6 ft band.  `SIZE`, `SIZE_KEY` and
    `QUANT` are the dials that matter for payload.

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
OWNER = {}
for _m in _MODULES:
    for _k, _fn in _m.PANELS.items():
        if _k in PANELS:
            raise KeyError("two art modules both claim %r" % _k)
        PANELS[_k] = _fn
        OWNER[_k] = _m

# ROUND 5.  Every one of the fifteen real machines is claimed by exactly one
# round-5 module.  `east-7-no-machine` is claimed by NONE of them, because the
# roster says that slot is EMPTY in every frame that sees the whole run -- the
# geometry stays (this round changes artwork, not layout) and it is dressed as
# an honest unbranded black upright.  Round 4's panels for it survive in
# `art_g2.LEGACY_PANELS`, so they are folded in here as a fallback rather than
# deleting EAST_RUN[6] or inventing a sixteenth title.  `setdefault`, so a
# module that later claims one of these wins.
for _m in _MODULES:
    for _k, _fn in getattr(_m, "LEGACY_PANELS", {}).items():
        if PANELS.setdefault(_k, _fn) is _fn:
            OWNER[_k] = _m


# ------------------------------------------------------------- panel aspect
# The quad a panel is mapped onto is nowhere near square: a marquee band is
# ~3.4:1 and a flank ~0.48:1.  Round 4 packed SQUARE tiles, so a marquee spent
# 120 rows on a band that needs ~50 and got only 120 columns of native detail
# across the widest, most-read surface on the machine.  Each module publishes
# the aspect (w/h) it authored its own panels to -- `art_g1.ASPECT`,
# `art_g0.ASPECT`, `art_g3.PANEL_AR`, `art_g2.ASPECT` (per class) -- and the
# OWNING module's number is the one used, because that is the pre-squeeze its
# paint function already applied (and, for `art_g1`, the aspect its native
# `.rect` path draws at).
_CLASS_AR = {"marquee": 3.35, "front": 1.25, "side": 0.48, "deck": 2.35,
             "bezel": 0.92, "screen": 1.30, "riser": 6.2}


def _module_aspect(mod, key):
    for attr in ("ASPECT", "PANEL_AR"):
        t = getattr(mod, attr, None)
        if isinstance(t, dict):
            if key in t:
                return float(t[key])
            cls = key.split(".")[-1]
            if cls in t:
                return float(t[cls])
    return None


ASPECT = {}
for _k in PANELS:
    _a = _module_aspect(OWNER[_k], _k)
    if _a is None:
        _a = _CLASS_AR.get(_k.split(".")[-1], 1.0)
    ASPECT[_k] = _a


def set_aspects(d):
    """Override panel aspects with numbers measured off the real geometry.

    `ar2.py` owns the run tables, so only it can compute the true world W/H of
    every quad; it calls this at import time.  Running this module standalone
    falls back to the art modules' own published aspects, which they derived
    from the same geometry and which agree to a few percent.
    """
    ASPECT.update(d)


# --------------------------------------------------------------- panel sizes
# ROUND 5.  `SIZE[cls]` is no longer a tile edge -- it is an ISOTROPIC SCALE:
# a panel of aspect A is packed at w = S*sqrt(A), h = S/sqrt(A), so its pixel
# count is still S*S but the pixels are spread the way the surface is shaped.
# That is the payload lever this round, and it is why four modules of new
# artwork fit under the cap without a line of it being deleted:
#
#   marquee, A=3.4:  square 120  ->  120 x 120 = 14400 px,  55 px/ft across
#                    iso    104  ->  192 x  56 = 10752 px,  87 px/ft across
#
# i.e. 25% FEWER bytes and 60% MORE resolution in the direction letterforms
# actually run.  (The idea, and the first measurement of it, are art_g1's.)
#
# What each class is worth, and why these numbers:
#   marquee  the hero surface, and the one round 4 passed on.  Kept at close to
#            its round-4 pixel count in the WIDE direction and cut in the tall
#            one, where a 0.6 ft band never needed 120 rows.
#   front    unchanged in effect (92 iso ~= 96 square on a 1.25:1 panel); the
#            fronts are the second-most-read surface and all four modules
#            rewrote them this round.
#   deck     RAISED.  Round 4's decks were near-empty dark slabs at 48 px; a
#            printed hardwood court, a brick street and a fairway now live
#            there, and a deck is 2.35:1, so 52 iso buys 80 columns against
#            round 4's 48 for +19% bytes.  The decks are half of what this
#            round is judged on.
#   side     cut to 48.  A flank is 0.48:1 and the run spacings leave 0.00-0.22
#            ft between cabinets, so most flanks are simply not visible; the
#            two that ARE keep their own larger size in SIZE_KEY below, and so
#            does Legends Ultimate at the west end of the south run.
SIZE = {
    "marquee": 102,
    "front":    92,
    "side":     42,
    "deck":     52,
    # ROUND 6 (screens).  Both classes are cut to pay for the curved,
    # vertex-graded CRT glass in `ar2.crt` (+2.5 KB of geometry across the
    # three runs).  MEASURED, all three atlases: bezel 40 -> 32 is -0.31 KB and
    # screen 40 -> 28 is -0.40 KB, together -0.71 KB.  It is a fidelity dial on
    # the two lowest-frequency panel classes in the room and no artwork is
    # removed to reach it: a bezel is a plain dark surround and the four
    # printed screens are dark glass carrying an instruction card and some room
    # reflection -- neither has a letterform in it at any size.
    "bezel":    32,
    "screen":   28,
    "riser":    58,
}

# Per-panel overrides.  Two flanks ARE the machine and stand at the end of
# their run where nothing occludes them: Star Wars' black art panel of TIE
# fighters on a yellow carcase, and the north-wall multicade's pale line-work
# wrap.  Everything else here is the reverse -- a flank the next cabinet hides
# almost completely, declared by the module that drew it:
#   `art_g0.SIZE_KEY_REQUEST`  nba-jam, pac-man   (0.1-0.2 ft gaps)
#   `art_g2`'s report          the three inner south flanks (0.10-0.22 ft)
# Legends Ultimate is NOT cut: it stands at the west end of the south run and
# its west flank is the one south flank a camera can see.
# `east-7-no-machine` is the empty slot -- an unbranded black upright carrying
# round 4's plain panels, so it gets the smallest budget in the room.
SIZE_KEY = {
    "star-wars-atari.side": 86,
    "north-1-graffiti-multicade.side": 86,
    "legends-ultimate.side": 60,
    "nba-jam.side": 46,
    "pac-man.side": 46,
    "street-fighter-2-champion-edition.side": 44,
    "time-crisis.side": 44,
    "terminator-2.side": 44,
    "east-7-no-machine.side": 40,
    "east-7-no-machine.front": 56,
    "east-7-no-machine.marquee": 64,
    "east-7-no-machine.deck": 36,
}
SS = 2                  # supersample factor; see note 3 above
DEFAULT_SIZE = 88

# Post-quantisation step, in levels.  The art modules all quantise to multiples
# of 8 and then rely on a fixed 4x4 Bayer pattern, which zlib matches cheaply.
# Box-averaging the supersampled panel destroys BOTH -- it produces every value
# in between -- and that alone cost 0.86 bytes/px against the modules' own
# 0.13-0.47.  Re-quantising the averaged result puts the compressor back where
# it was.  MEASURED, same panel sizes, all three runs: 243.2 KB at 8 levels,
# 209.2 at 12, 181.6 at 16, 146.8 at 24.  16 is what ships -- these are flat
# printed vinyl graphics, not photographs, and no banding is visible at panel
# scale in the sheets or in the render.
#
# ROUND 5 SHIPS 20, not 16.  Re-measured on the round-5 art at the isotropic
# sizes above, all three runs: 16 -> 158.1 KB, 20 -> 144.4, 24 -> 129.5.  Round
# 4 measured 24 as where banding begins on a marquee, which is the hero
# surface, so 24 is not taken.  20 buys 13.7 KB with no banding visible in
# atlas4_*.png or in the mq_* frames, and it is the difference between this
# room shipping under its cap and over it.  It is a fidelity dial, not a
# content one: no artwork is removed to reach the number.
QUANT = 20


def scale_of(key):
    if key in SIZE_KEY:
        return SIZE_KEY[key]
    return SIZE.get(key.split(".")[-1], DEFAULT_SIZE)


def dims(key):
    """(w, h) in texels for one panel -- isotropic at its own aspect."""
    s = scale_of(key)
    a = ASPECT.get(key, 1.0) ** 0.5
    return max(8, int(s * a + 0.5)), max(8, int(s / a + 0.5))


# ------------------------------------------------------------------- render
_CACHE = {}


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


def _box(buf, bw, bh, w, h):
    """Area-average a bw x bh pixel buffer down to w x h, then re-quantise."""
    out = []
    for y in range(h):
        y0 = y * bh // h
        y1 = max(y0 + 1, (y + 1) * bh // h)
        rows = buf[y0:y1]
        row = []
        for x in range(w):
            x0 = x * bw // w
            x1 = max(x0 + 1, (x + 1) * bw // w)
            r = g = b = n = 0
            for sr in rows:
                for c in sr[x0:x1]:
                    r += c[0]
                    g += c[1]
                    b += c[2]
                    n += 1
            inv = 1.0 / n
            row.append((_q(r * inv), _q(g * inv), _q(b * inv)))
        out.append(row)
    return out


def render(key, w, h):
    """One panel as h rows of w (r, g, b), supersampled and re-quantised.

    Two paths.  `art_g1`'s paint functions carry a `.rect(px, ox, oy, w, h)`
    that draws NATIVELY non-square, so they are handed the real shape and every
    pixel of the budget lands as drawn detail.  The other three modules only
    implement the square `paint(px, ox, oy, tile)` contract and pre-squeeze
    their own drawing to their published aspect, so they are painted into a
    square buffer big enough to oversample BOTH axes and area-averaged into the
    rectangle.  The square contract is unchanged -- nothing in art_g0/g2/g3 had
    to move for this.
    """
    ck = (key, w, h)
    if ck in _CACHE:
        return _CACHE[ck]
    fn = PANELS[key]
    rect = getattr(fn, "rect", None)
    if rect is not None:
        bw, bh = w * SS, h * SS
        buf = [[(0, 0, 0)] * bw for _ in range(bh)]
        rect(buf, 0, 0, bw, bh)
    else:
        bw = bh = max(w, h) * SS
        buf = [[(0, 0, 0)] * bw for _ in range(bh)]
        fn(buf, 0, 0, bw)
    out = _box(buf, bw, bh, w, h)
    _CACHE[ck] = out
    return out


# ------------------------------------------------------------ PNG encoding
# A NEGATIVE RESULT, recorded so nobody spends the afternoon on it twice.
# `roomkit.glb.png_rgb` writes PNG filter type 0 (None) on every row, and the
# obvious win looked like per-row adaptive filtering (Sub/Up/Average/Paeth by
# the PNG spec's minimum-sum-of-absolute-differences heuristic).  It was
# implemented, run on these exact three atlases, and it is 14% WORSE:
#
#     filter 0 (what ships)   158.1 KB
#     adaptive per-row        180.5 KB
#
# The reason is that this is synthetic flat printed art, not a photograph.
# Filter 0 leaves long runs of identical bytes, and identical or near-identical
# rows, which zlib's LZ77 stage matches across the whole sheet; a per-row
# predictor decorrelates each row against a different neighbour and destroys
# exactly those matches.  Adaptive filtering pays off on photographic gradients
# and loses on this.  So `png_rgb` stays.
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
        # shelf-pack, TALLEST first -- tiles are rectangles now, so height is
        # what wastes a shelf -- into the narrowest power-of-two width that
        # keeps the sheet roughly square
        items = sorted(keys, key=lambda k: (-dims(k)[1], -dims(k)[0], k))
        area = sum(w * h for w, h in (dims(k) for k in items))
        width = 128
        while width * width < area * 1.30:
            width *= 2
        while True:
            placed, x, y, shelf, over = {}, 0, 0, 0, False
            for k in items:
                w, h = dims(k)
                if w > width:
                    over = True
                    break
                if x + w > width:
                    x, y, shelf = 0, y + shelf, 0
                placed[k] = (x, y, w, h)
                x += w
                shelf = max(shelf, h)
            height = y + shelf
            if not over and height <= width * 2:
                break
            width *= 2
        height = max(1, height)

        px = [[(0, 0, 0)] * width for _ in range(height)]
        for k, (ox, oy, w, h) in placed.items():
            tile = render(k, w, h)
            for row in range(h):
                px[oy + row][ox:ox + w] = tile[row]

        self.w, self.h = width, height
        self.png = png_rgb(px)
        self.rects = {}
        for k, (ox, oy, w, h) in placed.items():
            self.rects[k] = ((ox + inset) / width, (oy + inset) / height,
                             (ox + w - inset) / width,
                             (oy + h - inset) / height)
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
#
# ROUND 5 adds two kinds of extra surface, both because a module produced
# photographic evidence for them and neither because it had one spare:
#   `marvel-super-heroes.bezel`  the one monitor surround on the east wall the
#       photographs show carrying printed art -- a dark blue-teal camo (v3 4 /
#       e_run3x).  art_g1 drew it and asked for it here.
#   `<slug>.screen` x4 (art_g2)  the four SOUTH monitors.  All four are DARK in
#       every frame and no attract loop is invented; what they carry is what is
#       photographed -- Champion Edition's pale yellow instruction card along
#       the bottom edge and Time Crisis's dim olive game image.  Round 4 gave
#       all sixteen machines one flat near-black quad, so the south run's own
#       identity stopped at the marquee.
# `ridge-racer.bezel` is painted and deliberately NOT packed: art_g3 called it
# a spare, and Ridge Racer is round the SW corner and out of all three judged
# frames.  `time-crisis.speaker` is not packed either -- the cabinet has no
# separate speaker quad to put it on, which is missing geometry, not missing
# art, and is recorded as such.
CORE = ("marquee", "side", "front", "deck")
EXTRA_KEYS = ("golden-tee-3d-golf.bezel", "marvel-super-heroes.bezel",
              "legends-ultimate.screen",
              "street-fighter-2-champion-edition.screen",
              "time-crisis.screen", "terminator-2.screen")


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
