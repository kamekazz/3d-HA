# -*- coding: utf-8 -*-
"""Round-7 payload delta for MY four decks, round 6 vs round 7.

Packs the four `.deck` panels alone, at the sizes atlas4 really uses, from
round 6's art_g2 (art_g2_r6.bak.py) and from round 7's, so the number is not
entangled with anyone else's work.  Also prints per-panel luma so the exposure
claims in the module can be checked.
"""
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
XFER = {"legends-ultimate": 0.88, "time-crisis": 0.88,
        "street-fighter-2-champion-edition": 3.05, "terminator-2": 3.05}


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def atlas_with(panels):
    for n in ("art_g0", "art_g1", "art_g2", "art_g3"):
        st = types.ModuleType(n)
        st.PANELS = panels if n == "art_g0" else {}
        sys.modules[n] = st
    sys.modules.pop("atlas4", None)
    import atlas4
    return atlas4


def report(label, mod, classes):
    keys = ["%s.%s" % (s, p) for s in SLUGS for p in classes]
    a4 = atlas_with({k: v for k, v in mod.PANELS.items() if k in keys})
    at = a4.Atlas(keys)
    kb = len(at.png) / 1024.0
    print("%-40s %8.2f KB   %s" % (label, kb, at))
    return kb, a4


old = load("g2r6", "art_g2_r6.bak.py")
new = load("g2r7", "art_g2.py")

print("--- the four DECK panels alone ----------------------------------")
a, _ = report("round 6 (art_g2_r6.bak.py)", old, ("deck",))
b, a4 = report("round 7 (art_g2.py)", new, ("deck",))
print("%-40s %+8.2f KB" % ("DELTA, decks only", b - a))
print()
print("--- all 16 core panels for my four machines ---------------------")
c, _ = report("round 6", old, ("marquee", "side", "front", "deck"))
e, _ = report("round 7", new, ("marquee", "side", "front", "deck"))
print("%-40s %+8.2f KB" % ("DELTA, my whole run", e - c))
print()
print("--- deck luma: authored, and x the measured material transfer ---")
for s in SLUGS:
    w, h = a4.dims("%s.deck" % s)
    px = [c for r in a4.render("%s.deck" % s, w, h) for c in r]
    lu = sum(p[0] * .299 + p[1] * .587 + p[2] * .114 for p in px) / len(px)
    # fine-scale gradient, native resolution, horizontal neighbours
    rows = a4.render("%s.deck" % s, w, h)
    d1 = n = 0.0
    for r in rows:
        for i in range(len(r) - 1):
            d1 += abs((r[i][0] * .299 + r[i][1] * .587 + r[i][2] * .114)
                      - (r[i + 1][0] * .299 + r[i + 1][1] * .587
                         + r[i + 1][2] * .114))
            n += 1
    d1 /= n
    m2 = sum((p[0] * .299 + p[1] * .587 + p[2] * .114 - lu) ** 2
             for p in px) / len(px)
    sd = m2 ** 0.5
    print("%-36s %2dx%-2d authored %5.1f -> renders ~%5.1f   sd %5.1f  "
          "mean|d1| %5.2f  |d1|/sd %.3f"
          % (s, w, h, lu, min(255.0, lu * XFER[s]), sd, d1,
             d1 / max(1e-6, sd)))
