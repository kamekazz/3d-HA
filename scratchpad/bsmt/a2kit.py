"""Round-3 additions for room 2 (Arcade).  Texture + swept-profile helpers.

Round 2's cabinets were seven boxes with the hue swapped: every zone a flat
untextured colour field and a control deck that projected 0.06 ft.  Two things
fix that and both live here:

  * `ART_TEX` -- one procedurally printed RGB atlas (4x4 tiles).  `glb.Material`
    gained `tex=` this run, so printed side art / front art / marquee titles are
    now a UV into a shared image instead of a colour block.  One image, shared
    by byte-identity across every material that uses it, so a GLB carries it
    once however many materials sample it.
  * `sweep()` -- a cabinet is now a swept 2-D SIDE PROFILE, not a stack of
    boxes.  The profile carries the real silhouette (base, apron, the control
    deck jutting 0.70 ft proud, the raked screen, the marquee overhang, the
    top), the two flanks come out as one polygon each carrying the art UVs, and
    the perimeter band closes it.  ~150 verts a cabinet against ~850 for the
    box stack, which is what pays for the north wall.
"""

import math

from bkit import Model, Material, Part, Rnd, mix, box, cylinder   # noqa: F401
from roomkit.glb import png_rgb

TILE = 64
NCOL = 4
ATLAS = NCOL * TILE


# --------------------------------------------------------------- the atlas
def _clamp8(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def _hex(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _art_atlas():
    """16 printed panels.  0-11 are cabinet side/front graphics, 12-15 are
    marquee title bands.  Authored bright (mean ~236) so a material `color`
    near white lands the panel where the photo's printed vinyl does."""
    img = [[(0, 0, 0)] * ATLAS for _ in range(ATLAS)]
    specs = [
        # (ground, accent, ink, motif)
        ("#c2172a", "#f2d43a", "#12131a", 0),   # red/gold hero
        ("#173a8c", "#37c7f0", "#0c1020", 1),   # blue/cyan
        ("#0f7a3c", "#c9f24a", "#0a1410", 2),   # green
        ("#5a1a86", "#ff5ec4", "#120a1c", 0),   # purple/pink
        ("#c4531a", "#ffc85c", "#1a0f08", 1),   # orange
        ("#101318", "#3ad6ff", "#05070a", 2),   # black/cyan
        ("#8c1440", "#ffd9e6", "#150610", 0),   # maroon
        ("#1d6f86", "#ffe27a", "#08131a", 1),   # teal
        ("#d8b026", "#242a12", "#141200", 2),   # yellow (Pac-Man-ish)
        ("#2a2f38", "#e8eef6", "#0a0d12", 0),   # steel
        ("#8f2a12", "#ffb03a", "#180a04", 1),   # rust
        ("#123f2c", "#7ef0b0", "#06120c", 2),   # jade
        # marquees
        ("#e8e4dc", "#c2172a", "#141018", 3),
        ("#dfe8f4", "#173a8c", "#0e1220", 3),
        ("#f2e6c4", "#c4531a", "#1a1208", 3),
        ("#e4f0e6", "#0f7a3c", "#08140c", 3),
    ]
    for idx, (g, a, ink, motif) in enumerate(specs):
        col, row = idx % NCOL, idx // NCOL
        _paint(img, col * TILE, row * TILE, _hex(g), _hex(a), _hex(ink),
               motif, Rnd(17 + idx * 7))
    return png_rgb(img)


def _paint(img, ox, oy, g, a, ink, motif, rnd):
    for y in range(TILE):
        v = y / (TILE - 1.0)
        for x in range(TILE):
            u = x / (TILE - 1.0)
            if motif == 3:                                   # marquee band
                t = 0.5 + 0.5 * math.sin(u * 5.0 + 0.7)
                c = [g[k] + (a[k] - g[k]) * t * 0.55 for k in range(3)]
                if v < 0.13 or v > 0.87:
                    c = [ink[k] + (a[k] - ink[k]) * 0.35 for k in range(3)]
                elif 0.26 < v < 0.74:
                    # blocky title lettering
                    s = (u * 9.0) % 1.0
                    if s < 0.62 and not (0.44 < v < 0.52 and s > 0.42):
                        c = [ink[k] + (a[k] - ink[k]) * 0.10 for k in range(3)]
            else:
                # vertical ground gradient, dark at the foot
                t = 0.30 + 0.62 * (1.0 - v) ** 0.8
                c = [g[k] * t + 10 for k in range(3)]
                if v < 0.19:                                 # header strip
                    c = [a[k] * (0.75 + 0.25 * u) for k in range(3)]
                    s = (u * 8.0) % 1.0
                    if 0.12 < v < 0.15 or (s < 0.5 and 0.05 < v < 0.13):
                        c = list(ink)
                else:
                    # the printed "character": a big off-centre blob
                    cx, cy, rr = 0.47, 0.52, 0.29
                    d = math.hypot((u - cx) * 1.08, (v - cy) * 0.80) / rr
                    if motif == 1:
                        d = (abs(u - cx) * 1.5 + abs(v - cy) * 1.1) / rr
                    elif motif == 2:
                        d = max(abs(u - cx) * 1.6, abs(v - cy) * 0.90) / rr
                    if d < 1.0:
                        k = 1.0 - d
                        c = [c[j] + (a[j] - c[j]) * min(1.0, 0.35 + k * 1.6)
                             for j in range(3)]
                        if d < 0.46:
                            c = [c[j] + (240 - c[j]) * (0.46 - d) * 1.5
                                 for j in range(3)]
                        if 0.30 < d < 0.40:
                            c = [ci * 0.45 for ci in c]
                    # diagonal print streaks
                    if ((u * 2.7 + v * 1.9) * 6.0) % 1.0 < 0.16:
                        c = [ci * 1.13 + 7 for ci in c]
                    if v > 0.88:                              # foot logo bar
                        c = [ink[k] + (a[k] - ink[k]) * 0.42 for k in range(3)]
            # a 4x4 ordered dither rather than white noise: printed vinyl has
            # grain, but random noise on 16 tiles cost 140 KB of PNG where the
            # dither costs 12 -- and the payload cap is the binding constraint
            n = (_BAYER[y & 3][x & 3] - 7.5) * 0.90
            img[oy + y][ox + x] = tuple(
                _clamp8(round((ci + n) / 8.0) * 8) for ci in c)


ART_TEX = _art_atlas()
ART = Material("a2art", "#ffffff", roughness=0.68, tex=ART_TEX)
ART_D = Material("a2artd", "#c9c9c9", roughness=0.72, tex=ART_TEX)
# an UP-facing surface in this scene collects roughly twice what a
# vertical one does, so control-deck art needs a much darker factor
ART_DK = Material("a2artk", "#4c4c4c", roughness=0.80, tex=ART_TEX)
MQ_MATS = [Material("a2mqx%d" % i, "#d6d2ca", roughness=0.42, tex=ART_TEX,
                    emissive=c, emissive_strength=0.95)
           for i, c in enumerate(("#e8b878", "#7fb6e0", "#e09ec0", "#9ad8a8"))]


def uvr(i, inset=0.5):
    """The (u0, v0, u1, v1) rect of atlas tile `i`, half-texel inset."""
    col, row = i % NCOL, i // NCOL
    return ((col * TILE + inset) / ATLAS, (row * TILE + inset) / ATLAS,
            ((col + 1) * TILE - inset) / ATLAS, ((row + 1) * TILE - inset) / ATLAS)


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
