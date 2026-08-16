"""Invert the app's render response so a surface can be aimed at a display byte.

Chain: linear radiance L -> *exposure(1.15) -> ACES filmic -> sRGB -> byte.
For near-neutral colours the ACES 3x3 matrices are close enough to identity that
the scalar RRT fit is accurate to a byte or two (checked against a measured
calibration strip: predicted 230 vs measured 233 on a white floor patch).

ILLUM is the measured "radiance per unit linear albedo" of each interior surface
orientation under `roomkit.shot --day` (sun el 42, az 155), derived from bare
#f2ede3 walls in the empty room:
    north 223 -> 1.471   west 187 -> 0.688   east 141 -> 0.354
    south 122 -> 0.274   floor 222 -> 1.621  ceiling (down) ~0.05
"""
import math

EXPOSURE = 1.15

# Measured, not assumed: a GLB whose baseColor is black and whose emissiveFactor
# is linear(0x808080)=0.2159 renders at byte 151/153 on two different walls,
# i.e. scene radiance 0.359 -- so the loader/renderer applies emissive at 1.664x,
# while the albedo term matches ILLUM below to within a byte (white patch 131 vs
# 130 predicted, mid-grey 42 vs 42, 92 vs 88).  Solve with the scale in hand.
EMISSIVE_SCALE = 1.664

ILLUM = {
    "floor": 1.621,
    "north": 1.471,     # inner face of the north wall (normal +Z)
    "west": 0.688,      # inner face of the west wall  (normal +X)
    "east": 0.354,      # inner face of the east wall  (normal -X)
    "south": 0.274,     # inner face of the south wall (normal -Z)
    "ceiling": 0.055,   # a downward-facing plane collects almost nothing
    "up": 1.621,
}


def srgb_to_linear(u):
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def linear_to_srgb(u):
    u = max(0.0, u)
    return u * 12.92 if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055


def hex_to_lin(h):
    h = h.lstrip("#")
    return [srgb_to_linear(int(h[2 * i:2 * i + 2], 16) / 255.0) for i in range(3)]


def lin_to_hex(v):
    out = "#"
    for c in v:
        out += "%02x" % max(0, min(255, round(linear_to_srgb(c) * 255)))
    return out


def _rrt(v):
    a = v * (v + 0.0245786) - 0.000090537
    b = v * (0.983729 * v + 0.4329510) + 0.238081
    return a / b


def byte_of(L):
    """Display byte for a scene radiance L."""
    return max(0, min(255, round(linear_to_srgb(min(1.0, _rrt(L * EXPOSURE))) * 255)))


def radiance_for(byte):
    """Scene radiance that renders as `byte` (bisection on the forward model)."""
    lo, hi = 0.0, 40.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if byte_of(mid) < byte:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def emissive_for(target_byte, albedo_hex, surface):
    """Emissive (hex, strength) that lands `albedo_hex` on `surface` at target_byte.

    The emissive keeps the albedo's hue: the green channel hits the target and
    the others are scaled by their albedo ratio.
    """
    I = ILLUM[surface]
    A = hex_to_lin(albedo_hex)
    Lg = radiance_for(target_byte)
    ratio = [A[i] / A[1] if A[1] > 1e-6 else 1.0 for i in range(3)]
    E = [max(0.0, (Lg * ratio[i] - A[i] * I) / EMISSIVE_SCALE) for i in range(3)]
    strength = 1.0
    if max(E) > 1.0:
        strength = max(E) / 0.98
        E = [c / strength for c in E]
    if max(E) < 0.002:
        return None, 1.0
    return lin_to_hex(E), strength


def predict(albedo_hex, surface, emissive_hex=None, strength=1.0):
    I = ILLUM[surface]
    A = hex_to_lin(albedo_hex)
    E = hex_to_lin(emissive_hex) if emissive_hex else [0, 0, 0]
    return tuple(byte_of(A[i] * I + E[i] * strength * EMISSIVE_SCALE)
                 for i in range(3))
