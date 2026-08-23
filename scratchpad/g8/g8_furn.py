"""Everything that stands in or hangs on room 7, from the v3 photos.

Wall assignment (derivation in the report):
  NORTH z=0     KIES banner, two skateboards, the broom rail and cleaning shelf
  WEST  x=0     three grey metal cabinets (the plan draws them at z 7.4-15.9),
                the red rolling tool chest, extinguisher, hose, feed sacks
  EAST  x=20.4  TV, prints, snowboard, skateboards, scooter, signage, the black
                pegboard and the Liqui Moly clock, the yellow ride-on car, the
                white moulded chair, the speaker cabinet and the wall fan

Everything on the north wall hangs off the furring face (gk.NF), not z=0.
"""
import math

from gk import *   # noqa: F401,F403
import gk as G
import g8_tex as TX

R90 = math.pi / 2


# =========================================================== NORTH: banner
BAN_X0, BAN_X1 = 10.60, 15.80
BAN_Y0, BAN_Y1 = 1.05, 8.15


def banner():
    """The KIES MOTORSPORTS vinyl, as ONE TEXTURED QUAD.

    Round 1 built this out of ~25 axis-aligned boxes -- blocked glyphs, a car
    made of stacked rectangles, a yellow rectangle for the plate -- and the
    critic called it 8-bit pixel art in the dead centre of the hero frame.  It
    is now a photo-derived albedo (see g8_tex.banner_png) on a single quad.

    PROPORTION was wrong too, and is corrected here.  Round 1 hung it 11.25 ft
    wide by 5.88 tall -- LANDSCAPE.  The vinyl rectifies out of the photograph
    at 0.73 W/H, i.e. PORTRAIT, and the check that the rectification is honest
    is that the KIES baseline comes out level and the car's centre split comes
    out vertical.  Sized against the service-door leaf (6.75 ft of opening,
    265 px in the photo) it is about 5.2 x 7.1 ft: a standard 5 x 7 banner.

    Its exact feet ALONG the wall stay approximate -- see _gaps in rooms/7.json;
    the photo's own scale disagrees with itself by 5 ft across this wall.
    """
    m = Model()
    x0, x1, y0, y1 = BAN_X0, BAN_X1, BAN_Y0, BAN_Y1
    VINYL = Material("gvinyl", "#c9c9c6", roughness=0.78,
                     tex=TX.banner_png(), double_sided=False)
    uv_panel(m, VINYL, "n", x0, x1, y0, y1, off=0.035)
    # a hemmed edge and grommets, so the vinyl reads as hung cloth not a decal
    HEM = Material("ghem", "#b9b8b4", roughness=0.80)
    for x in (x0 + 0.03, x1 - 0.03):
        slab(m, HEM, "n", x - 0.035, x + 0.035, y0, y1, t=0.02, off=0.020)
    for yy in (y0 + 0.02, y1 - 0.02):
        slab(m, HEM, "n", x0, x1, yy - 0.035, yy + 0.035, t=0.02, off=0.020)
    for (gx, gy) in [(x, y) for x in (x0 + 0.12, (x0 + x1) / 2, x1 - 0.12)
                     for y in (y1 - 0.10, y0 + 0.10)]:
        m.add(cylinder(0.045, 0.02, 8), STEELD, at=(gx, gy, NF + 0.055),
              rot_x=R90)
    return _banner_extras(m)


def _banner_extras(m):
    """The two oval car mirrors and the electrical panel beside the door.

    Photo 1 / photo 6: two lozenge-shaped mirrors printed with a BMW, hung one
    ABOVE the other on the east jamb side of the service door -- not one each
    side, which is what the round-1 verdict's "flanking" implies.  Called out
    as a disagreement in the report.
    """
    for i, (kind, a, b) in enumerate((("blue", 4.55, 7.30),
                                      ("silver", 1.55, 4.30))):
        MIR = Material("gmir_" + kind, "#e6e7e8", roughness=0.35,
                       tex=TX.mirror_car_png(kind), double_sided=False)
        uv_panel(m, MIR, "n", 7.15, 8.10, a, b, off=0.055)
        slab(m, Material("gmirf", "#b9bcc0", roughness=0.4, metallic=0.3), "n",
             7.10, 8.15, a - 0.04, b + 0.04, t=0.05, off=0.02)
    slab(m, GREY, "n", 8.60, 8.92, 7.55, 8.05, t=0.10, off=0.02)
    return m



# ================================================== NORTH: brooms and shelf
def brooms():
    """The mop-and-broom rail west of the service door, and the wire shelf.

    Photo 1 and photo 6: a five-hook rail at shoulder height with two mops, a
    push broom and a soft broom on it, and a white wire shelf below holding
    cleaning bottles.
    """
    m = Model()
    RAIL = Material("gbrail", "#f0efec", roughness=0.55)
    HOOK = Material("gbhook", "#5a5f63", roughness=0.45, metallic=0.4)
    HANDLE = [Material("gbh%d" % i, c, roughness=0.55)
              for i, c in enumerate(("#3557a8", "#3f9e52", "#b5b9bc", "#8fb04a"))]
    HEAD = [Material("gbd%d" % i, c, roughness=0.85)
            for i, c in enumerate(("#22242a", "#e3e2dd", "#6e737a", "#d9d3c2"))]

    bx(m, RAIL, 0.28, 3.20, 4.35, 4.60, NF, NF + 0.14)
    for i in range(5):
        x = 0.50 + i * 0.62
        bx(m, HOOK, x - 0.05, x + 0.05, 4.15, 4.38, NF + 0.02, NF + 0.24)
    # four hanging tools: a stick down to the floor, a head at the bottom
    for i, (x, hl, hw, hh) in enumerate(((0.52, 3.55, 0.55, 0.20),
                                         (1.14, 3.35, 0.42, 0.42),
                                         (1.76, 3.70, 0.75, 0.22),
                                         (2.38, 3.20, 0.50, 0.50))):
        top = 4.30
        m.add(cylinder(0.045, hl, 8), HANDLE[i], at=(x, top - hl, NF + 0.14))
        bx(m, HEAD[i], x - hw / 2, x + hw / 2, top - hl - hh, top - hl,
           NF + 0.03, NF + 0.28)
    # wire shelf with cleaning bottles
    SH = Material("gshelf", "#eceae6", roughness=0.5, metallic=0.3)
    bx(m, SH, 0.18, 2.10, 2.52, 2.60, NF, NF + 0.80)
    for x in (0.24, 2.02):
        bx(m, SH, x - 0.03, x + 0.03, 2.60, 3.05, NF + 0.70, NF + 0.78)
    bx(m, SH, 0.18, 2.10, 3.00, 3.06, NF + 0.68, NF + 0.80)
    for i, (x, r, h, c) in enumerate(((0.42, 0.14, 0.72, "#6b48a6"),
                                      (0.75, 0.12, 0.60, "#3f8f92"),
                                      (1.05, 0.15, 0.80, "#d9d5cc"),
                                      (1.40, 0.13, 0.66, "#c8b427"),
                                      (1.75, 0.14, 0.74, "#3557a8"))):
        m.add(cylinder(r, h, 10), Material("gbot%d" % i, c, roughness=0.4),
              at=(x, 2.60, NF + 0.36))
        m.add(cylinder(r * 0.45, 0.10, 8), PLASW, at=(x, 2.60 + h, NF + 0.36))
    return m


# ============================================== WEST: grey metal cabinets
def cabinets():
    """Three two-door grey steel cabinets, 8.55 ft of run.

    The floor plan draws this run at world x 19.46-21.68, z 20.41-28.90
    (garage-local x 0.56-2.78 by z 7.41-15.90) and photos 1, 2, 4 and 5 show
    what it is: matt grey two-door metal cabinets with white lever handles,
    boxes and a helmet bag stored on top.
    """
    m = Model()
    z0, dep, hh = 7.35, 2.20, 6.45
    for u in range(3):
        a = z0 + u * 2.85
        b = a + 2.80
        bx(m, GREY, 0.05, dep, 0.10, hh, a, b)                    # carcass
        bx(m, GREYD, 0.05, 0.16, 0.0, 0.10, a, b)                 # plinth
        for (c, d) in ((a + 0.05, (a + b) / 2 - 0.02),
                       ((a + b) / 2 + 0.02, b - 0.05)):           # two doors
            bx(m, GREY, dep, dep + 0.055, 0.30, hh - 0.10, c, d)
            bx(m, GREYD, dep + 0.02, dep + 0.03, 0.30, hh - 0.10,
               c - 0.015, c + 0.015)
        # white lever handles either side of the centre joint
        for dz in (-0.16, 0.16):
            bx(m, PLASW, dep + 0.055, dep + 0.20, 3.05, 3.24,
               (a + b) / 2 + dz - 0.03, (a + b) / 2 + dz + 0.03)
        bx(m, GREYD, dep, dep + 0.06, hh - 0.10, hh, a + 0.05, b - 0.05)
    # TWO KIES posters taped flat to the cabinet doors (photos 1 and 4 -- the
    # critic listed the second as missing).  Textured, not blocked out.
    POST = Material("gkpost", "#e9e9e6", roughness=0.72,
                    tex=TX.kies_poster_png(), double_sided=False)
    for a in (z0 + 0.55, z0 + 3.55):
        uv_panel(m, POST, "w", a, a + 1.05, 4.05, 5.60, off=dep + 0.062)
        slab(m, Material("gtape", "#f2f2ef", roughness=0.8), "w",
             a + 0.42, a + 0.62, 5.58, 5.70, t=0.02, off=dep + 0.056)
    # stored on top: a black helmet bag, two card boxes, a spare wheel bag
    m.add(rounded_box(1.75, 0.95, 1.35, 0.28, 3), BLKM,
          at=(1.05, hh, z0 + 1.35))
    bx(m, CARD, 0.25, 1.85, hh, hh + 0.85, z0 + 3.15, z0 + 4.55)
    bx(m, CARD, 0.30, 1.70, hh + 0.85, hh + 1.45, z0 + 3.40, z0 + 4.35)
    m.add(cylinder(0.72, 0.55, 14), BLKM, at=(1.10, hh, z0 + 7.05), rot_z=R90)

    # The red generator standing off the NORTH end of the run (photo 4).  One
    # of the critic's sixteen missing items.
    gz = z0 - 1.85
    bx(m, RED, 0.35, 2.15, 0.42, 1.95, gz, gz + 1.70)             # tank/body
    bx(m, REDD, 0.35, 2.15, 1.05, 1.15, gz - 0.02, gz + 1.72)
    bx(m, BLKM, 0.30, 2.20, 1.95, 2.18, gz - 0.05, gz + 1.75)     # control deck
    bx(m, STEELD, 0.55, 1.95, 2.18, 2.42, gz + 0.20, gz + 1.50)   # engine cowl
    for (a, b) in ((0.30, 0.44), (2.06, 2.20)):                   # tube frame
        for z in (gz - 0.05, gz + 1.75):
            bx(m, BLKM, a, b, 0.0, 2.55, z - 0.07, z + 0.07)
    bx(m, BLKM, 0.30, 2.20, 2.48, 2.62, gz - 0.05, gz + 1.75)
    for z in (gz + 0.28, gz + 1.42):                              # wheels
        m.add(cylinder(0.30, 0.24, 12), BLKM, at=(2.28, 0.30, z), rot_z=R90)
    return m


# ============================================== WEST: red chest and corner
def tool_chest():
    """The red rolling tool cabinet and the SW-corner clutter.

    Photos 2, 4 and 5: a red Milwaukee roller with a black work top, standing
    between the grey cabinets and the door opening.  Photo 1's near-left corner
    adds a white storage box with the red fire extinguisher over it, a coiled
    white hose and a sack of feed on the floor.
    """
    m = Model()
    z0, z1 = 16.40, 20.20
    bx(m, RED, 0.10, 1.95, 0.30, 3.05, z0, z1)                    # carcass
    bx(m, BLKM, 0.05, 2.02, 3.05, 3.22, z0 - 0.03, z1 + 0.03)     # work top
    for i in range(4):                                            # drawer faces
        y = 0.42 + i * 0.62
        bx(m, REDD, 1.95, 2.00, y, y + 0.52, z0 + 0.06, z1 - 0.06)
        bx(m, SILV, 1.98, 2.08, y + 0.34, y + 0.44, z0 + 0.30, z1 - 0.30)
    # castors: seated so the tyre's BOTTOM is exactly y=0.  Round 1 put the
    # wheel centre on the slab, which sank half of it and then, because the
    # piece was placed with on_floor, lifted the whole chest clear of the
    # floor -- the critic measured 0% darkening and no contact under it.
    for z in (z0 + 0.35, z1 - 0.35):
        for x in (0.35, 1.70):
            m.add(cylinder(0.15, 0.30, 10), BLKM, at=(x, 0.15, z), rot_z=R90)
    # a red top chest sitting on the roller
    bx(m, RED, 0.15, 1.85, 3.22, 4.05, z0 + 0.20, z1 - 1.30)
    bx(m, BLKM, 0.12, 1.90, 4.05, 4.14, z0 + 0.17, z1 - 1.27)

    # SW corner: the white storage box.  The coiled hose and the feed sack are
    # NO LONGER inside the chest's own footprint -- round 1 stood both at
    # x 1.1-1.35, z 18-19, which is x 0.10-1.95 / z 16.4-20.2, i.e. half buried
    # in the carcass.  Photo 1's foreground has them OUT on the open floor,
    # east of the chest and close to the camera.
    bx(m, PLASW, 0.10, 1.65, 0.0, 1.55, 20.55, 21.35)
    bx(m, Material("gwbl", "#c9cdd0", roughness=0.5),
       0.10, 1.65, 1.35, 1.45, 20.52, 21.38)
    HOSE = Material("ghose", "#e8e6e0", roughness=0.55)
    for i in range(6):                                            # hose coil
        m.add(torus(0.70 - i * 0.052, 0.078, 22, 6), HOSE,
              at=(3.00, 0.10 + i * 0.135, 19.45))
    m.add(rounded_box(1.65, 0.60, 1.10, 0.24, 3),
          Material("gfeed", "#ddd0a0", roughness=0.92), at=(3.25, 0.0, 20.55))
    m.add(rounded_box(1.42, 0.34, 0.94, 0.20, 3),
          Material("gfeedk", "#c8b445", roughness=0.92), at=(3.20, 0.58, 20.55))
    slab(m, Material("gfeedl", "#f0ece0", roughness=0.9), "w",
         20.25, 20.90, 0.16, 0.50, t=0.02, off=3.80)
    return m


# ============================================== WEST: fire extinguisher
def extinguisher():
    """The red ABC extinguisher on its wall bracket, west wall, south end.

    The critic's most-visible missing item: it fills the bottom-left foreground
    of the hero frame in photo 1 -- chrome valve and pull ring, a white
    instruction band with the yellow A/B/C column, a black hose strap.  Round 1
    had a 0.32 ft red cylinder buried inside the tool chest's own carcass.
    """
    m = Model()
    x, z, y0 = 0.42, 20.72, 2.55
    RD = Material("gextr", "#b01c17", roughness=0.42, metallic=0.10)
    CHR = Material("gextc", "#c8ccd0", roughness=0.28, metallic=0.65)
    m.add(cylinder(0.36, 1.42, 16), RD, at=(x + 0.36, y0, z))       # cylinder
    m.add(cylinder(0.36, 0.10, 16), Material("gextrd", "#8c1410",
                                             roughness=0.45),
          at=(x + 0.36, y0 - 0.09, z))                              # base ring
    m.add(cylinder(0.30, 0.20, 16), RD, at=(x + 0.36, y0 + 1.42, z))
    m.add(cylinder(0.09, 0.30, 10), CHR, at=(x + 0.36, y0 + 1.62, z))  # neck
    bx(m, CHR, x + 0.16, x + 0.66, y0 + 1.90, y0 + 2.02, z - 0.07, z + 0.07)
    m.add(torus(0.15, 0.028, 14, 6), CHR,
          at=(x + 0.36, y0 + 2.00, z - 0.16), rot_x=R90)             # pull ring
    m.add(cylinder(0.13, 0.09, 14), Material("gextg", "#d8dade",
                                             roughness=0.3, metallic=0.5),
          at=(x + 0.62, y0 + 1.72, z), rot_z=R90)                    # gauge
    # instruction band with the yellow A / B / C column
    m.add(cylinder(0.365, 0.46, 16), Material("gextlab", "#eeece6",
                                              roughness=0.6),
          at=(x + 0.36, y0 + 0.62, z))
    bx(m, Material("gexty", "#e3c418", roughness=0.6),
       x + 0.02, x + 0.20, y0 + 0.64, y0 + 1.04, z - 0.14, z + 0.14)
    m.add(cylinder(0.372, 0.09, 16), Material("gextbk", "#26282b",
                                              roughness=0.6),
          at=(x + 0.36, y0 + 0.52, z))
    # black hose looping down the front, and the wall bracket
    for i in range(5):
        t = i / 4.0
        m.add(cylinder(0.045, 0.34, 6), Material("gexth", "#232528",
                                                 roughness=0.6),
              at=(x + 0.74 - 0.10 * t, y0 + 1.55 - t * 1.15, z + 0.10),
              rot_z=0.35 - t * 0.55)
    bx(m, Material("gextbr", "#c62a20", roughness=0.5),
       x - 0.02, x + 0.22, y0 + 0.20, y0 + 1.20, z - 0.30, z + 0.30)
    return m


# ================================================================ EAST: TV
def tv():
    """A 65 in flat panel and the two small framed prints north of it."""
    m = Model()
    z0, z1 = 3.35, 8.05
    slab(m, BLKM, "e", z0, z1, 4.55, 7.20, t=0.13, off=0.05)
    slab(m, BLK, "e", z0 + 0.05, z1 - 0.05, 4.60, 7.15, t=0.03, off=0.18)
    # the two tie-dye prints in black frames, TEXTURED (photo 1, north of the
    # TV): round 1 had them as a yellow and a pink rectangle.
    RB = Material("gartrb", "#e8e8e8", roughness=0.62,
                  tex=TX.rainbow_png(), double_sided=False)
    for (a, b) in ((1.95, 2.75), (2.95, 3.75)):
        slab(m, Material("gfrm", "#26282b", roughness=0.5), "e",
             a, b, 5.35, 6.45, t=0.06, off=0.03)
        uv_panel(m, RB, "e", a + 0.07, b - 0.07, 5.42, 6.38, off=0.092)
    return m


# ========================================================== EAST: pegboard
def pegboard():
    """The black pegboard, the Liqui Moly clock and the small signage.

    Photo 1, right-hand wall, reading from the north end: a framed wave print,
    a line drawing of a car, an M badge, a PARKING ONLY sign, then the pegboard
    with its hooks and caps, with the round Liqui Moly clock above it.
    """
    m = Model()
    z0, z1, y0, y1 = 13.60, 17.60, 3.55, 6.25
    slab(m, CHAR, "e", z0, z1, y0, y1, t=0.09, off=0.03)
    slab(m, Material("gpegf", "#2c2f33", roughness=0.75), "e",
         z0 - 0.06, z1 + 0.06, y0 - 0.06, y1 + 0.06, t=0.05, off=0.03)
    # hook rows -- little dark pegs, dense enough to read as perforation
    for j in range(5):
        yy = y0 + 0.30 + j * 0.52
        for i in range(11):
            zz = z0 + 0.25 + i * 0.35
            slab(m, Material("gpeghk", "#1b1d20", roughness=0.5), "e",
                 zz, zz + 0.16, yy, yy + 0.05, t=0.10, off=0.12)
    # caps hanging on it
    for (zz, c) in ((14.15, "#1e1f22"), (14.75, "#2b2e33"), (16.55, "#23252a")):
        m.add(rounded_box(0.62, 0.36, 0.72, 0.16, 3),
              Material("gcap%d" % int(zz * 10), c, roughness=0.7),
              at=(W - 0.35, 4.55, zz), rot_y=R90)
    # tools on the pegboard
    for (zz, c, hh) in ((15.20, "#c04a2a", 0.75), (15.55, "#3f7fb0", 0.62),
                        (15.90, "#c9a227", 0.70)):
        m.add(cylinder(0.05, hh, 8), Material("gtl%d" % int(zz * 10), c,
                                              roughness=0.5),
              at=(W - 0.22, 5.05, zz))

    # Liqui Moly clock above it.  The photo has a FLAT DISC on the wall with a
    # silver bezel; round 1 built a 0.86 ft SPHERE with a red rectangle on it,
    # which the critic saw bulging off the wall.  Now a 0.09 ft-deep bezel with
    # a textured dial face.
    CLKB = Material("gclkb", "#b7bbbe", roughness=0.30, metallic=0.55)
    # The bezel is a TORUS, not a filled cylinder.  A 30-segment cylinder with
    # averaged normals blends its cap into its rim and shades like a dome --
    # which is how the clock came back as a grey egg a second time, having been
    # a white sphere in round 1.  A ring has no cap to blend.
    m.add(torus(0.685, 0.055, 30, 8), CLKB, at=(W - 0.135, 7.05, 15.45),
          rot_z=R90)
    m.add(cylinder(0.70, 0.045, 26), Material("gclkbk", "#8f9397",
                                              roughness=0.5),
          at=(W - 0.045, 7.05, 15.45), rot_z=R90)               # back can
    DIAL = Material("gclkd", "#f7f7f6", roughness=0.30,
                    tex=TX.clock_png())
    uv_disc(m, DIAL, "e", 15.45, 7.05, 0.660, off=0.125)

    # signage north of the pegboard, all TEXTURED
    PARK = Material("gpark", "#f2f1ee", roughness=0.62,
                    tex=TX.parking_png(), double_sided=False)
    slab(m, Material("gsignf", "#dcdad4", roughness=0.6), "e",
         10.70, 11.60, 4.90, 5.80, t=0.04, off=0.03)
    uv_panel(m, PARK, "e", 10.75, 11.55, 4.95, 5.75, off=0.072)
    slab(m, BLK, "e", 11.85, 13.05, 5.05, 5.40, t=0.04, off=0.03)   # M badge
    # the grey line drawing of an M4 coupe, drawn as a real outline
    LN = Material("gline", "#8f959b", roughness=0.7)
    ol = [(11.70, 5.66), (11.86, 5.90), (12.16, 6.04), (12.52, 6.12),
          (12.90, 6.06), (13.20, 5.90), (13.34, 5.68), (13.34, 5.58),
          (11.70, 5.58)]
    for i in range(len(ol) - 1):
        (za, ya), (zb, yb) = ol[i], ol[i + 1]
        tube(m, LN, (W - 0.06, ya, za), (W - 0.06, yb, zb), r=0.022, seg=5)
    for zc in (12.02, 13.02):                                       # wheels
        for k in range(12):
            a0 = 2 * math.pi * k / 12
            a1 = 2 * math.pi * (k + 1) / 12
            tube(m, LN, (W - 0.06, 5.66 + 0.13 * math.sin(a0),
                         zc + 0.13 * math.cos(a0)),
                 (W - 0.06, 5.66 + 0.13 * math.sin(a1),
                  zc + 0.13 * math.cos(a1)), r=0.020, seg=4)
    WV = Material("gwave", "#e6e9ea", roughness=0.6,
                  tex=TX.wave_png(), double_sided=False)
    slab(m, Material("gwavef", "#2a2c30", roughness=0.5), "e",      # wave print
         11.90, 13.30, 6.70, 7.55, t=0.05, off=0.03)
    uv_panel(m, WV, "e", 11.98, 13.22, 6.78, 7.47, off=0.082)
    return m


# ============================================================ EAST: boards
def boards():
    """The snowboard, two skateboards and the mounted scooter."""
    m = Model()
    # snowboard, nose up
    slab(m, Material("gsnow", "#1c1e22", roughness=0.45), "e",
         8.35, 8.92, 2.35, 7.15, t=0.10, off=0.04)
    slab(m, Material("gsnowe", "#3a3d42", roughness=0.45), "e",
         8.42, 8.85, 2.55, 6.95, t=0.05, off=0.14)
    # skateboards, hung deck-out.  The graphic is a TEXTURE now: round 1 put a
    # flat navy rectangle in the middle of a flat grey rectangle, which is the
    # same "collage of axis-aligned boxes" fault as the banner.
    for (z, a, b, kind) in ((9.55, 2.75, 5.60, "city"),
                            (10.30, 5.35, 7.15, "swirl")):
        DK = Material("gdeck_" + kind, "#e8e8e8", roughness=0.52,
                      tex=TX.deck_png(kind), double_sided=False)
        slab(m, Material("gsk%d" % int(z * 10), "#cfd3d8", roughness=0.55), "e",
             z, z + 0.52, a, b, t=0.09, off=0.04)
        uv_panel(m, DK, "e", z + 0.015, z + 0.505, a + 0.02, b - 0.02, off=0.132)
        for yy in (a + 0.28, b - 0.28):
            slab(m, BLKM, "e", z + 0.12, z + 0.40, yy - 0.09, yy + 0.09,
                 t=0.12, off=0.045)
    # scooter handlebar mounted on the wall
    SC = Material("gsc", "#b02a22", roughness=0.45, metallic=0.2)
    bx(m, SC, W - 0.55, W - 0.42, 4.85, 5.05, 10.05, 11.05)
    for z in (10.05, 11.05):
        m.add(cylinder(0.07, 0.42, 8), BLKM, at=(W - 0.48, 4.62, z))
    m.add(cylinder(0.06, 0.85, 8), Material("gscg", "#4fc9a0", roughness=0.6),
          at=(W - 0.48, 4.05, 10.55))
    return m


# ============================================================== EAST: gear
def gear():
    """Brooms leaning, hanging bags, a shovel and the cat-print towel."""
    m = Model()
    # Two brooms and a shovel leaning against the wall.  Their base slabs move
    # SOUTH of the ride-on's footprint (which now ends at z 14.30) -- round 1
    # ran them from z 14.25 and the car drove straight through them.  The heads
    # sit ON the slab at y=0, and the handle cylinders are seated at y 0.02 so
    # that after rot_x nothing dips below the floor plane: the piece is placed
    # without on_floor, so a negative minimum would sink it and a positive one
    # would leave the whole stand hanging clear of the floor, which is what the
    # critic measured.
    for (z, c, hh, hd) in ((14.95, "#d9d6cf", 5.10, "#2a2c30"),
                           (15.45, "#c9662a", 4.70, "#b8b4ab"),
                           (15.95, "#8a6a40", 5.30, "#3a3d42")):
        m.add(cylinder(0.055, hh, 8), Material("gbr%d" % int(z * 10), c,
                                               roughness=0.55),
              at=(W - 0.55, 0.02, z + 0.34), rot_x=-0.13)
        bx(m, Material("gbrh%d" % int(z * 10), hd, roughness=0.85),
           W - 1.30, W - 0.35, 0.0, 0.22, z - 0.30, z + 0.30)
    # the clear plastic drop sheet hanging behind the ride-on (photo 1) -- one
    # of the critic's missing items, and the reason that stretch of wall reads
    # milky rather than flat white in the photograph.
    SHEET = Material("gsheet", "#f4f5f5", roughness=0.22, opacity=0.55)
    m.add(sag_plane(2.30, 0.60, sag=0.05, nx=8, nz=3, y=0.0, edge_drop=0.02),
          SHEET, at=(W - 0.42, 4.85, 11.55), rot_z=R90 * 0.995)
    bx(m, SHEET, W - 0.52, W - 0.30, 0.02, 0.85, 10.05, 11.30)
    # black gear bag hanging off a wall hook
    bx(m, STEELD, W - 0.30, W - 0.08, 4.85, 5.05, 17.05, 17.45)
    m.add(rounded_box(0.75, 2.05, 1.55, 0.32, 3), BLKM,
          at=(W - 0.55, 2.75, 17.25))
    # a second, taller bag near the door end
    m.add(rounded_box(0.62, 2.60, 1.05, 0.26, 3),
          Material("ggbag", "#2b2f34", roughness=0.7), at=(W - 0.48, 0.0, 18.75))
    # cat-print towel over a rail
    bx(m, STEELD, W - 0.26, W - 0.10, 4.02, 4.14, 16.15, 16.95)
    slab(m, Material("gtow", "#efece4", roughness=0.85), "e",
         16.15, 16.95, 3.05, 4.10, t=0.06, off=0.16)
    for i, c in enumerate(("#d9534f", "#e8b83a", "#4a8fc0", "#5aa469")):
        slab(m, Material("gtowb%d" % i, c, roughness=0.85), "e",
             16.15, 16.95, 3.10 + i * 0.13, 3.18 + i * 0.13, t=0.03, off=0.23)
    return m


# ================================================== EAST floor: ride-on car
RIDE_TIP = 1.43                     # radians: stood on its tail, top facing WEST
RIDE_AT = (W - 1.28, 0.0, 12.60)


def ride_on():
    """The yellow ride-on Lamborghini, stood on its nose against the east wall.

    Round 1 built a flat wedge: a yellow tub, a yellow cowl and four black
    discs.  The eastwall crop of Garage v3 1.jpg shows a moulded toy supercar --
    a BLACK bonnet inlay across the nose, a BLACK bucket seat, a BLACK steering
    wheel on a raked column, a black lower valance and skirts, and five-spoke
    silver rims inside black tyres.  Those four black elements are what make it
    read as a car rather than a yellow slab, and the critic named three of them.

    Authored nose at +X, wheels at y=0, then tipped with rot_z (which runs
    BEFORE the translate, so it tips in the X-Y plane) and turned side-on with
    rot_y.
    """
    body = Model()
    BLKT = Material("gyt", "#181a1d", roughness=0.62)         # tyres, valance
    BLKS = Material("gys", "#232629", roughness=0.55)         # seat, bonnet
    RIM = Material("gyrim", "#b9bdc1", roughness=0.32, metallic=0.6)
    L, WD = 2.05, 1.10                                        # half length/width

    # lower valance and side skirts, black
    bx(body, BLKT, -L, L, 0.02, 0.22, -WD, WD)
    bx(body, BLKT, -L - 0.06, -L + 0.34, 0.16, 0.62, -WD, WD)     # rear diffuser
    bx(body, BLKT, L - 0.30, L + 0.05, 0.10, 0.44, -WD + 0.06, WD - 0.06)
    # yellow body, tapered: a wedge nose and a wide haunch over each axle
    for (a, b, y0, y1, w0) in ((-L, -0.95, 0.30, 0.98, WD),
                               (-0.95, 0.45, 0.30, 1.02, WD),
                               (0.45, 1.45, 0.30, 0.90, WD - 0.05),
                               (1.45, L, 0.28, 0.74, WD - 0.16)):
        bx(body, YEL, a, b, y0, y1, -w0, w0)
    bx(body, YELD, -L, L, 0.56, 0.64, -WD - 0.015, WD + 0.015)    # side crease
    for sz in (-1, 1):                                            # haunches
        body.add(rounded_box(1.10, 0.55, 0.42, 0.16, 3), YEL,
                 at=(-1.30, 0.72, sz * (WD - 0.16)))
        body.add(rounded_box(0.95, 0.48, 0.40, 0.16, 3), YEL,
                 at=(1.05, 0.66, sz * (WD - 0.16)))
    # BLACK bonnet inlay across the nose, and the scuttle/screen behind it
    bx(body, BLKS, 0.55, 1.72, 0.86, 0.99, -0.78, 0.78)
    bx(body, BLKS, 0.26, 0.66, 0.96, 1.26, -0.70, 0.70)
    # BLACK bucket seat with a raised back
    bx(body, BLKS, -1.05, -0.20, 1.00, 1.10, -0.52, 0.52)
    bx(body, BLKS, -1.16, -0.98, 1.00, 1.72, -0.52, 0.52)
    bx(body, BLKS, -1.16, -0.20, 1.06, 1.16, -0.56, -0.44)
    bx(body, BLKS, -1.16, -0.20, 1.06, 1.16, 0.44, 0.56)
    # BLACK steering wheel on a raked column
    body.add(cylinder(0.055, 0.52, 8), BLKS, at=(0.14, 1.04, 0.0), rot_z=-0.55)
    body.add(torus(0.26, 0.045, 16, 6), BLKS, at=(-0.12, 1.40, 0.0),
             rot_z=R90 - 0.55)
    bx(body, BLKS, -0.20, -0.04, 1.36, 1.44, -0.20, 0.20)
    # rear wing
    bx(body, BLKS, -L - 0.02, -L + 0.42, 1.02, 1.10, -0.86, 0.86)
    for sz in (-0.74, 0.74):
        bx(body, BLKS, -L + 0.04, -L + 0.20, 0.74, 1.04, sz - 0.05, sz + 0.05)
    # wheels: black tyre, silver five-spoke rim
    for sx in (-1.32, 1.28):
        for sz in (-1, 1):
            zz = sz * (WD - 0.02)
            body.add(cylinder(0.365, 0.30, 14), BLKT, at=(sx, 0.365, zz - sz * 0.15),
                     rot_x=R90)
            body.add(cylinder(0.215, 0.055, 12), RIM,
                     at=(sx, 0.365, zz + sz * 0.155), rot_x=R90)
            for k in range(5):
                a = 2 * math.pi * k / 5
                body.add(box(0.055, 0.30, 0.045), RIM,
                         at=(sx + 0.145 * math.cos(a), 0.365 + 0.145 * math.sin(a),
                             zz + sz * 0.14), rot_x=R90, rot_z=a)
    for sz in (-0.62, 0.62):                                      # headlights
        bx(body, Material("gyl", "#f2eddc", roughness=0.30),
           L - 0.10, L + 0.02, 0.52, 0.68, sz - 0.22, sz + 0.22)
    for sz in (-0.72, 0.72):                                      # tail lights
        bx(body, Material("gytl", "#a8241c", roughness=0.35),
           -L - 0.02, -L + 0.08, 0.66, 0.80, sz - 0.20, sz + 0.20)

    # Tip it, then measure and drop it so its lowest point lands EXACTLY on the
    # slab.  rot_z runs before the translate, so a 66-degree tip sends the tail
    # 1.9 ft below the origin; round 1 papered over that with on_floor, which
    # is what left the tyre hanging with floor visible underneath.
    # ORIENTATION, corrected.  Round 1 (and this round's first attempt) used
    # rot_z then rot_y=90, which leaves the car's TOP pointing south, so the
    # room sees its flat black UNDERSIDE -- a black slab with yellow edges.
    # rot_z alone at 82 degrees stands it on its tail with the top facing WEST,
    # into the room, which is the face the photograph shows: yellow shoulders,
    # the black bonnet inlay, the seat and the wheel.  Then it is measured and
    # dropped so its lowest point lands exactly on the slab.
    tmp = Model()
    for part, mat in body._parts:
        tmp.add(part, mat, at=(0, 0, 0), rot_z=RIDE_TIP)
    lo, hi = tmp.bounds()
    m = Model()
    for part, mat in body._parts:
        m.add(part, mat, at=((W - 0.11) - hi[0], -lo[1], RIDE_AT[2]),
              rot_z=RIDE_TIP)
    return m


# ========================================================== EAST: the chair
CHAIRS = ((17.55, 3.05, 0.0), (18.60, 4.05, -0.28))


def chair():
    """TWO white moulded shells on wooden dowel legs.

    Photo 1 has a pair of them nested in the NE corner, one carrying a printed
    bag; round 1 built only one.  The legs terminate exactly at y=0 so the
    contact ring under each one has something to sit against.
    """
    m = Model()
    for (cx, cz, ry) in CHAIRS:
        c, s = math.cos(ry), math.sin(ry)

        def at(dx, dz, y):
            return (cx + dx * c + dz * s, y, cz - dx * s + dz * c)

        m.add(rounded_box(1.55, 0.45, 1.45, 0.30, 3), PLASW,
              at=at(0, 0, 1.15), rot_y=ry)
        m.add(rounded_box(1.50, 1.35, 0.42, 0.28, 3), PLASW,
              at=at(0, -0.55, 1.45), rot_y=ry)
        for (dx, dz) in ((-0.55, -0.45), (0.55, -0.45),
                         (-0.55, 0.50), (0.55, 0.50)):
            # the dowel is raked, and the rake runs BEFORE the translate, so
            # the foot lands slightly off the anchor but still exactly on y=0.
            m.add(cylinder(0.055, 1.20, 8), WOOD, at=at(dx, dz, 0.0),
                  rot_x=0.10 if dz > 0 else -0.10,
                  rot_z=0.09 * (1 if dx > 0 else -1), rot_y=ry)
        for dz in (-0.45, 0.50):
            m.add(box(1.20, 0.08, 0.08), STEELD, at=at(0, dz, 1.09), rot_y=ry)
    cx, cz, ry = CHAIRS[1]
    m.add(rounded_box(0.80, 0.75, 0.60, 0.16, 3),
          Material("gseatbag", "#e6dfd2", roughness=0.85),
          at=(cx, 1.60, cz), rot_y=ry)
    m.add(rounded_box(0.62, 0.30, 0.46, 0.10, 2),
          Material("gseatbagr", "#c0392f", roughness=0.85),
          at=(cx, 1.86, cz - 0.06), rot_y=ry)
    return m


# ====================================== EAST corner: speaker, plant, fan
def corner():
    """The black speaker cabinet, the artificial garland and the wall fan."""
    m = Model()
    bx(m, BLK, W - 1.75, W - 0.20, 0.0, 3.05, 1.60, 3.10)
    bx(m, Material("gspkg", "#2f3237", roughness=0.85),
       W - 1.72, W - 0.62, 0.35, 2.75, 1.55, 1.62)
    # garland / artificial plant hooked on the wall
    GRN = [Material("ggl%d" % i, c, roughness=0.85)
           for i, c in enumerate(("#3f6b3c", "#4f7c46", "#33562f", "#5d8a4e"))]
    r = Rnd(19)
    for i in range(66):
        t = i / 65.0
        y = 3.20 + t * 2.35
        rad = 0.62 * math.sin(math.pi * (0.18 + 0.82 * t)) + 0.18
        a = r.f(0, 6.283)
        m.add(rounded_box(0.36, 0.16, 0.30, 0.07, 2), GRN[i % 4],
              at=(W - 0.42 - abs(rad * math.cos(a)) - r.f(0.0, 0.20),
                  y + r.f(-0.14, 0.14), 1.55 + rad * math.sin(a)),
              rot_y=a, rot_z=r.f(-0.5, 0.5))
    for i in range(14):                                       # red berries
        t = i / 13.0
        m.add(cylinder(0.05, 0.05, 6), Material("gberry", "#8e2a24",
                                                roughness=0.6),
              at=(W - 0.70 - r.f(0, 0.2), 3.35 + t * 2.05,
                  1.55 + r.f(-0.5, 0.5)))
    # a red bow and two red garden tools hung in the garland (photo 1: the
    # greenery in this corner carries a red bow and a red blower/saw).  The
    # critic listed the red-bow greenery as missing; the greenery was there,
    # the red was not.
    RED_B = Material("gbow", "#a3231d", roughness=0.55)
    for (dy, dz, rz) in ((0.0, 0.0, 0.0), (0.10, -0.30, 0.7), (0.10, 0.30, -0.7),
                         (-0.22, -0.16, 1.2), (-0.22, 0.16, -1.2)):
        m.add(rounded_box(0.30, 0.42, 0.20, 0.09, 2), RED_B,
              at=(W - 0.72, 4.32 + dy, 1.62 + dz), rot_z=rz)
    for (yy, zz) in ((4.95, 1.30), (4.05, 2.05)):                # red tools
        m.add(rounded_box(0.42, 0.42, 1.05, 0.14, 3), RED_B,
              at=(W - 0.62, yy, zz))
        m.add(cylinder(0.10, 0.85, 8), BLKM, at=(W - 0.62, yy - 0.10, zz + 0.62),
              rot_x=R90 * 0.9)

    # WALL FAN, north wall by the corner.  The photo has a chrome cage fan --
    # a rim, a hub and radial guard wires, all seen nearly face-on because it
    # is on the NORTH wall, not the east.
    CAGE = Material("gfanc", "#c2c6ca", roughness=0.28, metallic=0.65)
    fx, fy = 18.35, 6.55
    m.add(torus(0.78, 0.045, 26, 6), CAGE, at=(fx, fy, NF + 0.30), rot_x=R90)
    m.add(torus(0.46, 0.032, 20, 6), CAGE, at=(fx, fy, NF + 0.27), rot_x=R90)
    for k in range(14):
        a = 2 * math.pi * k / 14
        tube(m, CAGE, (fx, fy, NF + 0.30),
             (fx + 0.78 * math.cos(a), fy + 0.78 * math.sin(a), NF + 0.30),
             r=0.020, seg=4)
    m.add(cylinder(0.20, 0.28, 14), Material("gfanm", "#9aa0a5", roughness=0.4,
                                             metallic=0.5),
          at=(fx, fy, NF + 0.03), rot_x=-R90)
    for k in range(3):                                            # blades
        a = 2 * math.pi * k / 3
        m.add(box(0.62, 0.10, 0.05), Material("gfanb", "#d4d7da",
                                              roughness=0.35, metallic=0.4),
              at=(fx + 0.32 * math.cos(a), fy + 0.32 * math.sin(a), NF + 0.20),
              rot_z=a)
    bx(m, STEELD, fx - 0.09, fx + 0.09, fy + 0.72, 8.30, NF, NF + 0.10)

    # Two skate decks and two caps hung on the NORTH wall beside the corner
    # (photo 1: they read square-on, unlike the foreshortened east-wall art).
    for (x, kind, a, b) in ((16.55, "city", 3.55, 6.45),
                            (17.55, "swirl", 2.55, 5.45)):
        DK = Material("gndk_" + kind, "#e8e8e8", roughness=0.52,
                      tex=TX.deck_png(kind), double_sided=False)
        slab(m, Material("gndkb", "#cfd3d8", roughness=0.55), "n",
             x, x + 0.52, a, b, t=0.09, off=0.02)
        uv_panel(m, DK, "n", x + 0.02, x + 0.50, a + 0.02, b - 0.02, off=0.115)
    for (x, yy) in ((18.55, 5.05), (18.55, 3.45)):                # black caps
        m.add(rounded_box(0.66, 0.40, 0.74, 0.18, 3), BLKM,
              at=(x, yy, NF + 0.34))
        bx(m, BLKM, x - 0.30, x + 0.30, yy + 0.10, yy + 0.16, NF + 0.62,
           NF + 0.90)
    return m


# ================================================== NORTH floor: the stack
def paper():
    """The toilet-roll packs and the Scott box stacked beside the steps."""
    m = Model()
    WRAP = Material("gwrap", "#eef1f4", roughness=0.45)
    BLUE_W = Material("gwrapb", "#2f5f96", roughness=0.45)
    for (x, z, h) in ((7.05, 1.35, 1.15), (7.05, 2.20, 1.15), (7.90, 1.75, 1.15)):
        m.add(rounded_box(0.85, h, 0.80, 0.16, 3), WRAP, at=(x, 0.0, z))
        m.add(rounded_box(0.87, 0.22, 0.82, 0.16, 3), BLUE_W, at=(x, 0.42, z))
    m.add(rounded_box(0.90, 0.62, 0.72, 0.08, 2),
          Material("gscott", "#d9dde2", roughness=0.6), at=(7.45, 1.15, 1.75))
    m.add(rounded_box(0.62, 0.24, 0.50, 0.06, 2), BLUE_W, at=(7.45, 1.77, 1.75))
    return m


PIECES = [
    ("Garage Banner", banner),
    ("Garage Brooms", brooms),
    ("Garage Cabinets", cabinets),
    ("Garage Tool Chest", tool_chest),
    ("Garage TV", tv),
    ("Garage Pegboard", pegboard),
    ("Garage Boards", boards),
    ("Garage Gear", gear),
    ("Garage Ride On Car", ride_on),
    ("Garage Chair", chair),
    ("Garage Speaker", corner),
    ("Garage Paper Stack", paper),
    ("Garage Extinguisher", extinguisher),
]

if __name__ == "__main__":
    # NOTHING is placed with on_floor any more.  `place` seats a model's min-Y
    # at pos.y, and save_and_place's default pos.y IS the authored min-Y, so
    # the geometry lands exactly where it was authored.  on_floor forced pos.y
    # to 0, which lifted every piece whose lowest authored point was slightly
    # negative -- that is why the round-1 critic found the ride-on's tyre and
    # the broom stand's base hanging clear of the floor with floor visible
    # underneath.  Each piece now authors its own contact at y=0.
    tot = 0.0
    for name, fn in PIECES:
        tot += save_and_place(name, fn())["kb"]
    print("  furniture total %.1f KB" % tot)
