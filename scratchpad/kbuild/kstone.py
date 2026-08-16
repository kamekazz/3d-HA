"""ROUND 4 -- the quartz / marble program, as textures instead of raster cells.

One STONE SHEET per piece: a single greyscale image big enough to cover every
stone surface on that piece, with each surface mapped to its own window of it.
That way a cabinet run carries one ~30 KB image instead of ~40 000 quads, no two
surfaces repeat, and the finest mark the stone can hold is one texel (0.009 ft
on the island) instead of one raster cell (0.034 ft).

The response constants below turn a wanted RENDER value into an albedo.  They
are two-point fits measured on this room's own renders, not a formula:

  horizontal tops   albedo 74 -> 110, 192 -> 215      (slope 0.89, bias  44.1)
  vertical splash   albedo 222 -> 173 at the same slope (bias -24.6)

A vertical face in the cabinets' shade collects far less than a top in the sun,
which is why the backsplash needs a HIGHER albedo than the counter to sit 35
bytes below it -- the gap photo F genuinely has (backsplash 173, island 205.8),
and which the round-3 critic confirmed must not be closed.
"""
import numpy as np

import kfield
from ktex import TexMaterial, png_gray, tex_plane

TOP_SLOPE, TOP_BIAS = 0.89, 44.1
SPL_SLOPE, SPL_BIAS = 0.89, -24.6

# Global trims, so the whole stone program moves in one place after a probe.
TOP_GROUND = 206.0        # render value of clean white ground on a top
SPL_GROUND = 167.0        # ... and on a backsplash (lands ~178 after the net)

_LAYERS = ((1.0, 0.032, 1.00),      # (frequency, width in FEET, amplitude)
           (2.05, 0.021, 0.86),
           (4.20, 0.013, 0.70),
           (8.60, 0.008, 0.50))


class Sheet:
    """A stone image plus the TexMaterial that carries it.

    `plane()` takes room-local extents and the sheet-local feet the surface
    should be cut from, so two counters on the same piece never show the same
    veining.
    """

    def __init__(self, w_ft, h_ft, ppf, seed, ground=TOP_GROUND, vein=62.0,
                 scale=2.1, cloud=5.0, grain=3.2, slope=TOP_SLOPE,
                 bias=TOP_BIAS, roughness=0.46, emissive="#101010",
                 tint="#ffffff", name="stone", levels=64, mip=False):
        self.w, self.h = float(w_ft), float(h_ft)
        v = kfield.quartz(self.w, self.h, ppf, seed, ground=ground,
                          vein=vein, scale=scale, cloud=cloud, grain=grain,
                          layers=_LAYERS)
        self.render_stats = (float(v.mean()), float(v.std()))
        a = np.clip((v - bias) / slope, 0, 255)
        self.png = png_gray(a, levels=levels)
        self.mat = TexMaterial(name, self.png, tint=tint, roughness=roughness,
                               emissive=emissive, mip=mip)

    def uvrect(self, su0, sw0, su1, sw1):
        return (su0 / self.w, sw0 / self.h, su1 / self.w, sw1 / self.h)

    def plane(self, m, face, at, u0, u1, w0, w1, su=0.0, sw=0.0):
        """Map [u0,u1]x[w0,w1] onto the sheet starting at (su, sw) feet.

        Windows are laid out by hand per piece so no two surfaces on the same
        run are cut from the same part of the slab -- the giveaway that a
        surface is tiled rather than veined.
        """
        r = self.uvrect(su, sw, su + (u1 - u0), sw + (w1 - w0))
        tex_plane(m, self.mat, face, at, u0, u1, w0, w1, uvrect=r)


def top_sheet(w_ft, h_ft, ppf, seed, **kw):
    return Sheet(w_ft, h_ft, ppf, seed, **kw)


def splash_sheet(w_ft, h_ft, ppf, seed, **kw):
    """Backsplash marble: quieter than a top -- a slab cut from the calm part of
    the same stone, and sitting in the cabinets' shade."""
    kw.setdefault("ground", SPL_GROUND)
    kw.setdefault("vein", 30.0)
    kw.setdefault("scale", 1.7)
    kw.setdefault("cloud", 7.0)
    kw.setdefault("slope", SPL_SLOPE)
    kw.setdefault("bias", SPL_BIAS)
    kw.setdefault("roughness", 0.52)
    kw.setdefault("emissive", "#2a2a2a")
    kw.setdefault("name", "splash")
    return Sheet(w_ft, h_ft, ppf, seed, **kw)
