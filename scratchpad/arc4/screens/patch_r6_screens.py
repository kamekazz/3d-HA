# -*- coding: utf-8 -*-
"""ROUND 6 -- screens.  Surgical patch: 4 sites in ar2.py, 1 in a2kit.py."""
import io, os, sys

R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", ".."))
AR2 = os.path.join(R, "scratchpad", "bsmt", "ar2.py")
KIT = os.path.join(R, "scratchpad", "bsmt", "a2kit.py")


def sub(path, old, new, label):
    s = io.open(path, encoding="utf-8").read()
    if new in s:
        print("  already applied:", label)
        return
    if s.count(old) != 1:
        raise SystemExit("PATCH FAILED (%d matches): %s" % (s.count(old), label))
    io.open(path, "w", encoding="utf-8").write(s.replace(old, new))
    print("  patched:", label)


# ---- 1. the SCRN material -------------------------------------------------
sub(AR2, '''SCRN = Material("a2scr", "#0a0c10", roughness=0.25, emissive="#12202c",
                emissive_strength=1.1)''',
    '''# ROUND 6.  Every CRT in this room photographs DARK -- fifteen frames, day and
# night, and not one lit attract screen among them (the report lists them).  So
# this is the material of a switched-off monitor and the whole job is to make
# it read as GLASS and not as a hole cut in the cabinet.  Round 5's #12202c at
# strength 1.1 did the opposite: glTF emissive is a flat untextured factor, so
# every screen in the room rendered as one uniform navy slab BRIGHTER than its
# own bezel -- a dim television, which is precisely what the photographs do not
# show.  A dead CRT is a near-black diffuse behind smooth front glass, so:
# roughness 0.06, which lets `scene.environment` (a PMREM of three's
# RoomEnvironment, see scene.js) land a real specular that MOVES with the
# camera; and the emissive drops to a residue -- enough that the panel is not
# an absolute void on the night ramp, where the photographs show the glass
# picking up the RGB cove, and far too little to read as lit.
SCRN = Material("a2scr", "#0a0c10", roughness=0.06, emissive="#0a141c",
                emissive_strength=0.30)''', "SCRN material")

# ---- 2. the crt() helper, immediately before upright() --------------------
sub(AR2, '''def upright(m, cx, cz, rot, art, slug, bw=2.20, bd=2.55, top=6.10, seed=1,''',
    '''def crt(sub, mat, p, rect=None, bulge=0.060, n=2):
    """ROUND 6.  A monitor face as a shallow cap, where round 5 had a flat quad.

    `p` is the screen rectangle's four corners (bl, br, tr, tl, as `uvq` takes
    them) and this draws that rectangle pushed out along its own normal by
    `bulge * (1-(2u-1)^2) * (1-(2v-1)^2)` -- flush with the bezel all round the
    rim, proud at the centre.  Two things follow that a flat quad cannot do,
    and between them they are what makes a DARK screen read as glass rather
    than as a rectangular hole: the environment reflection sweeps ACROSS the
    face as the camera moves, instead of the whole panel changing value
    together on one shared normal; and the rim, tilted away from the room,
    falls into the soft edge shading a recessed tube has.  Both are lit by the
    scene, so neither survives the camera standing still -- which is the test
    ROOM-BRIEF sets for anything that looks like baked light.

    `rect` is an atlas UV rect for the four south machines that carry printed
    screen art, None for the twelve that carry none.
    """
    p0, p1, p2, p3 = p
    ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    vx, vy, vz = p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    u0, v0, u1, v1 = rect if rect else (0.0, 0.0, 1.0, 1.0)
    verts, uvs = [], []
    for j in range(n + 1):
        v = j / float(n)
        for i in range(n + 1):
            u = i / float(n)
            k = bulge * (1.0 - (2.0 * u - 1.0) ** 2) * (1.0 - (2.0 * v - 1.0) ** 2)
            a = [(1 - u) * (1 - v) * p0[c] + u * (1 - v) * p1[c]
                 + u * v * p2[c] + (1 - u) * v * p3[c] for c in range(3)]
            verts.append((a[0] + nx * k, a[1] + ny * k, a[2] + nz * k))
            uvs.append((u0 + (u1 - u0) * u, v1 + (v0 - v1) * v))
    tris = []
    for j in range(n):
        for i in range(n):
            q = j * (n + 1) + i
            tris.append((q, q + 1, q + n + 2))
            tris.append((q, q + n + 2, q + n + 1))
    sub.add(Part(verts, tris, smooth=True, uv=(uvs if rect else None)), mat)


def upright(m, cx, cz, rot, art, slug, bw=2.20, bd=2.55, top=6.10, seed=1,''',
    "crt() helper")

# ---- 3. the two screen draw calls ----------------------------------------
sub(AR2, '''        uvq(sub, art.SCREEN, scr, art.uv(slug + ".screen"))
    else:
        sub.add(quad(*scr), SCRN)''',
    '''        # ROUND 6 keeps every one of those panels and only curves the glass
        # they are printed on -- see `crt`.
        crt(sub, art.SCREEN, scr, art.uv(slug + ".screen"))
    else:
        # ROUND 6.  The other twelve carry no printed screen art because the
        # photographs show nothing on them to print: all twelve are dark in
        # every frame that sees them, in daylight and in the night set.  They
        # get the same curved dark glass, unpainted.
        crt(sub, SCRN, scr)''', "screen draw calls")

# ---- 4. a2kit's printed-screen factor material ---------------------------
sub(KIT, '''        self.SCREEN = Material("a2scrn_" + name, "#3a3a3a", roughness=0.24,
                               tex=tex, emissive="#12202c",
                               emissive_strength=0.55)''',
    '''        # ROUND 6 keeps the panels and re-tunes the factor to match `ar2.SCRN`,
        # the dark glass the room's other twelve monitors now use: the same
        # near-mirror roughness so the environment reflection reads, and the
        # emissive cut to a residue.  Round 5's 0.55 lifted all four south
        # screens above their own bezels.
        self.SCREEN = Material("a2scrn_" + name, "#343434", roughness=0.08,
                               tex=tex, emissive="#0a141c",
                               emissive_strength=0.22)''', "ArtSet.SCREEN")
print("done")
