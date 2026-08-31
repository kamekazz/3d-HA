p = 'art_g1.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


# Time Crisis: the swash was crossing the E of TIME like a stray bolt.  Put it
# where the photograph has it -- clear of the word, raking up to the right.
rep('''    # the swash off the end of TIME
    for k in range(3):
        cv.seg(1.36 + k * 0.005, 0.20 + k * 0.004, 1.66 + k * 0.005,
               0.09 + k * 0.004, 0.045 - k * 0.012,
               (blu if k == 2 else (wht if k == 1 else shd)))
    cv.seg(1.62, 0.10, 1.80, 0.20, 0.024, blu)''',
    '''    # the swash off the end of TIME, clear of the word
    for (w, c) in ((0.062, shd), (0.048, wht), (0.028, blu)):
        cv.seg(1.52, 0.245, 1.86, 0.115, w, c)
        cv.seg(1.86, 0.115, 2.02, 0.175, w * 0.62, c)''')

# TMNT marquee: the Foot soldier read as a black post.  Give it a head and a
# staff so it reads as a figure between the turtles.
rep('''cv.poly([(2.58, 0.98), (2.62, 0.44), (2.72, 0.44), (2.76, 0.98)],
            _hx("#1d1b28"))
    cv.disc(2.67, 0.395, 0.052, _hx("#1d1b28"), ry=0.058)''',
    '''cv.poly([(2.585, 0.98), (2.625, 0.46), (2.715, 0.46), (2.755, 0.98)],
            _hx("#1d1b28"))
    cv.disc(2.67, 0.410, 0.048, _hx("#1d1b28"), ry=0.054)
    cv.rect(2.628, 0.392, 2.712, 0.418, _hx("#5a1420"))
    cv.seg(2.63, 0.50, 2.52, 0.60, 0.030, _hx("#1d1b28"))
    cv.seg(2.71, 0.50, 2.82, 0.58, 0.030, _hx("#1d1b28"))
    cv.seg(2.50, 0.34, 2.86, 0.66, 0.018, _hx("#6d6455"))''')

open(p, 'w', encoding='utf-8').write(s)
print("patched")
