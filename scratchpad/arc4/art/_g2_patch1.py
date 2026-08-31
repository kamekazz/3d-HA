"""Round-5 G2, patch 1 -- what the first preview sheet exposed.

The big one: the Champion Edition marquee's oval was drawn WIDE in the tile
(rx 92 / ry 62).  The band is pre-squeezed 3.97:1, so a horizontal oval on
the panel has to be drawn TALL in the tile.  The first pass landed a circle
on the cabinet.  Same class of error made four wordmarks half-size.
"""
import io
import os

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_g2_frag.py")
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

# ---- 1. CHAMPION EDITION marquee, rebuilt
i0 = s.index("def ce_marquee(px, ox, oy, tile=TILE):")
i1 = s.index("def ce_side(px, ox, oy, tile=TILE):")
NEW = '''def ce_marquee(px, ox, oy, tile=TILE):
    """Navy ground; a wide gold-ringed OVAL badge fills the centre with
    'CHAMPION' arched over the top and 'EDITION' straight across the bottom;
    a green/gold brush wordmark in the black middle; silver wing forms spill
    out of the oval left and right onto the blue.

    NOTE THE PRE-SQUEEZE.  This band is 2.30 x 0.58 ft, so the tile is
    compressed 3.97:1 horizontally and a HORIZONTAL oval on the panel must be
    drawn TALL in the tile (rx 70, ry 100 -> 1.26 x 0.45 ft).  Drawing it
    wide in the tile, as the first pass did, lands a circle on the cabinet.
    """
    slug = "street-fighter-2-champion-edition"
    xs = _xs(slug, "marquee")
    b = _buf("#1d2a56")
    _field(b, lambda x, y, c: _mix(_c("#31468a"), _c("#131c46"),
                                   min(1.0, abs(y - 118) / 165.0
                                       + abs(x - 128) / 500.0)))
    _sheen(b, 128.0, 110.0, 0.0, 256.0, _c("#4560ad"), 0.35)
    # silver wing forms spilling out of the oval left and right
    for d in (-1, 1):
        base = 128 + d * 62
        tip = 128 + d * 126
        for k in range(6):
            t = k / 5.0
            y0 = 128 - 66 + k * 26
            _poly(b, [(base, y0), (tip, y0 + (t - 0.5) * 52),
                      (tip, y0 + 12 + (t - 0.5) * 52), (base, y0 + 16)],
                  _c("#d6dde9"), 0.78 - 0.07 * k)
        _seg(b, base, 128, tip, 128, 5.0, _c("#f0f3f8"), 0.85, kx=1.0)
    # the oval badge -- TALL in the tile, horizontal on the panel
    _disc(b, 128, 128, 74, 106, _c("#7a5f1c"), 1.0)
    _disc(b, 128, 128, 70, 101, _c("#eccf6a"), 1.0)
    _disc(b, 128, 128, 65, 95, _c("#8a6c22"), 1.0)
    _disc(b, 128, 128, 61, 90, _c("#0b0d16"), 1.0)
    _disc(b, 128, 124, 55, 80, _c("#151a28"), 1.0)
    # CHAMPION arched over the top of the oval
    for i, ch in enumerate("CHAMPION"):
        t = (i - 3.5) / 3.5
        _text(b, ch, 128 + t * 28.0, 74 + 16.0 * t * t, 34.0,
              _c("#f6f8fc"), weight=0.24, xs=xs, wide=1.15, align="c")
    # EDITION straight across the bottom
    _text(b, "EDITION", 128, 206, 30.0, _c("#eff2f8"), weight=0.24, xs=xs,
          wide=1.15, track=0.22, align="c")
    # the green-and-gold brush wordmark in the black middle of the oval
    _text(b, "STREET", 118, 122, 30.0, _c("#0a2610"), weight=0.38, xs=xs,
          wide=1.30, track=0.05, ital=0.24, align="c")
    _text(b, "STREET", 118, 121, 30.0, _c("#6cc94f"), weight=0.22, xs=xs,
          wide=1.30, track=0.05, ital=0.24, align="c")
    _text(b, "FIGHTER", 116, 158, 30.0, _c("#0a2610"), weight=0.38, xs=xs,
          wide=1.28, track=0.05, ital=0.24, align="c")
    _text(b, "FIGHTER", 116, 157, 30.0, _c("#9adc60"), weight=0.22, xs=xs,
          wide=1.28, track=0.05, ital=0.24, align="c")
    _text(b, "II", 162, 160, 44.0, _c("#f0c94e"), weight=0.30, xs=xs,
          wide=1.30, ital=0.26, align="c")
    _rect(b, 0, 0, 256, 6, _c("#0e1430"), 1.0)
    _rect(b, 0, 250, 256, 256, _c("#0e1430"), 1.0)
    _commit(px, ox, oy, b, tile)


'''
s = s[:i0] + NEW + s[i1:]


def sub(old, new, why):
    global s
    if old not in s:
        raise SystemExit("MISS (%s):\n%s" % (why, old[:110]))
    s = s.replace(old, new)


# ---- 2. CE side: round 4 shipped this flank at mean 179 and mine landed at
# 56 -- a regression on the one surface the run's 0.13 ft gap actually shows.
sub('    b = _buf("#131722")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#1c2231"), _c("#0b0e16"),',
    '    b = _buf("#1e2433")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#2f3850"), _c("#141926"),',
    "ce_side ground")
sub('_poly(b, [(0, 152), (256, 138), (256, 256), (0, 256)], _c(_CE_BLUE), 1.0)',
    '_poly(b, [(0, 152), (256, 138), (256, 256), (0, 256)],\n'
    '          _c("#3d74c8"), 1.0)', "ce_side blue")
sub('tuple(c), _c("#12294f"), min(0.55, (y - 150) / 240.0)))',
    'tuple(c), _c("#1b3a70"), min(0.45, (y - 150) / 240.0)))', "ce_side shade")

# ---- 3. the ghosted fighter read as a geometric mech.  Soften it: a second
# offset pass at half alpha is what makes an airbrushed ghost.
sub('    PALE = _c("#8fb6e8")', '    PALE = _c("#a8c8ef")', "pale")
for a, b_ in (("PALE, 0.42)", "PALE, 0.20)"), ("PALE, 0.34)", "PALE, 0.16)"),
               ("PALE, 0.40)", "PALE, 0.19)"), ("PALE, 0.46)", "PALE, 0.22)"),
               ("PALE, 0.30)", "PALE, 0.15)"), ("PALE, 0.26)", "PALE, 0.13)")):
    sub(a, b_, "ghost alpha")
sub('''    for (x0, y0, x1, y1, al) in ((104, 58, 130, 64, 0.5), (76, 100, 140, 108,
                                 0.34), (162, 84, 224, 92, 0.4),
                                (108, 166, 152, 174, 0.3)):
        _rect(b, x0, y0, x1, y1, _c("#cfe0f7"), al)
    _sheen(b, 128.0, 120.0, 20.0, 210.0, _c("#a9c8ee"), 0.20)''',
    '''    for (dx, dy, al) in ((-7, -5, 0.11), (8, 6, 0.10), (0, 10, 0.08)):
        _poly(b, [(70 + dx, 88 + dy), (150 + dx, 78 + dy),
                  (172 + dx, 116 + dy), (150 + dx, 158 + dy),
                  (96 + dx, 166 + dy), (62 + dx, 132 + dy)], PALE, al)
        _poly(b, [(150 + dx, 96 + dy), (222 + dx, 74 + dy),
                  (236 + dx, 96 + dy), (168 + dx, 126 + dy)], PALE, al)
    for (x0, y0, x1, y1, al) in ((104, 58, 130, 64, 0.24),
                                 (76, 100, 140, 108, 0.16),
                                 (162, 84, 224, 92, 0.19),
                                 (108, 166, 152, 174, 0.14)):
        _rect(b, x0, y0, x1, y1, _c("#d8e6fa"), al)
    _sheen(b, 128.0, 120.0, 20.0, 210.0, _c("#b9d2f2"), 0.18)''', "ghost soft")

# ---- 4. CE deck off the floor
sub('    b = _buf("#141826")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#1d2438"), _c("#0a0d18"),',
    '    b = _buf("#1e2740")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#2b3757"), _c("#131a2c"),',
    "ce_deck ground")

# ---- 5. TIME CRISIS: 'CRISIS' must cross the FULL band width (roster).
for col, w, y0, y1 in (("#1a2750", "0.30", 214, 216),
                       ("#f6f9ff", "0.20", 210, 212),
                       ("#3560bd", "0.105", 210, 212)):
    sub('"CRISIS", 128, %d, 96.0, _c("%s"), weight=%s, xs=xs,\n'
        '          wide=1.04' % (y0, col, w),
        '"CRISIS", 128, %d, 104.0, _c("%s"), weight=%s, xs=xs,\n'
        '          wide=1.52' % (y1, col, w),
        "tc CRISIS " + col)
sub('_text(b, "TIME", 74, 96, 52.0', '_text(b, "TIME", 82, 96, 56.0', "tc TIME a")
sub('_text(b, "TIME", 74, 94, 52.0', '_text(b, "TIME", 82, 94, 56.0', "tc TIME b")
s = s.replace('wide=1.02, track=0.06, ital=0.30', 'wide=1.45, track=0.06, ital=0.30')
sub('_seg(b, 108, 60, 150, 50, 4.0', '_seg(b, 132, 58, 186, 46, 4.0', "tc swash a")
sub('_seg(b, 112, 66, 148, 58, 3.0', '_seg(b, 136, 64, 182, 54, 3.0', "tc swash b")

# ---- 6. LEGENDS front: the four IDENTIFIED wordmarks were drawn half-size.
sub('_text(b, "MILLIPEDE", cx, cy + hh, hh * 2.0, c, weight=0.22,\n'
    '              xs=xs, wide=0.80',
    '_text(b, "MILLIPEDE", cx, cy + hh, hh * 2.1, c, weight=0.22,\n'
    '              xs=xs, wide=1.45', "millipede")
sub('_text(b, "STAR", cx, cy + hh * 0.15, hh * 1.4, c, weight=0.30,\n'
    '              xs=xs, wide=1.00',
    '_text(b, "STAR", cx, cy + hh * 0.15, hh * 1.55, c, weight=0.30,\n'
    '              xs=xs, wide=2.55', "star")
sub('_text(b, "WARS", cx, cy + hh * 1.45, hh * 1.4, c, weight=0.30,\n'
    '              xs=xs, wide=1.10',
    '_text(b, "WARS", cx, cy + hh * 1.55, hh * 1.55, c, weight=0.30,\n'
    '              xs=xs, wide=2.70', "wars")
sub('_text(b, "TRON", cx, cy + hh, hh * 2.1, _c("#0a0f2a"), weight=0.36,\n'
    '              xs=xs, wide=1.05',
    '_text(b, "TRON", cx, cy + hh, hh * 2.1, _c("#0a0f2a"), weight=0.36,\n'
    '              xs=xs, wide=2.70', "tron a")
sub('_text(b, "TRON", cx, cy + hh, hh * 2.1, c, weight=0.22, xs=xs,\n'
    '              wide=1.05',
    '_text(b, "TRON", cx, cy + hh, hh * 2.1, c, weight=0.22, xs=xs,\n'
    '              wide=2.70', "tron b")
sub('_text(b, "3D", cx - hw * 0.55, cy + hh, hh * 2.0, _c(sec),\n'
    '              weight=0.34, xs=xs, wide=1.0',
    '_text(b, "3D", cx - hw * 0.58, cy + hh, hh * 2.0, _c(sec),\n'
    '              weight=0.34, xs=xs, wide=2.10', "3d")

# ---- 7. LEGENDS deck read as an empty band; lift ground and guides.
sub('    b = _buf("#15171d")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#22252d"), _c("#0e1015"),',
    '    b = _buf("#20242d")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#31363f"), _c("#171a21"),',
    "lu_deck ground")
sub('_ring(b, sx, 128.0, 46.0, 40.0, 2.0, _c("#42474f"), 0.55, n=40)',
    '_ring(b, sx, 128.0, 46.0, 40.0, 2.6, _c("#767d88"), 0.75, n=40)', "lu ring1")
sub('_ring(b, sx, 128.0, 24.0, 21.0, 1.6, _c("#363a42"), 0.45, n=32)',
    '_ring(b, sx, 128.0, 24.0, 21.0, 2.0, _c("#5c626c"), 0.60, n=32)', "lu ring2")
sub('_text(b, "1", 72, 56, 22.0, _c("#5c6169")',
    '_text(b, "1", 72, 56, 24.0, _c("#8d939d")', "lu 1")
sub('_text(b, "2", 184, 56, 22.0, _c("#5c6169")',
    '_text(b, "2", 184, 56, 24.0, _c("#8d939d")', "lu 2")
sub('_c("#666c76"), weight=0.20,\n          xs=xs, wide=0.90, track=0.22',
    '_c("#959ba5"), weight=0.20,\n          xs=xs, wide=1.35, track=0.22', "lu wm")

# ---- 8. LEGENDS ground lifted so the ink survives the daylight render.
sub('_LU_BLACK = "#111318"', '_LU_BLACK = "#191d25"', "lu black")
sub('_field(b, lambda x, y, c: _mix(_c("#191c23"), _c("#0a0b10"),',
    '_field(b, lambda x, y, c: _mix(_c("#242934"), _c("#101319"),', "lu mq")
sub('''    _field(b, lambda x, y, c: _mix(_c("#191c24"), _c("#0a0b0f"),
                                   min(1.0, ((y / 255.0) ** 0.55
                                             * 0.8 + abs(x - 108) / 320.0))))''',
    '''    _field(b, lambda x, y, c: _mix(_c("#262b37"), _c("#101319"),
                                   min(1.0, ((y / 255.0) ** 0.55
                                             * 0.8 + abs(x - 108) / 320.0))))''',
    "lu front ground")

# ---- 9. T2 deck was the darkest panel in the room at 30.
sub('    b = _buf("#15121c")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#232030"), _c("#0b0910"),',
    '    b = _buf("#201d2b")\n'
    '    _field(b, lambda x, y, c: _mix(_c("#302c3f"), _c("#131019"),',
    "t2 deck ground")

io.open(p, "w", encoding="utf-8").write(s)
print("patched _g2_frag.py  %d -> %d chars" % (n0, len(s)))
