# -*- coding: utf-8 -*-
"""Second tuning pass: CE stays PALE, T2's player bars survive the box filter,
and the ART_DK divisor becomes a per-slug table the integrator can move."""
import io
import os

H = os.path.dirname(os.path.abspath(__file__))
Q = os.path.join(H, "_r7_decks.py")
d = io.open(Q, encoding="utf-8").read()

# ---- per-slug exposure table + the DECK_MAT note
d = d.replace('''_ART_DK = 3.05
''', '''# THE ONE NUMBER TO MOVE IF THE LIGHTING OR a2kit.DECK_MAT CHANGES.
DECK_XFER = {
    # a2kit.DECK_MAT today: ART_D (x0.88) for these two...
    "legends-ultimate": 0.88,
    "time-crisis": 0.88,
    # ...and ART_DK (x3.05) for these two.  Only the ART_DK pair is authored
    # through `_dk`; the ART_D pair is authored as-is.
    "street-fighter-2-champion-edition": 3.05,
    "terminator-2": 3.05,
}
_ART_DK = 3.05

# AN OPTIONAL, PAIRED CHANGE FOR THE INTEGRATOR -- BOTH LINES OR NEITHER.
# Champion Edition is the room's one PALE control deck (photo-read, see
# `ce_deck`).  Under ART_DK it has to live in the authored 0..84 band, and
# atlas4.QUANT = 20 leaves that band FIVE levels per channel; a busy pale
# collage posterises in it, which is visible in the AS RENDERED column of
# `deck_g2_r7.png`.  Adding one row to a2kit.DECK_MAT gives it the same
# thirteen-level ladder every other printed deck in the room has:
#
#     DECK_MAT["street-fighter-2-champion-edition"] = "D"
#     art_g2.DECK_XFER["street-fighter-2-champion-edition"] = 0.88
#
# Do BOTH or NEITHER: one without the other is 3.5x out either way.  The
# module SHIPS the un-requested value, so doing nothing is safe.
DECK_MAT_REQUEST = {
    "street-fighter-2-champion-edition": {
        "want": "D",
        "why": ("pale printed collage; ART_DK + QUANT 20 leaves 5 levels "
                "per channel and it posterises"),
        "paired_with": "art_g2.DECK_XFER[slug] = 0.88",
        "optional": True,
    },
}
''')
d = d.replace('''def _dk(v):
    """True-albedo hex -> the value to paint on an ART_DK deck."""
    c = _c(v)
    return (c[0] / _ART_DK, c[1] / _ART_DK, c[2] / _ART_DK)''',
'''def _dk(v):
    """True-albedo hex -> the value to paint on an ART_DK deck."""
    c = _c(v)
    f = DECK_XFER.get(_dk.slug, _ART_DK)
    return (c[0] / f, c[1] / f, c[2] / f)


_dk.slug = "terminator-2"          # set by each ART_DK deck before it paints''')
d = d.replace('''    def g(x, y):
        c = f(x, y)
        return (c[0] / _ART_DK, c[1] / _ART_DK, c[2] / _ART_DK)
    return g''',
'''    k = DECK_XFER.get(_dk.slug, _ART_DK)

    def g(x, y):
        c = f(x, y)
        return (c[0] / k, c[1] / k, c[2] / k)
    return g''')

# each ART_DK deck declares which slug it is painting, first thing
d = d.replace('''    slug = "street-fighter-2-champion-edition"
    xs = _xs(slug, "deck")''',
'''    slug = "street-fighter-2-champion-edition"
    _dk.slug = slug
    xs = _xs(slug, "deck")''')
d = d.replace('''    slug = "terminator-2"
    xs = _xs(slug, "deck")''',
'''    slug = "terminator-2"
    _dk.slug = slug
    xs = _xs(slug, "deck")''')

# ---- CE: keep the panel PALE.  Pale printed islands, quieter collage.
d = d.replace('''    _rect(b, 0, 0, 256, 26, _dk("#b6b24a"), 1.0)
    _rect(b, 0, 26, 256, 34, _dk("#3a3830"), 1.0)''',
'''    _rect(b, 0, 0, 256, 26, _dk("#9c9840"), 1.0)
    _rect(b, 0, 26, 256, 34, _dk("#312f28"), 1.0)''')
d = d.replace('''           ("#a03a44", "#2d5f8e", "#8b877c", "#96407a", "#2f8074",
            "#9c7a28", "#63308c", "#8f8b82", "#8c2626", "#38548a"),''',
'''           ("#9a6068", "#6d8aa6", "#b6b2a6", "#a0789a", "#6f9a92",
            "#a89a6c", "#8a76a2", "#c0bcb2", "#a06a66", "#7688a6"),''')
d = d.replace('''    for (i, j, col) in ((1, 0, "#c4bfae"), (3, 2, "#c4525e"),
                        (5, 1, "#4e8fd0"), (7, 3, "#bda23a"),
                        (2, 3, "#b06aa8"), (8, 0, "#9fb0a8")):''',
'''    for (i, j, col) in ((1, 0, "#e2ded0"), (3, 2, "#c4525e"),
                        (5, 1, "#4e8fd0"), (7, 3, "#c8ae44"),
                        (2, 3, "#b06aa8"), (8, 0, "#9fb0a8")):''')
d = d.replace('''               _dk("#5e5c54"), 0.96)''', '''               _dk("#c2bfb4"), 0.97)''')
d = d.replace('''                 rings_btn=[(1.00, "#191922", 0.95), (0.62, "#cfcdc2", 1.0)],
                 rings_stick=[(1.00, "#191922", 0.95), (0.70, "#e2e5ea", 0.95),
                              (0.44, "#1c1c24", 1.0)],''',
'''                 rings_btn=[(1.00, "#2a2a34", 0.95), (0.60, "#e8e6dc", 1.0)],
                 rings_stick=[(1.00, "#2a2a34", 0.95), (0.72, "#e8eaf0", 0.95),
                              (0.46, "#1c1c24", 1.0)],''')

# ---- T2: player bars tall enough to survive 34 output rows, neutral wells
d = d.replace('''        hw, hh = 0.40 * fx, 0.185 * fy''',
              '''        hw, hh = 0.40 * fx, 0.170 * fy''')
d = d.replace('''        _rrect(b, cx - hw, cy - hh, cx + hw, cy + hh, 16.0, _dk("#101018"), 1.0)''',
              '''        _rrect(b, cx - hw, cy - hh, cx + hw, cy + hh, 16.0, _dk("#111116"), 1.0)''')
d = d.replace('''               12.0, _dk("#0a0910"), 1.0)''',
              '''               12.0, _dk("#08080b"), 1.0)''')
d = d.replace('''        _rect(b, cx - hw, cy + hh + 8, cx + hw, cy + hh + 30, _dk(col), 0.95)
        _rect(b, cx - hw, cy + hh + 30, cx + hw, cy + hh + 36, _dk(bar), 0.9)''',
'''        _rect(b, cx - hw, cy + hh + 6, cx + hw, cy + hh + 42, _dk(col), 1.0)
        _rect(b, cx - hw, cy + hh + 42, cx + hw, cy + hh + 52, _dk(bar), 1.0)''')
d = d.replace('''    _rect(b, 0, 196, 256, 200, _dk("#151220"), 1.0)
    _rect(b, 0, 200, 256, 222, _dk("#7c2030"), 1.0)
    _rect(b, 0, 222, 256, 230, _dk("#a83a44"), 0.75)
    _rect(b, 0, 230, 256, 256, _dk("#100e16"), 1.0)''',
'''    _rect(b, 0, 208, 256, 214, _dk("#141220"), 1.0)
    _rect(b, 0, 214, 256, 238, _dk("#7c2030"), 1.0)
    _rect(b, 0, 238, 256, 246, _dk("#a83a44"), 0.8)
    _rect(b, 0, 246, 256, 256, _dk("#100e16"), 1.0)''')
d = d.replace('''    _rect(b, 0, 34, 256, 196, _dk("#2a2836"), 1.0)''',
              '''    _rect(b, 0, 34, 256, 208, _dk("#2a2836"), 1.0)''')

io.open(Q, "w", encoding="utf-8").write(d)
print("patched", Q)
