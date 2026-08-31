# -*- coding: utf-8 -*-
"""Third pass: Champion Edition's collage runs edge to edge, as photographed.

The two big printed islands were covering the thing the photograph is actually
about.  v4 4 at 30x shows the collage running UNDER the controls, so the
controls get ring collars and nothing else.
"""
import io
import os

Q = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_r7_decks.py")
d = io.open(Q, encoding="utf-8").read()

OLD = '''    # --- the two printed control islands.  A dark blob with a pale keyline
    # under each player's cluster: the buttons are modelled and must land on a
    # printed collar or they read as dots dropped on a collage.
    for (u, key) in ((-0.60, "#a83038"), (0.42, "#2f5aa8")):
        cx, _t = _uv(slug, u, 0.5)
        _rrect(b, cx - 0.47 * fx, 68.0, cx + 0.47 * fx, 178.0, 18.0,
               _dk("#c2bfb4"), 0.97)
        _keyline(b, [(cx - 0.47 * fx, 68.0), (cx + 0.47 * fx, 68.0),
                     (cx + 0.47 * fx, 178.0), (cx - 0.47 * fx, 178.0)],
                 9.0, key, 0.98, cf=_dk)
'''
NEW = '''    # --- NO printed island.  v4 4 at 30x shows the collage running UNDER the
    # controls edge to edge, which is what makes this deck the room's busiest
    # printed surface; the controls get ring collars and nothing else.  Two
    # thin printed player keylines mark the split, red for 1P and blue for 2P,
    # which is a Capcom convention and is declared as such in DECK_EVIDENCE.
    for (u, key) in ((-0.60, "#b03840"), (0.42, "#3462b4")):
        cx, _t = _uv(slug, u, 0.5)
        _keyline(b, [(cx - 0.47 * fx, 66.0), (cx + 0.47 * fx, 66.0),
                     (cx + 0.47 * fx, 180.0), (cx - 0.47 * fx, 180.0)],
                 8.0, key, 0.95, cf=_dk)
'''
assert OLD in d
d = d.replace(OLD, NEW)

# the collage now has to carry the whole panel, so give it more rows and a
# slightly wider tonal spread
d = d.replace("    _cells(b, 4, 38, 252, 198,", "    _cells(b, 4, 38, 252, 196,")
d = d.replace("           9, 4, seed=41, gut=4.0, a=0.97, cf=_dk)",
              "           9, 5, seed=41, gut=4.0, a=0.97, cf=_dk)")
d = d.replace('''        _rect(b, 4 + i * 27.6 + 2.0, 38 + j * 39.5 + 2.0,
              4 + (i + 1) * 27.6 - 2.0, 38 + (j + 1) * 39.5 - 2.0,
              _dk(col), 1.0)''',
'''        _rect(b, 4 + i * 27.6 + 2.0, 38 + j * 31.6 + 2.0,
              4 + (i + 1) * 27.6 - 2.0, 38 + (j + 1) * 31.6 - 2.0,
              _dk(col), 1.0)''')
d = d.replace('''    for (i, j, col) in ((1, 0, "#e2ded0"), (3, 2, "#c4525e"),
                        (5, 1, "#4e8fd0"), (7, 3, "#c8ae44"),
                        (2, 3, "#b06aa8"), (8, 0, "#9fb0a8")):''',
'''    for (i, j, col) in ((1, 0, "#e2ded0"), (3, 2, "#c4525e"),
                        (5, 1, "#4e8fd0"), (7, 3, "#c8ae44"),
                        (2, 4, "#b06aa8"), (8, 0, "#9fb0a8"),
                        (6, 4, "#d8d4c6"), (0, 2, "#7a90a8")):''')
# a slightly heavier collar so a control still separates from a busy ground
d = d.replace('''                 rings_btn=[(1.00, "#2a2a34", 0.95), (0.60, "#e8e6dc", 1.0)],''',
              '''                 rings_btn=[(1.00, "#26262e", 0.98), (0.64, "#eceadf", 1.0)],''')
d = d.replace("                 k_btn=1.9, k_stick=2.6, cf=_dk)",
              "                 k_btn=2.1, k_stick=2.8, cf=_dk)")

io.open(Q, "w", encoding="utf-8").write(d)
print("patched", Q)
