def _panel_grid(cv, u0, v0, u1, v1, seed):
    """Marvel's comic-collage flank: irregular panels, black gutters, teal."""
    teal = [_hx("#0e3742"), _hx("#14606b"), _hx("#1d8a92"), _hx("#2fb3ad"),
            _hx("#0b2630"), _hx("#186d7e")]
    rows = [0.00, 0.185, 0.375, 0.545, 0.735, 1.0]
    cols = [[0.0, 0.46, 1.0], [0.0, 1.0], [0.0, 0.33, 0.66, 1.0],
            [0.0, 0.58, 1.0], [0.0, 0.42, 1.0]]
    g = 0.010
    k = 0
    for ri in range(5):
        ra = v0 + (v1 - v0) * rows[ri]
        rb = v0 + (v1 - v0) * rows[ri + 1]
        cc = cols[ri]
        for ci in range(len(cc) - 1):
            ca = u0 + (u1 - u0) * cc[ci]
            cb = u0 + (u1 - u0) * cc[ci + 1]
            a, b = ca + g, cb - g
            c, d = ra + g * 2, rb - g * 2
            base = teal[k % len(teal)]
            cv.rect(a, c, b, d, base)
            cv.grad(a, c, b, d, _mix(base, (255, 255, 255), 0.22),
                    _mix(base, (0, 0, 0), 0.45))
            mu, mv = (a + b) * 0.5, (c + d) * 0.5
            wd, ht = b - a, d - c
            kind = k % 6
            lite = _mix(base, (235, 255, 250), 0.72)
            dark = _mix(base, (0, 8, 12), 0.75)
            if kind == 0:                                    # action burst
                for j in range(11):
                    ang = j * 2 * math.pi / 11 + 0.2
                    cv.seg(mu, mv, mu + math.cos(ang) * wd * 0.52,
                           mv + math.sin(ang) * ht * 0.52, ht * 0.035, lite)
                cv.disc(mu, mv, wd * 0.17, dark, ry=ht * 0.17)
            elif kind == 1:                                  # halftone field
                nx, ny = 9, max(3, int(9 * ht / max(wd, 1e-6) * 0.5))
                for iy in range(ny):
                    for ix in range(nx):
                        t = ix / (nx - 1.0)
                        rr = wd * 0.040 * (0.35 + t)
                        cv.disc(a + wd * (ix + 0.5) / nx,
                                c + ht * (iy + 0.5) / ny, rr, lite,
                                ry=rr * wd / max(ht, 1e-6) * 0.0 + rr)
            elif kind == 2:                                  # hero silhouette
                cv.disc(mu, c + ht * 0.30, wd * 0.16, dark, ry=ht * 0.16)
                cv.poly([(mu - wd * 0.30, d), (mu - wd * 0.12, c + ht * 0.42),
                         (mu + wd * 0.12, c + ht * 0.42), (mu + wd * 0.30, d)],
                        dark)
                cv.seg(mu - wd * 0.12, c + ht * 0.46, mu - wd * 0.40,
                       c + ht * 0.72, ht * 0.05, dark)
                cv.seg(mu + wd * 0.12, c + ht * 0.46, mu + wd * 0.40,
                       c + ht * 0.66, ht * 0.05, dark)
            elif kind == 3:                                  # speech balloon
                cv.disc(mu, mv - ht * 0.06, wd * 0.34, lite, ry=ht * 0.26)
                cv.poly([(mu - wd * 0.10, mv + ht * 0.14),
                         (mu + wd * 0.02, mv + ht * 0.14),
                         (mu - wd * 0.14, mv + ht * 0.36)], lite)
                for j in range(3):
                    cv.rect(mu - wd * 0.22, mv - ht * 0.14 + j * ht * 0.09,
                            mu + wd * 0.20, mv - ht * 0.11 + j * ht * 0.09,
                            dark)
            elif kind == 4:                                  # bold diagonals
                for j in range(6):
                    o = j * wd * 0.30 - wd * 0.5
                    cv.poly([(a + o, d), (a + o + wd * 0.14, d),
                             (a + o + wd * 0.44, c), (a + o + wd * 0.30, c)],
                            lite if j % 2 else dark)
            else:                                            # city skyline
                x = a
                j = 0
                while x < b:
                    bw = wd * (0.10 + 0.05 * ((j * 7) % 3))
                    bh = ht * (0.30 + 0.14 * ((j * 5) % 4))
                    cv.rect(x, d - bh, min(b, x + bw), d, dark)
                    x += bw + wd * 0.02
                    j += 1
                cv.disc(mu + wd * 0.24, c + ht * 0.26, wd * 0.11, lite,
                        ry=ht * 0.11)
            k += 1


