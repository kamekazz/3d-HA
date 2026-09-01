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
    """A PBR material. `color` is sRGB hex or an (r, g, b) 0-1 tuple.

    `tex` is OPTIONAL and takes raw PNG bytes (see `png_gray` / `png_rgb`).
    It is exported as `baseColorTexture` with a REPEAT sampler, so a small
    seamless tile plus UVs that run past 1.0 covers a whole floor or wall at a
    few KB. That is the cheap way to buy FINE-SCALE surface texture: the
    project's payload budget is 300 KB per piece and rasterising the same
    detail into geometry cells has cost whole megabytes and still metered
    smoother than the photo (see ROOM-BRIEF, "sd is SCALE-BLIND").

    The texture MULTIPLIES `color` (glTF says baseColor = factor x texel), and
    it is sampled as sRGB, so author the tile near white and let `color` carry
    the hue: a tile whose mean is 240/255 darkens the material by ~6%.
    """

    def __init__(self, name, color, roughness=0.85, metallic=0.0,
                 emissive=None, emissive_strength=1.0, opacity=1.0,
                 double_sided=True, tex=None):
        self.name = name
        self.color = _rgb(color)
        self.roughness = float(roughness)
        self.metallic = float(metallic)
        self.emissive = _rgb(emissive) if emissive else (0.0, 0.0, 0.0)
        self.emissive_strength = float(emissive_strength)
        self.opacity = float(opacity)
        self.double_sided = bool(double_sided)
        self.tex = tex

    def key(self):
        return (self.name, self.color, self.roughness, self.metallic,
                self.emissive, self.emissive_strength, self.opacity,
                self.double_sided,
                None if self.tex is None else hash(bytes(self.tex)))


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
    """Triangle soup in feet: positions plus a parallel index list.

    `colors` is OPTIONAL and, when given, must be one (r, g, b) 0-1 tuple per
    vertex. It is exported as glTF `COLOR_0`, which three.js turns into
    `material.vertexColors = true` and MULTIPLIES into the material's
    baseColor. That is the cheap way to bake a smooth gradient -- a light
    falloff down a wall, grain along a plank -- into a surface: 4 bytes per
    vertex on a mesh whose vertices are already shared, against the ~24 bytes
    per duplicated vertex that splitting the same field into per-cell material
    buckets costs. A Part with no colors exports exactly as it always did.

    Colours are authored in the SAME sRGB space as `Material.color`; they are
    converted to linear on export, so a vertex colour of 0.5 halves the
    material's rendered value the way a 50% grey swatch would.
    """

    def __init__(self, verts=None, tris=None, smooth=False, colors=None,
                 uv=None):
        self.verts = list(verts or [])   # [(x, y, z), ...]
        self.tris = list(tris or [])     # [(i, j, k), ...]
        self.smooth = smooth             # average normals instead of flat-shading
        self.colors = list(colors) if colors else None
        # [(u, v), ...] one per vertex; values outside 0..1 tile the material's
        # `tex` (the sampler wraps REPEAT). Only meaningful on a Part whose
        # material carries a texture; parts in the same material group that
        # have none are filled with (0, 0).
        self.uv = list(uv) if uv else None
        if self.colors and len(self.colors) != len(self.verts):
            raise ValueError("Part.colors must be one per vertex "
                             f"({len(self.colors)} vs {len(self.verts)})")
        if self.uv and len(self.uv) != len(self.verts):
            raise ValueError("Part.uv must be one per vertex "
                             f"({len(self.uv)} vs {len(self.verts)})")

    def copy(self):
        return Part(list(self.verts), list(self.tris), self.smooth,
                    list(self.colors) if self.colors else None,
                    list(self.uv) if self.uv else None)


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

        self._parts.append((Part(out, part.tris, part.smooth,
                                 part.colors, part.uv), mat))
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
            verts, norms, idx, cols, uvs = _weld(parts, with_uv=True)
            if not idx:
                continue

            pos = b"".join(struct.pack("<3f", v[0] * FT_TO_M, v[1] * FT_TO_M,
                                       v[2] * FT_TO_M) for v in verts)
            nrm = b"".join(struct.pack("<3f", *n) for n in norms)
            # Indices are UNSIGNED_SHORT whenever the primitive fits in one,
            # which is every primitive this project has ever exported.  glTF
            # allows 5121/5123/5125 and three.js handles all three; writing
            # 5125 unconditionally spent 6 bytes a triangle on zeros.  Measured
            # on the Arcade Room's three cabinet GLBs: 644.0 -> 592.5 KB for
            # byte-identical geometry.  The bufferView byteOffsets are already
            # padded to 4, which satisfies the 2-byte element alignment a
            # SHORT accessor needs, and the guard keeps the old path for any
            # primitive that ever does exceed 65535 vertices.
            if len(verts) <= 65535:
                i_ct = 5123
                ind = b"".join(struct.pack("<H", i) for i in idx)
            else:
                i_ct = 5125
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
            accessors.append({"bufferView": push(ind, 34963),
                              "componentType": i_ct,
                              "count": len(idx), "type": "SCALAR"})

            attrs = {"POSITION": a_pos, "NORMAL": a_nrm}
            if cols is not None:
                # VEC4 / UNSIGNED_BYTE normalized: 4 bytes per vertex, which is
                # also exactly the 4-byte element alignment glTF requires (a
                # VEC3 ubyte accessor is 3 bytes and would be illegal here).
                cbuf = b"".join(
                    struct.pack("<4B", *[max(0, min(255, int(round(v * 255.0))))
                                         for v in _srgb_to_linear(c)] + [255])
                    for c in cols)
                attrs["COLOR_0"] = len(accessors)
                accessors.append({"bufferView": push(cbuf, 34962),
                                  "componentType": 5121, "normalized": True,
                                  "count": len(cols), "type": "VEC4"})
            if uvs is not None:
                ubuf = b"".join(struct.pack("<2f", u, v) for (u, v) in uvs)
                attrs["TEXCOORD_0"] = len(accessors)
                accessors.append({"bufferView": push(ubuf, 34962),
                                  "componentType": 5126,
                                  "count": len(uvs), "type": "VEC2"})
            primitives.append({"attributes": attrs, "indices": a_idx,
                               "material": mat_index, "mode": 4})

        # Images go in the same binary chunk. One sampler, REPEAT/REPEAT with
        # trilinear mips, is all any tile here wants; identical PNG bytes share
        # one image so a tile reused by several materials is stored once.
        images, textures, tex_of_mat, by_bytes = [], [], {}, {}
        for mi, m in enumerate(mats):
            if m.tex is None:
                continue
            raw = bytes(m.tex)
            if raw not in by_bytes:
                view = push(raw, None)
                buffer_views[view].pop("target", None)
                images.append({"bufferView": view, "mimeType": "image/png"})
                textures.append({"sampler": 0, "source": len(images) - 1})
                by_bytes[raw] = len(textures) - 1
            tex_of_mat[mi] = by_bytes[raw]

        gltf_materials = []
        uses_emissive_strength = False
        for mi, m in enumerate(mats):
            entry = {
                "name": m.name,
                "pbrMetallicRoughness": {
                    "baseColorFactor": _srgb_to_linear(m.color) + [m.opacity],
                    "metallicFactor": m.metallic,
                    "roughnessFactor": m.roughness,
                },
                "doubleSided": m.double_sided,
            }
            if mi in tex_of_mat:
                entry["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": tex_of_mat[mi]}
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
        if images:
            gltf["images"] = images
            gltf["textures"] = textures
            # 9987 LINEAR_MIPMAP_LINEAR / 9729 LINEAR / 10497 REPEAT
            gltf["samplers"] = [{"magFilter": 9729, "minFilter": 9987,
                                 "wrapS": 10497, "wrapT": 10497}]
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


def _weld(parts, with_uv=False):
    """Flat-shade (duplicate verts per face) or smooth-shade (average) each part.

    Returns (verts, norms, idx, cols); `cols` is None unless at least one part
    in the group carried vertex colours, in which case the parts that did not
    are filled with white so the attribute stays parallel to POSITION.

    `with_uv=True` appends `uvs`, which works the same way and is filled with
    (0, 0). It is opt-in ONLY so the arity stays what it was -- other agents'
    build scripts import this and unpack it positionally.
    """
    verts, norms, idx, cols, uvs = [], [], [], [], []
    any_color = any(p.colors for p in parts)
    any_uv = any(p.uv for p in parts)
    for part in parts:
        pc = part.colors
        pu = part.uv
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
            if any_color:
                cols.extend(pc if pc else [(1.0, 1.0, 1.0)] * len(part.verts))
            if any_uv:
                uvs.extend(pu if pu else [(0.0, 0.0)] * len(part.verts))
        else:
            for (a, b, c) in part.tris:
                va, vb, vc = part.verts[a], part.verts[b], part.verts[c]
                n = _face_normal(va, vb, vc)
                base = len(verts)
                verts.extend((va, vb, vc))
                norms.extend((n, n, n))
                idx.extend((base, base + 1, base + 2))
                if any_color:
                    cols.extend((pc[a], pc[b], pc[c]) if pc
                                else ((1.0, 1.0, 1.0),) * 3)
                if any_uv:
                    uvs.extend((pu[a], pu[b], pu[c]) if pu
                               else ((0.0, 0.0),) * 3)
    out = (verts, norms, idx, (cols if any_color else None))
    return out + ((uvs if any_uv else None),) if with_uv else out


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


def uv_quad(p0, p1, p2, p3, uv0=(0, 0), uv1=(1, 0), uv2=(1, 1), uv3=(0, 1)):
    """A textured quad: four 3-D points CCW plus their UVs.

    UVs above 1 tile the material's `tex` — a 20 ft floor carrying a 2 ft tile
    is `uv2=(10, 10)`, which costs four vertices instead of a hundred cells.
    """
    return Part([p0, p1, p2, p3], [(0, 1, 2), (0, 2, 3)],
                uv=[uv0, uv1, uv2, uv3])


def uv_floor(w, d, tile=2.0, y=0.0, offset=(0.0, 0.0)):
    """Horizontal plane w x d centred on the origin, facing +Y, UV'd for `tile`.

    `tile` is how many FEET one texture repeat covers, so the pattern keeps its
    real-world scale however big the plane is.
    """
    u0, v0 = offset[0] / tile, offset[1] / tile
    u1, v1 = u0 + w / tile, v0 + d / tile
    return uv_quad((-w / 2, y, d / 2), (w / 2, y, d / 2),
                   (w / 2, y, -d / 2), (-w / 2, y, -d / 2),
                   (u0, v1), (u1, v1), (u1, v0), (u0, v0))


# --------------------------------------------------------------------------
# PNG writer -- stdlib only, so a tile can be generated in the build script
# --------------------------------------------------------------------------

def png_gray(pixels):
    """8-bit greyscale PNG bytes from a list of rows of 0-255 ints."""
    return _png(pixels, 0, 1)


def png_rgb(pixels):
    """8-bit RGB PNG bytes from a list of rows of (r, g, b) tuples."""
    flat = [[c for px in row for c in px] for row in pixels]
    return _png(flat, 2, 3)


def _png(rows, color_type, nchan):
    import zlib
    h = len(rows)
    w = len(rows[0]) // nchan if color_type == 2 else len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)                      # filter type 0 (None)
        raw.extend(int(v) & 0xFF for v in row)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


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
