"""Marginal cost of ONE button, measured in a saved GLB, three ways.

Builds N-1 copies against N so the fixed glTF header does not pollute the
number, exactly as the round-6 gun agent measured its extrusion.
"""
import os
import sys

_ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"),
           os.path.join(_ROOT, "scratchpad", "arc4", "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from bkit import Model, Material, Part                       # noqa: E402
import ar2                                                   # noqa: E402
import art_g1                                                # noqa: E402

TMP = os.path.join(_ROOT, "scratchpad", "arc4", "r7eng", "glb", "btn.glb")
M = Material("hw", "#ffffff", roughness=0.70)
R, CAPR, H, RISE = 0.082, 0.0623, 0.036, 0.015


def build(kind, n, smooth=True):
    m = Model()
    for i in range(n):
        if kind == "r6_fan":
            v, t, sm = art_g1.button_cap(R, H, 6, 0.45)
        else:
            v, t, sm = ar2.btn_geo(R, CAPR, H, RISE, 6)
        p = Part(v, t, smooth=(sm and smooth))
        p.colors = [(0.8, 0.2, 0.2)] * len(p.verts)
        m.add(p, M, at=(i * 0.5, 0.0, 0.0))
    m.save(TMP)
    return os.path.getsize(TMP), sum(len(q.tris) for q, _ in m._parts), \
        sum(len(q.verts) for q, _ in m._parts)


for kind, smooth, label in (("r6_fan", True, "round 6  domed fan, smooth"),
                            ("r7", True, "round 7  flange+dome, SMOOTH"),
                            ("r7", False, "round 7  flange+dome, FLAT")):
    a = build(kind, 41, smooth)
    b = build(kind, 1, smooth)
    print("%-34s  %5d B/button   %2d tris  %2d verts (authored)"
          % (label, (a[0] - b[0]) / 40.0, (a[1] - b[1]) / 40, (a[2] - b[2]) / 40))
