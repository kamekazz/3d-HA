"""Mask-probe for `Hall2F Knee Wall`.

Renders the piece three times with its parts painted pure R / G / B (everything
else neutral), builds a per-part pixel mask from which channel dominates, and
then meters the REAL render through those masks.  No hand-drawn sample box, so
nothing can swallow the plant stand, the runner or the stair rail -- which is
how two earlier reports in this repo went wrong.

The renderer desaturates hard (ambient + IBL is white), so a "pure red" face
comes back near (200, 60, 50).  Classifying by absolute distance to the key
fails; classifying by which channel leads, by a margin, does not.

    python kwprobe.py mask            # 3 passes x 3 poses, writes masks
    python kwprobe.py meter <tag>     # meter shots/<tag><pose>.png
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kneewall as K                                            # noqa: E402
from roomkit.glb import Material                                # noqa: E402
from roomkit.place import place                                 # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
POSES = ("p_runner", "p_stairs", "p_down")

NEUT = "#7a7a7a"
RGB = ("#ff0000", "#00ff00", "#0000ff")
# pass -> which part gets R, G, B
PASSES = [("hall", "well", "cap"), ("capnose", "band", "base"), ("end", None, None)]
PARTS = [p for grp in PASSES for p in grp if p]


def paint(which):
    """Repaint kneewall's module globals for one probe pass."""
    r, g, b = RGB
    def M(name, col, rough):
        return Material(name, col, roughness=rough)
    col = {p: NEUT for p in PARTS}
    for c, p in zip(RGB, which):
        if p:
            col[p] = c
    K.WM = M("kwpHall", col["hall"], 0.62)
    K.WG = M("kwpCap", col["cap"], 0.46)
    K.CORE = M("kwpCore", NEUT, 0.62)
    K.CAPF = M("kwpNose", col["capnose"], 0.46)
    K.CAPW = M("kwpNose", col["capnose"], 0.46)
    K.BANDF = M("kwpBand", col["band"], 0.56)
    K.BANDW = M("kwpBand", col["band"], 0.56)
    K.BBM = M("kwpBase", col["base"], 0.54)
    K.BBT = M("kwpBase", col["base"], 0.54)
    K.ENDM = M("kwpEnd", col["end"], 0.60)
    K.UND = M("kwpUnd", NEUT, 0.74)
    wellmat = M("kwpWell", col["well"], 0.62)
    orig = getattr(K, "_grid_orig", None) or K._grid
    K._grid_orig = orig
    state = {"n": 0}

    def grid(m, mat, nu, nv, pt, tone, flip=False):
        state["n"] += 1
        if state["n"] == 2:                      # the second grid is the well
            mat = wellmat
        return orig(m, mat, nu, nv, pt, lambda u, v: 1.0, flip=flip)
    K._grid = grid


def build_and_place():
    m = K.build()
    path = os.path.join(HERE, "glb", "hall2f_knee_wall.glb")
    m.save(path)
    lo, hi = m.bounds()
    place(K.NAME, path, K.ROOM,
          pos=((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0),
          rot_y_deg=0.0, scale=1.0)


def shoot(tag):
    for p in POSES:
        subprocess.run([sys.executable, "v3.py", p], cwd=HERE,
                       env={**os.environ, "TAG": tag}, capture_output=True)


def masks():
    acc = {p: {} for p in POSES}
    for i, which in enumerate(PASSES):
        paint(which)
        build_and_place()
        shoot(f"kwm{i}_")
        for pose in POSES:
            im = np.asarray(Image.open(os.path.join(SHOTS, f"kwm{i}_{pose}.png"))
                            .convert("RGB")).astype(float)
            s = im.sum(axis=2) + 1e-6
            n = im / s[:, :, None]
            srt = np.sort(n, axis=2)
            lead = srt[:, :, 2] - srt[:, :, 1]          # margin over 2nd place
            top = np.argmax(n, axis=2)
            for ch, part in enumerate(which):
                if part:
                    acc[pose][part] = (top == ch) & (lead > 0.10) & (s > 60)
    for pose in POSES:
        for part, m in acc[pose].items():
            print(f"{pose:9s} {part:8s} {int(m.sum()):6d} px")
        np.savez(os.path.join(SHOTS, f"kwmask_{pose}.npz"), **acc[pose])
    # restore the real piece
    K._grid = K._grid_orig
    import importlib
    importlib.reload(K)
    build_and_place()


# a clean patch of the room's OWN grey wall in each pose, to normalise against
# (the photographs are metered the same way -- see the report)
REF = {"p_runner": (630, 450, 700, 600),
       "p_stairs": (790, 430, 880, 680),
       "p_down": (60, 320, 200, 620)}


def meter(tag):
    print(f"== {tag} ==")
    for pose in POSES:
        f = os.path.join(SHOTS, f"{tag}{pose}.png")
        if not os.path.exists(f):
            continue
        im = np.asarray(Image.open(f).convert("RGB")).astype(float)
        L = im @ [0.2126, 0.7152, 0.0722]
        mk = np.load(os.path.join(SHOTS, f"kwmask_{pose}.npz"))
        x0, y0, x1, y1 = REF[pose]
        ref = L[y0:y1, x0:x1]
        row = [f"WALLref={ref.mean():5.1f} sd{ref.std():4.1f}"]
        for part in PARTS:
            if part not in mk.files:
                continue
            m = mk[part]
            if m.sum() < 60:
                continue
            v = L[m]
            # fine-scale gradient: mean |delta| between horizontally adjacent
            # pixels that are BOTH in the mask (scale-blind sd is not enough)
            a, b = m[:, :-1] & m[:, 1:], None
            d = np.abs(L[:, 1:] - L[:, :-1])[a]
            d1 = d.mean() if d.size else 0.0
            row.append(f"{part}={v.mean():5.1f} sd{v.std():4.1f} d1={d1:4.2f}")
        print(f"  {pose:9s} " + "  ".join(row))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "meter"
    if cmd == "mask":
        masks()
    elif cmd == "restore":
        build_and_place()
    else:
        meter(sys.argv[2] if len(sys.argv) > 2 else "kneewall_")
