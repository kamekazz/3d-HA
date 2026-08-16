"""ROUND 4 -- textured GLB export.

Round 3 drew every tone field by RASTERISING it into flat quads (kraster.py).
That fixed the tone statistics and broke two other things at once:

  * SPATIAL.  A quad per cell is expensive, so the cell has to be coarse
    (0.034-0.062 ft), so the finest mark the surface can carry is ~0.4 in.  The
    photo's quartz is a net of hairline wisps an order of magnitude finer, and
    the only way to hold the same variance on a coarse grid is with a few FAT
    marks -- which is exactly the "cracked, stained slab" the critic saw.
  * PAYLOAD.  Cells cost ~170 bytes each (flat shading duplicates every vertex),
    so the room hit 5.88 MB against a 1.5 MB budget.

A texture fixes both: 2 triangles carry detail as fine as the image, and a
compressed greyscale PNG of a low-contrast field is a few tens of KB.

`roomkit.glb` has no texture support and is shared with every other room agent,
so nothing there is touched -- `TexModel` subclasses `Model` and overrides
`add`/`save` to carry TEXCOORD_0 and embed the PNGs in the GLB's own buffer
(no external fetch, so the artifact CSP and the app's static root are unaffected).

Images are 8-bit GREYSCALE (PNG colour type 0) or greyscale+alpha (type 4): the
stone, the planks and the rug are all within a couple of bytes of neutral, so a
colour image would triple the payload to encode noise in channels that carry no
information.  A slight tint goes in `baseColorFactor`, which multiplies.
"""
import io
import json
import math
import struct

import numpy as np
from PIL import Image

from roomkit.glb import (Model, Material, Part, quad, _rgb, _srgb_to_linear,
                         _weld, FT_TO_M)


# ------------------------------------------------------------------ images
def png_gray(a, levels=0):
    """8-bit greyscale PNG bytes from a float array in 0..255.

    `levels` quantises before encoding.  A low-contrast noisy field costs most
    of its bytes in the bottom bits, and 48-64 levels over a 30-byte tone range
    is finer than the render can show -- it typically halves the file.
    """
    a = np.clip(np.asarray(a, dtype=np.float64), 0, 255)
    if levels:
        step = 255.0 / (levels - 1)
        a = np.round(a / step) * step
    im = Image.fromarray(np.round(a).astype(np.uint8), mode="L")
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def png_gray_alpha(l, a, levels=0):
    """Greyscale + alpha PNG (type 4) -- for overlays that darken what is under."""
    l = np.clip(np.asarray(l, dtype=np.float64), 0, 255)
    a = np.clip(np.asarray(a, dtype=np.float64), 0, 255)
    if levels:
        step = 255.0 / (levels - 1)
        a = np.round(a / step) * step
    arr = np.dstack([np.round(l).astype(np.uint8), np.round(a).astype(np.uint8)])
    im = Image.fromarray(arr, mode="LA")
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ------------------------------------------------------------------ material
class TexMaterial(Material):
    """A Material whose baseColour comes from an embedded PNG.

    `tint` multiplies the texture (glTF baseColorFactor), so a neutral greyscale
    image can carry a warm or cool surface without a colour image.
    """

    def __init__(self, name, png, tint="#ffffff", roughness=0.5, metallic=0.0,
                 emissive=None, emissive_strength=1.0, opacity=1.0,
                 double_sided=True, blend=False, mip=True):
        super().__init__(name, tint, roughness, metallic, emissive,
                         emissive_strength, opacity, double_sided)
        self.png = png
        self.blend = bool(blend)
        # `mip=False` asks for a plain LINEAR minFilter, so three.js skips
        # mipmaps and always samples level 0.  GLTFLoader leaves anisotropy at
        # 1, so a surface seen at a slant picks a mip level from its WORST axis
        # and the fine net is averaged away -- which is how round 4's first
        # textured island came back measuring d1 0.86 against the photo's 2.62.
        # These fields are low-contrast noise, so the aliasing that buys back is
        # far less visible than the blur it removes.
        self.mip = bool(mip)

    def key(self):
        return super().key() + (id(self.png), self.blend, self.mip)


# ------------------------------------------------------------------ model
class TexModel(Model):
    """Model + per-vertex UVs.  Untextured parts behave exactly as before."""

    def __init__(self):
        super().__init__()
        self._uv = []          # parallel to self._parts; None for untextured

    def add(self, part, mat, at=(0, 0, 0), rot_y=0.0, rot_x=0.0, rot_z=0.0,
            scale=(1, 1, 1), uv=None):
        n = len(self._parts)
        super().add(part, mat, at, rot_y, rot_x, rot_z, scale)
        while len(self._uv) < n:
            self._uv.append(None)
        self._uv.append(list(uv) if uv else None)
        return self

    # ---- export ---------------------------------------------------------
    def save(self, path):
        while len(self._uv) < len(self._parts):
            self._uv.append(None)

        mats, groups = [], []
        seen = {}
        for (part, mat), uv in zip(self._parts, self._uv):
            k = mat.key()
            if k not in seen:
                seen[k] = len(mats)
                mats.append(mat)
                groups.append([])
            groups[seen[k]].append((part, uv))

        bin_chunks, offset = [], 0
        accessors, buffer_views, primitives = [], [], []
        images, textures, samplers = [], [], []
        png_view = {}

        def push(data, target=None):
            nonlocal offset
            pad = (-len(data)) % 4
            bin_chunks.append(data + b"\x00" * pad)
            view = len(buffer_views)
            e = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
            if target:
                e["target"] = target
            buffer_views.append(e)
            offset += len(data) + pad
            return view

        for mat_index, entries in enumerate(groups):
            parts = [p for p, _ in entries]
            textured = isinstance(mats[mat_index], TexMaterial)
            verts, norms, idx = _weld(parts)
            if not idx:
                continue
            uvs = _weld_uv(entries) if textured else None
            if textured and len(uvs) != len(verts):
                raise ValueError(f"material {mats[mat_index].name}: "
                                 "every part on a textured material needs uv=")

            pos = b"".join(struct.pack("<3f", v[0] * FT_TO_M, v[1] * FT_TO_M,
                                       v[2] * FT_TO_M) for v in verts)
            nrm = b"".join(struct.pack("<3f", *n) for n in norms)
            ind = b"".join(struct.pack("<I", i) for i in idx)

            lo = [min(v[i] for v in verts) * FT_TO_M for i in range(3)]
            hi = [max(v[i] for v in verts) * FT_TO_M for i in range(3)]

            attrs = {}
            attrs["POSITION"] = len(accessors)
            accessors.append({"bufferView": push(pos, 34962), "componentType": 5126,
                              "count": len(verts), "type": "VEC3",
                              "min": lo, "max": hi})
            attrs["NORMAL"] = len(accessors)
            accessors.append({"bufferView": push(nrm, 34962), "componentType": 5126,
                              "count": len(norms), "type": "VEC3"})
            if textured:
                tc = b"".join(struct.pack("<2f", u, v) for (u, v) in uvs)
                attrs["TEXCOORD_0"] = len(accessors)
                accessors.append({"bufferView": push(tc, 34962),
                                  "componentType": 5126, "count": len(uvs),
                                  "type": "VEC2"})
            a_idx = len(accessors)
            accessors.append({"bufferView": push(ind, 34963), "componentType": 5125,
                              "count": len(idx), "type": "SCALAR"})
            primitives.append({"attributes": attrs, "indices": a_idx,
                               "material": mat_index, "mode": 4})

        gltf_materials = []
        uses_emissive_strength = False
        for m in mats:
            pbr = {
                "baseColorFactor": _srgb_to_linear(m.color) + [m.opacity],
                "metallicFactor": m.metallic,
                "roughnessFactor": m.roughness,
            }
            entry = {"name": m.name, "pbrMetallicRoughness": pbr,
                     "doubleSided": m.double_sided}
            if isinstance(m, TexMaterial):
                tkey = (id(m.png), m.mip)
                if tkey not in png_view:
                    v = push(m.png)
                    images.append({"bufferView": v, "mimeType": "image/png"})
                    samplers.append({"wrapS": 10497, "wrapT": 10497,
                                     "magFilter": 9729,
                                     "minFilter": 9987 if m.mip else 9729})
                    textures.append({"source": len(images) - 1,
                                     "sampler": len(samplers) - 1})
                    png_view[tkey] = len(textures) - 1
                pbr["baseColorTexture"] = {"index": png_view[tkey]}
                if m.blend:
                    entry["alphaMode"] = "BLEND"
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
            "asset": {"version": "2.0", "generator": "roomkit+ktex"},
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
            gltf["samplers"] = samplers
        if uses_emissive_strength:
            gltf["extensionsUsed"] = ["KHR_materials_emissive_strength"]

        js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        js += b" " * ((-len(js)) % 4)
        with open(path, "wb") as fh:
            fh.write(struct.pack("<III", 0x46546C67, 2,
                                 12 + 8 + len(js) + 8 + len(blob)))
            fh.write(struct.pack("<II", len(js), 0x4E4F534A))
            fh.write(js)
            fh.write(struct.pack("<II", len(blob), 0x004E4942))
            fh.write(blob)
        return path


def _weld_uv(entries):
    """Mirror glb._weld's vertex duplication so UVs stay in step with POSITION."""
    out = []
    for part, uv in entries:
        if part.smooth:
            out.extend(uv)
        else:
            for (a, b, c) in part.tris:
                out.extend((uv[a], uv[b], uv[c]))
    return out


# ------------------------------------------------------------------ helpers
_FACE = {
    "+y": lambda u, w, at: (u, at, w),
    "-y": lambda u, w, at: (u, at, w),
    "-x": lambda u, w, at: (at, w, u),
    "+x": lambda u, w, at: (at, w, u),
    "-z": lambda u, w, at: (u, w, at),
    "+z": lambda u, w, at: (u, w, at),
}
_NRM = {"+y": (0, 1, 0), "-y": (0, -1, 0), "-x": (-1, 0, 0), "+x": (1, 0, 0),
        "-z": (0, 0, -1), "+z": (0, 0, 1)}


def tex_plane(m, mat, face, at, u0, u1, w0, w1, rep=(1.0, 1.0), flip_v=False,
              uvrect=None):
    """One textured quad on an axis plane, wound so its normal matches `face`.

    `rep` is how many times the image tiles across (u, w); `uvrect`
    (a0, b0, a1, b1) instead maps the quad onto a WINDOW of the image, which is
    how several surfaces on one piece share a single stone sheet.  A quad per
    surface instead of a quad per cell is the whole point of round 4, so this is
    the only geometry a tone field costs now.
    """
    f, n = _FACE[face], _NRM[face]
    p = [f(u0, w0, at), f(u1, w0, at), f(u1, w1, at), f(u0, w1, at)]
    if uvrect is not None:
        a0, b0, a1, b1 = uvrect
        uv = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
    else:
        uv = [(0.0, 0.0), (rep[0], 0.0), (rep[0], rep[1]), (0.0, rep[1])]
    if flip_v:
        vmax = max(b for _, b in uv)
        vmin = min(b for _, b in uv)
        uv = [(a, vmax + vmin - b) for (a, b) in uv]
    ux, uy, uz = (p[1][i] - p[0][i] for i in range(3))
    vx, vy, vz = (p[2][i] - p[0][i] for i in range(3))
    cr = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    if cr[0] * n[0] + cr[1] * n[1] + cr[2] * n[2] < 0:
        p = [p[0], p[3], p[2], p[1]]
        uv = [uv[0], uv[3], uv[2], uv[1]]
    m.add(quad(*p), mat, uv=uv)


def tex_quad(m, mat, pts, uvs):
    """An arbitrary planar quad with explicit UVs (the bay trapezoid needs one)."""
    m.add(quad(*pts), mat, uv=list(uvs))


def tex_box(m, mat, x0, x1, y0, y1, z0, z1, ppf=1.0):
    """A box whose six faces all sample the texture at `ppf` repeats per foot."""
    from roomkit.glb import box as _box
    w, h, d = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    if min(w, h, d) < 1e-6:
        return
    p = _box(w, h, d)
    uv = []
    for (vx, vy, vz) in p.verts:
        uv.append(((vx + vz) * ppf, (vy + vz * 0.001) * ppf))
    m.add(p, mat, at=((x0 + x1) / 2.0, min(y0, y1), (z0 + z1) / 2.0), uv=uv)
