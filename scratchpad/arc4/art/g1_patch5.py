p = 'art_g1.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


# Time Crisis: the swash was twice the length the photograph shows.
rep('''    for (w, c) in ((0.062, shd), (0.048, wht), (0.028, blu)):
        cv.seg(1.52, 0.245, 1.86, 0.115, w, c)
        cv.seg(1.86, 0.115, 2.02, 0.175, w * 0.62, c)''',
    '''    for (w, c) in ((0.050, shd), (0.038, wht), (0.022, blu)):
        cv.seg(1.50, 0.215, 1.72, 0.130, w, c)
        cv.seg(1.72, 0.130, 1.81, 0.168, w * 0.60, c)''')

# TMNT marquee: a 0.7-wide strip of bare sky was showing between the alley
# and the street, and the shopfront glazing read as jail bars.
rep('cv.rect(1.62, 0.0, cv.A, 1.0, _hx("#3b2f2a"))',
    'cv.rect(1.12, 0.0, cv.A, 1.0, _hx("#3b2f2a"))')
rep('''    for j in range(9):
        u = 1.66 + j * 0.15
        cv.rect(u, 0.10, u + 0.10, 0.52, _hx("#6f6f86"))
        cv.rect(u, 0.10, u + 0.10, 0.30, _hx("#9aa6c4"))''',
    '''    for j in range(5):
        u = 1.20 + j * 0.30
        cv.rect(u, 0.09, u + 0.20, 0.50, _hx("#3f3a48"))
        cv.rect(u + 0.02, 0.11, u + 0.18, 0.46, _hx("#8a7f6a"))
        cv.rect(u + 0.02, 0.11, u + 0.18, 0.27, _hx("#c2b394"))
        cv.rect(u + 0.095, 0.11, u + 0.105, 0.46, _hx("#3f3a48"))''')
rep('cv.rect(1.62, 0.52, 2.86, 0.60, _hx("#8d8471"))',
    'cv.rect(1.12, 0.52, 2.86, 0.62, _hx("#7d6a4e"))')
rep('cv.rect(1.40, 0.80, cv.A, 1.0, _hx("#55504c"))',
    'cv.rect(0.86, 0.80, cv.A, 1.0, _hx("#55504c"))')
rep('_bricks(cv, 0.0, 0.0, 0.92, 1.0, _hx("#7c3f34"), _hx("#4a2620"),\n'
    '            0.115, 0.20, 71)\n    cv.rect(0.0, 0.0, 0.92, 1.0, _hx("#2a1830"), a=0.30)',
    '_bricks(cv, 0.0, 0.0, 1.14, 1.0, _hx("#7c3f34"), _hx("#4a2620"),\n'
    '            0.115, 0.20, 71)\n    cv.rect(0.0, 0.0, 1.14, 1.0, _hx("#2a1830"), a=0.30)')

# TMNT front: the photograph shows TURTLES IN TIME as an ARCHED blue-and-white
# wordmark straight on the black panel, not sitting in a pale slab.
rep('''    # the pale slab
    cv.rect(0.185, 0.415, 0.815, 0.545, _hx("#cfd6d0"))
    cv.rect(0.185, 0.415, 0.815, 0.432, _hx("#eef2ec"))
    cv.text("TURTLES IN TIME", 0.50, 0.448, 0.070, _hx("#16305e"), 0.0155,
            track=0.10, arch=0.024, align="c")
    cv.text("KONAMI", 0.50, 0.596, 0.048, _hx("#c22a2a"), 0.0115, track=0.20,
            align="c")''',
    '''    cv.text("TURTLES IN TIME", 0.50, 0.425, 0.088, _hx("#8fb8ee"), 0.0180,
            track=0.075, cond=0.82, arch=0.045, align="c",
            outline=_hx("#1a2f78"), ow=0.0075,
            shadow=(6, 8, 14), sh=(0.008, 0.009))
    cv.text("KONAMI", 0.50, 0.612, 0.044, _hx("#c22a2a"), 0.0105, track=0.20,
            align="c")''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
