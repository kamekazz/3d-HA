

# ======================================================= round-5 shared paint
def _edge(cv, w, c0, c1, sides="tblr"):
    """A T-molding / trim hairline round the panel edge."""
    if "t" in sides:
        cv.grad(0, 0, cv.A, w, c1, c0)
    if "b" in sides:
        cv.grad(0, 1 - w, cv.A, 1, c0, c1)
    if "l" in sides:
        cv.grad(0, 0, w, 1, c1, c0, horiz=True)
    if "r" in sides:
        cv.grad(cv.A - w, 0, cv.A, 1, c0, c1, horiz=True)


def _mottle(cv, u0, v0, u1, v1, cols, seed, n=26, rmin=0.06, rmax=0.24,
            a=0.5):
    """Soft overlapping blobs -- nebula, smoke, painted wash."""
    for j in range(n):
        u = u0 + (u1 - u0) * _hash(j, 1, seed)
        v = v0 + (v1 - v0) * _hash(j, 2, seed)
        r = rmin + (rmax - rmin) * _hash(j, 3, seed)
        c = cols[j % len(cols)]
        cv.disc(u, v, r, c, a=a, ry=r * (0.55 + 0.75 * _hash(j, 4, seed)))


def _speck(cv, u0, v0, u1, v1, n, c, seed, r=0.006, a=0.85):
    for j in range(n):
        u = u0 + (u1 - u0) * _hash(j, 7, seed)
        v = v0 + (v1 - v0) * _hash(j, 9, seed)
        rr = r * (0.5 + _hash(j, 11, seed))
        cv.disc(u, v, rr, c, a=a, ry=rr)


def _rays(cv, u, v, n, r0, r1, w, c, a, seed=0, spread=2 * math.pi):
    for j in range(n):
        ang = spread * (j + 0.5) / n + _hash(j, 3, seed) * 0.14
        ca, sa = math.cos(ang), math.sin(ang)
        cv.seg(u + ca * r0, v + sa * r0 * 0.9, u + ca * r1,
               v + sa * r1 * 0.9, w, c, a)


def _cracks(cv, u0, v0, u1, v1, n, c, seed, w=0.006, a=0.6):
    """Hairline fissures for a cast-stone / concrete field."""
    for j in range(n):
        u = u0 + (u1 - u0) * _hash(j, 21, seed)
        v = v0 + (v1 - v0) * _hash(j, 23, seed)
        ang = _hash(j, 25, seed) * 2 * math.pi
        L = 0.06 + 0.20 * _hash(j, 27, seed)
        pts = [(u, v)]
        for k in range(4):
            ang += (_hash(j, 31 + k, seed) - 0.5) * 1.1
            u += math.cos(ang) * L * 0.25
            v += math.sin(ang) * L * 0.25
            pts.append((u, v))
        cv.path(pts, w, c, a)


def _chrome(cv, s, u, v, h, w, ital=0.22, track=0.10, cond=1.0, align="c",
            dark=None, body=None, lite=None, shadow=(6, 7, 12)):
    """Chrome / brushed-silver display caps: a black drop, a steel underedge,
    the body, then a fine highlight lifted off the cap line.  Four passes of
    the same skeleton is what makes NFL BLITZ read as metal and not as grey."""
    dark = dark or _hx("#5c6472")
    body = body or _hx("#c4cad4")
    lite = lite or _hx("#f6f9ff")
    cv.text(s, u, v + h * 0.055, h, shadow, w * 2.05, track=track, ital=ital,
            cond=cond, align=align)
    cv.text(s, u, v + h * 0.012, h, dark, w * 1.50, track=track, ital=ital,
            cond=cond, align=align)
    cv.text(s, u, v, h, body, w, track=track, ital=ital, cond=cond,
            align=align)
    cv.text(s, u, v - h * 0.042, h, lite, w * 0.36, track=track, ital=ital,
            cond=cond, align=align)


def _fine(cv, u0, u1, v, h, c, seed, a=0.85, words=6):
    """A line of illegible small print, as printed panels actually carry."""
    u = u0
    j = 0
    while u < u1:
        w = (u1 - u0) / words * (0.35 + 0.85 * _hash(j, 5, seed))
        if u + w > u1:
            w = u1 - u
        cv.rect(u, v, u + w, v + h, c, a)
        u += w + (u1 - u0) * 0.035
        j += 1


def _plate(cv, u0, v0, u1, v1, face, bevel_hi, bevel_lo, bw=0.012):
    """A recessed metal plate: lit top/left bevel, dark bottom/right."""
    cv.rect(u0, v0, u1, v1, face)
    cv.rect(u0, v0, u1, v0 + bw, bevel_lo)
    cv.rect(u0, v0, u0 + bw, v1, bevel_lo)
    cv.rect(u0, v1 - bw, u1, v1, bevel_hi)
    cv.rect(u1 - bw, v0, u1, v1, bevel_hi)


# ---------------------------------------------------------- deck sockets
# `_deck_sockets` paints the printed ring under every control the DECKS table
# hands to ar2.py, so the graphic and the geometry are generated from ONE
# source and cannot drift.  Deck frame: u in [-0.5, 0.5] across the deck art
# quad, v in [0, 1] from its BACK edge (nearest the screen) to its FRONT edge.
def _du(cv, u):
    return (u + 0.5) * cv.A


def _dr(cv, r_ft, depth_ft):
    """A radius in feet, in this panel's normalised units."""
    return r_ft / depth_ft


def _socket(cv, u, v, r, rim, well, a=1.0):
    cv.disc(u, v + r * 0.22, r * 1.40, (0, 0, 0), a=0.34 * a, ry=r * 1.30)
    cv.disc(u, v, r * 1.30, rim, a=a, ry=r * 1.30)
    cv.disc(u, v, r * 1.06, well, a=a, ry=r * 1.06)


def _deck_sockets(cv, slug, rim, well, stick_rim=None, stick_well=None):
    d = DECKS[slug]
    dep = d["depth_ft"]
    sr, sw = stick_rim or rim, stick_well or well
    for s in d["sticks"]:
        r = _dr(cv, s["base_r"], dep)
        _socket(cv, _du(cv, s["u"]), s["v"], r, sr, sw)
    for b in d["buttons"]:
        r = _dr(cv, b["r"], dep)
        _socket(cv, _du(cv, b["u"]), b["v"], r * 1.16, rim, well)
