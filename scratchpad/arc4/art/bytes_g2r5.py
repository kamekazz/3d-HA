"""Round-5 G2 payload + brightness audit.

Packs MY sixteen core panels alone, and round 4's sixteen for the same four
machines alone, so the delta this round is honest and not entangled with the
other three agents' work.  Also prices the four optional `.screen` panels and
a smaller flank budget for this run.
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
CORE = ("marquee", "side", "front", "deck")


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def atlas_with(panels, sizes=None):
    """Fresh atlas4 bound to exactly `panels`."""
    for n in ("art_g0", "art_g1", "art_g2", "art_g3"):
        st = types.ModuleType(n)
        st.PANELS = panels if n == "art_g0" else {}
        sys.modules[n] = st
    sys.modules.pop("atlas4", None)
    import atlas4
    if sizes:
        atlas4.SIZE.update(sizes)
    return atlas4


def report(label, mod, keys, sizes=None):
    a4 = atlas_with(dict(mod), sizes)
    at = a4.Atlas(keys)
    print("%-46s %s" % (label, at))
    return len(at.png) / 1024.0


g2 = load("g2now", "art_g2.py")
r4 = load("g2r4", "art_g2_r4.bak.py")
g0 = load("g0src", "art_g0.py")
g3 = load("g3src", "art_g3.py")

mine = {k: v for k, v in g2.PANELS.items() if k.split(".")[-1] in CORE}
mine_scr = dict(g2.PANELS)
core_keys = ["%s.%s" % (s, p) for s in SLUGS for p in CORE]
scr_keys = core_keys + ["%s.screen" % s for s in SLUGS]

# Round 4's drawings for these four machines: only two survive on disk.
# art_g1 and art_g3 have already been rewritten for their round-5 scopes, so
# round 4's legends-ultimate and time-crisis panels are gone; art_g0 still
# carries its round-4 Champion Edition and my own backup carries T2.
old2 = {}
for m in (g0, r4):
    for k, v in m.PANELS.items():
        sl, pn = k.split(".")
        if sl in ("street-fighter-2-champion-edition", "terminator-2")                 and pn in CORE:
            old2.setdefault(k, v)
old2_keys = sorted(old2)
new2 = {k: mine[k] for k in old2_keys}

print("--- payload, MY four machines ------------------------------------")
b_new = report("round 5, 16 core panels", mine, core_keys)
b_scr = report("round 5 + 4 optional .screen at 48 px", mine_scr, scr_keys,
               {"screen": 48})
b_48 = report("round 5 + screens, flanks 64 -> 48 px", mine_scr, scr_keys,
              {"screen": 48, "side": 48})
print()
print("--- like-for-like where round 4 survives on disk (CE + T2) -------")
o = report("round 4 (art_g0 CE + art_g2 backup T2), 8 panels", old2, old2_keys)
n = report("round 5, the same 8 panels", new2, old2_keys)
print("  delta on those eight            : %+.1f KB" % (n - o))
print()
print("cost of the four .screen panels    : %+.1f KB" % (b_scr - b_new))
print("saving from flanks at 48 px        : %+.1f KB" % (b_48 - b_scr))
print("round-4 SOUTH atlas, 20 panels     : 47.8 KB   (rooms/2.json)")

print()
print("--- brightness, luma mean per panel ------------------------------")
a4 = atlas_with(dict(mine_scr), {"screen": 48})
for sl in SLUGS:
    row = []
    for pn in ("marquee", "side", "front", "deck", "screen"):
        n_ = a4.SIZE.get(pn, 96)
        px = [c for r in a4.render("%s.%s" % (sl, pn), n_) for c in r]
        row.append("%s %5.1f" % (pn[:4],
                   sum(c[0] * .299 + c[1] * .587 + c[2] * .114
                       for c in px) / len(px)))
    print("%-38s %s" % (sl, "  ".join(row)))
