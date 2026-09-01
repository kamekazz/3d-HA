# -*- coding: utf-8 -*-
"""Fourth pass: pay for the Legends Ultimate deck instead of asking someone
else's panel to.

The nebula was five ALPHA-BLENDED soft ellipses and the stars were 18
anti-aliased discs.  At 30 output rows the box filter destroys the softness
anyway, and every intermediate value it produces is a colour zlib has not seen
before -- the panel metered 0.65 bytes/texel against round 5's 0.15-0.30.  This
makes the same drawing out of OPAQUE masses and hard 1-texel stars: the same
composition, none of the intermediate values.  It is a fidelity dial on
sub-texel softness, not a content cut -- nothing is removed.
"""
import io
import os

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_r7_decks.py")
d = io.open(Q, encoding="utf-8").read()

OLD = '''    for (cx, cy, rx, ry, col, al) in (
            (214.0, 120.0, 62.0, 118.0, "#4e1442", 0.90),
            (226.0, 100.0, 40.0, 76.0, "#7a2260", 0.75),
            (238.0, 138.0, 26.0, 50.0, "#a8367a", 0.50),
            (168.0, 168.0, 40.0, 58.0, "#2a0e30", 0.70),
            (52.0, 70.0, 44.0, 62.0, "#1b1530", 0.65)):
        _disc(b, cx, cy, rx, ry, _c(col), al)
    # star specks -- sparse, and tall enough to survive the box filter
    for k in range(18):
        sx = 8.0 + _h2(k, 3, 77) * 240.0
        sy = 10.0 + _h2(k, 9, 91) * 200.0
        r = 1.3 + _h2(k, 5, 12) * 1.1
        _disc(b, sx, sy, r, r * 3.0, _c("#f2f0fa"), 0.95)'''
NEW = '''    for (cx, cy, rx, ry, col) in (
            (214.0, 120.0, 62.0, 118.0, "#3c1035"),
            (222.0, 112.0, 46.0, 88.0, "#5c1a4c"),
            (232.0, 126.0, 28.0, 54.0, "#8a2c66"),
            (166.0, 170.0, 38.0, 54.0, "#231029"),
            (52.0, 70.0, 42.0, 60.0, "#191428")):
        _disc(b, cx, cy, rx, ry, _c(col), 1.0)
    # star specks.  ONE OUTPUT TEXEL EACH, drawn as hard rectangles on the
    # texel grid: an anti-aliased disc here only manufactures intermediate
    # colours the box filter then averages away, and they are not free.
    for k in range(16):
        sx = 6.0 + int(_h2(k, 3, 77) * 78.0) * 3.1
        sy = 8.0 + int(_h2(k, 9, 91) * 24.0) * 8.0
        _rect(b, sx, sy, sx + 3.1, sy + 8.0, _c("#f2f0fa"), 1.0)'''
assert OLD in d
d = d.replace(OLD, NEW)
io.open(Q, "w", encoding="utf-8").write(d)
print("patched", Q)
