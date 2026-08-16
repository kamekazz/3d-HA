"""Circulation-rooms kit -- shared helpers for rooms 12, 17 and 27.

Imports the shell-pass kit (scratchpad/shellpass/kit.py) for the ceiling /
baseboard / door / contact-shadow primitives that were already proven, and adds
what a furnishing round for a HALLWAY needs on top:

  * `openings(room, want)`   -- idempotent real cut openings through the normal
                                /api/house/room/<id>/opening endpoints.
  * `wall_skin` / `skins`    -- per-wall NON-emissive albedo skins (ROOM-BRIEF
                                option 2), holes punched round every cut opening
                                so a skin never paints over a doorway.
  * `stair_dress`            -- treads / risers / stringer laid over the app's
                                own stair mesh (buildStairs in house.js), which
                                is a plain blue-grey stepped box.
  * `raked`                  -- a run of boxes swept along the stair rake, used
                                for the handrail and the skirt board.  Authored
                                as ONE rotated box per segment with the segments
                                overlapping, so the rail reads continuous.

Room-local feet everywhere.  Nothing here is emissive except what kit.py's
ceiling plane already carried.
"""

import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")

from kit import *                                              # noqa: F401,F403
from kit import _blit, _oriented                               # noqa: F401
from roomkit.glb import Part                                   # noqa: F401

BASE = "http://127.0.0.1:5000"
OUT = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ placement
def save_and_place(name, m, room, fname=None):
    """kit.save_and_place, but writing into scratchpad/circ/glb."""
    path = os.path.join(OUT, "glb",
                        (fname or name.replace(" ", "_").replace(".", "").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:34s} size={size}  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})"
          f"  {kb:7.1f} KB  {res['action']}")
    return {"name": name, "kb": round(kb, 1)}


# ------------------------------------------------------------------- openings
def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        txt = resp.read()
        return json.loads(txt) if txt.strip() else {}


def room_row(room_id):
    house = _req("GET", "/api/house")
    for f in house["floors"]:
        for r in f["rooms"]:
            if r["id"] == room_id:
                return r
    raise SystemExit(f"no room {room_id}")


def openings(room_id, want):
    """Reconcile room `room_id`'s openings to exactly `want`.

    want: [(type, edge_index, offset, width, elevation, height), ...]
    Matches existing rows by (edge, offset within 1.2 ft) so a re-run PATCHes
    instead of stacking, and deletes anything left over.
    """
    room = room_row(room_id)
    have = list(room.get("openings", []))
    used = set()
    for (t, e, off, w, el, h) in want:
        body = {"type": t, "edge_index": e, "offset": round(off, 3),
                "width": round(w, 3), "elevation": round(el, 3),
                "height": round(h, 3)}
        hit = None
        for o in have:
            if o["id"] in used or o["edge_index"] != e:
                continue
            if abs(o["offset"] - off) < 1.2:
                hit = o
                break
        if hit:
            used.add(hit["id"])
            _req("PATCH", f"/api/house/opening/{hit['id']}", body)
            print(f"    patched {hit['id']:>4}  {body}")
        else:
            r = _req("POST", f"/api/house/room/{room_id}/opening", body)
            used.add(r.get("id"))
            print(f"    added   {r.get('id'):>4}  {body}")
    for o in have:
        if o["id"] not in used:
            _req("DELETE", f"/api/house/opening/{o['id']}")
            print(f"    deleted {o['id']}")
    return room_row(room_id).get("openings", [])


def blit(m, sub, wall, W, D, depth0=0.0):
    """kit._blit, but taking a sub-model authored in ROOM-LOCAL axis order.

    _blit's 'n' and 'e' maps carry the wall-frame axis straight through, but its
    's' map lands at local x = W - x and its 'w' map at local z = D - x -- so a
    span authored as "local x 2.4..5.3" comes out mirrored on those two walls.
    (The shell pass hit exactly this: its west-wall casings were drawn at the
    mirror of the openings they were supposed to case.)  Mirror first, flip the
    winding to keep the determinant positive, then hand it over.
    """
    if wall in ("n", "e"):
        _blit(m, sub, wall, W, D, depth0)
        return
    total = W if wall == "s" else D
    tmp = Model()
    for part, mat in sub._parts:
        tmp._parts.append((Part([(total - x, y, z) for (x, y, z) in part.verts],
                                [(a, c, b) for (a, b, c) in part.tris],
                                part.smooth), mat))
    _blit(m, tmp, wall, W, D, depth0)


# ----------------------------------------------------------------- wall skins
def wall_skin(m, wall, W, D, color, y0, y1, holes=(), inset=0.026, rough=0.95):
    """A plain NON-emissive albedo skin over one whole wall face.

    holes: [(a0, a1, hy0, hy1)] in the wall's own axis (x for n/s, z for w/e).
    """
    mat = Material("skin" + color.lstrip("#"), color, roughness=rough,
                   metallic=0.0)
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
        bands = [b for b in nb if b[1] - b[0] > 0.01]
        merged = {}
        for (b0, b1, hs) in bands:
            merged.setdefault((round(b0, 4), round(b1, 4)), []).extend(hs)
        bands = [(k[0], k[1], v) for k, v in merged.items()]
    for (b0, b1, hs) in bands:
        for (a, b) in spans(total, hs):
            if wall == "n":
                bx(m, mat, a, b, b0, b1, inset, inset + 0.010)
            elif wall == "s":
                bx(m, mat, a, b, b0, b1, D - inset - 0.010, D - inset)
            elif wall == "w":
                bx(m, mat, inset, inset + 0.010, b0, b1, a, b)
            else:
                bx(m, mat, W - inset - 0.010, W - inset, b0, b1, a, b)


# ---------------------------------------------------------------- stair rake
def raked(m, mat, x0, x1, z_bot, z_top, y_bot, y_top, thick, extend=0.0,
          sink=0.0):
    """ONE continuous raked bar whose centre line runs (z_bot,y_bot)->(z_top,y_top).

    The shell pass drew the handrail as 34 separate boxes stepped along the
    flight, which reads as a chain of disconnected blocks.  A single box rotated
    about X by the rake angle is both cheaper and continuous.
    `thick` is the bar's depth perpendicular to the rake, `extend` lengthens
    both ends along it, `sink` drops the centre line vertically (a skirt board
    whose TOP follows the rake).
    """
    dz = z_bot - z_top
    dy = y_top - y_bot
    L = math.hypot(dz, dy) + 2.0 * extend
    ang = math.atan2(dy, dz)
    m.add(box(x1 - x0, thick, L, anchor="center"), mat,
          at=((x0 + x1) / 2.0, (y_bot + y_top) / 2.0 - sink,
              (z_bot + z_top) / 2.0), rot_x=ang)


def stair_dress(m, x0, x1, z_bot, z_top, steps, rise, tread_mat, riser_mat,
                runner_mat=None, runner_w=None, nose=0.06, skirt=None):
    """Lay treads, risers and (optionally) a runner over the app's stair mesh.

    The app builds each step as a solid box from y=0 to h_i, so only the top
    face and the riser face of the NEXT step are ever visible.  Everything here
    sits 0.012 ft proud of those faces.
    """
    run = abs(z_bot - z_top)
    tr = run / steps
    for i in range(steps):
        h = rise * (i + 1) / steps
        zb = z_bot - i * tr            # this step's south (low) edge
        za = z_bot - (i + 1) * tr      # its north (high) edge
        # NOTHING here may be COPLANAR with the app's own step boxes or the two
        # faces z-fight into a diagonal moire across the whole flight.  Every
        # back face below is pushed 0.002-0.05 ft INTO the solid step behind it.
        bx(m, tread_mat, x0, x1, h - 0.012, h + 0.030, za - 0.050, zb + nose)
        if runner_mat and runner_w:
            cx = (x0 + x1) / 2
            bx(m, runner_mat, cx - runner_w / 2, cx + runner_w / 2,
               h + 0.022, h + 0.082, za - 0.040, zb + nose)
        if i < steps - 1:
            h2 = rise * (i + 2) / steps
            bx(m, riser_mat, x0, x1, h + 0.030, h2 - 0.012, za - 0.034, za - 0.002)
            if runner_mat and runner_w:
                cx = (x0 + x1) / 2
                bx(m, runner_mat, cx - runner_w / 2, cx + runner_w / 2,
                   h + 0.030, h2 - 0.012, za - 0.070, za - 0.030)
    # bottom riser
    bx(m, riser_mat, x0, x1, 0.0, rise / steps - 0.012,
       z_bot - 0.002, z_bot + 0.030)
    if runner_mat and runner_w:
        cx = (x0 + x1) / 2
        bx(m, runner_mat, cx - runner_w / 2, cx + runner_w / 2, 0.0,
           rise / steps - 0.012, z_bot + 0.006, z_bot + 0.062)
    if skirt:                              # (side, thickness, board depth)
        side, st, dep = skirt
        sx0, sx1 = (x1 - st, x1) if side == "e" else (x0, x0 + st)
        raked(m, TRIM, sx0, sx1, z_bot, z_top, rise / steps, rise,
              dep, extend=0.35, sink=dep * 0.5 - 0.10)


# --------------------------------------------------------------------- extras
def plant_stand(m, cx, cz, r, h, mat):
    """A black wire plant stand: a hoop foot, three legs and a top ring."""
    # torus() is already built in the XZ plane -- rotating it would stand the
    # hoop on edge and blow the piece's bounding box open.
    m.add(torus(r, 0.028), mat, at=(cx, 0.03, cz))
    m.add(torus(r * 0.82, 0.028), mat, at=(cx, h, cz))
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        m.add(cylinder(0.030, h, 6), mat,
              at=(cx + r * 0.9 * math.cos(a), 0.0, cz + r * 0.9 * math.sin(a)))


def leafy(m, cx, cy, cz, spread, height, mat, n=9, seed=7, leaf=0.30):
    """A cheap houseplant: `n` tapered blades fanning out of a pot."""
    rn = Rnd(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rn.f(-0.3, 0.3)
        lean = rn.f(0.35, 1.0)
        hh = height * rn.f(0.6, 1.0)
        tip = (cx + spread * lean * math.cos(a), cy + hh,
               cz + spread * lean * math.sin(a))
        mid = ((cx + tip[0]) / 2 + leaf * 0.2, cy + hh * 0.55, (cz + tip[2]) / 2)
        w = leaf * rn.f(0.7, 1.2)
        v = [(cx - w / 2, cy, cz), (cx + w / 2, cy, cz),
             (mid[0] + w / 2, mid[1], mid[2]), (mid[0] - w / 2, mid[1], mid[2]),
             (tip[0], tip[1], tip[2])]
        tris = [(0, 1, 2), (0, 2, 3), (3, 2, 4)]
        m.add(Part(v, tris, smooth=True), mat)
