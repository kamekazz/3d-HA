# -*- coding: utf-8 -*-
"""Round 4: replace a2kit's 16-tile motif atlas with per-run ArtSets."""
import io
import os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "bsmt", "a2kit.py")
s = io.open(P, encoding="utf-8").read()

HEAD = '''"""Round-3/4 additions for room 2 (Arcade).  Texture + swept-profile helpers.

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

'''

MID = '''import math
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
# a high strength washes the printed title away -- the lit marquees sit at
# 0.85-1.15 and the ones the photos show dark sit at 0.22-0.40.
MARQUEE = {
    # ---- east wall
    # turned ~40 deg off the wall, head cropped or facing away; not lit
    "star-wars-atari":            ("#3a3226", 0.22),
    # full-bleed painted art, "reads dim, not brightly lit"
    "marvel-super-heroes":        ("#6e5a48", 0.50),
    # character-battle illustration in reds, blues and oranges
    "marvel-vs-capcom":           ("#b8724e", 0.70),
    # navy-to-black ground behind the pale dragon roundel
    "mortal-kombat":              ("#8fa2d0", 0.80),
    # lit cream/tan band -- one of the two most legible marquees in the room
    "nba-jam":                    ("#f0e2bc", 1.10),
    # printed art panel, green title over a New York street
    "tmnt-turtles-in-time":       ("#cfd4a8", 0.85),
    # the slot the photographs show empty -- see the roster
    "east-7-no-machine":          ("#3c4048", 0.30),
    # ---- south wall
    # a BLACK band with silver italic type; it must not glow green
    "legends-ultimate":           ("#59616f", 0.55),
    # dark navy ground, value unresolved in every frame
    "street-fighter-2-champion-edition": ("#4a6ab0", 0.85),
    # pale gold/cream ground, lit
    "time-crisis":                ("#e6d5a4", 1.05),
    # black ground, chrome type only
    "terminator-2":               ("#8f95a8", 0.60),
    # yellow band with dark type
    "ridge-racer":                ("#f0dc78", 1.00),
    # ---- north wall
    # "does NOT read as lit"; pale abstract lettering on near-black
    "north-1-graffiti-multicade": ("#3c3f48", 0.28),
    # white ground, yellow bubble caps -- the brightest object in the run
    "pac-man":                    ("#fff0c8", 1.15),
    # near-black/navy, chrome italic caps; not lit
    "nfl-blitz":                  ("#4a4a58", 0.40),
    # photographic golf-course scene, lit
    "golden-tee-3d-golf":         ("#a8c88a", 1.05),
}

# Which deck material each machine's printed control panel was authored for.
# The four art agents did not author to one exposure.  A control deck faces UP
# and an up-facing surface in this scene collects roughly twice what a vertical
# one does, so `ART_DK` (#4c4c4c) is the default -- but TMNT's brick street and
# the Marvel decks are bright printed art that ART_DK crushes to mud, and
# Marvel vs Capcom's is a genuinely pale silver panel.
DECK_MAT = {
    "tmnt-turtles-in-time": "D",
    "marvel-super-heroes": "D",
    "time-crisis": "D",
    "marvel-vs-capcom": "M",
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
        self._mq = {}

    def uv(self, key):
        return self.atlas.uv(key)

    def has(self, key):
        return key in self.atlas

    def kb(self):
        return len(self.atlas.png) / 1024.0

    def deck(self, slug):
        return {"D": self.ART_D, "M": self.ART_DM}.get(
            DECK_MAT.get(slug), self.ART_DK)

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


'''

s = HEAD + s[s.index("import math"):]
s = s[:s.index("import math")] + MID + s[s.index("def uvq("):]

io.open(P, "w", encoding="utf-8").write(s)
print("patched", P)
