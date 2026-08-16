"""Round 5 — a tone-field rasteriser, so a soft surface stops rendering as plastic.

Round 4's rug and duvet metered sigma 3.6 / 2.8 against the photo's ~33 / ~12.
Both carried their texture as GEOMETRY (a 0.013 ft ripple field, a wrinkle term)
and in this scene geometry buys almost no contrast: there is one directional sun
and a big isotropic hemisphere/IBL term, so tilting a normal 20 degrees barely
changes what a surface collects.  Contrast has to come from ALBEDO.

So this is the Kitchen's trick (scratchpad/kbuild/kraster.py), generalised:

    field(u, w) -> t in [0, 1]  ->  quantised to a palette of N tones
    equal-tone cells merged into runs along u  ->  one quad per run

with two changes that matter for the payload budget the Kitchen blew:

  * the surface is PARAMETRIC -- `pt(u, w) -> (x, y, z)` -- so a tilted sham
    face or a duvet top with a fall over the mattress edge can carry the same
    field as a flat floor, instead of needing its own hand-meshed grid.
  * every quad of one tone accumulates into ONE welded Part with a position ->
    index dict and smooth normals, so a run shares its vertices with its
    neighbours.  kraster emits a standalone flat quad (6 verts, 168 B); this
    emits ~2 new verts (~48 B).  That is the whole difference between the
    Kitchen's 6.2 MB and staying inside 1.5 MB/room.

Winding is CHECKED against a reference normal per quad, never assumed -- a
one-sided face turned away from every light renders solid black.
"""
import math

from roomkit.glb import Material, Part


# ------------------------------------------------------------------ noise ---
def _h2(ix, iw, seed):
    h = (ix * 374761393 + iw * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0xFFFFFF


def _sm(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise(u, w, seed):
    ix, iw = math.floor(u), math.floor(w)
    su, sw = _sm(u - ix), _sm(w - iw)
    a, b = _h2(ix, iw, seed), _h2(ix + 1, iw, seed)
    c, d = _h2(ix, iw + 1, seed), _h2(ix + 1, iw + 1, seed)
    return (a + (b - a) * su) * (1 - sw) + (c + (d - c) * su) * sw


def fbm(u, w, seed, octaves=4, freq=1.0, gain=0.52, lac=2.13):
    s = tot = 0.0
    amp = 1.0
    for _ in range(octaves):
        s += amp * vnoise(u * freq, w * freq, seed)
        tot += amp
        amp *= gain
        freq *= lac
        seed += 7919
    return s / tot


def hash01(ix, iw, seed=1):
    return _h2(int(ix), int(iw), seed)


# --------------------------------------------------------------- palettes ---
def _hex(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def ramp(lo, hi, n, name, roughness=0.97, metallic=0.0, gamma=1.0):
    """n materials stepping lo -> hi (sRGB hex); index 0 is the darkest."""
    a, b = _hex(lo), _hex(hi)
    out = []
    for i in range(n):
        t = (i / (n - 1.0)) ** gamma if n > 1 else 1.0
        col = "#" + "".join("%02x" % int(round(a[k] + (b[k] - a[k]) * t))
                            for k in range(3))
        out.append(Material("%s%d" % (name, i), col, roughness=roughness,
                            metallic=metallic))
    return out


# ------------------------------------------------------------ rasteriser ----
class Field:
    """Accumulates merged tone runs, one welded Part per material."""

    def __init__(self, mats):
        self.mats = mats
        self._v = [[] for _ in mats]
        self._t = [[] for _ in mats]
        self._i = [{} for _ in mats]

    def _vid(self, k, p):
        key = (round(p[0], 5), round(p[1], 5), round(p[2], 5))
        d = self._i[k]
        j = d.get(key)
        if j is None:
            j = len(self._v[k])
            d[key] = j
            self._v[k].append(p)
        return j

    def quad(self, k, p0, p1, p2, p3, ref):
        n = _cross(p0, p1, p2)
        if n[0] * ref[0] + n[1] * ref[1] + n[2] * ref[2] < 0:
            p1, p3 = p3, p1
        a = self._vid(k, p0)
        b = self._vid(k, p1)
        c = self._vid(k, p2)
        d = self._vid(k, p3)
        self._t[k] += [(a, b, c), (a, c, d)]

    def emit(self, m, at=(0.0, 0.0, 0.0)):
        n = 0
        for k, mat in enumerate(self.mats):
            if self._t[k]:
                m.add(Part(self._v[k], self._t[k], smooth=True), mat, at=at)
                n += len(self._v[k])
        return n

    def verts(self):
        return sum(len(v) for v in self._v)


def _cross(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


def raster(fld, pt, nrm, u0, u1, w0, w1, nu, nw, fn):
    """Rasterise fn(u, w) -> palette index (or None for a hole).

    `pt(u, w)` places a parameter point in 3-D, `nrm(u, w)` gives the direction
    that point's face must end up pointing.  Equal-index cells merge into one
    quad along u.
    """
    du, dw = (u1 - u0) / nu, (w1 - w0) / nw
    for j in range(nw):
        wa, wb = w0 + j * dw, w0 + (j + 1) * dw
        wc = 0.5 * (wa + wb)
        cur, start = None, 0
        for i in range(nu + 1):
            v = fn(u0 + (i + 0.5) * du, wc) if i < nu else None
            if v != cur:
                if cur is not None:
                    ua, ub = u0 + start * du, u0 + i * du
                    fld.quad(cur, pt(ua, wa), pt(ub, wa), pt(ub, wb),
                             pt(ua, wb), nrm(0.5 * (ua + ub), wc))
                cur, start = v, i


def plane_xz(y):
    """pt/nrm pair for a horizontal +y plane: u -> x, w -> z."""
    return (lambda u, w: (u, y, w)), (lambda u, w: (0.0, 1.0, 0.0))
