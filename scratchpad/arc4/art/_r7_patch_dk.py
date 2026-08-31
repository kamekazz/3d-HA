# -*- coding: utf-8 -*-
"""One-shot: move the two ART_DK decks (CE, T2) onto TRUE-ALBEDO authoring.

Run once against _r7_decks.py, then re-run _r7_splice.py.
"""
import io
import os

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_r7_decks.py")
d = io.open(Q, encoding="utf-8").read()

if "_ART_DK = 3.05" in d:
    raise SystemExit("already applied")

HDR = '''_ART_DK = 3.05
# MEASURED, not assumed.  An ART_DK (#4c4c4c) deck faces UP, and this scene
# gives an up-facing surface far more than the 0.30 albedo factor takes away:
# round 5 authored terminator-2's deck ground at ~(26,24,33) and the round-6
# render (`shots/r6_full_south.png`, sample (160,240)-(300,262)) meters it at
# (80,78,79).  That is why round 5's "black" T2 deck arrived as a MID GREY
# slab and round 5's dark-navy Champion Edition arrived pale blue-grey.
# ART_D (#c9c9c9) decks measure ~0.88 and are authored as-is.
#
# So the two ART_DK decks below are written in TRUE ALBEDO -- the colour the
# surface should be in the finished render, which is the number a critic can
# hold against the photograph -- and `_dk` divides by this on the way into the
# buffer.  If a2kit's DECK_MAT or the daylight changes, this ONE number moves.


def _buf_dk(v):
    """`_buf` for an ART_DK panel: fill with a TRUE-ALBEDO hex, divided."""
    c = _dk(v)
    return _buf("#%02x%02x%02x"
                % tuple(min(255, int(x * 255 + 0.5)) for x in c))


def _dk(v):
    """True-albedo hex -> the value to paint on an ART_DK deck."""
    c = _c(v)
    return (c[0] / _ART_DK, c[1] / _ART_DK, c[2] / _ART_DK)


def _dkv(y0, y1, stops):
    """`_vgrad` in true albedo, divided for ART_DK."""
    f = _vgrad(y0, y1, stops)

    def g(x, y):
        c = f(x, y)
        return (c[0] / _ART_DK, c[1] / _ART_DK, c[2] / _ART_DK)
    return g


def _collar(b, cx, cy, rx, ry, rings):'''

d = d.replace("def _collar(b, cx, cy, rx, ry, rings):", HDR, 1)

d = d.replace(
    "    for (f, col, a) in rings:\n"
    "        _disc(b, cx, cy, rx * f, ry * f, _c(col), a)",
    "    for (f, col, a) in rings:\n"
    "        _disc(b, cx, cy, rx * f, ry * f,\n"
    "              _c(col) if isinstance(col, str) else col, a)")

d = d.replace(
    "def _collars_for(b, slug, rings_btn, rings_stick, k_btn=2.7, k_stick=3.5):",
    "def _collars_for(b, slug, rings_btn, rings_stick, k_btn=2.7, k_stick=3.5,\n"
    "                 cf=None):")
d = d.replace(
    '    """Paint one collar under every button and stick in `DECKS[slug]`."""\n'
    "    fx, fy = _dk_px(slug)\n"
    "    d = DECKS[slug]",
    '    """Paint one collar under every button and stick in `DECKS[slug]`."""\n'
    "    fx, fy = _dk_px(slug)\n"
    "    if cf is not None:\n"
    "        rings_btn = [(f, cf(c), a) for (f, c, a) in rings_btn]\n"
    "        rings_stick = [(f, cf(c), a) for (f, c, a) in rings_stick]\n"
    "    d = DECKS[slug]")

d = d.replace(
    "def _cells(b, x0, y0, x1, y1, cols, nx, ny, seed, gut=2.0, a=1.0):",
    "def _cells(b, x0, y0, x1, y1, cols, nx, ny, seed, gut=2.0, a=1.0,\n"
    "           cf=None):")
d = d.replace(
    "    cw = (x1 - x0) / float(nx)\n    ch = (y1 - y0) / float(ny)",
    "    cf = cf or _c\n"
    "    cw = (x1 - x0) / float(nx)\n    ch = (y1 - y0) / float(ny)")
d = d.replace(
    "                  y0 + (j + 1) * ch - gut * 0.5, _c(col), a)",
    "                  y0 + (j + 1) * ch - gut * 0.5, cf(col), a)")

d = d.replace(
    "def _keyline(b, pts, w, col, a=1.0, closed=True):",
    "def _keyline(b, pts, w, col, a=1.0, closed=True, cf=None):")
d = d.replace(
    "    _pline(b, pts, w, _c(col), a, kx=1.0, closed=closed)",
    "    _pline(b, pts, w, (cf or _c)(col), a, kx=1.0, closed=closed)")

CE_MAP = {
    "#4b4a45": "#d8d6d0",
    "#3f3d18": "#b6b24a", "#171712": "#3a3830",
    "#5a1b24": "#a03a44", "#173a5e": "#2d5f8e", "#4e4b46": "#8b877c",
    "#5c2246": "#96407a", "#1d4a44": "#2f8074", "#5e4718": "#9c7a28",
    "#3a1c52": "#63308c", "#565149": "#8f8b82", "#4a1414": "#8c2626",
    "#20304f": "#38548a",
    "#7c7768": "#c4bfae", "#8a2f3a": "#c4525e", "#2f649a": "#4e8fd0",
    "#7a6822": "#bda23a", "#7a4470": "#b06aa8", "#67766f": "#9fb0a8",
    "#3b3a35": "#5e5c54",
    "#5f1c1e": "#a83038", "#1d3358": "#2f5aa8",
    "#0e0e14": "#191922", "#8e8c82": "#cfcdc2",
    "#c6c9d0": "#e2e5ea", "#101018": "#1c1c24",
    "#1c1c26": "#34343f",
    "#0a0a0e": "#14141a", "#8e9099": "#eef1f6", "#5e6068": "#a8aeb8",
    "#33353c": "#6a6e78", "#6e7078": "#c4c9d2", "#0c0c10": "#16161c",
}
T2_MAP = {
    "#0b0a0f": "#22202c", "#050509": "#141220", "#100f16": "#2a2836",
    "#171622": "#3a374c",
    "#2f5fd0": "#4a7ae0", "#cf2424": "#d83a3a",
    "#1d3f96": "#2a4a9e", "#8f1a1a": "#9a2020",
    "#08070c": "#101018", "#cdd2da": "#c2c8d2", "#050408": "#0a0910",
    "#0a0a0e": "#141018",
    "#0a0910": "#151220", "#5c1620": "#7c2030", "#8d2a33": "#a83a44",
    "#07060b": "#100e16",
}


def to_dk(txt, mapping):
    txt = txt.replace("_c(", "_dk(").replace("_vgrad(", "_dkv(")
    txt = txt.replace('_buf("', '_buf_dk("')
    for a, b in mapping.items():
        txt = txt.replace('"%s"' % a, '"%s"' % b)
    return txt


i = d.index("CE = r")
j = d.index("TC = r")
d = d[:i] + to_dk(d[i:j], CE_MAP) + d[j:]
i = d.index("T2 = r")
d = d[:i] + to_dk(d[i:], T2_MAP)

# the helper calls inside CE / T2 need to be told to divide as well
d = d.replace('                 k_btn=1.9, k_stick=2.6)',
              '                 k_btn=1.9, k_stick=2.6, cf=_dk)')
d = d.replace('                 rings_stick=[], k_btn=2.8)',
              '                 rings_stick=[], k_btn=2.8, cf=_dk)')
d = d.replace('           9, 4, seed=41, gut=4.0, a=0.97)',
              '           9, 4, seed=41, gut=4.0, a=0.97, cf=_dk)')
d = d.replace('                 9.0, key, 0.98)',
              '                 9.0, key, 0.98, cf=_dk)')
d = d.replace('                 9.0, "#c2c8d2", 0.92)',
              '                 9.0, "#c2c8d2", 0.92, cf=_dk)')
d = d.replace('    _keyline(b, _shard, 3.0, "#141018", 0.8)',
              '    _keyline(b, _shard, 3.0, "#141018", 0.8, cf=_dk)')

io.open(Q, "w", encoding="utf-8").write(d)
print("patched", Q)
