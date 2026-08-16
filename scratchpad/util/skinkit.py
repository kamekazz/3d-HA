"""Per-wall non-emissive albedo skins, generalised from the garage calibration.

Method (all four rooms of the utility set):

1. Meter the room's four walls on CLEAN fields with the room's own `wall_color`.
   That gives, per wall, wall_resp = linear(render) / linear(wall albedo).
2. A GLB skin on the same wall does NOT collect the same light.  Measured on the
   garage (skin placed, rendered, re-metered), the piece/wall response ratio is
       north 2.077   west 1.242   east 1.033   south 1.019
   -- i.e. ROOM-BRIEF's "a piece collects ~1.7x a wall" is only true for the
   sun-facing walls; on the two shaded ones a piece and a wall are within 3%.
   The ratios are a property of wall orientation, not of the room, so they carry
   from the garage to the laundry and the pantry.
3. Skin albedo per wall = target_linear / (wall_resp * ratio), clamped at white.

Each skin is ONE-SIDED, wound to face INTO the room, so it culls from outside
exactly like the wall it paints; roughness 0.95 matches the room wall; no
emissive anywhere.
"""
import urllib.request

from gkit import *   # noqa: F401,F403
import gkit as G
from roomkit.place import find_model, find_object

RATIO = {"n": 2.077, "w": 1.242, "e": 1.033, "s": 1.019}
INSET = 0.022


def s2l(u):
    u = u / 255.0
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def l2s(v):
    v = max(0.0, min(1.0, v))
    u = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return int(round(u * 255))


def hexlum(hx):
    c = [s2l(int(hx[1 + 2 * i:3 + 2 * i], 16)) for i in range(3)]
    return c, 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def albedos(wall_hex, measured, target_srgb):
    """measured = {'n':..,'s':..,'e':..,'w':..} sRGB of the BARE wall."""
    c, lum = hexlum(wall_hex)
    T = s2l(target_srgb)
    out = {}
    for w, val in measured.items():
        r = (s2l(val) / lum) * RATIO[w]
        k = min(1.0 / (max(c) / lum), T / r) / lum
        out[w] = ("#%02x%02x%02x" % tuple(l2s(min(1.0, ch * k)) for ch in c),
                  l2s(min(T, r)))          # (hex, predicted sRGB)
    return out


def build(W, D, H, hexes, holes=None):
    holes = holes or {}
    m = Model()
    for wall in "nswe":
        mat = Material("skin_" + wall, hexes[wall], roughness=0.95,
                       double_sided=False)
        total = W if wall in "ns" else D
        hs = holes.get(wall, [])
        bands, cur = [], 0.0
        for (a, b, _y0, _y1) in sorted(hs):
            if a > cur:
                bands.append((cur, a, 0.0, H))
            cur = max(cur, b)
        if cur < total:
            bands.append((cur, total, 0.0, H))
        for (a, b, y0, y1) in hs:
            bands.append((a, b, y1, H))
        for (a, b, y0, y1) in bands:
            if b - a < 0.02 or y1 - y0 < 0.02:
                continue
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


def drop(room, name):
    o = find_object(room, name)
    if o:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/object/%d" % o["id"], method="DELETE"))
    mo = find_model(name)
    if mo:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/model/%d" % mo["id"], method="DELETE"))
