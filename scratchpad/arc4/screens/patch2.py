# -*- coding: utf-8 -*-
import io, os
R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
AR2 = os.path.join(R, "scratchpad", "bsmt", "ar2.py")
def sub(path, old, new, label):
    s = io.open(path, encoding="utf-8").read()
    if s.count(old) != 1:
        raise SystemExit("FAILED (%d): %s" % (s.count(old), label))
    io.open(path, "w", encoding="utf-8").write(s.replace(old, new)); print("patched:", label)

sub(AR2, 'SCRN = Material("a2scr", "#303338", roughness=0.50, metallic=0.05)',
    '''SCRN = Material("a2scr", "#3f434a", roughness=0.34, metallic=0.10)''',
    "SCRN material")

OLD_CRT = '''    u0, v0, u1, v1 = rect if rect else (0.0, 0.0, 1.0, 1.0)
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
    sub.add(Part(verts, tris, smooth=True, uv=(uvs if rect else None)), mat)'''
NEW_CRT = '''    u0, v0, u1, v1 = rect if rect else (0.0, 0.0, 1.0, 1.0)
    verts, uvs, cols = [], [], []
    for j in range(n + 1):
        v = j / float(n)
        for i in range(n + 1):
            u = i / float(n)
            k = bulge * (1.0 - (2.0 * u - 1.0) ** 2) * (1.0 - (2.0 * v - 1.0) ** 2)
            a = [(1 - u) * (1 - v) * p0[c] + u * (1 - v) * p1[c]
                 + u * v * p2[c] + (1 - u) * v * p3[c] for c in range(3)]
            verts.append((a[0] + nx * k, a[1] + ny * k, a[2] + nz * k))
            uvs.append((u0 + (u1 - u0) * u, v1 + (v0 - v1) * v))
            # THE GRADIENT.  A near-vertical sheet of dark glass in a room with
            # a bright ceiling and a dark floor is brighter across its top and
            # darker across its bottom -- read it off any of the daylight
            # frames (v4 6 Golden Tee, v4 7 NBA Jam).  It is a GRADIENT, not a
            # highlight: it does not name a light source, it does not stay put
            # in the wrong place when the camera moves, and it is the one thing
            # this renderer cannot supply on its own -- `scene.environment` is
            # measured below as contributing nothing here (see the report's
            # mirror probe: a perfect white mirror on this quad renders luma
            # 8.4, sd 0.7).  `rim` darkens the whole perimeter, which is the
            # soft edge shading a tube recessed behind a bezel has.
            rim = 0.93 if (i in (0, n) or j in (0, n)) else 1.0
            g = (0.72 + 0.25 * v) * rim
            cols.append((g, g, g))
    tris = []
    for j in range(n):
        for i in range(n):
            q = j * (n + 1) + i
            tris.append((q, q + 1, q + n + 2))
            tris.append((q, q + n + 2, q + n + 1))
    sub.add(Part(verts, tris, smooth=True, colors=cols,
                 uv=(uvs if rect else None)), mat)'''
sub(AR2, OLD_CRT, NEW_CRT, "crt() vertex-colour gradient")
