"""Invert the app's display response: scene radiance -> exposure 1.15 -> ACES -> sRGB byte.

Lets a colour be METERED instead of guessed: render, sample the byte a surface
comes out at, divide by the byte its authored albedo *should* have produced, and
you have that surface's lit factor; then solve for the albedo that lands on the
byte the photo shows.
"""
EXPOSURE = 1.15

IN_MAT = ((0.59719, 0.35458, 0.04823),
          (0.07600, 0.90834, 0.01566),
          (0.02840, 0.13383, 0.83777))
OUT_MAT = ((1.60475, -0.53108, -0.07367),
           (-0.10208, 1.10813, -0.00605),
           (-0.00327, -0.07276, 1.07602))


def _mul(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def _fit(v):
    a = v * (v + 0.0245786) - 0.000090537
    b = v * (0.983729 * v + 0.4329510) + 0.238081
    return a / b


def aces(rgb, exposure=EXPOSURE):
    c = tuple(x * exposure / 0.6 for x in rgb)
    c = _mul(IN_MAT, c)
    c = tuple(_fit(x) for x in c)
    c = _mul(OUT_MAT, c)
    return tuple(min(1.0, max(0.0, x)) for x in c)


def lin_to_srgb(u):
    u = min(1.0, max(0.0, u))
    return 12.92 * u if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055


def srgb_to_lin(u):
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def render_bytes(radiance):
    """linear scene radiance triple -> display bytes."""
    return tuple(round(255 * lin_to_srgb(c)) for c in aces(radiance))


def radiance_for_byte(byte, lo=0.0, hi=40.0):
    """scalar: what grey scene radiance lands on this display byte?"""
    t = byte / 255.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        if lin_to_srgb(aces((m, m, m))[0]) < t:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def radiance_for_rgb(bytes3):
    """solve a radiance triple that renders to these display bytes (per-channel
    solve inside the full 3x3 chain, iterated -- the matrices cross-talk)."""
    tgt = [b / 255.0 for b in bytes3]
    r = [radiance_for_byte(b) for b in bytes3]
    for _ in range(60):
        cur = [lin_to_srgb(c) for c in aces(r)]
        err = [tgt[i] - cur[i] for i in range(3)]
        if max(abs(e) for e in err) < 1e-5:
            break
        for i in range(3):
            r[i] = max(0.0, r[i] * (1.0 + 2.0 * err[i] / max(cur[i], 0.02)))
    return tuple(r)


def hex_of(lin):
    """linear 0..1 -> sRGB hex string (what Material(color=...) wants)."""
    return "#" + "".join("%02x" % max(0, min(255, round(255 * lin_to_srgb(c))))
                         for c in lin)


if __name__ == "__main__":
    for b in (120, 150, 180, 200, 212, 223, 234, 245):
        print(b, "-> radiance %.4f" % radiance_for_byte(b))
