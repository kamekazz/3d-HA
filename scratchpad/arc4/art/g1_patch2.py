p = 'art_g1.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


# 'I' and '1' were set on a 0.14 body, so "TURTLES IN TIME" read as "N TIME"
rep('''_ADV[" "] = 0.42''', '''_ADV["I"] = 0.28
_ADV["1"] = 0.40
_ADV[" "] = 0.42''')
rep('''    "I": [[(0.14, 0.0), (0.14, 1.0)]],''',
    '''    "I": [[(0.14, 0.0), (0.14, 1.0)]],   # _ADV widened below, see _ADV[]''')

# Marvel marquee: the figures read as flat vector cutouts.  Knock them back
# behind a painted scrim and a vignette so they read as cover art.
rep('''    cv.text("MARVEL", 1.42, 0.30, 0.34, (243, 244, 248), 0.055, track=0.10,''',
    '''    for j in range(7):                    # painted scrim over the figures
        cv.rect(0, 0, cv.A, 1, (6, 8, 18), a=0.055)
        cv.disc(cv.A * 0.5, 0.5, 1.9 - j * 0.12, _hx("#1b2a52"), a=0.05,
                ry=0.62 - j * 0.04)
    for j in range(9):                    # vignette
        cv.rect(0, 0, 0.10 + j * 0.05, 1, (3, 4, 10), a=0.055)
        cv.rect(cv.A - 0.10 - j * 0.05, 0, cv.A, 1, (3, 4, 10), a=0.055)
    cv.text("MARVEL", 1.42, 0.30, 0.34, (243, 244, 248), 0.055, track=0.10,''')

# TMNT deck: the fire escapes read as plus signs; make them ladder rungs, and
# lift the manhole out of the brick.
rep('''    for u in (0.34, 1.30, 2.26):
        cv.rect(u, 0.06, u + 0.020, 0.94, _hx("#241c18"))
        for j in range(5):
            cv.rect(u - 0.10, 0.10 + j * 0.19, u + 0.13, 0.125 + j * 0.19,
                    _hx("#241c18"))''',
    '''    for u in (0.30, 1.26, 2.30):
        cv.rect(u - 0.115, 0.055, u - 0.098, 0.70, _hx("#241c18"))
        cv.rect(u + 0.098, 0.055, u + 0.115, 0.70, _hx("#241c18"))
        for j in range(7):
            cv.rect(u - 0.115, 0.075 + j * 0.092, u + 0.115,
                    0.090 + j * 0.092, _hx("#2c231d"))''')
rep('''    cv.disc(1.86, 0.60, 0.115, _hx("#3b3735"), ry=0.150)     # manhole
    cv.disc(1.86, 0.60, 0.082, _hx("#4c4744"), ry=0.108)
    for j in range(4):
        cv.disc(1.86, 0.60, 0.082 - j * 0.020, _hx("#332f2d"), a=0.5,
                ry=0.108 - j * 0.026)''',
    '''    cv.disc(1.80, 0.575, 0.145, _hx("#22201e"), ry=0.190)    # manhole
    cv.disc(1.80, 0.575, 0.125, _hx("#5a5450"), ry=0.163)
    cv.disc(1.80, 0.575, 0.108, _hx("#403b38"), ry=0.141)
    for j in range(5):
        cv.disc(1.80, 0.575, 0.096 - j * 0.020, _hx("#5a5450"), a=0.45,
                ry=0.125 - j * 0.026)''')

# TMNT riser: the head swallowed the body.  Shrink it, show the plastron and
# shell edge, and add the nunchuck so it is a turtle, not a frog.
rep('''    cu = cv.A * 0.42
    # a large turtle bust: shoulders, shell edge, head, bandana tails
    cv.poly([(cu - 0.62, 1.0), (cu - 0.40, 0.52), (cu + 0.40, 0.52),
             (cu + 0.62, 1.0)], _hx("#2c6a30"))
    cv.poly([(cu - 0.34, 1.0), (cu - 0.24, 0.62), (cu + 0.24, 0.62),
             (cu + 0.34, 1.0)], _hx("#b8a05e"))
    cv.disc(cu, 0.36, 0.26, _hx("#5ea832"), ry=0.26)
    cv.rect(cu - 0.28, 0.28, cu + 0.28, 0.40, _hx("#c22a2a"))
    cv.poly([(cu + 0.25, 0.30), (cu + 0.86, 0.20), (cu + 0.90, 0.36),
             (cu + 0.26, 0.40)], _hx("#c22a2a"))
    for sx in (-1, 1):
        cv.disc(cu + sx * 0.105, 0.335, 0.052, (244, 244, 236), ry=0.050)
        cv.disc(cu + sx * 0.105, 0.335, 0.020, (14, 16, 12), ry=0.020)
    cv.disc(cu, 0.505, 0.085, _hx("#2f6b1c"), ry=0.040)
    cv.seg(cu - 0.44, 0.60, cu - 0.92, 0.86, 0.075, _hx("#5ea832"))
    cv.disc(cu - 0.98, 0.90, 0.075, _hx("#5ea832"), ry=0.075)''',
    '''    cu = cv.A * 0.40
    # a turtle bust: shell rim, shoulders, plastron, head, bandana, nunchuck
    cv.disc(cu, 0.86, 0.62, _hx("#6b4a18"), ry=0.44)
    cv.disc(cu, 0.88, 0.52, _hx("#8a6222"), ry=0.36)
    cv.poly([(cu - 0.52, 1.0), (cu - 0.34, 0.58), (cu + 0.34, 0.58),
             (cu + 0.52, 1.0)], _hx("#3f8a2a"))
    cv.poly([(cu - 0.28, 1.0), (cu - 0.19, 0.63), (cu + 0.19, 0.63),
             (cu + 0.28, 1.0)], _hx("#c3ad6a"))
    for j in range(3):
        cv.rect(cu - 0.24 + j * 0.005, 0.72 + j * 0.09,
                cu + 0.24 - j * 0.005, 0.735 + j * 0.09, _hx("#8d7a44"))
    cv.seg(cu - 0.36, 0.66, cu - 0.86, 0.86, 0.085, _hx("#4f9a2c"))
    cv.seg(cu + 0.36, 0.66, cu + 0.80, 0.50, 0.085, _hx("#4f9a2c"))
    cv.disc(cu, 0.40, 0.185, _hx("#5ea832"), ry=0.205)
    cv.rect(cu - 0.20, 0.345, cu + 0.20, 0.435, _hx("#c22a2a"))
    cv.poly([(cu + 0.18, 0.355), (cu + 0.62, 0.285), (cu + 0.66, 0.375),
             (cu + 0.19, 0.435)], _hx("#c22a2a"))
    for sx in (-1, 1):
        cv.disc(cu + sx * 0.072, 0.390, 0.040, (244, 244, 236), ry=0.040)
        cv.disc(cu + sx * 0.072, 0.390, 0.016, (14, 16, 12), ry=0.016)
    cv.disc(cu, 0.505, 0.062, _hx("#2f6b1c"), ry=0.030)
    cv.seg(cu - 0.92, 0.42, cu - 0.86, 0.84, 0.045, _hx("#3a2a16"))
    cv.seg(cu - 0.92, 0.42, cu - 1.14, 0.66, 0.045, _hx("#3a2a16"))''')

# Pac-Man marquee: the wordmark ran edge to edge; the real one keeps a margin.
rep('''    cv.text("PAC", 0.86, 0.235, 0.44, ylw, 0.150, track=0.10, arch=0.055,
            align="c", outline=blk, ow=0.038)
    cv.text("MAN", 2.52, 0.235, 0.44, ylw, 0.150, track=0.10, arch=0.055,
            align="c", outline=blk, ow=0.038)
    # the hyphen, between the words and above the chase
    cv.seg(1.60, 0.34, 1.78, 0.34, 0.085, ylw)
    cv.seg(1.60, 0.34, 1.78, 0.34, 0.085 - 0.030, ylw)
    cv.seg(1.585, 0.34, 1.795, 0.34, 0.105, blk)
    cv.seg(1.60, 0.34, 1.78, 0.34, 0.075, ylw)
    # chase art: a blue ghost, then Pac-Man and a dot trail
    _ghost(cv, 1.56, 0.470, 0.235, 0.300, _hx("#2438cf"))
    _pac(cv, 1.98, 0.700, 0.115, ylw, ang=0.0, mouth=0.85)
    for j in range(4):
        cv.disc(2.16 + j * 0.115, 0.700, 0.021, _hx("#c9922a"))''',
    '''    cv.text("PAC", 0.94, 0.250, 0.375, ylw, 0.128, track=0.10, arch=0.048,
            align="c", outline=blk, ow=0.034)
    cv.text("MAN", 2.46, 0.250, 0.375, ylw, 0.128, track=0.10, arch=0.048,
            align="c", outline=blk, ow=0.034)
    cv.seg(1.585, 0.335, 1.795, 0.335, 0.098, blk)
    cv.seg(1.60, 0.335, 1.78, 0.335, 0.064, ylw)
    # chase art: a blue ghost, then Pac-Man and a dot trail
    _ghost(cv, 1.58, 0.470, 0.250, 0.315, _hx("#2438cf"))
    _pac(cv, 2.02, 0.690, 0.125, ylw, ang=0.0, mouth=0.85)
    for j in range(4):
        cv.disc(2.24 + j * 0.120, 0.690, 0.023, _hx("#c9922a"))''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
