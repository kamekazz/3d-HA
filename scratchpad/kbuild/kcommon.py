"""Shared materials + helpers for the room-6 (Kitchen) build -- ROUND 3.

The footprint was re-traced under round 1: the room is now 14.87 x 16.74 ft and
a POLYGON (three-facet bay on the west wall), anchored 5.31/7.24 ft away from
where round 1 built.  Everything here is authored in ROOM-LOCAL FEET:

    x 2.28 .. 14.87   west wall -> east wall   (bay reaches out to x = 0)
    z 0.00 .. 16.74   north wall -> south wall
    y 0.00 ..  9.00   slab -> ceiling

`emit()` reads the model bbox back and hands place() the centre/floor it
implies, so every piece is placed at rot 0.

ROUND-2 CHANGES TO THE SHARED LAYER
  * daylight.js was fixed app-wide (hemisphere ground + daytime IBL raised), so
    every emissive term round 1 metered is now too bright.  Re-metered against
    the photos: white doors want ~210 (were 220), quartz tops ~209 (were 237),
    ceiling ~205 (was 220).  Emissives below are pulled down to match.
  * HARDWARE: the photos show small round BLACK KNOBS on doors and black bar
    pulls on DRAWERS ONLY.  Round 1 put long vertical bar pulls on ~30 doors.
    `pull=("k", frac)` is the knob; ("h", frac) stays the drawer bar.
  * VEINING: round 1's veins were 0.29 in wide and 15 tone steps off the field,
    so they vanished past 6 ft.  `veins()` now draws a soft halo plus a dark
    core at ~0.5 ft spacing, which is what the Calacatta-look tops really do.

ROUND-3 CHANGES TO THE SHARED LAYER  (round 2 was failed by a critic)
  * STONE.  `veins()` is GONE.  Every quartz top and marble backsplash is now a
    rasterised tone field -- broad soft grey cloud + fine grain + a connected
    net of soft veins -- built by kraster.py and driven through `top_stone()` /
    `splash_stone()`.  The critic metered round 2's backsplash at 163 / sd 5.1
    against photo F's 173.4 / sd 19.0 and called it "a flat mid-grey field with
    a scatter of pale straight stick-marks".  It now meters 173.1 / sd 12.0, and
    the island top 204.4 / sd 20.2 against the photo's 205.0 / sd 24.9 (it was
    222.6 / sd 18.2).
  * HARDWARE, REGRESSION FIXED.  Photo F was re-cropped at 2x: every UPPER door
    carries a black vertical bar pull and only the BASE doors have knobs.  Round
    1 had this right, round 1's critic wrongly called for knobs everywhere, and
    round 2 built it.  `two_door(..., kind="v")` restores the uppers.
  * CROWN.  `crown_run()` -- five members, 0.30 ft past the door faces, 0.62 ft
    tall, over a dark reveal.  Round 2's four thin steps still read as a band.
  * CASED OPENINGS.  `cased_opening()` gives each one real jamb linings (running
    away from the room, into the wall cavity, so the casing stays flush with the
    wall plane) drawn a few tone steps below the casing, since this renderer has
    no shadows to sell the reveal.
  * BLACKS.  BLACK/GLASSBLK carry an emissive floor and appliances use APPL*: a
    face turned away from the single sun was rendering at literally 0, which is
    the "large PURE BLACK surface" the critic found from the south-east pose.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part, box, rounded_box, cylinder, prism, quad, sag_plane, torus  # noqa
from roomkit.place import place  # noqa
from kraster import (ramp, raster, stone_field, Veins, Shadows, shadow_ramp,  # noqa
                     fbm, vnoise, khash, rng as krng)

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- the room
# footprint polygon, room-local feet, in the order the DB stores it (edge i
# runs POLY[i] -> POLY[i+1]; house.js indexes openings by that same i).
POLY = [(14.87, 16.74), (2.28, 16.74), (2.28, 11.16), (0.0, 10.0),
        (0.0, 4.51), (2.28, 3.35), (2.28, 0.0), (14.87, 0.0)]
E_SOUTH, E_WSOUTH, E_BAY_S, E_BAY_F, E_BAY_N, E_WNORTH, E_NORTH, E_EAST = range(8)

XW_WEST, XW_EAST = 2.28, 14.87      # main-rect wall planes
ZW_NORTH, ZW_SOUTH = 0.0, 16.74
HGT = 9.0                           # wall height (ground truth)
CEIL_Y = HGT - 0.03

# p_floor.py lays real plank geometry over the app's slab, so everything that
# stands on the floor is emitted at this height instead of 0 -- otherwise the
# planks and the baked contact shadows cut through the bottom half-inch of
# every toe kick.
FLOOR_TOP = 0.046

CT, CB = 3.00, 2.88                 # counter top / underside
TOE = 0.32
UP0, UP1 = 4.50, 8.10               # wall-cabinet band
CR1 = 8.55                          # top of the stepped crown

# ---------------------------------------------------------------- materials
# Vertical interior faces still collect well under half the scene radiance, so
# the whites carry an emissive stand-in for the bounce the renderer skips --
# but ~15% less of one than round 1 used, see the header.
EM_W = "#757575"
WHITE     = Material("white",   "#eeece8", roughness=0.52, emissive=EM_W)
WHITE_LO  = Material("whitelo", "#dbd8d3", roughness=0.55, emissive="#565656")
TRIM      = Material("trim",    "#f6f5f2", roughness=0.55, emissive="#6d6d6d")
# QUARTZ / MARBLE are now only the EDGES of a stone surface (front lips, ends,
# returns) -- the faces you look at are rasterised tone fields, see TOPS/SPLASH
# below.  Both are set to the middle of their palette so an edge never steps
# away from the face it belongs to.
QUARTZ    = Material("quartz",  "#aeaeab", roughness=0.46, emissive="#1a1a1a")
VEIN      = Material("vein",    "#a4a9ad", roughness=0.48, emissive="#1c1c1c")
MARBLE    = Material("marble",  "#d7d7d4", roughness=0.52, emissive="#303030")
# ROUND 3: both blacks carry a small emissive floor.  With none, a face turned
# away from this scene's single sun renders at literally 0 and reads as a hole
# in the room -- see APPL below and p_south.fridge().
BLACK     = Material("black",   "#1e2023", roughness=0.40, metallic=0.25,
                     emissive="#121314")
GLASSBLK  = Material("blkglass", "#141619", roughness=0.14, metallic=0.35,
                     emissive="#0e0f11")
PULL      = Material("pull",    "#202226", roughness=0.32, metallic=0.55)
STEEL     = Material("steel",   "#c0c3c7", roughness=0.28, metallic=0.70,
                     emissive="#414141")
GREYFAB   = Material("greyfab", "#d3d2cf", roughness=0.92, emissive="#5e5e5e")
DARKFAB   = Material("darkfab", "#5e6062", roughness=0.95, emissive="#2e2e2e")
CEIL      = Material("ceil",    "#fbfbfa", roughness=0.90, emissive="#b2b2b2",
                     double_sided=False)
CEIL_TRIM = Material("ceiltrim", "#f7f7f5", roughness=0.70, emissive="#8b8b8b")
GLOW      = Material("glow",    "#ffffff", roughness=0.9, emissive="#ffffff",
                     emissive_strength=1.55, double_sided=False)
GLASS     = Material("glass",   "#dfe7ea", roughness=0.10, emissive="#98a1a6")
GREEN     = Material("green",   "#5d7f4e", roughness=0.85, emissive="#28331f")
WOODBLK   = Material("woodblk", "#8d6a4b", roughness=0.75, emissive="#372a1d")
# the app paints its own walls; this matches them for the bits of wall we build
# ourselves (the peninsula half-wall's back, opening jambs).
# ROUND 4: follows wall_color down (#eae6de -> #bcbdbf).  This paints the
# peninsula half wall's back and the opening jambs; left at round 3's value
# it would now read as a lighter panel standing in a darker room.
WALLPT    = Material("wallpt",  "#c9cacd", roughness=0.94, emissive="#464646")

FT = 1.0

# --------------------------------------------------------- ROUND 3: the stone
# The round-2 critic's headline defect: "the backsplash renders as a flat
# mid-grey field (mean 163, sd 5.1) with a scatter of pale straight stick-marks;
# photo F's is near-white marble at essentially counter value with broad soft
# clouding (167 / sd 41)".  Same for the island top, 18 points too bright at
# half the photo's spread.  Both surfaces are ~40% of the pixels in the two hero
# views, so they are rebuilt as rasterised TONE FIELDS (kraster.py): broad soft
# grey cloud, fine grain, and a connected net of soft veins -- no sticks.
#
# Two palettes, both 14 steps, shared by every stone surface in the room so the
# exporter still emits one primitive per tone.  Calibrated by rendering and
# metering, not by eye:
#   island top   render 222.6 / sd 18.2  ->  photo F 205.0 / sd 24.9
#   backsplash   render 163.0 / sd  5.1  ->  photo F 173.4 / sd 19.0
# The tops clip hard under direct sun in this renderer, so their albedo runs
# well below the value they land on.
# Calibrated against this renderer's response curve, measured on our own
# surfaces: albedo 74 lands on 110, albedo 192 on 215, albedo 205 on 222.6 --
# so the slope is ~0.89 down low and ~0.58 up in the highlights.  To put the
# field on the photo's 205 the albedo has to be 175, and to put a vein core on
# the photo's 155 it has to be 125.  Those two points fix the ramp.
TOP_N = 16
TOPS = ramp("#6f757b", "#b9b9b6", TOP_N, "top", roughness=0.46,
            emissive_lo="#101010", emissive_hi="#1a1a1a")
SPL_N = 16
SPLASH = ramp("#7a7f85", "#ededea", SPL_N, "spl", roughness=0.52,
              emissive_lo="#1a1a1a", emissive_hi="#3a3a3a")

# Appliance black.  #141517 with no emissive renders at literally 0 on a face
# turned away from the sun -- the round-2 critic found a "pure black surface
# filling much of the frame" from the south-east pose, which is the fridge side
# 1.6 ft from the camera.  The photos' black appliances measure 55-134 with
# strong grazing reflection, never 0, so the appliance blacks carry a small
# emissive floor and a lighter sheen tone for the reflective faces.
APPL      = Material("appl",    "#26282b", roughness=0.34, metallic=0.30,
                     emissive="#161719")
APPL_LO   = Material("appllo",  "#1b1d20", roughness=0.30, metallic=0.34,
                     emissive="#101113")
APPL_HI   = Material("applhi",  "#3a3d42", roughness=0.22, metallic=0.42,
                     emissive="#232529")
SHADOWLN  = Material("shadowln", "#b9b6b0", roughness=0.85, emissive="#2c2c2c")
# ROUND 4.  The fridge's east side face is 1.6 ft from the stock south-east
# camera and fills ~40% of that frame; round 3 lifted it off pure black to 41.9
# but left it perfectly flat (sd 2.4) against photo A's 54.7-57.7.  These are the
# five steps of a vertical sheen ramp -- a tall black steel panel always carries
# one, and it is the only thing that stops a 6 ft slab reading as a painted card.
SIDE = [Material(f"side{i}", c, roughness=0.26, metallic=0.38, emissive=e)
        for i, (c, e) in enumerate((("#393a3c", "#252627"), ("#424345", "#2b2c2e"),
                                    ("#4d4e50", "#333436"), ("#454648", "#2d2e30"),
                                    ("#3d3e40", "#282929")))]

# the can trim must sit at CEIL's own value, not CEIL_TRIM's: a down-facing
# disc with the trim's dimmer emissive read as a grey hole in the plaster.
CEIL_TRIM_1S = Material("ceiltrim1s", "#fbfbfa", roughness=0.88,
                        emissive="#a8a8a8", double_sided=False)


def disc_down(radius, y, cx, cz, seg=20):
    """A flat disc whose single face points DOWN.

    Recessed cans were built as short cylinders.  The ceiling plane is
    one-sided (it must be, or it hides the room from the dollhouse camera), so
    from above the cans were the only thing left -- and the critic read six
    white cylinders hovering over the counters and floor as golf balls.  A disc
    with only a downward face is invisible from every camera above the ceiling
    and identical from every camera below it.
    """
    import math as _m
    v = [(cx, y, cz)]
    for i in range(seg):
        a = 2 * _m.pi * i / seg
        v.append((cx + radius * _m.cos(a), y, cz + radius * _m.sin(a)))
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    return Part(v, t)


# ---------------------------------------------------------------- helpers
def bx(m, mat, x0, x1, y0, y1, z0, z1):
    """Axis-aligned box given absolute room-local extents."""
    if abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6 or abs(z1 - z0) < 1e-6:
        return
    m.add(box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat,
          at=((x0 + x1) / 2.0, min(y0, y1), (z0 + z1) / 2.0))


_AX = {"+x": (0, 1), "-x": (0, -1), "+z": (2, 1), "-z": (2, -1)}


def knob(m, mat, face, at, u, y, r=0.058):
    """A small round cabinet knob standing off the door face.

    This is the hardware the photos actually show on every DOOR; bar pulls are
    on drawers only.  `at` is the outer surface of the door's proud rails.
    """
    axis, d = _AX[face]

    def cyl(rad, h, off, r_top=None):
        p = cylinder(rad, h, seg=12, r_top=r_top)
        if axis == 0:
            m.add(p, mat, at=(at + d * off, y, u),
                  rot_z=(math.pi / 2 if d < 0 else -math.pi / 2))
        else:
            m.add(p, mat, at=(u, y, at + d * off),
                  rot_x=(math.pi / 2 if d > 0 else -math.pi / 2))

    cyl(0.022, 0.060, 0.0)                       # stem
    cyl(r, 0.052, 0.058, r_top=r * 0.86)         # head


def door(m, mat, face, at, u0, u1, y0, y1, depth=0.055, rail=0.135,
         proud=0.028, pull=None, pull_mat=None, panel=None, pull_y=0.5):
    """A shaker door/drawer front on a vertical plane.

    face: which way the front looks ('-x' means the front faces west).
    at:   the coordinate of the outer surface on the face axis.
    u0/u1: the in-plane horizontal extent (z for x-faces, x for z-faces).
    pull: None | ('k', frac) knob | ('h', frac) drawer bar | ('v', frac) bar.
    """
    axis, d = _AX[face]
    panel = panel or mat
    a0, a1 = at, at + d * depth                    # recessed panel
    p0, p1 = a1, at + d * (depth + proud)          # stiles/rails

    def put(mt, lo, hi, uu0, uu1, yy0, yy1):
        if axis == 0:
            bx(m, mt, min(lo, hi), max(lo, hi), yy0, yy1, uu0, uu1)
        else:
            bx(m, mt, uu0, uu1, yy0, yy1, min(lo, hi), max(lo, hi))

    put(panel, a0, a1, u0, u1, y0, y1)
    r = min(rail, (u1 - u0) / 2.5, (y1 - y0) / 2.5)
    put(mat, p0, p1, u0, u1, y0, y0 + r)          # bottom rail
    put(mat, p0, p1, u0, u1, y1 - r, y1)          # top rail
    put(mat, p0, p1, u0, u0 + r, y0, y1)          # left stile
    put(mat, p0, p1, u1 - r, u1, y0, y1)          # right stile

    if pull:
        kind, frac = pull
        pm = pull_mat or PULL
        h0, h1 = p1, at + d * (depth + proud + 0.055)
        uc = u0 + (u1 - u0) * frac
        if kind == "k":
            yc = y0 + (y1 - y0) * pull_y
            yc = min(max(yc, y0 + 0.16), y1 - 0.16)
            knob(m, pm, face, p1, uc, yc)
        elif kind == "v":
            L = min(0.46, (y1 - y0) * 0.42)
            yc = y0 + (y1 - y0) * pull_y
            yc = min(max(yc, y0 + L / 2 + 0.1), y1 - L / 2 - 0.1)
            put(pm, h0, h1, uc - 0.028, uc + 0.028, yc - L / 2, yc + L / 2)
        else:
            yc = y0 + (y1 - y0) * frac
            L = min(0.95, (u1 - u0) * 0.58)
            uc = (u0 + u1) / 2.0
            put(pm, h0, h1, uc - L / 2, uc + L / 2, yc - 0.030, yc + 0.030)
            for s in (-1, 1):                      # posts back to the drawer
                put(pm, p1, p1 + d * 0.026, uc + s * (L / 2 - 0.035),
                    uc + s * (L / 2 - 0.005), yc - 0.030, yc + 0.030)


def two_door(m, mat, face, at, u0, u1, y0, y1, pull_y=0.88, kind="k", **kw):
    """A pair of shaker doors with hardware on the meeting stiles.

    ROUND-3 REGRESSION FIX.  Round 1 put vertical BAR PULLS on the upper doors,
    which is what photo F actually shows; round 1's critic called for knobs,
    round 2 changed all ~30 doors, and round 2's critic re-checked the photo and
    found bar pulls on every upper door with knobs only on base doors.  Photo F
    (crop: docs/photos-jpg/Kitchen F.jpg, upper run) confirms it -- so `kind`
    is now explicit at every call site: "v" for uppers, "k" for base doors.
    """
    mid = (u0 + u1) / 2.0
    g = 0.014
    door(m, mat, face, at, u0, mid - g, y0, y1, pull=(kind, 0.86),
         pull_y=pull_y, **kw)
    door(m, mat, face, at, mid + g, u1, y0, y1, pull=(kind, 0.14),
         pull_y=pull_y, **kw)


def crown_run(m, mat, face, at, front, u0, u1, y0, shadow=None, proj=0.34,
              h=0.62):
    """Chunky built-up cabinet crown: fillet, cove, ogee, cap + a shadow line.

    Round 2's was four thin steps totalling 0.27 ft of projection and the critic
    still read it as "a thin band"; photo F's is a deep built-up stack with a
    hard dark line where it meets the door faces.

    `at` is the WALL plane the cabinets hang on, `front` how far the door faces
    already stand off it, and `proj` how much further the widest crown member
    projects past those doors.  Every member is drawn back to the wall so the
    run reads solid from below.
    """
    axis, d = _AX[face]
    steps = ((0.02, 0.000, 0.055),      # tight fillet against the door face
             (proj * 0.40, 0.055, 0.190),
             (proj * 0.72, 0.190, 0.330),
             (proj * 1.00, 0.330, 0.470),
             (proj * 0.84, 0.470, h))

    def put(mt, off, a, b):
        lo, hi = at, at + d * (front + off)
        if axis == 0:
            bx(m, mt, min(lo, hi), max(lo, hi), y0 + a, y0 + b, u0, u1)
        else:
            bx(m, mt, u0, u1, y0 + a, y0 + b, min(lo, hi), max(lo, hi))

    if shadow is not None:                       # dark reveal under the crown
        put(shadow, 0.055, -0.045, 0.002)
    for off, a, b in steps:
        put(mat, off, a, b)


def cased_opening(m, mat, face, at, u0, u1, y1, depth=0.46, casing=0.42,
                  proud=0.055, shadow=None):
    """A cased opening built as a REAL thickness: jamb returns + head + casing.

    The app cuts a genuine hole for a `passage` opening and draws no panel, so
    what the round-2 critic read as "a pale translucent slab" is the far room's
    bare wall seen through an unframed hole.  A doorway only reads as a doorway
    when it has depth, so this stands a lining `depth` ft into the room on both
    jambs and the head, and lays casing on the room face around it.

    `at` is the wall plane, `face` points INTO the room, `u0..u1` the hole.
    """
    axis, d = _AX[face]

    def put(mt, o0, o1, uu0, uu1, yy0, yy1):
        """o* = distance into the room from the wall plane; uu* along the wall."""
        lo, hi = at + d * o0, at + d * o1
        if axis == 0:
            bx(m, mt, min(lo, hi), max(lo, hi), yy0, yy1, uu0, uu1)
        else:
            bx(m, mt, uu0, uu1, yy0, yy1, min(lo, hi), max(lo, hi))

    # The jamb lining runs AWAY from the room, into the wall cavity between the
    # two rooms -- that is where a real jamb is, and it keeps the casing flush
    # with the room's wall plane (a lining projecting inward would leave the
    # casing floating half a foot off the wall, above the baseboard).
    # This renderer has no shadows, so the depth of the reveal has to come from
    # albedo: the jamb is drawn a few steps below the casing, which is what a
    # real jamb reads as anyway.
    jamb = shadow or mat
    t = 0.075
    put(jamb, 0.0, -depth, u0, u0 + t, 0.0, y1)          # jamb lining, side 1
    put(jamb, 0.0, -depth, u1 - t, u1, 0.0, y1)          # jamb lining, side 2
    put(jamb, 0.0, -depth, u0, u1, y1 - t, y1)           # head lining
    # casing on the room face, flush with the wall plane and standing proud
    put(mat, 0.0, proud, u0 - casing, u0 + t, 0.0, y1 + casing)
    put(mat, 0.0, proud, u1 - t, u1 + casing, 0.0, y1 + casing)
    put(mat, 0.0, proud, u0 - casing, u1 + casing, y1 - t, y1 + casing)


# ------------------------------------------------------- ROUND 3 stone facades
# Every quartz top and every marble backsplash in the room goes through one of
# these two, so the whole stone program is tuned in one place.

def top_stone(m, at, u0, u1, w0, w1, seed, cell=0.044, base=0.855, face="+y"):
    """A quartz top: cloudy white ground under a soft vein net.

    A short `step` with a high `meander` is what keeps the veins CURVING.  The
    first round-3 pass used step 0.20 / meander 0.44 and the veins came out as
    long straight diagonals with branches -- a palm frond, not stone.
    """
    v = Veins(u0, u1, w0, w1, seed, count=max(5, int((u1 - u0 + w1 - w0) / 0.85)),
              step=0.125, width=0.085, meander=0.80, branch=1.1)
    stone_field(m, TOPS, face, at, u0, u1, w0, w1, seed, cell=cell,
                base=base, cloud=0.52, cloud_scale=0.72, grain=0.155,
                grain_scale=5.2, veins=v, vein_amp=0.80)


def splash_stone(m, face, at, u0, u1, w0, w1, seed, cell=0.052, base=0.86):
    """The backsplash.  The critic metered ours at 163 / sd 5.1 against photo F's
    173.4 / sd 19.0 and asked for "counter value with broad soft clouding" -- so
    this is nearly all cloud: the veining is half the width and a third of the
    depth of the tops', because a backsplash slab is cut from the quieter part
    of the same stone and sits in the cabinets' shade."""
    v = Veins(u0, u1, w0, w1, seed, count=max(4, int((u1 - u0) / 1.15)),
              step=0.115, width=0.055, meander=0.85, branch=0.7)
    stone_field(m, SPLASH, face, at, u0, u1, w0, w1, seed, cell=cell,
                base=base, cloud=0.66, cloud_scale=0.78, grain=0.19,
                grain_scale=5.6, veins=v, vein_amp=0.42)


def _rng(seed):
    s = [seed & 0xFFFFFFFF]

    def nxt():
        s[0] = (1103515245 * s[0] + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return nxt


def arc_tube(m, mat, r, cx, cy, cz, a0, a1, segs, tube, plane="zy"):
    """Sweep a small cylinder along a circular arc (for the gooseneck faucet)."""
    prev = None
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        if plane == "zy":
            p = (cx, cy + r * math.sin(a), cz + r * math.cos(a))
        else:
            p = (cx + r * math.cos(a), cy + r * math.sin(a), cz)
        if prev is not None:
            dx, dy, dz = p[0] - prev[0], p[1] - prev[1], p[2] - prev[2]
            L = math.sqrt(dx * dx + dy * dy + dz * dz)
            mid = ((p[0] + prev[0]) / 2, (p[1] + prev[1]) / 2, (p[2] + prev[2]) / 2)
            rx = math.atan2(dz, dy) if abs(dy) + abs(dz) > 1e-9 else 0.0
            m.add(cylinder(tube, L * 1.25, seg=10, anchor="center"), mat,
                  at=mid, rot_x=-rx)
        prev = p


# ---------------------------------------------------------------- polygon walls
_CENTROID = (sum(p[0] for p in POLY) / len(POLY),
             sum(p[1] for p in POLY) / len(POLY))


def edge_info(i):
    ax, az = POLY[i]
    bx_, bz = POLY[(i + 1) % len(POLY)]
    dx, dz = bx_ - ax, bz - az
    ln = math.hypot(dx, dz)
    ux, uz = dx / ln, dz / ln
    nx, nz = -uz, ux                       # one of the two normals
    mx, mz = (ax + bx_) / 2, (az + bz) / 2
    if (_CENTROID[0] - mx) * nx + (_CENTROID[1] - mz) * nz < 0:
        nx, nz = -nx, -nz                  # point it INTO the room
    return {"a": (ax, az), "b": (bx_, bz), "u": (ux, uz), "n": (nx, nz),
            "len": ln, "rot": math.atan2(-dz, dx)}


def edge_box(m, mat, i, y0, y1, thick, u0=None, u1=None, out=0.0):
    """A box lying along wall edge `i`, `thick` deep into the room.

    u0/u1 are distances along the edge from POLY[i]; `out` pushes the box
    further into the room (for the projecting steps of a crown).
    """
    e = edge_info(i)
    u0 = 0.0 if u0 is None else u0
    u1 = e["len"] if u1 is None else u1
    if u1 - u0 < 1e-4:
        return
    ux, uz = e["u"]
    nx, nz = e["n"]
    cu = (u0 + u1) / 2.0
    cx = e["a"][0] + ux * cu + nx * (thick / 2.0 + out)
    cz = e["a"][1] + uz * cu + nz * (thick / 2.0 + out)
    m.add(box(u1 - u0, y1 - y0, thick), mat, at=(cx, y0, cz), rot_y=e["rot"])


def emit(m, name, room=6, y=None, scale=1.0):
    lo, hi = m.bounds()
    path = os.path.join(OUT, name.replace(" ", "_") + ".glb")
    m.save(path)
    pos = ((lo[0] + hi[0]) / 2.0, lo[1] if y is None else y, (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=scale)
    print(f"{name:26s} x{lo[0]:6.2f}..{hi[0]:6.2f} y{lo[1]:5.2f}..{hi[1]:5.2f} "
          f"z{lo[2]:6.2f}..{hi[2]:6.2f} -> {res['action']}")
    return res
