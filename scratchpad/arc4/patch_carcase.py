# -*- coding: utf-8 -*-
"""Per-machine carcase / T-molding colour.

`sweep()` extrudes the side profile and gives every perimeter quad `body_mat`.
Those quads are the cabinet's TOP, BACK and FRONT faces -- and because the
printed front panel is drawn 0.08 ft inset and 0.008 proud, what shows of the
front face is a strip down each vertical edge: the T-molding.  Round 3 passed
one black `CABBLK` for all sixteen machines, so the loudest identifying colour
in the photographs (Turtles' grass-green molding, Pac-Man's yellow body, Star
Wars' yellow carcase, Time Crisis' red body) was thrown away.

Material colour only.  No geometry, no positions, no profile changes.
"""
import io
import os

BS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "bsmt")

# ---------------------------------------------------------------- a2kit.py
P = os.path.join(BS, "a2kit.py")
s = io.open(P, encoding="utf-8").read()

BLOCK = '''

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
'''
anchor = "\n\nclass ArtSet(object):"
assert s.count(anchor) == 1
s = s.replace(anchor, BLOCK + anchor)

old = """        self.BEZEL = Material("a2bez_" + name, "#15151a", roughness=0.50)
        self._mq = {}
"""
new = """        self.BEZEL = Material("a2bez_" + name, "#15151a", roughness=0.50)
        self._mq = {}
        self._cc = {}
"""
assert s.count(old) == 1
s = s.replace(old, new)

old = """    def marquee(self, slug):"""
new = """    def carcase(self, slug):
        if slug not in self._cc:
            self._cc[slug] = Material("a2cc_" + slug, CARCASE[slug],
                                      roughness=0.55)
        return self._cc[slug]

    def marquee(self, slug):"""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8").write(s)

# ------------------------------------------------------------------ ar2.py
P = os.path.join(BS, "ar2.py")
s = io.open(P, encoding="utf-8").read()
old = "    sweep(sub, prof, x0, x1, art.ART, CABBLK, art.uv(slug + \".side\"))"
new = ("    sweep(sub, prof, x0, x1, art.ART, art.carcase(slug),\n"
       "          art.uv(slug + \".side\"))")
assert s.count(old) == 1
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8").write(s)
print("carcase colours wired")
