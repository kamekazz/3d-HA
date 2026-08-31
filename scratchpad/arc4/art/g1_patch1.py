import io
p = 'art_g1.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


rep('''def _turtle_logo(cv, u, v, h, small=True):
    """The 'TEENAGE MUTANT NINJA / TURTLES' lockup, arched, as printed."""
    red = _hx("#c9202a")
    grn = _hx("#5fbf2b")
    ylw = _hx("#f5c119")
    blk = (10, 12, 10)
    top = h * 0.30
    cv.text("TEENAGE MUTANT NINJA", u, v, top * 0.72, red, top * 0.14,
            track=0.10, arch=top * 0.16, align="c",
            outline=blk, ow=top * 0.05)
    cv.text("TURTLES", u, v + top * 1.05, h, grn, h * 0.20, track=0.03,
            arch=h * 0.11, align="c", outline=ylw, ow=h * 0.075,
            shadow=blk, sh=(h * 0.10, h * 0.09))
    if not small:
        cv.text("TURTLES", u, v + top * 1.05, h, grn, h * 0.20, track=0.03,
                arch=h * 0.11, align="c")''',
    '''def _turtle_logo(cv, u, v, h, cond=0.80):
    """The 'TEENAGE MUTANT NINJA / TURTLES' lockup, arched, as printed.

    ``h`` is the cap height of TURTLES; the whole lockup is about 5.6*h*cond
    wide and 1.5*h tall, which is the real marquee's proportion.
    """
    red = _hx("#c9202a")
    grn = _hx("#5fbf2b")
    ylw = _hx("#f5c119")
    blk = (10, 12, 10)
    top = h * 0.26
    bw = cv.width("TEENAGE MUTANT NINJA", top, 0.08, cond * 0.95) * 0.5
    cv.poly([(u - bw - top * 0.5, v + top * 1.30), (u + bw, v - top * 0.05),
             (u + bw + top * 0.5, v + top * 0.72),
             (u - bw, v + top * 2.05)], red)
    cv.text("TEENAGE MUTANT NINJA", u, v + top * 0.42, top, (250, 246, 240),
            top * 0.16, track=0.08, cond=cond * 0.95, arch=top * 0.10,
            align="c")
    cv.text("TURTLES", u, v + top * 2.10, h, grn, h * 0.19, track=0.02,
            cond=cond, arch=h * 0.13, align="c", outline=ylw, ow=h * 0.070,
            shadow=blk, sh=(h * 0.085, h * 0.080))''')

rep('''_turtle_figure(cv, 2.16, 0.28, 0.36, _hx("#2f5fd0"))
    _turtle_figure(cv, 2.52, 0.22, 0.40, _hx("#8f2fd0"), flip=True)
    _turtle_figure(cv, 2.90, 0.30, 0.35, _hx("#d02f2f"))
    _turtle_figure(cv, 3.20, 0.24, 0.38, _hx("#e07a1c"), flip=True)''',
    '''_turtle_figure(cv, 1.90, 0.26, 0.40, _hx("#2f5fd0"))
    _turtle_figure(cv, 2.34, 0.20, 0.44, _hx("#8f2fd0"), flip=True)
    _turtle_figure(cv, 2.80, 0.28, 0.39, _hx("#d02f2f"))
    _turtle_figure(cv, 3.18, 0.22, 0.42, _hx("#e07a1c"), flip=True)''')

rep('''cv.poly([(2.72, 0.98), (2.76, 0.44), (2.86, 0.44), (2.90, 0.98)],
            _hx("#1d1b28"))
    cv.disc(2.81, 0.395, 0.052, _hx("#1d1b28"), ry=0.058)
    # --- the logo, over the join
    _turtle_logo(cv, 1.45, 0.08, 0.40)''',
    '''cv.poly([(2.58, 0.98), (2.62, 0.44), (2.72, 0.44), (2.76, 0.98)],
            _hx("#1d1b28"))
    cv.disc(2.67, 0.395, 0.052, _hx("#1d1b28"), ry=0.058)
    # --- the logo, occupying the left third as the real marquee does
    _turtle_logo(cv, 1.02, 0.10, 0.235, cond=0.78)''')

rep('cv.rect(2.02, 0.0, cv.A, 1.0, _hx("#3b2f2a"))',
    'cv.rect(1.62, 0.0, cv.A, 1.0, _hx("#3b2f2a"))')
rep('''    for j in range(5):
        u = 2.06 + j * 0.15
''', '''    for j in range(9):
        u = 1.66 + j * 0.15
''')
rep('cv.rect(2.02, 0.52, 2.86, 0.60, _hx("#8d8471"))',
    'cv.rect(1.62, 0.52, 2.86, 0.60, _hx("#8d8471"))')
rep('cv.rect(1.28, 0.78, cv.A, 1.0, _hx("#55504c"))',
    'cv.rect(1.40, 0.80, cv.A, 1.0, _hx("#55504c"))')
rep('''cv.disc(2.30, 0.905, 0.085, _hx("#3a3735"), ry=0.055)     # manhole
    cv.disc(2.30, 0.905, 0.062, _hx("#4b4744"), ry=0.040)''',
    '''cv.disc(2.08, 0.925, 0.085, _hx("#3a3735"), ry=0.042)     # manhole
    cv.disc(2.08, 0.925, 0.062, _hx("#4b4744"), ry=0.030)''')

rep('_turtle_logo(cv, 0.50, 0.075, 0.185)',
    '_turtle_logo(cv, 0.50, 0.068, 0.132, cond=0.74)')

rep('''    for (u, v, h, c, o) in ((0.62, 0.16, 0.20, _hx("#5fbf2b"), _hx("#f5c119")),
                            (1.55, 0.10, 0.13, _hx("#3f8fe0"), _hx("#dbe8f6")),
                            (2.18, 0.30, 0.24, _hx("#f0c81e"), _hx("#8a4a12"))):
        cv.text("TURTLES", u, v, h, c, h * 0.20, track=0.03, arch=h * 0.11,
                align="c", outline=o, ow=h * 0.075,
                shadow=(10, 10, 8), sh=(h * 0.09, h * 0.09))''',
    '''    for (u, v, h, c, o) in ((0.60, 0.13, 0.145, _hx("#5fbf2b"), _hx("#f5c119")),
                            (1.46, 0.09, 0.095, _hx("#3f8fe0"), _hx("#dbe8f6")),
                            (2.08, 0.30, 0.170, _hx("#f0c81e"), _hx("#8a4a12"))):
        cv.text("TURTLES", u, v, h, c, h * 0.19, track=0.02, cond=0.80,
                arch=h * 0.13, align="c", outline=o, ow=h * 0.070,
                shadow=(10, 10, 8), sh=(h * 0.085, h * 0.085))''')

rep('''cv.text("TURTLES", cv.A - 0.72, 0.30, 0.22, _hx("#5fbf2b"), 0.045,
            track=0.03, arch=0.026, align="c", outline=_hx("#f5c119"),
            ow=0.017)''',
    '''cv.text("TURTLES", cv.A - 0.62, 0.32, 0.165, _hx("#5fbf2b"), 0.031,
            track=0.02, cond=0.80, arch=0.021, align="c",
            outline=_hx("#f5c119"), ow=0.012, shadow=(10, 10, 8),
            sh=(0.014, 0.013))''')

rep('''    for i, hc in enumerate(heads):
        u = 0.300 + i * 0.0645
        base = _hx(hc)
        cv.disc(u, 0.775, 0.0255, base, ry=0.030)
        cv.poly([(u - 0.026, 0.800), (u + 0.026, 0.800),
                 (u + 0.036, 0.878), (u - 0.036, 0.878)],
                _mix(base, (0, 0, 0), 0.30))
        cv.disc(u - 0.009, 0.770, 0.0055, (18, 14, 12))
        cv.disc(u + 0.009, 0.770, 0.0055, (18, 14, 12))
        cv.rect(u - 0.018, 0.748, u + 0.018, 0.757,
                _mix(base, (255, 240, 220), 0.55))''',
    '''    for i, hc in enumerate(heads):
        u = 0.300 + i * 0.0645
        base = _hx(hc)
        cv.poly([(u - 0.031, 0.878), (u - 0.026, 0.806),
                 (u - 0.014, 0.792), (u + 0.014, 0.792),
                 (u + 0.026, 0.806), (u + 0.031, 0.878)],
                _mix(base, (0, 0, 0), 0.34))
        cv.disc(u, 0.772, 0.0285, base, ry=0.0300)
        cv.poly([(u - 0.030, 0.762), (u - 0.024, 0.735), (u + 0.024, 0.735),
                 (u + 0.030, 0.762)], _mix(base, (18, 12, 10), 0.55))
        cv.disc(u - 0.011, 0.770, 0.0060, (20, 16, 14), ry=0.0055)
        cv.disc(u + 0.011, 0.770, 0.0060, (20, 16, 14), ry=0.0055)
        cv.seg(u - 0.010, 0.790, u + 0.010, 0.790, 0.0050,
               _mix(base, (0, 0, 0), 0.5))''')

rep('''    cv.grad(0, 0, cv.A, 1, _hx("#191b22"), _hx("#0c0e13"))
    for j in range(9):
        u = 0.16 + j * 0.28
        cv.disc(u, 0.30 + 0.34 * ((j * 5) % 3) / 2.0, 0.34,
                _hx("#12414c"), a=0.16, ry=0.30)
    for j in range(26):
        u = 0.04 + j * 0.10
        cv.seg(u, 0.0, u - 0.10, 1.0, 0.010, _hx("#1b4b57"), a=0.20)
    gold = _hx("#a98536")
    cv.rect(0, 0, cv.A, 0.020, gold)
    cv.rect(0, 0.980, cv.A, 1, gold)
    cv.noise(4.0, 47)''',
    '''    cv.grad(0, 0, cv.A, 1, _hx("#20242e"), _hx("#0d1014"))
    for j in range(11):
        u = 0.10 + j * 0.235
        cv.disc(u, 0.24 + 0.42 * ((j * 5) % 3) / 2.0, 0.40,
                _hx("#1a5c69"), a=0.34, ry=0.34)
        cv.disc(u, 0.24 + 0.42 * ((j * 5) % 3) / 2.0, 0.19,
                _hx("#2b96a0"), a=0.24, ry=0.16)
    for j in range(30):
        u = 0.02 + j * 0.09
        cv.seg(u, 0.0, u - 0.11, 1.0, 0.011, _hx("#2f7f8e"), a=0.28)
    for u in (cv.A * 0.27, cv.A * 0.73):
        cv.poly([(u - 0.44, 0.16), (u + 0.44, 0.16), (u + 0.50, 0.86),
                 (u - 0.50, 0.86)], (8, 12, 16), a=0.55)
    gold = _hx("#b8923c")
    cv.rect(0, 0, cv.A, 0.022, gold)
    cv.rect(0, 0.978, cv.A, 1, gold)
    cv.noise(4.6, 47)''')

rep('''    cv.text("PAC-MAN", cv.A * 0.5, 0.400, 0.135, (188, 186, 172), 0.026,
            track=0.22, align="c", a=0.55)
    cv.noise(3.2, 293)''', '''    cv.noise(3.2, 293)''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
