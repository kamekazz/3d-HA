"""Per-wall non-emissive albedo skins for the garage.

Metered EMPTY, this room's four walls rendered at
    north 233.1 (n=175k) / west 200.3 (245k) / east 167.9 (245k) / south 141.6 (16k)
-- a 91-byte spread, worse than the 50-80 ROOM-BRIEF calls the renderer's floor.
There is one sun and no bounce, so the fix allowed is "give each wall its own
albedo" (ROOM-BRIEF, "a known limit"): a plain painted plane, no emissive,
roughness matched to the room wall's 0.95, covering each wall corner to corner
so there is no rectangular edge.

Two things had to be measured rather than assumed:

1. ROOM-BRIEF says a GLB piece collects ~1.7x what a room wall of the same
   albedo does.  On these walls it is the other way round: a #b4b0a8 skin on the
   south wall metered 105.5 against the bare wall's 141.6 at #dad7d0, i.e. the
   piece response is 0.88x the wall's, not 1.7x.  (The 1.7x note was measured on
   a ceiling; it does not carry to a vertical wall facing away from the sun.)
2. Because of that, the brightest reachable value on the SOUTH wall is a pure
   white skin, so the common target has to be set by the south wall, not by the
   room average.

Each skin is ONE-SIDED and wound to face INTO the room, so it culls from outside
exactly like the wall it paints -- a double-sided plane would stand up as an
opaque sheet in the dollhouse view where the wall itself is culled.
"""
import json
import urllib.request

from gkit import *   # noqa: F401,F403
import gkit as G
from roomkit.place import find_model, find_object

ROOM = 7
W, D, H = 20.4, 21.7, 9.0
T = 0.4564            # common target, LINEAR luminance (= 180 sRGB)
INSET = 0.022

# MEASURED response of a skin on each wall: linear render / linear albedo.
# Round 1 skinned the walls with a guessed model, rendered, and metered clean
# fields (sd = 0.0 on three of the four); these are the numbers that came back:
#   n #7f7d79 -> 185.1 (n=127500)   w #94928d -> 146.1 (n=38950)
#   e #e9e6de -> 177.8 (n=59800)     s #fffcf3 -> 167.5 (n=4800)
RESP = {"n": 2.448, "w": 1.059, "e": 0.5836, "s": 0.3996}
WALL_HEX = "#dad7d0"

# openings to leave uncovered (wall -> [(a0, a1, y0, y1)] along that wall's axis)
HOLES = {"n": [(2.30, 6.75, 0.0, 7.15)],                 # person door to laundry
         "s": [(1.60, 18.80, 0.0, 8.20)]}                # sectional door


def s2l(u):
    u = u / 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    u = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return int(round(u * 255))


def skin_hex(wall):
    """Albedo that lands this wall on the common target T (clamped at white).

    The SOUTH wall cannot reach 180: even a pure-white skin only measures 159
    there, so it is left at white and reported as the one wall that misses.
    """
    wl = [s2l(int(WALL_HEX[1 + 2 * i:3 + 2 * i], 16)) for i in range(3)]
    lum = 0.2126 * wl[0] + 0.7152 * wl[1] + 0.0722 * wl[2]
    k = min(1.0 / (max(wl) / lum), T / RESP[wall]) / lum
    return "#%02x%02x%02x" % tuple(l2s(min(1.0, c * k)) for c in wl)


def spans(total, holes):
    out, cur = [], 0.0
    for a, b in sorted(holes):
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if cur < total:
        out.append((cur, total))
    return [(a, b) for a, b in out if b - a > 0.02]


def skins():
    m = Model()
    for wall in "nswe":
        hx = skin_hex(wall)
        mat = Material("skin_" + wall, hx, roughness=0.95, double_sided=False)
        total = W if wall in "ns" else D
        hs = HOLES.get(wall, [])
        bands = []
        top = max([h[3] for h in hs], default=0.0)
        for (a, b) in spans(total, [(h[0], h[1]) for h in hs]):
            bands.append((a, b, 0.0, H))
        if hs:
            bands.append((min(h[0] for h in hs), max(h[1] for h in hs), top, H))
        for (a, b, y0, y1) in bands:
            if wall == "n":
                Z = INSET
                m.add(quad((a, y0, Z), (b, y0, Z), (b, y1, Z), (a, y1, Z)), mat)
            elif wall == "s":
                Z = D - INSET
                m.add(quad((a, y0, Z), (a, y1, Z), (b, y1, Z), (b, y0, Z)), mat)
            elif wall == "w":
                X = INSET
                m.add(quad((X, y0, b), (X, y0, a), (X, y1, a), (X, y1, b)), mat)
            else:
                X = W - INSET
                m.add(quad((X, y0, a), (X, y0, b), (X, y1, b), (X, y1, a)), mat)
    return m


def drop(name):
    for path, finder in (("object", None), ("model", None)):
        pass
    o = find_object(ROOM, name)
    if o:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/object/%d" % o["id"], method="DELETE"))
    mo = find_model(name)
    if mo:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/model/%d" % mo["id"], method="DELETE"))
    print("  dropped %s (%s / %s)" % (name, bool(o), bool(mo)))


if __name__ == "__main__":
    drop("Garage Wall Wash South")
    for w in "nswe":
        print("   %s skin %s" % (w, skin_hex(w)))
    G.save_and_place("Garage Wall Wash", skins(), ROOM)
