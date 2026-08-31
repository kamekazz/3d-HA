"""Round-3/4 additions for room 2 (Arcade).  Texture + swept-profile helpers.

Round 2's cabinets were seven boxes with the hue swapped: every zone a flat
untextured colour field and a control deck that projected 0.06 ft.  Two things
fix that and both live here:

  * printed ARTWORK -- a UV into a shared image rather than a colour block.
  * `sweep()` -- a cabinet is a swept 2-D SIDE PROFILE, not a stack of boxes.
    The profile carries the real silhouette (base, apron, the control deck
    jutting 0.70 ft proud, the raked screen, the marquee overhang, the top),
    the two flanks come out as one polygon each carrying the art UVs, and the
    perimeter band closes it.  ~150 verts a cabinet against ~850 for the box
    stack, which is what pays for the north wall.

ROUND 4 REPLACED THE ARTWORK.  Round 3's `_art_atlas()` painted 16 tiles of
which twelve were the same drawing in a different hue and four were sine-wash
bands with rectangles standing in for letters; its critic correctly counted one
machine repeated sixteen times.  It is GONE -- deleted, not deprecated -- and
with it `ART_TEX`, the module-level `ART*` materials, `MQ_MATS` and `uvr()`, so
nothing can quietly keep sampling it.  What replaces them is `ArtSet`: one
`scratchpad/arc4/atlas4.Atlas` per wall run, carrying only the machines that
stand on that wall, plus the materials that sample it.  `ArtSet.uv(
"<slug>.<panel>")` is the drop-in for `uvr(i)` -- same (u0, v0, u1, v1) shape,
same half-texel inset -- so every `uvq`/`sweep` call site takes a rect exactly
as before.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "arc4"))

from bkit import Model, Material, Part, Rnd, mix, box, cylinder   # noqa: F401
from roomkit.glb import png_rgb

from atlas4 import Atlas, keys_for                              # noqa: E402


# --------------------------------------------------------------- the marquee
# A marquee IS a backlit lamp in the photographs, so it legitimately stays
# emissive where ROOM-BRIEF forbids emissive on room-scale surfaces -- it is a
# fixture the photograph shows, at the size the photograph shows it.  Round 3
# gave all sixteen machines one of four shared pastels, which is part of why
# the run read as one machine restyled.  Each tint below is that machine's OWN
# marquee, read off the roster: hue from the band, strength from whether the
# photographs show it LIT.  glTF emissive is a flat factor with no texture, so
# a high strength washes the printed title away.  MEASURED: the first pass
# used each band's own light hue at strength up to 1.15 and NBA Jam's
# crimson caps came out pink while the Turtles marquee bleached to flat
# green.  So the tint is that marquee's hue taken to a LOW VALUE -- the lit
# bands sit around luma 60-85 and the ones the photographs show dark around
# 22-30 -- and the strength stays near 1.  The glow reads at night; the
# printed title survives the day.
MARQUEE = {
    # ---- east wall
    # turned ~40 deg off the wall, head cropped or facing away; not lit
    "star-wars-atari":            ("#171410", 0.90),
    # full-bleed painted art, "reads dim, not brightly lit"
    "marvel-super-heroes":        ("#2b2118", 1.00),
    # character-battle illustration in reds, blues and oranges
    "marvel-vs-capcom":           ("#3c2618", 1.00),
    # navy-to-black ground behind the pale dragon roundel
    "mortal-kombat":              ("#28304a", 1.00),
    # lit cream/tan band -- one of the two most legible marquees in the room
    "nba-jam":                    ("#514226", 1.00),
    # printed art panel, green title over a New York street
    "tmnt-turtles-in-time":       ("#2e3618", 1.00),
    # the slot the photographs show empty -- see the roster
    "east-7-no-machine":          ("#16181c", 0.90),
    # ---- south wall
    # a BLACK band with silver italic type; it must not glow green
    "legends-ultimate":           ("#1e222c", 1.00),
    # dark navy ground, value unresolved in every frame
    "street-fighter-2-champion-edition": ("#182448", 1.00),
    # pale gold/cream ground, lit
    "time-crisis":                ("#4c4024", 1.00),
    # black ground, chrome type only
    "terminator-2":               ("#23252e", 1.00),
    # yellow band with dark type
    "ridge-racer":                ("#50441a", 1.00),
    # ---- north wall
    # "does NOT read as lit"; pale abstract lettering on near-black
    "north-1-graffiti-multicade": ("#16181f", 0.90),
    # white ground, yellow bubble caps -- the brightest object in the run
    "pac-man":                    ("#5a4a2a", 1.00),
    # near-black/navy, chrome italic caps; not lit
    "nfl-blitz":                  ("#1b1b24", 0.90),
    # photographic golf-course scene, lit
    "golden-tee-3d-golf":         ("#303c22", 1.00),
}

# Which deck material each machine's printed control panel was authored for.
# The four art agents did not author to one exposure.  A control deck faces UP
# and an up-facing surface in this scene collects roughly twice what a vertical
# one does, so `ART_DK` (#4c4c4c) is the default -- but TMNT's brick street and
# the Marvel decks are bright printed art that ART_DK crushes to mud, and
# Marvel vs Capcom's is a genuinely pale silver panel.
# ROUND 5 added six rows, and it is worth knowing which were asked for.
#
# FOUR ARE MODULE REQUESTS, all making the same argument -- the printed graphic
# is the machine's identity and ART_DK (#4c4c4c) crushes it:
#   nba-jam, golden-tee-3d-golf   art_g0.DECK_MAT_REQUEST: without "D" the
#       hardwood court and the fairway "render at 0.30 albedo and go to mud"
#   mortal-kombat, nfl-blitz      art_g1.MATERIAL_HINT: the ice-blue lightning
#       field and the violet nebula ARE those machines' identity
#
# TWO ARE THE INTEGRATOR'S CALL, declared as such: legends-ultimate and
# north-1-graffiti-multicade.  Neither module named a factor.  art_g2 measured
# its Legends deck at luma 56 and wrote "if the integrator's render still
# crushes them, the grounds are cheap to raise"; ART_DK would put it at ~17,
# which is a black shelf.  Choosing the lighter factor is the same remedy
# without editing another agent's artwork.
#
# Pac-Man is deliberately NOT here -- art_g0 authored that deck black and
# lifted for the x0.30 factor, so ART_DK is correct for it.
DECK_MAT = {
    "tmnt-turtles-in-time": "D",
    "marvel-super-heroes": "D",
    "time-crisis": "D",
    "marvel-vs-capcom": "M",
    "nba-jam": "D",
    "golden-tee-3d-golf": "D",
    "mortal-kombat": "D",
    "nfl-blitz": "D",
    "legends-ultimate": "D",
    "north-1-graffiti-multicade": "D",
}


# The carcase / T-molding colour of each machine, off the roster.  `sweep()`
# hands this to every perimeter quad, which is the cabinet's top, back and the
# strip of front face either side of the printed panel -- i.e. the T-molding,
# which is what makes Turtles read from across the room and what round 3 threw
# away by painting all sixteen cabinets one black.  Where the roster warns a
# sample is a SHADED or RGB-washed reading (Star Wars' #969129, Pac-Man's
# #c9c15a) the hue is kept and the value/saturation lifted, as it says to.
CARCASE = {
    # ---- east wall
    "star-wars-atari":            "#c9b52c",   # golden yellow carcase
    "marvel-super-heroes":        "#8a7038",   # gold/tan molding on black
    "marvel-vs-capcom":           "#17181c",   # black, black molding
    "mortal-kombat":              "#5a1d22",   # dark red / maroon molding
    "nba-jam":                    "#5e1a20",   # deep red / maroon molding
    "tmnt-turtles-in-time":       "#3f9b4a",   # BRIGHT grass-green molding
    "east-7-no-machine":          "#191a1e",   # unbranded black upright
    # ---- south wall
    "legends-ultimate":           "#111318",   # matte black throughout
    "street-fighter-2-champion-edition": "#14161c",
    "time-crisis":                "#7e3230",   # red body under a cream head
    "terminator-2":               "#3a1c1e",   # dark red-maroon molding
    "ridge-racer":                "#8e2a26",   # red body, yellow marquee band
    # ---- north wall
    "north-1-graffiti-multicade": "#2b2e38",   # near-black, blue-grey lift
    "pac-man":                    "#d8b81e",   # yellow body
    "nfl-blitz":                  "#22222a",   # the darkest machine on the wall
    "golden-tee-3d-golf":         "#2a2b2f",   # flat black
}


class ArtSet(object):
    """One wall run's printed artwork: the packed atlas plus its materials.

    `glb.py` shares an image by byte identity INSIDE one file, but Cabinets
    East / North / South are three separate GLBs, so a room-wide atlas would be
    paid for three times.  Each run therefore carries only its own machines.
    """

    def __init__(self, name, slugs):
        self.name = name
        self.slugs = list(slugs)
        self.atlas = Atlas(keys_for(slugs))
        tex = self.atlas.png
        self.tex = tex
        self.ART = Material("a2art_" + name, "#ffffff", roughness=0.68, tex=tex)
        self.ART_D = Material("a2artd_" + name, "#c9c9c9", roughness=0.72,
                              tex=tex)
        # an UP-facing surface in this scene collects roughly twice what a
        # vertical one does, so control-deck art needs a much darker factor
        self.ART_DK = Material("a2artk_" + name, "#4c4c4c", roughness=0.80,
                               tex=tex)
        self.ART_DM = Material("a2artm_" + name, "#9a9a9a", roughness=0.78,
                               tex=tex)
        # a screen surround carrying no printed graphic: round 3 reused the
        # front-panel tile here, which smeared NBA Jam's flaming ball round its
        # monitor.  Machines whose module DID author a bezel use that instead.
        self.BEZEL = Material("a2bez_" + name, "#15151a", roughness=0.50)
        # ROUND 5: a printed CRT.  Only the four south machines have one, and
        # all four are DARK in the photographs -- what the panel carries is the
        # instruction card and the room reflections, not an attract loop.  The
        # factor is dark glass (#3a3a3a) with the same faint blue emissive
        # `SCRN` uses, or four monitors would render as lit televisions.
        # ROUND 6 keeps all four painted panels -- they are what the
        # photographs show on those four monitors, and not one of them is an
        # invented attract loop -- and changes only the factor they are printed
        # through.  It is now WHITE, which round 5's comment warned against,
        # and the warning was wrong: MEASURED, the four panels come out of
        # atlas4 at mean luma 13.0 / 21.6 / 25.7 / 29.4 out of 255.  They are
        # ALREADY dark glass.  Multiplying them by a dark factor as well
        # rendered Time Crisis's monitor at luma 0.71 and Champion Edition's at
        # 5.17 in this room's daylight -- black holes -- and round 5 only got
        # away with it because a strength-0.55 emissive was doing all the
        # visible work, which is what made the four south screens read as
        # switched-on.  With the emissive gone the factor's job is to let the
        # printed albedo through as authored, so it is white; `crt`'s vertex
        # grade then supplies the same top-to-bottom fall the other twelve get.
        self.SCREEN = Material("a2scrn_" + name, "#ffffff", roughness=0.30,
                               tex=tex, emissive="#16181c",
                               emissive_strength=0.40)
        self._mq = {}
        self._cc = {}

    def uv(self, key):
        return self.atlas.uv(key)

    def has(self, key):
        return key in self.atlas

    def kb(self):
        return len(self.atlas.png) / 1024.0

    def deck(self, slug):
        return {"D": self.ART_D, "M": self.ART_DM}.get(
            DECK_MAT.get(slug), self.ART_DK)

    def carcase(self, slug):
        if slug not in self._cc:
            self._cc[slug] = Material("a2cc_" + slug, CARCASE[slug],
                                      roughness=0.55)
        return self._cc[slug]

    def marquee(self, slug):
        if slug not in self._mq:
            col, st = MARQUEE[slug]
            self._mq[slug] = Material(
                "a2mq_" + slug, "#f4f2ee", roughness=0.42, tex=self.tex,
                emissive=col, emissive_strength=st)
        return self._mq[slug]

    def __repr__(self):
        return "<ArtSet %s %r>" % (self.name, self.atlas)


def _clamp8(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def _hex(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def uvq(m, mat, p, rect, flip=False):
    """A textured quad from four (x, y, z) points, UV'd across `rect`."""
    u0, v0, u1, v1 = rect
    uv = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    if flip:
        uv = [(u1, v1), (u0, v1), (u0, v0), (u1, v0)]
    m.add(Part(list(p), [(0, 1, 2), (0, 2, 3)], uv=uv), mat)


def uvblit(m, sub, wall, W, D, depth0=0.0):
    """`kit._blit` drops Part.uv and Part.colors -- this one keeps them."""
    for part, mat in sub._parts:
        v = []
        for (x, y, z) in part.verts:
            if wall == "n":
                v.append((x, y, depth0 + z))
            elif wall == "s":
                v.append((W - x, y, D - depth0 - z))
            elif wall == "w":
                v.append((depth0 + z, y, D - x))
            else:
                v.append((W - depth0 - z, y, x))
        m._parts.append((Part(v, part.tris, part.smooth, part.colors,
                              part.uv), mat))


# ------------------------------------------------------------ 2-D triangulation
def _area2(p):
    s = 0.0
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        s += a[0] * b[1] - b[0] * a[1]
    return s


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _inside(a, b, c, p):
    return (_cross(a, b, p) >= 0 and _cross(b, c, p) >= 0
            and _cross(c, a, p) >= 0)


def earclip(poly):
    """Triangulate a simple CCW polygon.  Returns index triples."""
    n = len(poly)
    idx = list(range(n))
    if _area2(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4 * n * n:
        guard += 1
        for k in range(len(idx)):
            i0 = idx[k - 1]
            i1 = idx[k]
            i2 = idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if _cross(a, b, c) <= 1e-12:
                continue
            bad = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                if _inside(a, b, c, poly[j]):
                    bad = True
                    break
            if bad:
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            break
        else:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


# ------------------------------------------------------------------ sweeping
def sweep(m, prof, x0, x1, side_mat, body_mat, rect, edge_mats=None,
          shift=(0.0, 0.0)):
    """Extrude a CCW (z, y) profile between x0 and x1.

    The two flanks come out as single polygons carrying UVs into `rect` (so
    the printed side art is one quad's worth of data, not a strip grid), and
    the perimeter is a band of quads in `body_mat`.  `edge_mats` optionally
    overrides the material of edge i.
    """
    dz, dy = shift
    p = [(z + dz, y + dy) for (z, y) in prof]
    tris = earclip(p)
    zs = [q[0] for q in p]
    ys = [q[1] for q in p]
    z0, z1 = min(zs), max(zs)
    y0, y1 = min(ys), max(ys)
    u0, v0, u1, v1 = rect

    def uvof(z, y):
        return (u0 + (u1 - u0) * (z - z0) / max(1e-6, z1 - z0),
                v0 + (v1 - v0) * (y1 - y) / max(1e-6, y1 - y0))

    uv = [uvof(z, y) for (z, y) in p]
    # x0 flank: CCW in (z, y) gives a -x normal
    m.add(Part([(x0, y, z) for (z, y) in p], list(tris), smooth=True,
               uv=list(uv)), side_mat)
    n = len(p)
    rp = list(range(n))[::-1]
    inv = {v: k for k, v in enumerate(rp)}
    m.add(Part([(x1, p[i][1], p[i][0]) for i in rp],
               [tuple(inv[t] for t in tri) for tri in tris],
               smooth=True, uv=[uv[i] for i in rp]), side_mat)
    for i in range(n):
        za, ya = p[i]
        zb, yb = p[(i + 1) % n]
        mat = body_mat
        if edge_mats and i in edge_mats:
            mat = edge_mats[i]
        m.add(Part([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)],
                   [(0, 1, 2), (0, 2, 3)]), mat)


# ------------------------------------------------------------- noise tiles
def noise_tex(n, mean, sd, d1, seed=5, streak=0.0):
    """A seamless-ish grey tile: `sd` is the spread, `d1` the adjacent-pixel
    step (this project's scale-blind lesson -- sd alone metered plastic), and
    `streak` biases the correlation along x so a rug reads as directional nap.
    """
    rnd = Rnd(seed)
    row_bias = [rnd.f(-sd, sd) * 0.75 for _ in range(n)]
    out = []
    prev = None
    for y in range(n):
        row = []
        v = mean + row_bias[y]
        for x in range(n):
            v += rnd.f(-d1, d1)
            v += (mean + row_bias[y] - v) * (0.10 + 0.55 * (1.0 - streak))
            c = v
            if prev is not None:
                c = c * (1.0 - streak * 0.55) + prev[x] * (streak * 0.55)
            row.append(c)
        prev = row
        out.append([(_clamp8(c), _clamp8(c), _clamp8(c)) for c in row])
    return png_rgb(out)
