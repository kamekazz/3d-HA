"""Round-5 G2, patch 2 -- second preview pass.

  * Legends Ultimate's deck read as two big grey rings, i.e. a face.  The
    photograph resolves NO controls there, so the print should be a plain
    printed plate for the real controls (DECKS) to sit on, not screened
    target rings.
  * Its flank was still a near-black slab at 64 px; the seam and the kick
    rail carry it, so they get contrast.
  * T2's screen metered 8.1 -- ROOM-BRIEF: a pure-black surface reads as a
    hole in the room.  Lifted to a dark reflection.
  * Champion Edition's ghosted fighter still had polygon edges.  Broken up
    with soft discs.
"""
import io
import os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_g2_frag.py")
s = io.open(p, encoding="utf-8").read()


def sub(old, new, why):
    global s
    if old not in s:
        raise SystemExit("MISS (%s):\n%s" % (why, old[:120]))
    s = s.replace(old, new)


# ---- 1. Legends Ultimate deck: printed plate, not target rings
sub('''    # two screened cluster outlines -- printed guides, not controls
    for sx in (72.0, 184.0):
        _ring(b, sx, 128.0, 46.0, 40.0, 2.6, _c("#767d88"), 0.75, n=40)
        _ring(b, sx, 128.0, 24.0, 21.0, 2.0, _c("#5c626c"), 0.60, n=32)
    _text(b, "1", 72, 56, 24.0, _c("#8d939d"), weight=0.22, xs=xs, align="c")
    _text(b, "2", 184, 56, 24.0, _c("#8d939d"), weight=0.22, xs=xs, align="c")''',
    '''    # ONE printed control plate with a silver keyline -- the real controls
    # (DECKS['legends-ultimate']) stand on it.  An earlier pass screened two
    # big target rings here and they read as a face at panel scale.
    _rrect(b, 10, 46, 246, 208, 8.0, _c("#2a2f39"), 1.0)
    _rrect(b, 14, 50, 242, 204, 6.0, _c("#1c2028"), 1.0)
    _rect(b, 14, 50, 242, 54, _c("#8b919b"), 0.55)
    _rect(b, 14, 200, 242, 204, _c("#0b0d11"), 0.7)
    _rect(b, 126, 54, 130, 200, _c("#3d434d"), 0.55)
    _text(b, "1", 66, 78, 24.0, _c("#7d838d"), weight=0.22, xs=xs, align="c")
    _text(b, "2", 190, 78, 24.0, _c("#7d838d"), weight=0.22, xs=xs, align="c")''',
    "lu deck plate")

# ---- 2. Legends Ultimate flank: raise the seam and kick so it is not a slab
sub('''    _rect(b, 0, 148, 256, 151, _c("#040407"), 0.85)
    _rect(b, 0, 151, 256, 154, _c("#31353e"), 0.55)''',
    '''    _rect(b, 0, 146, 256, 150, _c("#050508"), 0.95)
    _rect(b, 0, 150, 256, 156, _c("#4a4f5a"), 0.75)
    _rect(b, 0, 62, 256, 65, _c("#050508"), 0.55)
    _rect(b, 0, 65, 256, 68, _c("#3b4049"), 0.45)''', "lu side seam")
sub('_rect(b, 0, 243, 256, 250, _c("#6d727c"), 0.75)',
    '_rect(b, 0, 240, 256, 250, _c("#878d97"), 0.90)', "lu side kick")
sub('_sheen(b, 150.0, 74.0, 4.0, 252.0, _c("#3a3f4a"), 0.55)',
    '_sheen(b, 150.0, 74.0, 4.0, 252.0, _c("#464c58"), 0.65)', "lu side sheen")

# ---- 3. T2 screen: lift off pure black
sub('''    b = _buf("#08080d")
    _field(b, lambda x, y, c: _mix(_c("#101019"), _c("#040407"),
                                   min(1.0, (y / 220.0) ** 0.7
                                       + abs(x - 70) / 420.0)))
    _sheen(b, 44.0, 40.0, 0.0, 256.0, _c("#1d2433"), 0.5)
    _poly(b, [(150, 22), (250, 8), (250, 34), (150, 50)], _c("#171d29"), 0.6)''',
    '''    b = _buf("#14161f")
    _field(b, lambda x, y, c: _mix(_c("#1e2231"), _c("#0a0b11"),
                                   min(1.0, (y / 220.0) ** 0.7
                                       + abs(x - 70) / 420.0)))
    _sheen(b, 44.0, 44.0, 0.0, 256.0, _c("#39435c"), 0.6)
    _poly(b, [(150, 22), (250, 8), (250, 34), (150, 50)], _c("#2b3346"), 0.7)
    _poly(b, [(24, 176), (96, 168), (104, 214), (28, 222)], _c("#242b3c"),
          0.55)''', "t2 screen")

# ---- 4. Champion Edition ghost: break the polygon edges with soft discs
sub('    _sheen(b, 128.0, 120.0, 20.0, 210.0, _c("#b9d2f2"), 0.18)',
    '''    for (cx, cy, rx, ry, al) in ((104, 92, 34, 26, 0.13),
                                 (128, 124, 62, 44, 0.10),
                                 (188, 96, 40, 24, 0.12),
                                 (232, 82, 22, 18, 0.14),
                                 (124, 178, 46, 30, 0.10),
                                 (66, 156, 32, 30, 0.09),
                                 (150, 116, 74, 52, 0.07)):
        _disc(b, cx, cy, rx, ry, PALE, al)
    _sheen(b, 128.0, 120.0, 20.0, 210.0, _c("#b9d2f2"), 0.18)''', "ce ghost soft")

io.open(p, "w", encoding="utf-8").write(s)
print("patched _g2_frag.py")
