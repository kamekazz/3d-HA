"""Round-5 helpers for the Living Room (room 5).

Round 4 matched every surface's sd and still read plastic, because sd is
scale-blind.  Measured as mean |delta| between ADJACENT pixels at native
render resolution (m5.py), photo f's clean fields are

    stone       sd  8.4-11.2   |d1| 1.7-2.7   |d1|/sd 0.21-0.24
    upholstery  sd 18.4-39.2   |d1| 4.8-9.5   |d1|/sd 0.26-0.32
    rug         sd 15.5-27.3   |d1| 5.2-11.8  |d1|/sd 0.26-0.43

and the round-4 render sat at |d1|/sd 0.070.  Three causes, all in kit4:

 1. FIXED SPLIT DIAGONALS.  `plate` fans its cap through a centre vertex,
    `mottle` splits every cell on (0,2,1)/(0,3,2) and `puff` on (a,c,b)/(b,c,e).
    Under smooth normals a whole field of parallel diagonals folds into visible
    creases -- the fold-card look that splits every seat cushion.  Everything
    here alternates the diagonal per cell.
 2. FACET SIZE.  At rings=7/seg=14 a cushion's facets are ~0.2-0.35 ft, which is
    15-30 px in the reference render.  |d1| is (luminance swing)/(facet px), so
    coarse facets cannot produce fine gradient no matter how big the swing is.
    `puff5`/`grid5` take a `cell` in FEET and tessellate to it.
 3. PER-VERTEX RANDOM JITTER.  kit4's `nub` is white noise on the vertices, so
    its amplitude is tied to the tessellation and it cancels out as the mesh
    refines.  Displacement here comes from a spatial NOISE FIELD sampled at the
    undisplaced surface point, so the feature size is authored in feet and is
    independent of how finely the surface happens to be cut.

Payload: `save5` writes UNSIGNED_SHORT indices when a primitive has <= 65535
vertices (glb.py always writes UNSIGNED_INT).  On a smooth indexed grid that is
24V + 6T instead of 24V + 12T bytes -- a flat 25% off exactly the pieces this
round has to make finer.  It is a local copy on purpose: glb.py is shared with
other agents mid-build.  It is worth folding back into glb.py later.
"""
import json
import math
import os
import struct

from kit4 import *                       # noqa: F401,F403
from kit4 import Part, Material, Model, _shrink

from roomkit.glb import FT_TO_M, _srgb_to_linear, _face_normal, _norm


# ===================================================================== textures
# THE lever this room was missing.  Shading alone cannot carry fine texture in
# this scene: a MEASURED +/-15 deg normal wobble on a horizontal surface moves
# its luminance by about +/-3 bytes, because one soft sun plus a near-uniform
# IBL is what lights everything.  So geometry can buy silhouette and mid-scale
# form, and nothing finer -- which is why round 4's `nub` metered |d1| 0.77 on a
# clean deck against photo f's 4.8-9.5.
#
# ROOM-BRIEF already names the answer ("prefer a tiled texture or vertex
# colours ... they also give finer spatial detail, which is what the eye
# actually reads"); nothing had implemented it because glb.py writes POSITION
# and NORMAL only.  A 64x64 seamless PNG repeated every ~1.5 ft is 3-6 KB and
# puts detail at ONE render pixel, which no amount of geometry can do inside the
# payload budget.
class Tex:
    """A tiled baseColor texture: seamless PNG bytes + a repeat period in feet."""

    def __init__(self, png, repeat=1.5, name="tile"):
        self.png, self.repeat, self.name = png, float(repeat), name


def noise_tile(n=64, lo=0.55, hi=1.0, seed=1, blur=0, streak=0, sat=0.0):
    """A SEAMLESS greyscale-ish noise tile as PNG bytes.

    Seamless because the smoothing wraps.  `streak` > 0 stretches the field
    along x, which is what a flatweave rug and a ticking stripe look like;
    `blur` softens it towards a boucle slub rather than sensor noise.
    """
    import numpy as np
    from PIL import Image
    rs = np.random.RandomState(seed)
    a = rs.rand(n, n).astype(np.float32)
    if streak:
        k = int(streak)
        acc = np.zeros_like(a)
        for s in range(-k, k + 1):
            acc += np.roll(a, s, axis=1)
        a = 0.45 * a + 0.55 * (acc / (2 * k + 1))
    for _ in range(blur):
        a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0)
             + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5.0
    a -= a.min()
    a /= (a.max() or 1.0)
    a = lo + (hi - lo) * a
    g8 = (a * 255.0 + 0.5).astype(np.uint8)
    import io
    buf = io.BytesIO()
    if sat:
        rgb = np.repeat(g8[:, :, None], 3, axis=2).astype(np.float32)
        rgb[:, :, 0] *= (1.0 + sat)
        rgb[:, :, 2] *= (1.0 - sat)
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").save(
            buf, format="PNG", optimize=True)
    else:                       # 8-bit grey: a third of the bytes of RGB
        Image.fromarray(g8, "L").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def tex_lift(tex):
    """The sRGB factor an albedo must be scaled by so that multiplying it with
    `tex` leaves the surface's MEAN where it was.  Solved from the tile's own
    linear mean, not guessed: baseColorTexture multiplies baseColorFactor in
    LINEAR space, so a tile running 0.80-1.0 in sRGB darkens by ~20 bytes."""
    import io
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(tex.png)).convert("L")).astype(np.float32) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return float((1.0 / max(1e-6, lin.mean())) ** (1.0 / 2.2))


class TMaterial(Material):
    """Material plus an optional tiled baseColor `Tex`."""

    def __init__(self, name, color, tex=None, **kw):
        Material.__init__(self, name, color, **kw)
        self.tex = tex

    def key(self):
        return Material.key(self) + (id(self.tex),)


def add5(m, part, mat, **kw):
    """Model.add that carries the part's UVs through the transform."""
    uv = getattr(part, "uvs", None)
    m.add(part, mat, **kw)
    if uv is not None:
        m._parts[-1][0].uvs = uv
    return m


def _weld5(parts):
    """glb._weld, but carrying TEXCOORD_0."""
    verts, norms, uvs, idx = [], [], [], []
    for part in parts:
        pu = getattr(part, "uvs", None)
        if part.smooth:
            base = len(verts)
            acc = [[0.0, 0.0, 0.0] for _ in part.verts]
            for (a, b, c) in part.tris:
                n = _face_normal(part.verts[a], part.verts[b], part.verts[c])
                for i in (a, b, c):
                    acc[i][0] += n[0]
                    acc[i][1] += n[1]
                    acc[i][2] += n[2]
            verts.extend(part.verts)
            norms.extend(_norm(v) if any(v) else (0.0, 1.0, 0.0) for v in acc)
            uvs.extend(pu if pu else [(0.0, 0.0)] * len(part.verts))
            idx.extend(base + i for tri in part.tris for i in tri)
        else:
            for (a, b, c) in part.tris:
                va, vb, vc = part.verts[a], part.verts[b], part.verts[c]
                n = _face_normal(va, vb, vc)
                base = len(verts)
                verts.extend((va, vb, vc))
                norms.extend((n, n, n))
                uvs.extend((pu[a], pu[b], pu[c]) if pu
                           else ((0.0, 0.0), (0.0, 0.0), (0.0, 0.0)))
                idx.extend((base, base + 1, base + 2))
    return verts, norms, uvs, idx


# ====================================================================== export
def save5(m, name, out=None):
    """glb.Model.save with 16-bit indices where they fit, plus tiled textures."""
    path = os.path.join(out or OUT, name + ".glb")
    mats, groups, seen = [], [], {}
    for part, mat in m._parts:
        k = mat.key()
        if k not in seen:
            seen[k] = len(mats)
            mats.append(mat)
            groups.append([])
        groups[seen[k]].append(part)

    bin_chunks, offset = [], 0
    accessors, buffer_views, primitives = [], [], []

    def push(data, target):
        nonlocal offset
        pad = (-len(data)) % 4
        bin_chunks.append(data + b"\x00" * pad)
        view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset,
                             "byteLength": len(data), "target": target})
        offset += len(data) + pad
        return view

    for mat_index, parts in enumerate(groups):
        verts, norms, uvs, idx = _weld5(parts)
        if not idx:
            continue
        pos = b"".join(struct.pack("<3f", v[0] * FT_TO_M, v[1] * FT_TO_M,
                                   v[2] * FT_TO_M) for v in verts)
        nrm = b"".join(struct.pack("<3f", *n) for n in norms)
        if len(verts) <= 65535:
            ind, ctype = struct.pack("<%dH" % len(idx), *idx), 5123
        else:
            ind, ctype = struct.pack("<%dI" % len(idx), *idx), 5125
        lo = [min(v[i] for v in verts) * FT_TO_M for i in range(3)]
        hi = [max(v[i] for v in verts) * FT_TO_M for i in range(3)]
        a_pos = len(accessors)
        accessors.append({"bufferView": push(pos, 34962), "componentType": 5126,
                          "count": len(verts), "type": "VEC3",
                          "min": lo, "max": hi})
        a_nrm = len(accessors)
        accessors.append({"bufferView": push(nrm, 34962), "componentType": 5126,
                          "count": len(norms), "type": "VEC3"})
        a_idx = len(accessors)
        accessors.append({"bufferView": push(ind, 34963), "componentType": ctype,
                          "count": len(idx), "type": "SCALAR"})
        attrs = {"POSITION": a_pos, "NORMAL": a_nrm}
        if getattr(mats[mat_index], "tex", None) is not None:
            uvb = b"".join(struct.pack("<2f", u, v) for (u, v) in uvs)
            a_uv = len(accessors)
            accessors.append({"bufferView": push(uvb, 34962),
                              "componentType": 5126, "count": len(uvs),
                              "type": "VEC2"})
            attrs["TEXCOORD_0"] = a_uv
        primitives.append({"attributes": attrs, "indices": a_idx,
                           "material": mat_index, "mode": 4})

    images, samplers, textures, tex_index = [], [], [], {}
    gmats, uses_es = [], False
    for mt in mats:
        e = {"name": mt.name,
             "pbrMetallicRoughness": {
                 "baseColorFactor": _srgb_to_linear(mt.color) + [mt.opacity],
                 "metallicFactor": mt.metallic,
                 "roughnessFactor": mt.roughness},
             "doubleSided": mt.double_sided}
        tx = getattr(mt, "tex", None)
        if tx is not None:
            if id(tx) not in tex_index:
                iv = push(tx.png, None)
                buffer_views[iv].pop("target", None)
                images.append({"bufferView": iv, "mimeType": "image/png",
                               "name": tx.name})
                if not samplers:
                    samplers.append({"magFilter": 9729, "minFilter": 9987,
                                     "wrapS": 10497, "wrapT": 10497})
                textures.append({"sampler": 0, "source": len(images) - 1})
                tex_index[id(tx)] = len(textures) - 1
            e["pbrMetallicRoughness"]["baseColorTexture"] = {
                "index": tex_index[id(tx)], "texCoord": 0}
        if mt.opacity < 1.0:
            e["alphaMode"] = "BLEND"
        if mt.emissive != (0.0, 0.0, 0.0):
            e["emissiveFactor"] = _srgb_to_linear(mt.emissive)
            if mt.emissive_strength != 1.0:
                uses_es = True
                e["extensions"] = {"KHR_materials_emissive_strength":
                                   {"emissiveStrength": mt.emissive_strength}}
        gmats.append(e)

    blob = b"".join(bin_chunks)
    g = {"asset": {"version": "2.0", "generator": "roomkit/kit5"},
         "scene": 0, "scenes": [{"nodes": [0]}],
         "nodes": [{"mesh": 0, "name": "root"}],
         "meshes": [{"primitives": primitives}], "materials": gmats,
         "accessors": accessors, "bufferViews": buffer_views,
         "buffers": [{"byteLength": len(blob)}]}
    if images:
        g["images"] = images
        g["samplers"] = samplers
        g["textures"] = textures
    if uses_es:
        g["extensionsUsed"] = ["KHR_materials_emissive_strength"]
    js = json.dumps(g, separators=(",", ":")).encode("utf-8")
    js += b" " * ((-len(js)) % 4)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2,
                             12 + 8 + len(js) + 8 + len(blob)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A))
        fh.write(js)
        fh.write(struct.pack("<II", len(blob), 0x004E4942))
        fh.write(blob)
    lo, hi = m.bounds()
    print("  %-16s %6.1f KB  size=(%.2f,%.2f,%.2f)" %
          (name, os.path.getsize(path) / 1024.0,
           hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    return path


# ======================================================================= noise
_M1, _M2, _M3 = 374761393, 668265263, 1442695040888963407
_MASK = 0xFFFFFFFF


def _hash3(i, j, k, seed):
    n = (i * _M1 + j * _M2 + k * 2147483647 + seed * 1013904223) & _MASK
    n = ((n ^ (n >> 13)) * 1274126177) & _MASK
    n ^= n >> 16
    return (n & 0xFFFFFF) / 8388607.5 - 1.0


def _sm(t):
    return t * t * (3.0 - 2.0 * t)


def _val(x, y, z, s, seed):
    """Trilinear value noise on a lattice of spacing `s`, in -1..1."""
    xi, yi, zi = x / s, y / s, z / s
    i0, j0, k0 = math.floor(xi), math.floor(yi), math.floor(zi)
    fx, fy, fz = _sm(xi - i0), _sm(yi - j0), _sm(zi - k0)
    i0, j0, k0 = int(i0), int(j0), int(k0)
    c = _hash3
    c00 = c(i0, j0, k0, seed) * (1 - fx) + c(i0 + 1, j0, k0, seed) * fx
    c10 = c(i0, j0 + 1, k0, seed) * (1 - fx) + c(i0 + 1, j0 + 1, k0, seed) * fx
    c01 = c(i0, j0, k0 + 1, seed) * (1 - fx) + c(i0 + 1, j0, k0 + 1, seed) * fx
    c11 = (c(i0, j0 + 1, k0 + 1, seed) * (1 - fx)
           + c(i0 + 1, j0 + 1, k0 + 1, seed) * fx)
    return ((c00 * (1 - fy) + c10 * fy) * (1 - fz)
            + (c01 * (1 - fy) + c11 * fy) * fz)


class Grain:
    """A two-octave displacement field, authored in FEET.

    `fine` is the octave that produces |d1| -- its lattice spacing must be
    about 2x the mesh cell or the mesh cannot carry it.  `coarse` is the octave
    that produces sd: big soft undulations that a human reads as the shape of a
    stuffed cushion, and which contribute almost nothing to |d1|.
    """

    def __init__(self, seed=1, fine=0.20, fine_amp=0.016,
                 coarse=0.85, coarse_amp=0.030):
        self.seed = seed
        self.f, self.fa = fine, fine_amp
        self.c, self.ca = coarse, coarse_amp

    def at(self, x, y, z):
        return (_val(x, y, z, self.f, self.seed) * self.fa
                + _val(x, y, z, self.c, self.seed + 77) * self.ca)


FLAT = Grain(1, fine_amp=0.0, coarse_amp=0.0)


# ================================================================ tessellation
def _quads(ni, nj, wrap_j, flip=True):
    """Triangles of an (ni+1) x nj/(nj+1) vertex grid, ALTERNATING the split
    diagonal per cell.  A fixed diagonal folds a smooth-shaded field into
    parallel creases -- kit4's puff/mottle/plate all did that."""
    t = []
    jn = nj if wrap_j else nj  # cells along j
    for i in range(ni):
        for j in range(jn):
            a = i * (nj if wrap_j else nj + 1) + j
            b = i * (nj if wrap_j else nj + 1) + ((j + 1) % nj if wrap_j else j + 1)
            c = a + (nj if wrap_j else nj + 1)
            e = b + (nj if wrap_j else nj + 1)
            if flip and ((i + j) & 1):
                t += [(a, c, e), (a, e, b)]
            else:
                t += [(a, c, b), (b, c, e)]
    return t


def _sgnpow(t, e):
    s = -1.0 if t < 0 else 1.0
    return s * (abs(t) ** e)


def _arclen_params(fn, n, closed):
    """n parameter values whose points are EQUALLY SPACED along the curve
    `fn(t)`, t in 0..1.  A superellipse sampled uniformly in angle piles its
    samples into the corners and leaves each flat face with one huge quad --
    which is the artefact kit4's `puff` shipped."""
    D = 720
    pts = [fn(k / float(D)) for k in range(D + 1)]
    cum = [0.0]
    for k in range(D):
        a, b = pts[k], pts[k + 1]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1] or 1.0
    out, k = [], 0
    m = n if closed else n - 1
    for i in range(n):
        want = total * i / float(m)
        while k < D - 1 and cum[k + 1] < want:
            k += 1
        span = (cum[k + 1] - cum[k]) or 1.0
        f = min(1.0, (want - cum[k]) / span)
        out.append((k + f) / float(D))
    return out


def tbox(w, h, d, repeat=1.0, anchor="base"):
    """A box whose six faces each carry planar UVs, so a tiled texture lands on
    it at the same texel size as on the puffs beside it.  glb.box shares eight
    vertices between faces, which cannot hold per-face UVs."""
    y0, y1 = (0.0, h) if anchor == "base" else (-h / 2, h / 2)
    x0, x1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2
    R = repeat or 1.0
    faces = [
        ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 1)),
        ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (0, 1)),
        ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (2, 1)),
        ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (2, 1)),
        ([(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], (0, 2)),
        ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, 2))]
    v, t, uv = [], [], []
    for (quad, (ax, ay)) in faces:
        b = len(v)
        v.extend(quad)
        uv.extend([(q[ax] / R, q[ay] / R) for q in quad])
        t += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    part = Part(v, t)
    part.uvs = uv
    return part


def puff5(w, h, d, r=None, cell=0.16, grain=None, anchor="base",
          box_u=0.42, box_v=0.46, seg=None, rings=None, v0=0.0,
          uv_repeat=0.0):
    """A plump upholstery volume: a superellipsoid, arc-length tessellated to
    `cell` FEET and displaced along its own normal by a spatial `grain` field.
    Drop-in replacement for kit4.puff.

    Why not kit4's rounded cube.  It placed each vertex at
    (sign(n) * half_extent) + r * n, which is the correct rounded box -- but
    that map is DEGENERATE on every flat face: the whole +Y face has normal
    (0,1,0), so all of it collapses to a single parameter value.  In the mesh
    each flat face therefore came out as ONE quad bridging the sign flip, split
    on one fixed diagonal.  That is the crease across every seat cushion, and it
    is also why round 4 metered |d1|/sd 0.070: the largest and most
    camera-facing part of every cushion carried no tessellation at all.

    A superellipsoid has no degenerate region, and arc-length sampling puts
    even-sized cells on the flat faces where the camera looks.  `box_u`/`box_v`
    are squareness exponents (1.0 = ellipsoid, 0.2 = nearly a box); 0.42/0.46
    reads as a stuffed cushion.
    """
    A, B, C = w / 2.0, h / 2.0, d / 2.0
    if r is not None:                     # kit4 call sites pass a corner radius
        box_u = max(0.24, min(0.85, 1.7 * r / max(1e-6, min(A, C))))
        box_v = max(0.26, min(0.90, 1.7 * r / max(1e-6, min(B, min(A, C)))))

    def ring_xy(t):
        u = 2 * math.pi * t
        return (A * _sgnpow(math.cos(u), box_u), C * _sgnpow(math.sin(u), box_u))

    def prof_xy(t):
        vv = -math.pi / 2 + math.pi * t
        return (_sgnpow(math.cos(vv), box_v), B * _sgnpow(math.sin(vv), box_v))

    def _len(fn, sx, sy):
        L = 0.0
        for k in range(240):
            a, b = fn(k / 240.0), fn((k + 1) / 240.0)
            L += math.hypot((b[0] - a[0]) * sx, (b[1] - a[1]) * sy)
        return L

    if seg is None:
        seg = max(10, int(round(_len(ring_xy, 1.0, 1.0) / cell)))
        seg += seg & 1
    if rings is None:
        # MEAN radial scale, not max: a lat-long grid on an elongated part is
        # already over-sampled across its short axis, and using max(A, C) here
        # doubled the ring count of every sofa arm for no visible detail.
        rings = max(5, int(round(_len(prof_xy, 0.5 * (A + C), 1.0) / cell)))
    rings_full = rings

    ring_len = _len(ring_xy, 1.0, 1.0)
    prof_len = _len(prof_xy, 0.5 * (A + C), 1.0)
    us = _arclen_params(ring_xy, seg, True) + [1.0]   # duplicated seam column
    vs = _arclen_params(prof_xy, rings + 1, False)
    v_drop = 0
    if v0 > 0.0:
        # drop the underside: a seat cushion's bottom sits on the deck and no
        # camera in this app is below it.
        v_drop = int(round(rings * v0))
        vs = vs[v_drop:]
        rings = len(vs) - 1
    base = []
    for t in vs:
        sr, py = prof_xy(t)
        base.append([(ring_xy(s)[0] * sr, py, ring_xy(s)[1] * sr)
                     for s in us[:seg]])

    g = grain or FLAT
    y0 = h / 2.0 if anchor == "base" else 0.0
    ku = max(1, int(round(ring_len / uv_repeat))) if uv_repeat else 0
    v, uv = [], []
    for i in range(rings + 1):
        ip, iN, row = base[max(0, i - 1)], base[min(rings, i + 1)], base[i]
        for j in range(seg + 1):
            px, py, pz = row[j % seg]
            a, b = row[(j + 1) % seg], row[(j - 1) % seg]
            tu = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
            jm = j % seg
            tv = (iN[jm][0] - ip[jm][0], iN[jm][1] - ip[jm][1],
                  iN[jm][2] - ip[jm][2])
            # tv x tu, not tu x tv: the triangle winding in _quads makes +u x +v
            # point INTO the volume, so displacing along it would dent the mesh.
            nx = tv[1] * tu[2] - tv[2] * tu[1]
            ny = tv[2] * tu[0] - tv[0] * tu[2]
            nz = tv[0] * tu[1] - tv[1] * tu[0]
            L = math.sqrt(nx * nx + ny * ny + nz * nz)
            if L < 1e-9:
                nx, ny, nz = px, py * 2.0, pz
                L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / L, ny / L, nz / L
            dr = g.at(px, py, pz)
            v.append((px + nx * dr, py + ny * dr + y0, pz + nz * dr))
            if uv_repeat:
                uv.append((ku * j / float(seg),
                           (v_drop + i) * prof_len / (rings_full * uv_repeat)))
    part = Part(v, _quads(rings, seg, False), smooth=True)
    if uv_repeat:
        part.uvs = uv
    return part


def bolster5(length, r, cell=0.13, grain=None, box=0.55, uv_repeat=0.0):
    return puff5(length, 2 * r, 2 * r, cell=cell, grain=grain, anchor="center",
                 box_u=box, box_v=0.85, uv_repeat=uv_repeat)


def grid5(w, d, cell=0.15, grain=None, y=0.0, warp=0.0, rnd=None,
          uv_repeat=0.0):
    """Flat panel tessellated to `cell` and displaced in Y by `grain`.

    One indexed Part -- (n+1)^2 shared vertices for n^2 cells -- where kit4's
    `mottle` wrote 4 unshared verts per cell.  That is what makes a rug fine
    enough to carry pixel-scale gradient without a 4 MB file.
    """
    g = grain or FLAT
    nx = max(1, int(round(w / cell)))
    nz = max(1, int(round(d / cell)))
    v = []
    for iz in range(nz + 1):
        z = -d / 2 + d * iz / nz
        for ix in range(nx + 1):
            x = -w / 2 + w * ix / nx
            jx = jz = 0.0
            if warp and rnd and 0 < ix < nx and 0 < iz < nz:
                jx, jz = rnd.uniform(-warp, warp), rnd.uniform(-warp, warp)
            v.append((x + jx, y + g.at(x, y, z), z + jz))
    part = Part(v, _quads(nz, nx, False), smooth=True)
    if uv_repeat:
        part.uvs = [(p[0] / uv_repeat, p[2] / uv_repeat) for p in v]
    return part


def drape5(w, d, sag=0.06, edge_drop=0.0, cell=0.14, grain=None,
           uv_repeat=0.0):
    """A throw: a sagging panel, alternating diagonals, with grain."""
    g = grain or FLAT
    nx = max(2, int(round(w / cell)))
    nz = max(2, int(round(d / cell)))
    v = []
    for iz in range(nz + 1):
        tz = iz / nz
        z = -d / 2 + d * tz
        for ix in range(nx + 1):
            tx = ix / nx
            x = -w / 2 + w * tx
            bowl = math.sin(math.pi * tx) * math.sin(math.pi * tz)
            edge = (1.0 - bowl)
            y = -sag * bowl - edge_drop * (edge ** 2.2)
            v.append((x, y + g.at(x, y, z), z))
    part = Part(v, _quads(nz, nx, False), smooth=True)
    if uv_repeat:
        part.uvs = [(p[0] / uv_repeat, p[2] / uv_repeat) for p in v]
    return part


# ================================================================== fieldstone
def plate5(poly, z0, h, bevel=0.055, rise=0.30, tilt=(0.0, 0.0), grain=None,
           n_ring=2, uv_repeat=0.0):
    """A painted fieldstone with the SHALLOW relief round 4 deleted.

    Round 3 put a 3-ring dome behind a dark recessed joint and metered sd 34
    against the photo's 8-11; round 4 answered by deleting the bevel entirely
    and shipped flat caps with no relief at all.  Photo f (p5_stone.png at
    native resolution) shows neither: large white plates with SOFT ROLLED edges
    and hairline joints, 1st-99th percentile 152-194 on a 8.4 sd.

    So: `n_ring` intermediate rings step the cap up over a `bevel` inset, each
    ring a fraction `rise` further -- a soft shoulder rather than a cliff -- and
    the cap itself is displaced by the grain field.  No centre fan vertex: the
    cap is a strip-wound polygon, because a fan through one centre vertex is a
    fixed diagonal and drew a star crease across every stone.
    """
    g = grain or FLAT
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    rings = [poly]
    for k in range(1, n_ring + 1):
        rings.append(_shrink(poly, bevel * k / n_ring))
    zs = [z0]
    for k in range(1, n_ring + 1):
        f = (k / float(n_ring)) ** 0.65
        zs.append(z0 + h * (rise + (1.0 - rise) * f))
    v, t = [], []
    for k, ring in enumerate(rings):
        for (x, y) in ring:
            zz = zs[k]
            if k == n_ring:
                zz += (tilt[0] * (x - cx) + tilt[1] * (y - cy)
                       + g.at(x, y, 0.0))
            v.append((x, y, zz))
    for k in range(n_ring):
        b0, b1 = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            if (i + k) & 1:
                t += [(b0 + i, b0 + j, b1 + j), (b0 + i, b1 + j, b1 + i)]
            else:
                t += [(b0 + i, b0 + j, b1 + i), (b0 + j, b1 + j, b1 + i)]
    top = n_ring * n
    for i in range(1, n - 1):
        t.append((top, top + i, top + i + 1))
    part = Part(v, t, smooth=True)
    if uv_repeat:
        part.uvs = [(p[0] / uv_repeat, p[1] / uv_repeat) for p in v]
    return part


# ======================================================================= walls
def wall_skin(m, edge, color, y0, y1, gaps=(), inset=0.035, thick=0.014,
              rough=0.95):
    """A plain NON-emissive albedo skin over one whole wall face of the room
    polygon.  ROOM-BRIEF "give each wall its own albedo": one sun and no bounce
    leaves the four walls 100+ bytes apart at a single wall_color, and this is
    the only lever that closes it (office 85.5 -> 22.9, garage 91.5 -> 12.3).
    Not the rejected wall wash: no emissive, corner to corner, roughness
    matched to the room wall's 0.95.

    `gaps` are (t0, t1) spans along the edge to leave open (window/door cuts),
    given in the edge's own offset parameter.
    """
    mat = Material("lrskin" + color.lstrip("#"), color, roughness=rough,
                   metallic=0.0, double_sided=False)
    a, b = EDGES[edge]
    nrm, L = edge_normal(a, b)
    dx, dz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    spans, lo = [], 0.0
    for (g0, g1) in sorted(gaps):
        if g0 > lo:
            spans.append((lo, min(g0, L)))
        lo = max(lo, g1)
    if lo < L:
        spans.append((lo, L))
    for (t0, t1) in spans:
        if t1 - t0 < 0.02:
            continue
        p0 = (a[0] + dx * t0 + nrm[0] * inset, a[1] + dz * t0 + nrm[1] * inset)
        p1 = (a[0] + dx * t1 + nrm[0] * inset, a[1] + dz * t1 + nrm[1] * inset)
        q0 = (p0[0] - nrm[0] * thick, p0[1] - nrm[1] * thick)
        q1 = (p1[0] - nrm[0] * thick, p1[1] - nrm[1] * thick)
        v = [(p0[0], y0, p0[1]), (p1[0], y0, p1[1]),
             (p1[0], y1, p1[1]), (p0[0], y1, p0[1]),
             (q0[0], y0, q0[1]), (q1[0], y0, q1[1]),
             (q1[0], y1, q1[1]), (q0[0], y1, q0[1])]
        m.add(Part(v, [(0, 1, 2), (0, 2, 3),          # room-facing
                       (5, 4, 7), (5, 7, 6),          # back
                       (4, 5, 1), (4, 1, 0),
                       (3, 2, 6), (3, 6, 7),
                       (1, 5, 6), (1, 6, 2),
                       (4, 0, 3), (4, 3, 7)]), mat)
