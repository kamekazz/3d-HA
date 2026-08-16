"""Zero-dependency glTF 2.0 / GLB writer plus the primitives our furniture is built from.

Authoring is in FEET (the whole app thinks in feet); glTF is a metres format and
frontend/js/models.js scales every loaded model by 3.28084, so everything is
converted to metres exactly once, on export.

Transforms are baked into vertex positions as parts are added, so the exported
file is a flat node with one primitive per material -- no TRS to get wrong, and
the loader's bbox (which models.js uses to seat furniture on the slab) is just
the vertex bounds.

    m = Model()
    m.add(box(2, 1, 3), mat=WOOD, at=(0, 0, 0))
    m.save("bed.glb")
"""

import json
import math
import struct

FT_TO_M = 0.3048


# --------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------

class Material:
    """A PBR material. `color` is sRGB hex or an (r, g, b) 0-1 tuple."""

    def __init__(self, name, color, roughness=0.85, metallic=0.0,
                 emissive=None, emissive_strength=1.0, opacity=1.0,
                 double_sided=True):
        self.name = name
        self.color = _rgb(color)
        self.roughness = float(roughness)
        self.metallic = float(metallic)
        self.emissive = _rgb(emissive) if emissive else (0.0, 0.0, 0.0)
        self.emissive_strength = float(emissive_strength)
        self.opacity = float(opacity)
        self.double_sided = bool(double_sided)

    def key(self):
        return (self.name, self.color, self.roughness, self.metallic,
                self.emissive, self.emissive_strength, self.opacity,
                self.double_sided)


def _rgb(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return (int(c[0:2], 16) / 255.0,
                int(c[2:4], 16) / 255.0,
                int(c[4:6], 16) / 255.0)
    return (float(c[0]), float(c[1]), float(c[2]))


def _srgb_to_linear(c):
    # glTF baseColorFactor is LINEAR; hex swatches picked off a photo are sRGB.
    def f(u):
        return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return [f(c[0]), f(c[1]), f(c[2])]


# --------------------------------------------------------------------------
# geometry container
# --------------------------------------------------------------------------

class Part:
    """Triangle soup in feet: positions plus a parallel index list."""

    def __init__(self, verts=None, tris=None, smooth=False):
        self.verts = list(verts or [])   # [(x, y, z), ...]
        self.tris = list(tris or [])     # [(i, j, k), ...]
        self.smooth = smooth             # average normals instead of flat-shading

    def copy(self):
        return Part(list(self.verts), list(self.tris), self.smooth)


class Model:
    def __init__(self):
        self._parts = []  # (Part, Material)

    def add(self, part, mat, at=(0, 0, 0), rot_y=0.0, rot_x=0.0, rot_z=0.0,
            scale=(1, 1, 1)):
        """Bake `part` into the model with the given transform (feet, radians).

        Rotation order is Z, then X, then Y -- Y last so `rot_y` always reads as
        "spin this piece of furniture on the floor" no matter what else is set.
        """
        if isinstance(scale, (int, float)):
            scale = (scale, scale, scale)
        cy, sy = math.cos(rot_y), math.sin(rot_y)
        cx, sx = math.cos(rot_x), math.sin(rot_x)
        cz, sz = math.cos(rot_z), math.sin(rot_z)

        out = []
        for (x, y, z) in part.verts:
            x, y, z = x * scale[0], y * scale[1], z * scale[2]
            x, y = x * cz - y * sz, x * sz + y * cz
            y, z = y * cx - z * sx, y * sx + z * cx
            x, z = x * cy + z * sy, -x * sy + z * cy
            out.append((x + at[0], y + at[1], z + at[2]))

        self._parts.append((Part(out, part.tris, part.smooth), mat))
        return self

    def bounds(self):
        lo = [float("inf")] * 3
        hi = [float("-inf")] * 3
        for part, _ in self._parts:
            for v in part.verts:
                for i in range(3):
                    lo[i] = min(lo[i], v[i])
                    hi[i] = max(hi[i], v[i])
        return tuple(lo), tuple(hi)

    # ---- export ----------------------------------------------------------

    def save(self, path):
        mats, groups = [], []
        seen = {}
        for part, mat in self._parts:
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
            verts, norms, idx = _weld(parts)
            if not idx:
                continue

            pos = b"".join(struct.pack("<3f", v[0] * FT_TO_M, v[1] * FT_TO_M,
                                       v[2] * FT_TO_M) for v in verts)
            nrm = b"".join(struct.pack("<3f", *n) for n in norms)
            ind = b"".join(struct.pack("<I", i) for i in idx)

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
            accessors.append({"bufferView": push(ind, 34963), "componentType": 5125,
                              "count": len(idx), "type": "SCALAR"})

            primitives.append({"attributes": {"POSITION": a_pos, "NORMAL": a_nrm},
                               "indices": a_idx, "material": mat_index, "mode": 4})

        gltf_materials = []
        uses_emissive_strength = False
        for m in mats:
            entry = {
                "name": m.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": _srgb_to_linear(m.color) + [m.opacity],
                    "metallicFactor": m.metallic,
                    "roughnessFactor": m.roughness,
                },
                "doubleSided": m.double_sided,
            }
            if m.opacity < 1.0:
                entry["alphaMode"] = "BLEND"
            if m.emissive != (0.0, 0.0, 0.0):
                entry["emissiveFactor"] = _srgb_to_linear(m.emissive)
                if m.emissive_strength != 1.0:
                    uses_emissive_strength = True
                    entry["extensions"] = {"KHR_materials_emissive_strength":
                                           {"emissiveStrength": m.emissive_strength}}
            gltf_materials.append(entry)

        blob = b"".join(bin_chunks)
        gltf = {
            "asset": {"version": "2.0", "generator": "roomkit"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0, "name": "root"}],
            "meshes": [{"primitives": primitives}],
            "materials": gltf_materials,
            "accessors": accessors,
            "bufferViews": buffer_views,
            "buffers": [{"byteLength": len(blob)}],
        }
        if uses_emissive_strength:
            gltf["extensionsUsed"] = ["KHR_materials_emissive_strength"]

        js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        js += b" " * ((-len(js)) % 4)

        with open(path, "wb") as fh:
            fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
            fh.write(struct.pack("<II", len(js), 0x4E4F534A))
            fh.write(js)
            fh.write(struct.pack("<II", len(blob), 0x004E4942))
            fh.write(blob)
        return path


def _weld(parts):
    """Flat-shade (duplicate verts per face) or smooth-shade (average) each part."""
    verts, norms, idx = [], [], []
    for part in parts:
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
            idx.extend(base + i for tri in part.tris for i in tri)
        else:
            for (a, b, c) in part.tris:
                va, vb, vc = part.verts[a], part.verts[b], part.verts[c]
                n = _face_normal(va, vb, vc)
                base = len(verts)
                verts.extend((va, vb, vc))
                norms.extend((n, n, n))
                idx.extend((base, base + 1, base + 2))
    return verts, norms, idx


def _face_normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return _norm((uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx))


def _norm(v):
    L = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (0.0, 1.0, 0.0) if L < 1e-12 else (v[0] / L, v[1] / L, v[2] / L)


# --------------------------------------------------------------------------
# primitives -- all sized in feet, all centred on X/Z with the base at y=0
# --------------------------------------------------------------------------

def box(w, h, d, anchor="base"):
    """Axis-aligned box. anchor 'base' puts y=0 at the bottom, 'center' centres it."""
    y0, y1 = (0.0, h) if anchor == "base" else (-h / 2, h / 2)
    x0, x1, z0, z1 = -w / 2, w / 2, -d / 2, d / 2
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
         (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    t = [(0, 2, 1), (0, 3, 2),            # bottom
         (4, 5, 6), (4, 6, 7),            # top
         (0, 1, 5), (0, 5, 4),            # -z
         (2, 3, 7), (2, 7, 6),            # +z
         (1, 2, 6), (1, 6, 5),            # +x
         (3, 0, 4), (3, 4, 7)]            # -x
    return Part(v, t)


def rounded_box(w, h, d, r=0.05, seg=3, anchor="base"):
    """Box with rounded vertical edges -- reads as upholstery/soft furniture."""
    r = min(r, w / 2 - 1e-4, d / 2 - 1e-4)
    ring = []
    for cx, cz, a0 in ((w / 2 - r, d / 2 - r, 0.0),
                       (-(w / 2 - r), d / 2 - r, math.pi / 2),
                       (-(w / 2 - r), -(d / 2 - r), math.pi),
                       (w / 2 - r, -(d / 2 - r), 3 * math.pi / 2)):
        for s in range(seg + 1):
            a = a0 + (math.pi / 2) * s / seg
            ring.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return _prism(ring, h, anchor, smooth=True)


def cylinder(radius, h, seg=24, anchor="base", r_top=None):
    """Cylinder or truncated cone (set r_top) about the Y axis."""
    r_top = radius if r_top is None else r_top
    y0, y1 = (0.0, h) if anchor == "base" else (-h / 2, h / 2)
    v, t = [], []
    for s in range(seg):
        a = 2 * math.pi * s / seg
        v.append((radius * math.cos(a), y0, radius * math.sin(a)))
        v.append((r_top * math.cos(a), y1, r_top * math.sin(a)))
    # Winding: every face outward. This was inverted on all three surfaces --
    # the side wall faced the axis, the bottom cap faced UP and the top cap
    # faced DOWN -- which went unnoticed for a long time because Material
    # defaults to double_sided. It bites the moment a piece needs one-sided
    # faces: a ceiling built with double_sided=False (so its slopes cull when
    # seen from above) left one bright emissive disc per recessed can shining
    # up through the culled ceiling and projecting onto the floor below.
    for s in range(seg):
        b, n = 2 * s, 2 * ((s + 1) % seg)
        t += [(b, b + 1, n), (b + 1, n + 1, n)]
    cb, ct = len(v), len(v) + 1
    v += [(0.0, y0, 0.0), (0.0, y1, 0.0)]
    for s in range(seg):
        b, n = 2 * s, 2 * ((s + 1) % seg)
        t += [(cb, b, n), (ct, n + 1, b + 1)]
    return Part(v, t, smooth=True)


def prism(points, h, anchor="base", smooth=False):
    """Extrude a CCW 2-D polygon [(x, z), ...] upward by h."""
    return _prism(points, h, anchor, smooth)


def _prism(points, h, anchor, smooth):
    y0, y1 = (0.0, h) if anchor == "base" else (-h / 2, h / 2)
    n = len(points)
    v = [(p[0], y0, p[1]) for p in points] + [(p[0], y1, p[1]) for p in points]
    t = []
    for i in range(n):
        j = (i + 1) % n
        t += [(i, j, i + n), (j, j + n, i + n)]
    for i in range(1, n - 1):                 # caps (fan; convex or near-convex)
        t.append((0, i + 1, i))               # bottom, facing -Y
        t.append((n, n + i, n + i + 1))       # top, facing +Y
    return Part(v, t, smooth=smooth)


def quad(p0, p1, p2, p3):
    """A single planar quad from four 3-D points in CCW order."""
    return Part([p0, p1, p2, p3], [(0, 1, 2), (0, 2, 3)])


def sag_plane(w, d, sag=0.08, nx=10, nz=10, y=0.0, edge_drop=0.0):
    """A subdivided plane pulled down in the middle -- bedding, rugs, throws.

    `sag` is the dip at the centre; `edge_drop` pulls the perimeter down instead,
    which is what makes a duvet look like it is hanging over the mattress edge.
    """
    v, t = [], []
    for iz in range(nz + 1):
        for ix in range(nx + 1):
            u, w_ = ix / nx, iz / nz
            x, z = (u - 0.5) * w, (w_ - 0.5) * d
            bulge = math.sin(math.pi * u) * math.sin(math.pi * w_)
            edge = 1.0 - bulge
            v.append((x, y - sag * bulge - edge_drop * edge, z))
    for iz in range(nz):
        for ix in range(nx):
            a = iz * (nx + 1) + ix
            b, c, dd = a + 1, a + nx + 1, a + nx + 2
            t += [(a, c, b), (b, c, dd)]
    return Part(v, t, smooth=True)


def torus(radius, tube, seg=20, ring=10):
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        for j in range(ring):
            b = 2 * math.pi * j / ring
            rr = radius + tube * math.cos(b)
            v.append((rr * math.cos(a), tube * math.sin(b), rr * math.sin(a)))
    for i in range(seg):
        for j in range(ring):
            a0 = i * ring + j
            a1 = i * ring + (j + 1) % ring
            b0 = ((i + 1) % seg) * ring + j
            b1 = ((i + 1) % seg) * ring + (j + 1) % ring
            t += [(a0, b0, a1), (a1, b0, b1)]
    return Part(v, t, smooth=True)
