"""ROUND 3 -- a tone-field rasteriser, and the stone / floor / rug / shadow
fields built on it.

Round 2 drew every surface texture as discrete little sticks: veins as 0.05 ft
boxes walking across the slab, floor planks as one flat tone each, contact
shadows as five nested rectangles.  Three separate critic defects all come from
the same mistake -- drawing MARKS where the photograph has a FIELD.

So this module rasterises a continuous scalar field into flat quads:

    field(u, w) -> t in [0, 1]  ->  quantised to a palette of N tones
    equal-tone cells merged into runs along u  ->  one quad per run

One quad per run keeps the triangle count near a plain textured plane's while
giving a real gradient, and because the quantisation contours follow a smooth
noise field they are irregular -- no rings, no banding, no stripes.

Everything is authored in ROOM-LOCAL FEET like the rest of kbuild.
"""
import math

from roomkit.glb import Model, Material, quad  # noqa


# --------------------------------------------------------------- value noise
def _h2(ix, iw, seed):
    h = (ix * 374761393 + iw * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 0xFFFFFF


khash = _h2          # a stable per-cell hash, for lattice patterns


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
    for i in range(octaves):
        s += amp * vnoise(u * freq, w * freq, seed + i * 7919)
        tot += amp
        amp *= gain
        freq *= lac
    return s / tot


def rng(seed):
    s = [seed & 0xFFFFFFFF]

    def nxt():
        s[0] = (1103515245 * s[0] + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return nxt


# --------------------------------------------------------------- palettes
def _hex(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def ramp(lo, hi, n, name, roughness=0.5, emissive_lo=None, emissive_hi=None,
         gamma=1.0):
    """N materials stepping lo -> hi (both sRGB hex), index 0 = darkest."""
    a, b = _hex(lo), _hex(hi)
    ea = _hex(emissive_lo) if emissive_lo else None
    eb = _hex(emissive_hi) if emissive_hi else ea
    out = []
    for i in range(n):
        t = (i / (n - 1.0)) ** gamma if n > 1 else 1.0
        col = "#" + "".join(f"{int(round(a[k] + (b[k] - a[k]) * t)):02x}"
                            for k in range(3))
        em = None
        if ea:
            em = "#" + "".join(f"{int(round(ea[k] + (eb[k] - ea[k]) * t)):02x}"
                               for k in range(3))
        out.append(Material(f"{name}{i}", col, roughness=roughness, emissive=em))
    return out


# --------------------------------------------------------------- rasteriser
# (u, w) -> (x, y, z) per face, plus the outward normal that face must carry.
_FACES = {
    "+y": (lambda u, w, at: (u, at, w), (0.0, 1.0, 0.0)),
    "-y": (lambda u, w, at: (u, at, w), (0.0, -1.0, 0.0)),
    "-x": (lambda u, w, at: (at, w, u), (-1.0, 0.0, 0.0)),
    "+x": (lambda u, w, at: (at, w, u), (1.0, 0.0, 0.0)),
    "-z": (lambda u, w, at: (u, w, at), (0.0, 0.0, -1.0)),
    "+z": (lambda u, w, at: (u, w, at), (0.0, 0.0, 1.0)),
}


def _cross(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


def raster(m, mats, face, at, u0, u1, w0, w1, cell, fn, lift=0.004):
    """Rasterise fn(u, w) -> palette index (or None to leave a hole).

    Emits one quad per run of equal index along u, wound so the face normal
    points the way `face` says.  A one-sided-looking black slab in a render is
    almost always a normal pointing into the wall, so this is checked per quad
    rather than trusted to vertex order.
    """
    fmap, n = _FACES[face]
    at2 = at + lift * (n[0] + n[1] + n[2])
    nu = max(1, int(round((u1 - u0) / cell)))
    nw = max(1, int(round((w1 - w0) / cell)))
    du, dw = (u1 - u0) / nu, (w1 - w0) / nw
    for j in range(nw):
        wa, wb = w0 + j * dw, w0 + (j + 1) * dw
        wc = (wa + wb) * 0.5
        cur, start = None, 0
        for i in range(nu + 1):
            v = fn(u0 + (i + 0.5) * du, wc) if i < nu else None
            if v != cur:
                if cur is not None:
                    ua, ub = u0 + start * du, u0 + i * du
                    p = [fmap(ua, wa, at2), fmap(ub, wa, at2),
                         fmap(ub, wb, at2), fmap(ua, wb, at2)]
                    nn = _cross(p[0], p[1], p[2])
                    if nn[0] * n[0] + nn[1] * n[1] + nn[2] * n[2] < 0:
                        p = [p[0], p[3], p[2], p[1]]
                    m.add(quad(*p), mats[cur])
                cur, start = v, i


# --------------------------------------------------------------- vein network
class Veins:
    """A branching network of soft veins, sampled as a distance field.

    Photo F's quartz is not a family of parallel hairlines (round 1) nor free
    scribbles (round 2): it is a connected NET of broad soft grey strokes over a
    cloudy white ground.  So veins here start on the edges, wander with a low
    meander, and spawn branches off points already drawn -- and every sample is
    a smooth falloff, never a hard line.
    """

    def __init__(self, u0, u1, w0, w1, seed, count=6, step=0.22, width=0.055,
                 meander=0.34, branch=0.8, strength=1.0):
        self.segs = []
        self.width = width
        self.strength = strength
        r = rng(seed)
        pts = []

        def walk(u, w, ang, wid, steps):
            for _ in range(steps):
                ang += (r() - 0.5) * meander
                nu, nw = u + math.cos(ang) * step, w + math.sin(ang) * step
                if not (u0 - step <= nu <= u1 + step and
                        w0 - step <= nw <= w1 + step):
                    break
                self.segs.append((u, w, nu, nw, wid))
                pts.append((nu, nw, ang, wid))
                u, w = nu, nw
            return u, w, ang

        span = math.hypot(u1 - u0, w1 - w0)
        for k in range(count):
            side = r()
            if side < 0.34:
                u, w, ang = u0, w0 + (w1 - w0) * r(), 0.35 + r() * 0.8
            elif side < 0.68:
                u, w, ang = u0 + (u1 - u0) * r(), w0, 0.9 + r() * 0.9
            else:
                u, w, ang = u1, w0 + (u1 - u0) * 0.0 + w0 + (w1 - w0) * r(), \
                    math.pi + 0.35 + r() * 0.8
            walk(u, w, ang, width * (0.7 + r() * 0.7),
                 int(span / step) + 6)
        # branches hang off the trunks, which is what makes it read as a net
        for _ in range(int(count * branch * 2)):
            if not pts:
                break
            u, w, ang, wid = pts[int(r() * (len(pts) - 1))]
            walk(u, w, ang + (0.5 + r() * 0.7) * (1 if r() < 0.5 else -1),
                 wid * (0.35 + r() * 0.35), 3 + int(r() * 7))

        # bucket the segments so the per-cell nearest-distance query is cheap
        self.cs = max(0.35, step * 2.5)
        self.grid = {}
        for s in self.segs:
            i0, i1 = sorted((int(s[0] / self.cs), int(s[2] / self.cs)))
            j0, j1 = sorted((int(s[1] / self.cs), int(s[3] / self.cs)))
            for i in range(i0, i1 + 1):
                for j in range(j0, j1 + 1):
                    self.grid.setdefault((i, j), []).append(s)

    def at(self, u, w):
        """0 (clear) .. 1 (vein core), with a broad soft halo around each vein."""
        gi, gj = int(u / self.cs), int(w / self.cs)
        best = 1e9
        wid = self.width
        for i in (gi - 1, gi, gi + 1):
            for j in (gj - 1, gj, gj + 1):
                for (au, aw, bu, bw, sw) in self.grid.get((i, j), ()):
                    dx, dy = bu - au, bw - aw
                    L2 = dx * dx + dy * dy
                    t = 0.0 if L2 < 1e-9 else \
                        max(0.0, min(1.0, ((u - au) * dx + (w - aw) * dy) / L2))
                    px, py = au + dx * t - u, aw + dy * t - w
                    d = math.hypot(px, py) / max(sw, 1e-4)
                    if d < best:
                        best = d
                        wid = sw
        if best > 6.0:
            return 0.0
        core = math.exp(-(best * best) * 1.35)
        halo = math.exp(-(best * best) * 0.075) * 0.42
        return min(1.0, (core + halo)) * self.strength


# --------------------------------------------------------------- stone field
def stone_field(m, mats, face, at, u0, u1, w0, w1, seed, cell=0.085,
                base=0.80, cloud=0.42, cloud_scale=0.62, grain=0.10,
                grain_scale=3.4, veins=None, vein_amp=0.55, lift=0.004,
                mask=None):
    """Broad soft grey clouding + an optional vein net, as a tone field.

    `base` is where the field sits in the palette (1 = lightest tone), `cloud`
    the low-frequency swing that makes the mottling, `grain` the fine speckle
    that stops large flats reading as paint.
    """
    n = len(mats)

    def fn(u, w):
        if mask and not mask(u, w):
            return None
        t = base
        t += (fbm(u * cloud_scale, w * cloud_scale, seed, 4) - 0.5) * cloud
        t += (fbm(u * grain_scale, w * grain_scale, seed + 101, 2) - 0.5) * grain
        if veins is not None:
            t -= veins.at(u, w) * vein_amp
        return max(0, min(n - 1, int(t * n)))

    raster(m, mats, face, at, u0, u1, w0, w1, cell, fn, lift)


# --------------------------------------------------------------- soft shadows
class Shadows:
    """Every contact shadow in a room as ONE smooth field over the floor.

    Round 2 baked them as five nested hard-edged rectangles per object and the
    critic read them as bullseye decals painted on the planks.  A distance
    field with an exponential falloff, rasterised through the same quantiser as
    the stone, has round corners and no visible contour.
    """

    def __init__(self):
        self.rects = []      # (x0, x1, z0, z1, reach, strength)
        self.discs = []      # (cx, cz, r, reach, strength)

    def rect(self, x0, x1, z0, z1, reach=0.55, strength=1.0):
        self.rects.append((x0, x1, z0, z1, reach, strength))
        return self

    def disc(self, cx, cz, r, reach=0.40, strength=1.0):
        self.discs.append((cx, cz, r, reach, strength))
        return self

    def at(self, x, z):
        v = 0.0
        for (x0, x1, z0, z1, reach, s) in self.rects:
            dx = max(x0 - x, 0.0, x - x1)
            dz = max(z0 - z, 0.0, z - z1)
            d = math.hypot(dx, dz)
            if d < reach * 3.2:
                v = max(v, s * math.exp(-(d / reach) ** 1.55))
        for (cx, cz, r, reach, s) in self.discs:
            d = max(0.0, math.hypot(x - cx, z - cz) - r)
            if d < reach * 3.2:
                v = max(v, s * math.exp(-(d / reach) ** 1.55))
        return v

    def bake(self, m, mats, y, x0, x1, z0, z1, cell=0.11, mask=None,
             lift=0.0):
        """mats[0] is darkest; index len-1 is 'no shadow' and is never drawn.

        `mats` MUST be semi-transparent (see shadow_ramp).  An opaque shadow
        decal paints one flat tone over planks that are themselves varying, so
        its outline shows up as a tone discontinuity no matter how fine the
        falloff is -- which is what made round 3's first attempt still read as a
        stepped patch even after the rings were gone.  Alpha blending darkens
        whatever is underneath instead, so the boundary is genuinely invisible.
        """
        n = len(mats)

        def fn(x, z):
            if mask and not mask(x, z):
                return None
            v = self.at(x, z)
            if v < 0.03:
                return None
            i = int((1.0 - v) * (n - 1) + 0.5)
            return None if i >= n - 1 else max(0, i)

        raster(m, mats, "+y", y, x0, x1, z0, z1, cell, fn, lift)


def shadow_ramp(n, color="#232628", max_alpha=0.34, name="ao"):
    """A ramp of translucent darks for Shadows.bake: index 0 is the deepest."""
    return [Material(f"{name}{i}", color, roughness=0.9,
                     opacity=round(max_alpha * (1.0 - i / (n - 1.0)), 4))
            for i in range(n)]
