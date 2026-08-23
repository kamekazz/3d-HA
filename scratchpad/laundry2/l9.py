"""Laundry (room 9) -- the appliance wall, refitted to the room's REAL footprint.

WHY THIS EXISTS
---------------
`scratchpad/util/l_main.py` built this wall when room 9 was traced 11.0 x 5.7 ft
(world x 21.9-32.9).  The footprint has since been re-traced to **4.4 x 5.7**
(world x 28.5-32.9) and the placements still carried the old local coordinates,
so the whole run -- washer, dryer, ledge, baskets, uppers, shelf, print -- sat
6.6 ft too far east, standing inside room 22 (Office printers), while the
laundry itself was empty.  Everything here is authored in the NEW frame.

ORIENTATION (stated, per ROOM-BRIEF)
------------------------------------
The run is on the NORTH wall (z = 0), washer WEST, dryer EAST.  Three
independent reasons, none of them the photo's apparent geometry alone:
  1. The floor plan's appliance icon registers to this room's north side.
  2. In 'Laundry room and garage door right next to it.jpg' the dryer's right
     flank meets an INSIDE CORNER immediately -- that is the room's east wall.
     The washer's left is closed by a full-height white return -- the west wall.
  3. A real Samsung pair is 27.5 + 27 in = 4.54 ft wide.  The north wall is
     4.40 ft.  No other wall in this room is that length (the others are 5.7).

DECLARED COMPROMISE
-------------------
4.54 ft of appliance will not fit a 4.40 ft wall.  Each machine is authored
2.10 / 2.13 ft wide -- about 7% narrower than the real product.  Room geometry
is ground truth (ROOM-BRIEF) so the machines give, not the wall.

DECLARED PHOTO-DERIVED SURFACE
------------------------------
The 'Wash Dry Fold' print's paper is a rectified albedo taken from the reference
photograph, divided by a wide-gaussian estimate of that photograph's own
illumination.  It is a flat printed artefact, which ROOM-BRIEF admits.  Its
geometric claim, in checkable form:
  source corners (px, in 'Laundry room and garage door right next to it.jpg',
  1200x1600): UL (215.0, 441.3)  LL (223.8, 627.5)  LR (313.0, 631.3)
              UR (320.0, 471.3)
  scale reference: the print's width against the cabinet gap it hangs in,
  corrected for the 1.25x magnification of the cabinet faces (1.2 ft nearer the
  camera than the wall) -> 0.71 x 1.36 ft = 0.97 ft wide.
  built size: outer frame 0.95 x 1.21 ft (an 11 x 14 in. frame).
Nothing else in this room is photo-derived.

WALL DEPTH
----------
Walls extrude OUTWARD from their own footprint line, so a neighbour's wall mass
lands inside this room.  From the room rects: the Office's south wall
(z 7.1 + 0.35) reaches laundry local z 0.15; the Garage's north wall
(z 13.0 - 0.35) reaches local z 5.35; room 22's west wall (x 33.2 - 0.35)
reaches local x 4.35.  So the surfaces a viewer in this room actually sees are
z 0.15 / z 5.35 / x 4.35, not 0 / 5.7 / 4.4.  Everything on the north wall is
authored at z >= 0.18, nothing goes past x 4.33, and the wall skins are placed
on those real faces -- the previous skin sat at a flat 0.022 inset and was
buried behind the neighbours, which is why the wall rendered unpainted.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "util"))
from gkit import *          # noqa: F401,F403  (roomkit.glb + kit + place)
import gkit as G
from roomkit.glb import png_gray, uv_quad
from roomkit.place import find_model, find_object

ROOM = 9
W, D, H = 4.4, 5.7, 9.0
NZ = 0.18                    # face of the north wall, clear of the neighbour
EX = 4.33                    # east limit, clear of room 22's wall mass
SZ = 5.32                    # face of the south wall (the garage's wall mass)

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "..", "..", "docs", "photos-jpg",
                     "Laundry room and garage door right next to it.jpg")


# --------------------------------------------------------------- shadows
# kit.contact_shadow stacks coincident translucent layers, which meter as
# 0.5-9% darkening in this scene instead of the brief's 34% -- coincident
# transparent triangles inside one primitive do not accumulate here.  This is
# the working shape (one coplanar layer of NON-OVERLAPPING annuli, each with
# its own alpha, ramping out PAST the footprint), as proven in the basement.
SH_N = 6
SHMATS = [Material("l9sh%d" % j, "#24242a", roughness=0.98,
                   opacity=round(0.50 * (1.0 - j / float(SH_N)) ** 1.25 + 0.015, 4))
          for j in range(SH_N)]


def _sell(cx, cz, ex, ez, y, seg=16, n=2.6):
    pts = []
    for k in range(seg):
        t = 2 * math.pi * k / seg
        ct, st = math.cos(t), math.sin(t)
        px = cx + ex * math.copysign(abs(ct) ** (2.0 / n), ct)
        pz = cz + ez * math.copysign(abs(st) ** (2.0 / n), st)
        pts.append((min(max(px, 0.04), W - 0.04),
                    y, min(max(pz, 0.04), D - 0.04)))
    return pts


def cshadow(m, cx, cz, hx, hz, feather=0.78, y=0.050, strength=1.0, seg=16):
    inner = _sell(cx, cz, hx, hz, y, seg)
    m.add(Part([(cx, y, cz)] + inner,
               [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)], smooth=True),
          SHMATS[0] if strength > 0.85 else SHMATS[2])
    for j in range(SH_N):
        a = _sell(cx, cz, hx + feather * j / SH_N, hz + feather * j / SH_N, y, seg)
        b = _sell(cx, cz, hx + feather * (j + 1) / SH_N,
                  hz + feather * (j + 1) / SH_N, y, seg)
        tris = []
        for k in range(seg):
            k2 = (k + 1) % seg
            tris += [(k, seg + k2, seg + k), (k, k2, seg + k2)]
        m.add(Part(a + b, tris, smooth=True),
              SHMATS[min(SH_N - 1, int(j / max(0.15, strength)))])


# -------------------------------------------------------------- textures
def weave_png(n=48, band=8, lo=110, hi=255, seed=11):
    """A seamless basket-weave tile: alternating over/under strands with a
    rounded cross-section and a little fibre noise.  Buys FINE-SCALE gradient
    at ~1 KB, which is what the eye reads (ROOM-BRIEF, 'sd is SCALE-BLIND') --
    the old baskets were flat boxes with three painted bands."""
    rnd = Rnd(seed)
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            horiz = ((x // band) + (y // band)) % 2 == 0
            t = ((y % band) if horiz else (x % band)) / (band - 1.0)
            v = 1.0 - 3.6 * (t - 0.5) ** 2          # rounded strand
            g = lo + (hi - lo) * (0.30 + 0.70 * v) + rnd.f(-9, 9)
            if t < 0.06 or t > 0.94:
                g -= 26                              # the gap between strands
            row.append(max(0, min(255, int(g))))
        rows.append(row)
    return png_gray(rows)


def paper_png():
    """Rectified, illumination-divided albedo of the 'Wash Dry Fold' paper."""
    from PIL import Image, ImageFilter, ImageDraw, ImageStat
    im = Image.open(PHOTO).convert("RGB")
    q = (215.0, 441.3, 223.8, 627.5, 313.0, 631.3, 320.0, 471.3)
    rect = im.transform((260, 330), Image.QUAD, q, Image.BICUBIC)
    paper = rect.crop((20, 12, 245, 305))            # inside the frame
    # divide out the photograph's own illumination
    blur = paper.filter(ImageFilter.GaussianBlur(radius=44))
    bm = ImageStat.Stat(blur).mean
    px, pb = paper.load(), blur.load()
    w, h = paper.size
    for yy in range(h):
        for xx in range(w):
            r, g, b = px[xx, yy]
            br, bg2, bb = pb[xx, yy]
            px[xx, yy] = (min(255, int(r * bm[0] / max(1, br))),
                          min(255, int(g * bm[1] / max(1, bg2))),
                          min(255, int(b * bm[2] / max(1, bb))))
    paper = paper.resize((150, 191), Image.LANCZOS).convert("L")
    # the black soap bottle occludes the bottom-centre.  Paint it out AFTER the
    # division (before it, the patch takes the photo's own shading and ships as
    # a grey rectangle) with the paper's own near-white.
    hi = sorted(paper.getdata())[int(len(paper.getdata()) * 0.92)]
    ImageDraw.Draw(paper).rectangle((68, 157, 128, 191), fill=hi)
    # The script is 1-2 px wide at this size and mipmaps away to nothing when
    # the print is 60 px tall in a render -- round 1 shipped it as a ghost.
    # Thicken the strokes, then put the contrast back: gamma holds white at
    # white and takes the ink down to ~30% of it.
    paper = paper.filter(ImageFilter.MinFilter(3))
    lut = [min(255, int(255 * min(1.0, v / 228.0) ** 2.20)) for v in range(256)]
    paper = paper.point(lut)
    return png_gray([[paper.getpixel((x, y)) for x in range(paper.width)]
                     for y in range(paper.height)])


WEAVE = weave_png()
WEAVE_F = weave_png(n=40, band=5, lo=150, hi=255, seed=23)   # finer, the box


def lift(hexs, amp):
    """Brighten a hex by the amount `shaded_plane`'s field darkens it.

    The field can only go DOWN from 1.0 (see shaded_plane), so its mean is
    1 - amp in LINEAR space; a shaded plane sharing a material with unshaded
    parts would otherwise sit a few per cent darker than them and show a step.
    """
    k = (1.0 / (1.0 - amp)) ** (1 / 2.2)
    c = hexs.lstrip("#")
    return "#%02x%02x%02x" % tuple(
        min(255, int(round(int(c[i:i + 2], 16) * k))) for i in (0, 2, 4))


# -------------------------------------------------------------- palette
# picked off 'Laundry room and garage door right next to it.jpg'
APP = Material("l9app", "#f4f3f0", roughness=0.30)            # glossy enamel
APP_D = Material("l9appd", "#dedcd7", roughness=0.34)         # its shaded return
APP_T = Material("l9appt", "#fbfaf8", roughness=0.22)         # lit top deck
GLASS = Material("l9glass", "#141517", roughness=0.10, metallic=0.15)
CONS = Material("l9cons", "#1a1b1d", roughness=0.20, metallic=0.10)
ROSE = Material("l9rose", "#c8a68d", roughness=0.28, metallic=0.55)
CHR = Material("l9chr", "#b6b9bb", roughness=0.24, metallic=0.60)
LEGEND = Material("l9leg", "#9fa2a5", roughness=0.55)
PLINTH = Material("l9plin", "#1e1f21", roughness=0.70)
CABW = Material("l9cabw", "#f6f5f2", roughness=0.52)
CABD = Material("l9cabd", "#e7e5e0", roughness=0.55)
TRIMW = Material("l9trim", "#f8f7f4", roughness=0.58)
PULL = Material("l9pull", "#232427", roughness=0.34, metallic=0.35)
# the photo's seagrass baskets meter (129,116,111) and (140,126,119) sd~38 --
# a cool mid-brown, not the kraft tan the previous round shipped
# round 1 rendered these at mean 181 against the photo's 119/132; the tile's
# own mean darkens the material a further ~18%, so the hex is set for the
# product of the two and re-metered below.
WICK = Material("l9wick", "#746353", roughness=0.90, tex=WEAVE)
WICK_R = Material("l9wickr", "#5b4e42", roughness=0.90)       # rim, no texture
WICK_I = Material("l9wicki", "#382f28", roughness=0.95)       # inside the tub
BOXW = Material("l9boxw", "#b0a897", roughness=0.88, tex=WEAVE_F)  # photo 185
BOXR = Material("l9boxr", "#9e9484", roughness=0.88)
BOTL = Material("l9botl", "#25272a", roughness=0.22, metallic=0.10)
FRAME = Material("l9frame", "#4b4c4e", roughness=0.60)
PAPER = Material("l9paper", "#fbfbfa", roughness=0.80, tex=paper_png())
GREEN = Material("l9green", "#5f8a55", roughness=0.85)
GREEN_D = Material("l9greend", "#4a6f43", roughness=0.85)
POTW = Material("l9pot", "#f1f0ec", roughness=0.50)
SIGN = Material("l9sign", "#f4f3f0", roughness=0.60)
CORD = Material("l9cord", "#2a2b2d", roughness=0.60)

# Shading-field twins.  A shaded_plane's field only rides DOWN from 1.0, so its
# mean is 1 - amp; these are the same paints lifted by exactly that much, which
# keeps a shaded panel level with the unshaded rails beside it.
CAB_AMP, APP_AMP, TRIM_AMP = 0.17, 0.15, 0.14
CABW_S = Material("l9cabws", lift("#f6f5f2", CAB_AMP), roughness=0.52)
APP_S = Material("l9apps", lift("#f4f3f0", APP_AMP), roughness=0.30)
APP_TS = Material("l9appts", lift("#fbfaf8", 0.11), roughness=0.22)
TRIMW_S = Material("l9trims", lift("#f8f7f4", TRIM_AMP), roughness=0.58)


# ------------------------------------------------------------- helpers
def uv_sides(m, mat, x0, x1, y0, y1, z0, z1, tile=0.20):
    """Four vertical faces of a box plus its top, UV'd in real feet so
    `mat.tex` keeps its physical scale.  box() emits no UVs, so a tex on it
    samples texel (0,0) and renders as flat paint -- these must be quads."""
    wx, wz, hy = (x1 - x0) / tile, (z1 - z0) / tile, (y1 - y0) / tile
    m.add(uv_quad((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
                  (0, 0), (wx, 0), (wx, hy), (0, hy)), mat)          # +z
    m.add(uv_quad((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0),
                  (0, 0), (wx, 0), (wx, hy), (0, hy)), mat)          # -z
    m.add(uv_quad((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1),
                  (0, 0), (wz, 0), (wz, hy), (0, hy)), mat)          # +x
    m.add(uv_quad((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0),
                  (0, 0), (wz, 0), (wz, hy), (0, hy)), mat)          # -x
    m.add(uv_quad((x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1),
                  (0, 0), (wx, 0), (wx, wz), (0, wz)), mat)          # top


def disc_z(m, mat, cx, cy, z, r, seg=24, flip=False):
    """A FLAT disc facing +z.  cylinder() welds smooth normals across its caps,
    so a short wide cylinder shades like a dome -- round 1 here built the
    dryer's dial that way and it rendered as a brass ball."""
    v = [(cx, cy, z)] + [(cx + r * math.cos(2 * math.pi * k / seg),
                          cy + r * math.sin(2 * math.pi * k / seg), z)
                         for k in range(seg)]
    t = [(0, 1 + k, 1 + (k + 1) % seg) for k in range(seg)]
    if flip:
        t = [(a, c, b) for (a, b, c) in t]
    m.add(Part(v, t), mat)


def ring_z(m, mat, cx, cy, z, r0, r1, seg=28):
    """A flat annulus facing +z."""
    v, t = [], []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a), z))
        v.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a), z))
    for k in range(seg):
        a0, b0 = 2 * k, 2 * k + 1
        a1, b1 = (2 * k + 2) % (2 * seg), (2 * k + 3) % (2 * seg)
        t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t), mat)


def shaded_plane(m, mat, a0, a1, y0, y1, c, axis="z", flip=False,
                 amp=0.055, seed=1, nx=7, ny=9):
    """A flat plane carrying a SMOOTH low-frequency vertex-colour field.

    The photo's painted surfaces meter sd 5-12 with |d1| only 0.3-0.5 -- gentle
    shading across the surface, NOT grain -- so a noise texture would put the
    fine-scale gradient an order of magnitude too high while a single hex
    leaves sd 0.00 (ROOM-BRIEF: 'do not ship a skin as flat colour', and three
    rooms have shipped algebraically perfect paint).  A coarse mesh with
    per-vertex tone is the shape that matches, and it costs 63 vertices.
    """
    rnd = Rnd(seed)
    ph = [(rnd.f(0, 6.28), rnd.f(0, 6.28), rnd.f(0.8, 2.4), rnd.f(0.8, 2.4))
          for _ in range(3)]
    verts, cols = [], []
    for j in range(ny):
        for i in range(nx):
            u, v = i / (nx - 1.0), j / (ny - 1.0)
            a, y = a0 + (a1 - a0) * u, y0 + (y1 - y0) * v
            # divide by SQRT(n), not n: three random-phase harmonics summed and
            # divided by 3 have an RMS of only 0.17, which shipped a field
            # metering sd 1.9 where the photo's wall is 11.8.  sqrt(n) keeps
            # the RMS at ~0.5, so `amp` means what it says.
            t = sum(math.sin(p + fu * math.pi * u) * math.cos(q + fv * math.pi * v)
                    for (p, q, fu, fv) in ph) / math.sqrt(len(ph))
            # glb.py packs COLOR_0 as a normalised UBYTE after an sRGB->linear
            # conversion, so ANY authored value above 1.0 clamps to 1.0 and the
            # bright half of a field centred on 1.0 is silently thrown away.
            # Ride the field DOWN from 1.0 instead, and `lift` the material.
            g = 1.0 - amp * (1.0 - max(-1.0, min(1.0, t)))
            cols.append((g, g, g))
            verts.append((a, y, c) if axis == "z" else (c, y, a))
    tris = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            A = j * nx + i
            B, C, Dg = A + 1, A + nx, A + nx + 1
            tris += ([(A, Dg, B), (A, C, Dg)] if flip
                     else [(A, B, Dg), (A, Dg, C)])
    m.add(Part(verts, tris, smooth=True, colors=cols), mat)


def uv_wall(m, mat, x0, x1, y0, y1, z, tile=None, flip=False):
    """One vertical quad on the north wall, facing +z (into the room).

    `tile` in feet repeats the material's texture; `tile=None` maps the whole
    texture ONCE across the quad, which is what a picture wants."""
    if tile:
        u, v = (x1 - x0) / tile, (y1 - y0) / tile
    else:
        u = v = 1.0
    # glTF UV origin is the image's TOP-left, so v runs down: bottom edge = v
    return m.add(uv_quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
                         (0, v), (u, v), (u, 0), (0, 0)), mat)


def basket(m, x0, x1, z0, z1, y0, h, taper=0.055, label=False):
    """A woven seagrass basket: a TAPERED tub (narrower at the foot, as the
    photo's are), woven albedo on all four faces, rolled rim on top."""
    yt = y0 + h - 0.05
    ax0, ax1, az0, az1 = x0 + taper, x1 - taper, z0 + taper, z1 - taper
    tw, td, th = (x1 - x0) / 0.10, (z1 - z0) / 0.10, h / 0.10
    for (p0, p1, p2, p3, w) in (
            ((ax0, y0, az1), (ax1, y0, az1), (x1, yt, z1), (x0, yt, z1), tw),
            ((ax1, y0, az0), (ax0, y0, az0), (x0, yt, z0), (x1, yt, z0), tw),
            ((ax1, y0, az1), (ax1, y0, az0), (x1, yt, z0), (x1, yt, z1), td),
            ((ax0, y0, az0), (ax0, y0, az1), (x0, yt, z1), (x0, yt, z0), td)):
        m.add(uv_quad(p0, p1, p2, p3, (0, th), (w, th), (w, 0), (0, 0)), WICK)
    bx(m, WICK_I, x0 + 0.05, x1 - 0.05, yt - 0.10, yt - 0.06,
       z0 + 0.05, z1 - 0.05)                                      # dark inside
    bx(m, WICK_R, x0 - 0.028, x1 + 0.028, yt, y0 + h,
       z0 - 0.028, z1 + 0.028)                                    # rolled rim
    if label:                       # the little card holder on the front face
        bx(m, SIGN, x0 + 0.24, x0 + 0.48, y0 + h * 0.48, y0 + h * 0.70,
           z1 - 0.02, z1)
        bx(m, PULL, x0 + 0.24, x0 + 0.48, y0 + h * 0.68, y0 + h * 0.71,
           z1 - 0.02, z1 + 0.008)


def sprig(m, cx, cz, y0, h=0.30, r=0.16, seed=3):
    """A small potted green -- the photo has one at each end of the ledge."""
    rnd = Rnd(seed)
    m.add(cylinder(r, h * 0.52, 12, r_top=r * 0.90), POTW, at=(cx, y0, cz))
    top = y0 + h * 0.52
    for k in range(9):
        a = 2 * math.pi * k / 9 + rnd.f(0, 0.5)
        lr = r * rnd.f(0.55, 1.05)
        m.add(cylinder(0.030, h * rnd.f(0.55, 1.0), 6, r_top=0.012),
              GREEN if k % 2 else GREEN_D,
              at=(cx + lr * math.cos(a) * 0.5, top - 0.02,
                  cz + lr * math.sin(a) * 0.5),
              rot_x=G.R(rnd.f(-26, 26)), rot_z=G.R(rnd.f(-26, 26)))


# ============================================================ APPLIANCES
def appliances():
    m = Model()

    # ---------------------------------------------------- washer (top-load)
    wx0, wx1 = 0.07, 2.17
    wz1 = NZ + 2.44
    bx(m, PLINTH, wx0 + 0.05, wx1 - 0.05, 0.0, 0.20, NZ + 0.06, wz1 - 0.05)
    bx(m, APP, wx0, wx1, 0.20, 3.06, NZ, wz1)                    # body
    bx(m, APP_D, wx0 + 0.02, wx1 - 0.02, 0.20, 0.235, NZ, wz1 + 0.004)
    bx(m, APP_D, wx0 + 0.03, wx1 - 0.03, 2.90, 2.93, wz1, wz1 + 0.006)  # lid line
    bx(m, CONS, wx1 - 0.44, wx1 - 0.10, 2.60, 2.74, wz1, wz1 + 0.010)   # badge
    bx(m, APP_T, wx0, wx1, 3.06, 3.17, NZ, wz1)                  # top deck
    # black glass lid, sunk into a WHITE RIM that shows all the way round it
    # (the photo's rim is ~2 in. at the sides and a wide band at the front)
    bx(m, GLASS, wx0 + 0.20, wx1 - 0.20, 3.15, 3.215, NZ + 0.80, wz1 - 0.30)
    bx(m, GLASS, wx0 + 0.30, wx1 - 0.30, 3.215, 3.238, NZ + 0.90, wz1 - 0.40)
    bx(m, APP_T, wx0 + 0.16, wx1 - 0.16, 3.17, 3.205, wz1 - 0.34, wz1 - 0.24)
    # console: a black glossy slab across the back, dial + legends on its top
    cz0, cz1 = NZ + 0.02, NZ + 0.56
    bx(m, APP, wx0, wx1, 3.17, 3.52, cz0, cz1)
    bx(m, CONS, wx0 + 0.02, wx1 - 0.02, 3.52, 3.60, cz0 - 0.01, cz1 + 0.02)
    bx(m, CONS, wx0 + 0.02, wx1 - 0.02, 3.30, 3.52, cz1, cz1 + 0.03)
    m.add(cylinder(0.145, 0.045, 18), ROSE, at=(wx0 + 0.86, 3.60, cz0 + 0.27))
    m.add(cylinder(0.105, 0.020, 18), CHR, at=(wx0 + 0.86, 3.645, cz0 + 0.27))
    bx(m, LEGEND, wx0 + 0.12, wx0 + 0.46, 3.60, 3.606, cz0 + 0.22, cz0 + 0.27)
    for i in range(6):                                  # button legends
        a = wx0 + 1.09 + i * 0.155
        for k in range(2):
            bx(m, LEGEND, a, a + 0.085, 3.60, 3.606,
               cz0 + 0.16 + k * 0.19, cz0 + 0.20 + k * 0.19)
    for i in range(3):                                  # cycle chevrons
        a = wx0 + 1.09 + i * 0.155
        bx(m, LEGEND, a, a + 0.06, 3.60, 3.606, cz0 + 0.40, cz0 + 0.435)

    # ---------------------------------------------------- dryer (front-load)
    dx0, dx1 = 2.21, EX
    dz1 = NZ + 2.60
    bx(m, PLINTH, dx0 + 0.05, dx1 - 0.05, 0.0, 0.14, NZ + 0.06, dz1 - 0.05)
    bx(m, APP, dx0, dx1, 0.14, 3.22, NZ, dz1)
    bx(m, APP_T, dx0, dx1, 3.22, 3.30, NZ, dz1)                  # top deck
    # control panel, then the rose-gold band under it, then the door
    bx(m, APP_T, dx0 + 0.02, dx1 - 0.02, 2.62, 3.22, dz1, dz1 + 0.035)
    bx(m, ROSE, dx0 + 0.02, dx1 - 0.02, 2.525, 2.610, dz1, dz1 + 0.028)
    bx(m, APP_D, dx0 + 0.02, dx1 - 0.02, 2.495, 2.525, dz1, dz1 + 0.020)
    # the dial is a FLAT rose-gold disc on the panel face, not a knob standing
    # off it -- round 1 here made it 0.09 ft proud and it read as a brass ball
    disc_z(m, ROSE, dx0 + 0.80, 2.87, dz1 + 0.040, 0.115, 22)
    disc_z(m, CHR, dx0 + 0.80, 2.87, dz1 + 0.046, 0.030, 16)
    bx(m, CONS, dx0 + 1.06, dx1 - 0.20, 2.755, 3.005, dz1 + 0.035, dz1 + 0.046)
    for i in range(4):                                  # button pips
        for k in range(2):
            a = dx0 + 1.13 + i * 0.125
            bx(m, LEGEND, a, a + 0.058, 2.80 + k * 0.115, 2.828 + k * 0.115,
               dz1 + 0.046, dz1 + 0.051)
    bx(m, LEGEND, dx0 + 0.14, dx0 + 0.44, 2.865, 2.895, dz1 + 0.035, dz1 + 0.040)
    for i in range(5):                                  # vent slots by the dial
        a = dx0 + 0.50 + i * 0.038
        bx(m, APP_D, a, a + 0.016, 2.78, 2.96, dz1 + 0.035, dz1 + 0.040)
    # The door: three FLAT coplanar-free layers.  Round 1 stacked a ring on the
    # front cap of a cylinder at the same z and the pair z-fought into a
    # shimmering saw-edge; cylinder() also welds smooth normals across its cap,
    # so a 0.03 ft disc of radius 0.9 shades like a dome.
    dcx, dcy = (dx0 + dx1) / 2.0, 1.42
    ring_z(m, APP, dcx, dcy, dz1 + 0.032, 0.665, 0.840)      # white door face
    ring_z(m, CHR, dcx, dcy, dz1 + 0.044, 0.610, 0.672)      # chrome rim
    disc_z(m, GLASS, dcx, dcy, dz1 + 0.038, 0.625, 32)       # black glass
    bx(m, Material("l9lint", "#3a3d40", roughness=0.65),
       dcx - 0.20, dcx - 0.02, dcy - 0.30, dcy - 0.16,
       dz1 + 0.040, dz1 + 0.043)                        # lint grille, through it
    bx(m, APP_D, dx1 - 0.085, dx1 - 0.02, dcy - 0.11, dcy + 0.11,
       dz1, dz1 + 0.038)                                # door catch

    # ---------------------------------------------------- on the dryer top
    # the pale woven lidded box the photo parks there (NOT kraft cardboard)
    uv_sides(m, BOXW, dx0 + 0.20, dx0 + 1.02, 3.30, 3.72, NZ + 0.52, NZ + 1.36,
             tile=0.11)
    bx(m, BOXR, dx0 + 0.17, dx0 + 1.05, 3.72, 3.80, NZ + 0.49, NZ + 1.39)

    # the washer's cord, up into the outlet under the ledge
    bx(m, CORD, wx1 - 0.30, wx1 - 0.26, 3.17, 3.86, NZ + 0.04, NZ + 0.08)

    # Both fronts are the biggest flat white areas in the frame and metered
    # sd 0.00 in round 1 against the photo's 5.3 / 21.2.  A shading field, not
    # a grain texture -- the photo's |d1| on these is 0.29 / 4.04.
    shaded_plane(m, APP_S, wx0 + 0.005, wx1 - 0.005, 0.24, 3.02, wz1 + 0.004,
                 amp=APP_AMP, seed=61, nx=6, ny=8)
    shaded_plane(m, APP_S, dx0 + 0.005, dx1 - 0.005, 0.18, 2.44, dz1 + 0.004,
                 amp=APP_AMP, seed=67, nx=6, ny=7)
    shaded_plane(m, APP_TS, wx0 + 0.005, wx1 - 0.005, 3.07, 3.16, wz1 + 0.004,
                 amp=0.11, seed=71, nx=5, ny=3)
    return m


# ================================================== LEDGE / UPPERS / ART
LY = 3.94                      # ledge underside
LT = 4.07                      # ledge top
CB, CT = 5.35, 7.80            # cabinet bottom / top
SH_Y = 5.78                    # floating-shelf top
GAP0, GAP1 = 1.52, 2.88        # the wall gap the print and shelf live in


def uppers():
    m = Model()

    # ---------------------------------------------------------- the ledge
    bx(m, TRIMW, 0.02, EX, LY, LT, NZ, NZ + 1.24)
    bx(m, CABD, 0.02, EX, LY - 0.045, LY, NZ, NZ + 1.24)   # shadow line
    shaded_plane(m, TRIMW_S, 0.03, EX - 0.01, LY + 0.004, LT - 0.004,
                 NZ + 1.244, amp=TRIM_AMP, seed=53, nx=7, ny=2)  # front edge
    # an outlet and a dark power block on the wall under it (the photo has both)
    bx(m, SIGN, 1.30, 1.52, 3.40, 3.68, NZ, NZ + 0.030)
    bx(m, PULL, 1.35, 1.47, 3.47, 3.61, NZ + 0.030, NZ + 0.042)
    bx(m, PULL, 0.62, 0.98, 3.52, 3.66, NZ, NZ + 0.12)

    # ------------------------------------------------ the two wall cabinets
    def cabinet(x0, x1, pull_right):
        bx(m, CABD, x0, x1, CB, CT, NZ, NZ + 1.18)                # carcase
        # a shaker door is a frame around a RECESSED panel: four rails standing
        # proud, the panel set back behind them.  Round 1 drew the panel PROUD
        # of the door face, which is the reverse of the joinery.
        a0, a1 = x0 + 0.015, x1 - 0.015
        b0, b1 = CB + 0.02, CT - 0.02
        p0, p1, q0, q1 = a0 + 0.13, a1 - 0.13, b0 + 0.15, b1 - 0.15
        bx(m, CABD, p0, p1, q0, q1, NZ + 1.18, NZ + 1.222)         # sunk panel
        shaded_plane(m, CABW_S, p0, p1, q0, q1, NZ + 1.224,
                     amp=CAB_AMP, seed=41 if pull_right else 47, nx=5, ny=7)
        for (u0, u1, v0, v1) in ((a0, a1, b0, q0), (a0, a1, q1, b1),
                                 (a0, p0, q0, q1), (p1, a1, q0, q1)):
            bx(m, CABW, u0, u1, v0, v1, NZ + 1.18, NZ + 1.245)     # rails
        px = (x1 - 0.115) if pull_right else (x0 + 0.075)
        bx(m, PULL, px, px + 0.045, CB + 0.20, CB + 0.82,
           NZ + 1.245, NZ + 1.335)                                # bar pull
        bx(m, CABD, x0, x1, CB - 0.035, CB, NZ, NZ + 1.20)        # under-shadow
        # crown: two steps, as photographed
        bx(m, TRIMW, x0 - 0.055, x1 + 0.055, CT, CT + 0.13, NZ, NZ + 1.32)
        bx(m, TRIMW, x0 - 0.025, x1 + 0.025, CT + 0.13, CT + 0.235, NZ, NZ + 1.26)

    cabinet(0.02, GAP0, True)
    cabinet(GAP1, EX, False)

    # --------------------------------- floating shelf + bottles + the print
    bx(m, TRIMW, GAP0, GAP1, SH_Y - 0.115, SH_Y, NZ, NZ + 0.62)
    bx(m, CABD, GAP0, GAP1, SH_Y - 0.155, SH_Y - 0.115, NZ, NZ + 0.58)

    pw, ph = 0.95, 1.21                       # 11 x 14 in. frame, see docstring
    px0 = (GAP0 + GAP1) / 2.0 - pw / 2.0
    bx(m, FRAME, px0, px0 + pw, SH_Y, SH_Y + ph, NZ + 0.015, NZ + 0.078)
    # the paper MUST be a uv_quad: box() emits no UVs, so a tex on a bx() samples
    # texel (0,0) and the print shipped as a blank white panel in round 1 here.
    uv_wall(m, PAPER, px0 + 0.062, px0 + pw - 0.062, SH_Y + 0.062,
            SH_Y + ph - 0.062, NZ + 0.079)
    for cx in (GAP0 + 0.19, (GAP0 + GAP1) / 2.0 + 0.06, GAP1 - 0.17):
        m.add(cylinder(0.098, 0.40, 14, r_top=0.082), BOTL,
              at=(cx, SH_Y, NZ + 0.30))
        m.add(cylinder(0.042, 0.10, 10), BOTL, at=(cx, SH_Y + 0.40, NZ + 0.30))
        bx(m, PULL, cx - 0.018, cx + 0.10, SH_Y + 0.48, SH_Y + 0.515,
           NZ + 0.285, NZ + 0.315)                                # pump spout
    bx(m, SIGN, GAP1 - 0.34, GAP1 - 0.12, SH_Y, SH_Y + 0.17,
       NZ + 0.16, NZ + 0.185)                                     # little card

    # --------------------------------------------------- props on the ledge
    basket(m, 1.22, 2.06, NZ + 0.22, NZ + 0.96, LT, 0.68, label=True)
    basket(m, 2.46, 3.26, NZ + 0.24, NZ + 0.94, LT, 0.66)
    # the white 'CLEAN' block between them
    bx(m, SIGN, 2.16, 2.42, LT, LT + 0.42, NZ + 0.46, NZ + 0.50)
    bx(m, PULL, 2.20, 2.38, LT + 0.14, LT + 0.20, NZ + 0.44, NZ + 0.462)
    bx(m, SIGN, 2.18, 2.40, LT, LT + 0.06, NZ + 0.40, NZ + 0.56)
    sprig(m, 0.28, NZ + 0.52, LT, h=0.34, r=0.14, seed=5)
    sprig(m, 3.96, NZ + 0.60, LT, h=0.40, r=0.17, seed=9)
    m.add(cylinder(0.075, 0.15, 12, r_top=0.058), CHR,
          at=(3.52, LT, NZ + 0.50))                               # little knob
    return m


# ============================================================ ROOM SHELL
def floor_marks():
    m = Model()
    RG = Material("l9reg", "#e8e6e2", roughness=0.55)
    RGS = Material("l9regs", "#8d8f91", roughness=0.70)
    bx(m, RG, 1.55, 2.72, 0.0, 0.022, 4.18, 4.78)
    for i in range(8):
        zz = 4.24 + i * 0.062
        bx(m, RGS, 1.62, 2.65, 0.022, 0.030, zz, zz + 0.034)
    cshadow(m, 1.12, NZ + 1.30, 1.10, 1.28, strength=1.0)      # washer
    cshadow(m, 3.28, NZ + 1.38, 1.12, 1.36, strength=1.0)      # dryer
    return m


def skins():
    """Per-wall non-emissive albedo, refitted to the new footprint.

    The hexes are the ones fitted by probe for this room in the previous round.
    The fit is a property of wall ORIENTATION (skinkit's RATIO), which a change
    of footprint does not alter, so they carry over; re-metered after the build.

    NOT skinkit.build -- that insets every skin a flat 0.022 ft, and on this
    room's north and south walls a NEIGHBOUR'S wall mass stands 0.15 / 0.35 ft
    inside the footprint, so a 0.022 skin is buried behind it and the wall
    renders unpainted.  Each face here is placed on the surface a viewer in
    this room can actually see.
    """
    m = Model()
    hexes = {"n": "#a1a1a0", "w": "#b3b3b2", "e": "#f2f2f1", "s": "#fffffe"}
    # measured from the room rects: office south wall -> local z 0.15,
    # garage north wall -> local z 5.35, room 22 west wall -> local x 4.35
    face = {"n": NZ - 0.01, "s": SZ, "w": 0.022, "e": EX + 0.015}
    # n and e wind normally, s and w are reversed (same convention skinkit uses)
    for k, wall in enumerate("nswe"):
        amp = 0.26
        mat = Material("l9skin_" + wall, lift(hexes[wall], amp),
                       roughness=0.95, double_sided=False)
        shaded_plane(m, mat, 0.0, W if wall in "ns" else D, 0.0, H,
                     face[wall], axis="z" if wall in "ns" else "x",
                     flip=wall in "sw", amp=amp, seed=31 + k * 7)
    return m


def drop(name):
    import urllib.request
    o = find_object(ROOM, name)
    if o:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/object/%d" % o["id"],
            method="DELETE"))
        print("  dropped object %s" % name)
    mo = find_model(name)
    if mo:
        urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:5000/api/house/model/%d" % mo["id"],
            method="DELETE"))


if __name__ == "__main__":
    import kit as SK
    # 11-ft-frame leftovers with nowhere to stand in a 4.4-ft room
    for n in ("Laundry Tall Cabinet", "Laundry Hamper"):
        drop(n)

    tot = 0.0
    D_W = (1.50, 4.20)          # west wall -> hall / pantry (unchanged)
    D_S = (0.85, 3.55)          # south wall -> garage.  The old x 7.40-10.10
                                # is off the end of the re-traced room; the
                                # garage is directly south, and this is the
                                # only wall a 2.7 ft door now fits on.
    tot += G.save_and_place("Laundry Ceiling",
                            SK.ceiling(W, D, H, cans=[(1.5, 1.4), (3.0, 4.2)],
                                       vents=[(3.6, 5.1, 0.80, 0.45)]), ROOM)
    mb = SK.baseboards(W, D, doors=[("w", *D_W), ("s", *D_S)])
    SK.door_unit(mb, "w", W, D, *D_W)
    SK.door_unit(mb, "s", W, D, *D_S)
    tot += G.save_and_place("Laundry Baseboards", mb, ROOM)
    tot += G.save_and_place("Laundry Wall Wash", skins(), ROOM)
    tot += G.save_and_place("Laundry Washer Dryer", appliances(), ROOM)
    tot += G.save_and_place("Laundry Uppers", uppers(), ROOM)
    tot += G.save_and_place("Laundry Floor Marks", floor_marks(), ROOM)
    print("  laundry total %.1f KB" % tot)
