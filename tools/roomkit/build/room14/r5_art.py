"""Wall art — round 5.  Same painting, 1/8th of the payload.

Round 2 built the poppy canvas as ~8000 hand-scattered paint-stroke quads in 37
materials: 47,784 vertices, 1.43 MB.  That is ONE PIECE eating most of the
1.5 MB the whole room is allowed, and the room was at 3.41 MB because of it and
the rug.  It is also 24k triangles for a flat rectangle seen from 15 ft.

So the canvas is now SAMPLED FROM THE PHOTOGRAPH: the four corners of the real
canvas in `Master bedroom.jpg` are un-keystoned into a u,v grid, the pixels are
quantised to a small palette, and equal-tone cells merge into runs (r5_raster).
That is strictly more faithful than round 2's procedural scatter -- it is the
actual painting -- and it costs about 150 KB.

SIZE re-solved for the king bed.  The photo fact round 2 measured still stands:
canvas / headboard = 0.83 in the image, and the gap from the canvas foot to the
headboard cap is 0.19 of the headboard's width.  What changed is the headboard:
5.30 ft (queen) -> 7.10 ft (king, the plan's own bed icon), so the canvas goes
4.44 -> 5.95 ft wide and the gap 1.00 -> 1.34 ft.

    python r5_art.py out.glb [--gain 0.78]
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, box       # noqa: E402
from r5_raster import Field, raster               # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "wall_art.glb"
GAIN = 0.78
for i, a in enumerate(sys.argv):
    if a == "--gain":
        GAIN = float(sys.argv[i + 1])

PHOTO = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg\Master bedroom.jpg"
# the canvas's four corners in the photo, read off a 3x crop: it is keystoned,
# so the sampler un-warps it rather than using a bounding box
TL, TR, BR, BL = (636.7, 363.3), (863.3, 302.7), (853.3, 543.3), (631.7, 548.3)

W, H = 5.95, 5.45          # feet
# The cells are DELIBERATELY not square.  Runs merge vertically (see the
# raster call), so extra rows are nearly free while extra columns cost one quad
# each; a fine vertical / coarse horizontal grid buys the stem structure that
# makes this painting readable at a third of the payload of a square grid.
CELL_X, CELL_Y = 0.086, 0.050
NU, NV = int(W / CELL_X), int(H / CELL_Y)
NPAL = 10

img = np.asarray(Image.open(PHOTO).convert("RGB")).astype(np.float32)


def at(u, v):
    """u,v in 0..1 across the canvas -> photo pixel (bilinear on the quad)."""
    x = (TL[0] * (1 - u) + TR[0] * u) * (1 - v) + (BL[0] * (1 - u) + BR[0] * u) * v
    y = (TL[1] * (1 - u) + TR[1] * u) * (1 - v) + (BL[1] * (1 - u) + BR[1] * u) * v
    return img[int(round(y)), int(round(x))]


# AREA-AVERAGE each cell.  Point-sampling a 66 x 60 grid out of a painting whose
# every mark is 2-3 px wide aliases catastrophically: the first attempt read as
# scattered confetti on a pale ground instead of a dense poppy field.
SUB = 5
INSET = 0.008                     # keep the sampler off the canvas's own edge
grid = np.zeros((NV, NU, 3), dtype=np.float32)
for j in range(NV):
    for i in range(NU):
        acc = np.zeros(3, dtype=np.float32)
        for sj in range(SUB):
            for si in range(SUB):
                u = INSET + (1 - 2 * INSET) * (i + (si + 0.5) / SUB) / NU
                v = INSET + (1 - 2 * INSET) * (j + (sj + 0.5) / SUB) / NV
                acc += at(u, v)
        grid[j, i] = acc / (SUB * SUB)

# ---- palette: k-means on the sampled pixels -------------------------------
flat = grid.reshape(-1, 3)
rng = np.random.default_rng(7)
cent = flat[rng.choice(len(flat), NPAL, replace=False)].copy()
for _ in range(24):
    d = ((flat[:, None, :] - cent[None, :, :]) ** 2).sum(2)
    lab = d.argmin(1)
    for k in range(NPAL):
        if (lab == k).any():
            cent[k] = flat[lab == k].mean(0)
order = np.argsort(cent @ np.array([0.2126, 0.7152, 0.0722]))
cent = cent[order]
remap = np.zeros(NPAL, dtype=int)
remap[order] = np.arange(NPAL)
idx = remap[lab].reshape(NV, NU)

# ---- tone.  SOLVED, not guessed.  Using the photo's pixels straight as albedo
# gave a render of mean 193 / sd 13 against the photo's 131 / 37 -- far too pale
# and, worse, four times too FLAT, because the exposure+ACES curve compresses
# hard near white and an object material collects ~1.7x a room wall's light
# here.  So each palette entry is solved backwards:
#
#   target byte  = wall_render * (photo_pixel / wall_photo)      (keep the ratio)
#   radiance     = tone.radiance_for_byte(target)
#   albedo       = radiance / LIT
#
# LIT is measured off the previous render: a palette whose mean linear albedo
# was `_A0` came out at byte `_B0`.
from tone import radiance_for_byte, lin_to_srgb, srgb_to_lin      # noqa: E402

WALL_PHOTO, WALL_REND = 176.2, 221.3
_A0, _B0 = 0.1454, 154.6                  # measured off render t8
LIT = radiance_for_byte(_B0) / _A0
LUMW = np.array([0.2126, 0.7152, 0.0722])


def solve(rgb):
    lum = float(rgb @ LUMW)
    tgt = min(252.0, max(24.0, WALL_REND * (lum / WALL_PHOTO)))
    want = radiance_for_byte(tgt) / LIT               # linear albedo we need
    have = srgb_to_lin(max(lum, 1.0) / 255.0)
    k = want / max(have, 1e-6)
    out = []
    for c in rgb:
        out.append(min(1.0, max(0.0, srgb_to_lin(float(c) / 255.0) * k)))
    return tuple(out)


MATS = [Material("art%02d" % k, tuple(lin_to_srgb(v) for v in solve(cent[k])),
                 roughness=0.92) for k in range(NPAL)]
pal = np.array([[255 * lin_to_srgb(v) for v in solve(cent[k])]
                for k in range(NPAL)])

m = Model()
fld = Field(MATS)
# The rasteriser merges equal-tone cells into runs along its FIRST axis, so the
# first axis is the canvas's VERTICAL one: this painting is a field of upright
# stems, and its tone is far more coherent up a stem than across one.  Merging
# vertically instead of horizontally cut the mesh by a third at the same cell
# size, and the streaks it does leave run with the brushwork instead of across
# it.  NB `a` runs UP the canvas while idx row 0 is the TOP of the photo, so
# the row index is flipped -- without this the painting hangs upside down,
# which is exactly what the first r5 render showed.
raster(fld,
       lambda a, b: (b, a, 0.062),
       lambda a, b: (0.0, 0.0, 1.0),
       0.0, H, -W / 2, W / 2, NV, NU,
       lambda a, b: int(idx[NV - 1 - min(NV - 1, max(0, int(a / H * NV))),
                            min(NU - 1, max(0, int((b + W / 2) / W * NU)))]))
verts = fld.emit(m)
# Stretcher: a shallow box BEHIND the paint.  Its front face must not be
# coplanar with the paint plane -- at 0.055 it was, and the two z-fought so
# roughly half the canvas rendered as mid-grey stretcher, which is why the
# painting metered 191 flat when its albedo was 0.04..0.22 linear.
m.add(box(W, H, 0.055), Material("art_side", "#8e8a86", roughness=0.9),
      at=(0, 0, 0.0275))

if os.environ.get("R5_ART_DEBUG"):
    from PIL import Image as _I
    _dbg = pal[idx].astype(np.uint8)
    _I.fromarray(_dbg).resize((NU * 6, NV * 6), _I.NEAREST).save(
        os.environ["R5_ART_DEBUG"])

m.save(OUT)
lo, hi = m.bounds()
lum = (pal @ np.array([0.2126, 0.7152, 0.0722])).mean()
print("canvas %.2f x %.2f ft, %dx%d cells, %d verts, palette lum %.0f, %.1f KB"
      % (hi[0] - lo[0], hi[1] - lo[1], NU, NV, verts, lum,
         os.path.getsize(OUT) / 1024))
