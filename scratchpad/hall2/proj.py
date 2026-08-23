"""Project room-17 wall faces into a v3.py pose, so a measurement can say WHICH
wall a pixel belongs to instead of guessing from the picture.

Replicates three.js's PerspectiveCamera + Matrix4.lookAt exactly: z = eye-target,
x = cross(up, z), y = cross(z, x); fov is VERTICAL degrees; aspect = w/h.
"""
import math
import numpy as np

from v3 import POSES
from walls3 import WALLS, Y_BOT, Y_CEIL

ANCHOR = (6.70, 6.55)
SLAB = 18.0


def basis(pose):
    p = np.array(pose["pos"], dtype=float)
    t = np.array(pose["target"], dtype=float)
    z = p - t
    z /= np.linalg.norm(z)
    up = np.array([0.0, 1.0, 0.0])
    x = np.cross(up, z)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return p, x, y, z


def project(pose, pts):
    """pts: (N,3) WORLD.  -> (N,2) pixel + (N,) depth (positive = in front)."""
    p, x, y, z = basis(pose)
    w, h = pose["size"]
    d = np.asarray(pts, dtype=float) - p
    cx, cy, cz = d @ x, d @ y, d @ z
    depth = -cz                                    # camera looks down -z
    tan = math.tan(math.radians(pose["fov"]) / 2.0)
    ndc_x = (cx / np.maximum(depth, 1e-6)) / (tan * (w / h))
    ndc_y = (cy / np.maximum(depth, 1e-6)) / tan
    return np.stack([(ndc_x + 1) * 0.5 * w, (1 - ndc_y) * 0.5 * h], 1), depth


def _face_points(key, shrink, ny, na):
    for wl in WALLS:
        if wl[0] == key:
            break
    else:
        raise KeyError(key)
    _, axis, plane, n, a0, a1, _ = wl
    aa = np.linspace(a0 + shrink, a1 - shrink, na)
    yy = np.linspace(Y_BOT + shrink + 0.14, Y_CEIL - shrink, ny)
    A, Y = np.meshgrid(aa, yy)
    A, Y = A.ravel(), Y.ravel()
    P = np.empty((A.size, 3))
    P[:, 1] = Y + SLAB
    if axis == "x":
        P[:, 0] = plane + ANCHOR[0]
        P[:, 2] = A + ANCHOR[1]
    else:
        P[:, 2] = plane + ANCHOR[1]
        P[:, 0] = A + ANCHOR[0]
    return P


def wall_ids(pose_name, keys=None, shrink=0.14, ny=260, na=620):
    """Z-BUFFERED wall-id map: -1 where no face lands, else the index into
    `keys` of the NEAREST wall face at that pixel.

    Without the depth test the alcove's three walls project straight through the
    long west wall that hides them, and a "which wall is this pixel" question
    answers with whichever wall was tested last.  That contaminated the first
    fit: 34.6k of p_runner's supposed alcove-north pixels were really the west
    wall seen through it.
    """
    keys = list(keys or [w[0] for w in WALLS])
    pose = POSES[pose_name]
    w, h = pose["size"]
    ids = np.full((h, w), -1, np.int16)
    zbuf = np.full((h, w), 1e9)
    for idx, k in enumerate(keys):
        P = _face_points(k, shrink, ny, na)
        px, depth = project(pose, P)
        ok = (depth > 0.05) & (px[:, 0] >= 0) & (px[:, 0] < w) \
            & (px[:, 1] >= 0) & (px[:, 1] < h)
        xi, yi, dp = px[ok, 0].astype(int), px[ok, 1].astype(int), depth[ok]
        order = np.argsort(-dp)                 # far first, near overwrites
        xi, yi, dp = xi[order], yi[order], dp[order]
        near = dp < zbuf[yi, xi]
        zbuf[yi[near], xi[near]] = dp[near]
        ids[yi[near], xi[near]] = idx
    return keys, ids


def wall_mask(pose_name, key, shrink=0.14, ny=90, na=220):
    """Boolean mask of the pixels one wall's face plane projects onto.

    Shrunk in from every edge so a corner or a ceiling seam never leaks into a
    neighbouring surface's sample.  It does NOT know about occlusion -- pair it
    with a difference mask (two renders, one changed skin) when that matters.
    """
    pose = POSES[pose_name]
    w, h = pose["size"]
    for wl in WALLS:
        if wl[0] == key:
            break
    else:
        raise KeyError(key)
    _, axis, plane, n, a0, a1, _ = wl
    aa = np.linspace(a0 + shrink, a1 - shrink, na)
    yy = np.linspace(Y_BOT + shrink + 0.14, Y_CEIL - shrink, ny)
    A, Y = np.meshgrid(aa, yy)
    A, Y = A.ravel(), Y.ravel()
    P = np.empty((A.size, 3))
    P[:, 1] = Y + SLAB
    if axis == "x":
        P[:, 0] = plane + ANCHOR[0]
        P[:, 2] = A + ANCHOR[1]
    else:
        P[:, 2] = plane + ANCHOR[1]
        P[:, 0] = A + ANCHOR[0]
    px, depth = project(pose, P)
    ok = (depth > 0.05) & (px[:, 0] >= 0) & (px[:, 0] < w - 1) \
        & (px[:, 1] >= 0) & (px[:, 1] < h - 1)
    m = np.zeros((h, w), bool)
    xi = px[ok, 0].astype(int)
    yi = px[ok, 1].astype(int)
    for dx in (0, 1):
        for dy in (0, 1):
            m[np.clip(yi + dy, 0, h - 1), np.clip(xi + dx, 0, w - 1)] = True
    return m
