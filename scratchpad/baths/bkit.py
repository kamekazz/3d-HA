"""Furnishing-pass kit for the three bathrooms (rooms 16, 26, 23).

Builds on scratchpad/shellpass/kit.py (imported wholesale) and adds:

  * openings()      -- real cut openings via the API, idempotent by (edge, offset)
  * wall_skin()     -- per-wall NON-emissive albedo skin, all four walls
  * fit_skin()      -- solve a skin colour from a two-point probe
  * oval_face()     -- flat ellipse in a wall plane (mirrors)
  * tube()          -- a cylinder along an arbitrary axis (towel bars, rails)
  * rug()           -- soft bath mat + its own radial contact shadow

NO EMISSIVE on any room-scale run.  Only the downward ceiling plane and the
window panes carry emissive, both inherited from the shell pass.
"""
import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from kit import *                                                   # noqa: F401,F403
from kit import (Model, Material, box, rounded_box, cylinder, prism, quad,
                 sag_plane, torus, Part, place, bx, rect_down, rect_up,
                 disc_down, ring_down, spans, wall_band, ceiling, baseboards,
                 door_unit, cased_opening, window_unit, contact_shadow,
                 save_and_place, surfaces, mix, Rnd, R, _blit, panel_door,
                 TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT,
                 WHITEWD, DOORSHADE, BLACKMET, CHROME, GLASS, MARBLE,
                 TILEW, GROUT, PORC, BB_H, BB_T, CROWN_H, CASE_W, DOOR_TOP)

OUT = os.path.dirname(os.path.abspath(__file__))
BASE = "http://127.0.0.1:5000"


# --------------------------------------------------------------- placement
def save_here(name, m, room, fname=None):
    """save_and_place but writing into scratchpad/baths/glb."""
    path = os.path.join(OUT, "glb",
                        (fname or name.replace(" ", "_").replace(".", "").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    print(f"  {name:34s} {kb:7.1f} KB  size={size}  {res['action']}")
    return {"name": name, "size_ft": list(size),
            "pos": [round(p, 3) for p in pos], "rot": 0, "kb": round(kb, 1)}


# ---------------------------------------------------------------- openings
def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read() or b"{}")


def room_record(room):
    house = _req("GET", "/api/house")
    for f in house["floors"]:
        for r in f["rooms"]:
            if r["id"] == room:
                return r
    raise SystemExit(f"room {room} not found")


def openings(room, want):
    """want = [(type, edge_index, offset, width, elevation, height), ...]

    Rect edge order in house.js: 0 = N (offset from x=0, ascending),
    1 = E (from z=0 asc), 2 = S (from x=W, descending), 3 = W (from z=D desc).
    Matched by (edge, nearest offset) so re-runs update rather than stack.
    """
    have = list(room_record(room).get("openings", []))
    for (t, e, off, w, el, h) in want:
        body = {"type": t, "edge_index": e, "offset": off, "width": w,
                "elevation": el, "height": h}
        hit = None
        for o in have:
            if o["edge_index"] == e and abs(o["offset"] - off) < 1.2 \
                    and not o.get("_used"):
                hit = o
                break
        if hit:
            hit["_used"] = True
            _req("PATCH", f"/api/house/opening/{hit['id']}", body)
            print(f"  opening patched {hit['id']:4d} {t:8s} edge {e} off {off:5.2f} w {w:4.2f}")
        else:
            _req("POST", f"/api/house/room/{room}/opening", body)
            print(f"  opening added       {t:8s} edge {e} off {off:5.2f} w {w:4.2f}")
    # drop any leftovers this build did not claim
    for o in have:
        if not o.get("_used"):
            _req("DELETE", f"/api/house/opening/{o['id']}")
            print(f"  opening removed {o['id']} (stale)")


# -------------------------------------------------------------- wall skins
def wall_skin(m, wall, W, D, color, y0, y1, holes=(), inset=0.028, rough=0.95,
              grad=0.085, nband=9):
    """A plain NON-emissive albedo skin over one whole wall face.

    Not the rejected emissive "wall wash": no emissive, and it covers the wall
    corner to corner so there is no hard rectangular edge.  roughness matches
    the room wall's 0.95 so the seam under the crown does not show.
    holes = [(a0, a1, y0, y1), ...] in the wall's own axis.

    `grad` adds a gentle VERTICAL value ramp, +-grad about the solved albedo,
    peaking around 62% of the wall height and falling off toward the skirting
    and the crown.  One flat quad metered sd 2.7-4.6 against the photographs'
    8.3-15.0: a real wall is never one value, it darkens into the floor line and
    under the crown.  This is not emissive and it is not a rectangle painted on
    part of the wall -- it is the same corner-to-corner skin, subdivided.  The
    step between adjacent bands is under 2 levels at these values, which is
    below where banding becomes visible.
    """
    def _f(t):
        if grad <= 0:
            return 1.0
        # dark at the skirting, peak at ~0.62 height, easing back under the crown
        return (1.0 + grad * (2.0 * math.sin(math.pi * 0.5
                                             * min(t / 0.62, 1.0) ** 0.9) - 1.0)
                - grad * 0.55 * max(0.0, (t - 0.62) / 0.38) ** 1.6)

    # keep the AVERAGE albedo exactly where the two-point fit put it, so the
    # ramp adds variation without moving the wall's metered mean
    _norm = sum(_f((i + 0.5) / nband) for i in range(nband)) / nband

    def mat_at(yc):
        f = _f((yc - y0) / max(y1 - y0, 1e-6)) / _norm
        c = "#%02x%02x%02x" % tuple(
            min(255, max(0, int(round(int(color.lstrip("#")[i:i + 2], 16) * f))))
            for i in (0, 2, 4))
        return Material("skin" + c.lstrip("#"), c, roughness=rough,
                        metallic=0.0, double_sided=False)

    # ONE-SIDED, wound to face into the room.  A solid box here shows its back
    # from the dollhouse camera -- the two camera-side room walls are culled but
    # a placed object never is, so a dark skin reads as a slab in mid-air.
    total = W if wall in "ns" else D
    bands = [(y0, y1, [])]
    for (a0, a1, hy0, hy1) in holes:
        nb = []
        for (b0, b1, hs) in bands:
            if hy1 <= b0 or hy0 >= b1:
                nb.append((b0, b1, hs))
                continue
            if b0 < hy0:
                nb.append((b0, hy0, list(hs)))
            nb.append((max(b0, hy0), min(b1, hy1), list(hs) + [(a0, a1)]))
            if b1 > hy1:
                nb.append((hy1, b1, list(hs)))
        merged = {}
        for (b0, b1, hs) in [b for b in nb if b[1] - b[0] > 0.01]:
            merged.setdefault((round(b0, 4), round(b1, 4)), []).extend(hs)
        bands = [(k[0], k[1], v) for k, v in merged.items()]
    steps = [y0 + (y1 - y0) * i / nband for i in range(nband + 1)]
    for (b0, b1, hs) in bands:
        cuts = sorted({b0, b1} | {s for s in steps if b0 < s < b1})
        for (c0, c1) in zip(cuts, cuts[1:]):
            mat = mat_at((c0 + c1) / 2.0)
            for (a, b) in spans(total, hs):
                if wall == "n":
                    z = inset
                    m.add(quad((a, c0, z), (b, c0, z), (b, c1, z), (a, c1, z)),
                          mat)
                elif wall == "s":
                    z = D - inset
                    m.add(quad((b, c0, z), (a, c0, z), (a, c1, z), (b, c1, z)),
                          mat)
                elif wall == "w":
                    x = inset
                    m.add(quad((x, c0, b), (x, c0, a), (x, c1, a), (x, c1, b)),
                          mat)
                else:
                    x = W - inset
                    m.add(quad((x, c0, a), (x, c0, b), (x, c1, b), (x, c1, a)),
                          mat)


def fit_skin(probe_a, meter_a, probe_b, meter_b, target):
    """Two-point log-linear fit of rendered luminance vs authored 8-bit albedo.

    Returns the 8-bit channel value whose render meters `target`.  Measured off
    real renders (the analytic tone inverse stopped predicting after the
    daylight change -- ROOM-BRIEF).
    """
    la, lb = math.log(max(meter_a, 1.0)), math.log(max(meter_b, 1.0))
    ga, gb = math.log(max(probe_a, 1.0)), math.log(max(probe_b, 1.0))
    if abs(la - lb) < 1e-6:
        return probe_a
    k = (ga - gb) / (la - lb)
    g = ga + k * (math.log(max(target, 1.0)) - la)
    return int(round(min(255.0, max(0.0, math.exp(g)))))


def grey(v):
    v = int(round(min(255, max(0, v))))
    return "#%02x%02x%02x" % (v, v, v)


def tint(v, warm=1.0, cool=1.0):
    """Neutral-ish paint: v is the mid channel."""
    r = int(round(min(255, max(0, v * warm))))
    g = int(round(min(255, max(0, v))))
    b = int(round(min(255, max(0, v * cool))))
    return "#%02x%02x%02x" % (r, g, b)


# ---------------------------------------------------------------- geometry
def oval_face(m, mat, plane, cu, cv, ru, rv, w, facing, seg=30):
    """A flat ellipse standing in a wall plane.

    plane 'xy' -> in the x/y plane at z = w  (north/south walls)
    plane 'zy' -> in the z/y plane at x = w  (east/west walls)
    facing: +1 or -1, the axis direction the face must point.
    """
    pts = []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        pts.append((cu + ru * math.cos(t), cv + rv * math.sin(t)))
    if plane == "xy":
        v = [(cu, cv, w)] + [(u, vv, w) for (u, vv) in pts]
    else:
        v = [(w, cv, cu)] + [(w, vv, u) for (u, vv) in pts]
    # fan; pick the winding that points at `facing`
    fwd = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    rev = [(0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)]
    n = _tri_normal(v[0], v[fwd[0][1]], v[fwd[0][2]])
    ax = 2 if plane == "xy" else 0
    m.add(Part(v, fwd if (n[ax] * facing) > 0 else rev), mat)


def oval_ring(m, mat, plane, cu, cv, ru, rv, t, w0, w1, seg=30):
    """The frame round an oval_face -- a thin extruded elliptical band."""
    v, tris = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for (rr, ww) in (((ru, rv), w0), ((ru + t, rv + t), w0),
                         ((ru + t, rv + t), w1), ((ru, rv), w1)):
            u = cu + rr[0] * math.cos(a)
            vv = cv + rr[1] * math.sin(a)
            v.append((u, vv, ww) if plane == "xy" else (ww, vv, u))
    for i in range(seg):
        a = 4 * i
        b = 4 * ((i + 1) % seg)
        for k in range(4):
            k2 = (k + 1) % 4
            tris += [(a + k, b + k, b + k2), (a + k, b + k2, a + k2)]
    m.add(Part(v, tris, smooth=True), mat)


def _tri_normal(a, b, c):
    u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    return (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
            u[0] * w[1] - u[1] * w[0])


def _ring(y, rx, rz, seg, n):
    out = []
    for k in range(seg):
        t = 2 * math.pi * k / seg
        ct, st = math.cos(t), math.sin(t)
        out.append((rx * math.copysign(abs(ct) ** (2.0 / n), ct), y,
                    rz * math.copysign(abs(st) ** (2.0 / n), st)))
    return out


def sweep_shell(levels, seg=28, n=2.3, cap_bottom=True, inward=False):
    """A smooth swept surface through `levels` = [(y, rx, rz), ...].

    Stacking rounded_box slabs to fake a flared tub terraces visibly at eye
    height -- this is one continuous surface instead.
    """
    verts, tris = [], []
    for (y, rx, rz) in levels:
        verts += _ring(y, rx, rz, seg, n)
    for i in range(len(levels) - 1):
        for k in range(seg):
            a, b = i * seg + k, i * seg + (k + 1) % seg
            c, d = (i + 1) * seg + k, (i + 1) * seg + (k + 1) % seg
            tris += ([(a, b, c), (b, d, c)] if inward
                     else [(a, c, b), (b, c, d)])
    if cap_bottom:
        verts.append((0.0, levels[0][0], 0.0))
        ci = len(verts) - 1
        for k in range(seg):
            tris.append((ci, (k + 1) % seg, k) if inward else (ci, k, (k + 1) % seg))
    return Part(verts, tris, smooth=True)


def oval_tub(m, mat, inner_mat, cx, cz, w, l, h, wall=0.20, seg=30):
    """Freestanding oval soaker: one continuous flared outer skin, a flat rim,
    an inward-facing basin and a basin floor."""
    N = 9
    lv = []
    for i in range(N):
        t = i / (N - 1.0)
        f = math.sin(math.pi / 2 * (t ** 0.50))
        lv.append((t * h, (0.545 + 0.455 * f) * w / 2,
                   (0.575 + 0.425 * f) * l / 2))
    m.add(sweep_shell(lv, seg=seg), mat, at=(cx, 0.0, cz))
    # rim: a flat annulus between the outer top ring and the basin lip
    o = _ring(h, w / 2, l / 2, seg, 2.3)
    i_ = _ring(h, w / 2 - wall, l / 2 - wall, seg, 2.3)
    v = [(p[0] + cx, p[1], p[2] + cz) for p in o] + \
        [(p[0] + cx, p[1], p[2] + cz) for p in i_]
    t = []
    for k in range(seg):
        a, b = k, (k + 1) % seg
        t += [(a, seg + a, b), (b, seg + a, seg + b)]
    m.add(Part(v, t, smooth=True), mat)
    # basin
    bl = []
    M = 5
    for i in range(M):
        u = i / (M - 1.0)
        g = math.sin(math.pi / 2 * ((1 - u) ** 0.55))
        bl.append((h - u * (h - 0.42), (w / 2 - wall) * (0.62 + 0.38 * g),
                   (l / 2 - wall) * (0.66 + 0.34 * g)))
    bl.reverse()
    m.add(sweep_shell(bl, seg=seg, cap_bottom=False, inward=True), inner_mat,
          at=(cx, 0.0, cz))
    b0 = bl[0]
    v = [(cx, b0[0], cz)] + [(p[0] + cx, b0[0], p[2] + cz)
                             for p in _ring(0, b0[1], b0[2], seg, 2.3)]
    m.add(Part(v, [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]),
          inner_mat)


def tube(m, mat, p0, p1, r, seg=10):
    """A cylinder between two 3-D points."""
    d = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in d)) or 1e-6
    part = cylinder(r, L, seg, anchor="base")
    # rotate +Y onto d:  rot_z then rot_y
    rz = math.atan2(math.hypot(d[0], d[2]), d[1])
    ry = math.atan2(d[0], d[2])
    # cylinder is along +Y; tilt by rz about Z then spin by ry about Y
    m.add(part, mat, at=p0, rot_z=-rz, rot_y=ry - math.pi / 2)


def bottle(m, mat, x, z, r, h, y=0.0, cap=None, seg=8):
    m.add(cylinder(r, h, seg), mat, at=(x, y, z))
    if cap:
        m.add(cylinder(r * 0.55, h * 0.13, seg), cap, at=(x, y + h, z))


_SH_PAL = {}
SHADOW_Y = 0.050        # see docstring: 0.018 still loses, 0.05 wins


def soft_shadow(m, cx, cz, rx, rz, floor=None, strength=0.62, spill=0.85,
                y=SHADOW_Y, steps=10, seg=26, n=2.7, room=None, tone="#121211"):
    """A smooth radial contact shadow: ONE coplanar layer of ALPHA-BLENDED
    concentric annuli.

    Three things had to be true at once and no earlier version had all three.

    1. It has to WIN THE DEPTH FIGHT.  The room slab is drawn with
       `polygonOffsetFactor -1` (house.js), which pulls it toward the camera in
       the depth buffer, so a decal laid just above it loses.  kit.contact_shadow
       sits at y=0.012 and 0.005-0.018 all z-fight into faint crescents; 0.05 is
       the height that clears it at dollhouse range.
    2. It must not be a BULLSEYE.  Round 2 stacked hard-edged rings and the
       critic called it worse than no shadow, so the annuli here are
       non-overlapping, 14 of them, on a smooth (1-u^2)^1.7 alpha ramp that
       reaches 0 at the rim -- there is no outer outline to see.
    3. It must not ERASE THE FLOOR.  The opaque-colour version this replaces
       painted `mix(floor_color, tone)` over the slab, which killed the plank
       texture and -- because the authored floor_color is lighter than the
       textured render -- left a *pale* disc round every piece.  Alpha over the
       real slab darkens whatever is under it and the planks read straight
       through.

    4. It must actually SPILL PAST THE PIECE.  This is what killed the previous
       attempt and it is easy to miss: `rx, rz` are the piece's own half-extents,
       so a ramp that runs 0 -> 1 across `rx` puts every dark ring UNDER the
       piece, where nothing can see it, and leaves the ring that is visible at
       alpha 0.03.  Here the core is a solid superellipse at the FOOTPRINT and
       the ramp happens over an extra `spill` FEET outside it -- so the shadow is
       full strength where the piece touches the floor and fades over ~0.6 ft,
       which is what a soft contact shadow looks like.

    `strength` is the alpha at the contact edge, so 0.58 is a 58% darkening
    there: a 15% darkening was measured invisible at dollhouse distance.
    `floor` is accepted and ignored (kept so old call sites still work).
    """
    def mat_for(a):
        key = (tone, round(a, 3))
        if key not in _SH_PAL:
            _SH_PAL[key] = Material("csh%d" % len(_SH_PAL), tone,
                                    roughness=0.99, metallic=0.0,
                                    opacity=round(max(a, 0.01), 3))
        return _SH_PAL[key]

    def ring_pts(gx, gz):
        out = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            px = cx + gx * math.copysign(abs(ct) ** (2.0 / n), ct)
            pz = cz + gz * math.copysign(abs(st) ** (2.0 / n), st)
            if room:
                px = min(max(px, 0.04), room[0] - 0.04)
                pz = min(max(pz, 0.04), room[1] - 0.04)
            out.append((px, y, pz))
        return out

    # solid core over the footprint -- visible under legs, plinths and rims
    prev = ring_pts(rx, rz)
    m.add(Part([(cx, y, cz)] + prev,
               [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)], smooth=True),
          mat_for(strength))
    for i in range(steps):
        t = (i + 1.0) / steps
        cur = ring_pts(rx + spill * t, rz + spill * t)
        v = prev + cur
        tris = []
        for k in range(seg):
            a, b = k, (k + 1) % seg
            tris += [(a, seg + b, seg + a), (a, b, seg + b)]
        # alpha at the OUTER edge of this band; smooth fall to 0 at rx+spill
        # exponent 1.15, not 1.5: at 1.5 almost all of the darkness lands in the
        # first band, which measures fine up close and reads as a 2 px OUTLINE
        # from the dollhouse camera (metered 15% darkening 10 px out -- the same
        # invisible-at-range failure a sibling room was rejected for)
        m.add(Part(v, tris, smooth=True), mat_for(strength * (1.0 - t) ** 1.15))
        prev = cur


def rug(m, x0, x1, z0, z1, color="#eceae6", pile=0.075, shadow=0.50):
    """A bath mat: puffy sagged pile, a slightly darker rolled edge so the
    silhouette is not a flat white rectangle, and its own radial shadow.

    The mat body starts just ABOVE the shadow plane so the two never fight; the
    shadow only shows where it spills past the mat's edge.
    """
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    rx, rz = (x1 - x0) / 2, (z1 - z0) / 2
    soft_shadow(m, cx, cz, rx, rz, strength=shadow, spill=0.72, n=3.6, steps=8)
    y0 = SHADOW_Y + 0.004
    RM = Material("rugm" + color.lstrip("#"), color, roughness=0.99)
    RE = Material("ruge" + color.lstrip("#"), mix(color, "#8d8a85", 0.34),
                  roughness=0.99)
    bx(m, RE, x0, x1, y0, y0 + 0.042, z0, z1)                # rolled edge
    m.add(sag_plane(x1 - x0 - 0.10, z1 - z0 - 0.10, sag=-pile, nx=6, nz=6,
                    y=0.0, edge_drop=0.016), RM, at=(cx, y0 + 0.042, cz))


# ------------------------------------------------------- tiled wall faces
def tile_face(m, mat, plane, w, a0, a1, y0, y1, tw, th, gap=0.028,
              stagger=0.5, facing=1, jitter=None):
    """Rows of flat tile QUADS standing proud of a grout plane.

    Boxes cost 24 verts a tile and a subway wall is ~150 tiles; a quad costs 4
    and the grout line is the gap between them, which is all the eye reads at
    dollhouse range.  `plane` 'xy' -> face at z = w (n/s walls); 'zy' -> at x = w.
    `facing` +1/-1 is the axis direction the tile face must point.
    """
    rows = int((y1 - y0) / th) + 1
    for r in range(rows):
        yy0 = y0 + r * th
        yy1 = min(yy0 + th - gap, y1)
        if yy1 - yy0 < 0.02:
            continue
        off = (stagger * tw) if (r % 2) else 0.0
        a = a0 - off
        while a < a1:
            ta0, ta1 = max(a, a0), min(a + tw - gap, a1)
            a += tw
            if ta1 - ta0 < 0.04:
                continue
            c = mat if jitter is None else jitter(r, ta0)
            if plane == "xy":
                p = [(ta0, yy0, w), (ta1, yy0, w), (ta1, yy1, w), (ta0, yy1, w)]
                if facing < 0:
                    p = p[::-1]
            else:
                p = [(w, yy0, ta0), (w, yy0, ta1), (w, yy1, ta1), (w, yy1, ta0)]
                if facing > 0:
                    p = p[::-1]
            m.add(quad(*p), c)


def hex_pan(m, mat, grout, x0, x1, z0, z1, y, r=0.135, gap=0.022):
    """Hexagon mosaic floor, as flat hex quads over a grout plane."""
    rect_down(m, grout, x0, x1, y, z0, z1)
    dx = r * 1.732
    dz = r * 1.5
    row = 0
    z = z0 + r
    while z < z1 + r:
        x = x0 + (dx / 2 if row % 2 else 0) + dx / 2
        while x < x1 + dx:
            pts, ok = [], True
            for k in range(6):
                a = math.pi / 6 + k * math.pi / 3
                px = x + (r - gap) * math.cos(a)
                pz = z + (r - gap) * math.sin(a)
                if not (x0 - 0.01 <= px <= x1 + 0.01 and z0 - 0.01 <= pz <= z1 + 0.01):
                    ok = False
                pts.append((min(max(px, x0), x1), y + 0.004, min(max(pz, z0), z1)))
            if ok:
                m.add(Part([(x, y + 0.004, z)] + pts,
                           [(0, 1 + (k + 1) % 6, 1 + k) for k in range(6)]), mat)
            x += dx
        z += dz
        row += 1
