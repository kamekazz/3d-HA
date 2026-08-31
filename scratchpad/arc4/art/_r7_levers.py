# -*- coding: utf-8 -*-
"""Levers to pay for round 7's +2.3 KB of deck artwork, measured on MY run."""
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
INNER = ["street-fighter-2-champion-edition", "time-crisis", "terminator-2"]


def load(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, path))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def run(label, mod, keymod=None):
    for n in ("art_g0", "art_g1", "art_g2", "art_g3"):
        st = types.ModuleType(n)
        st.PANELS = dict(mod.PANELS) if n == "art_g0" else {}
        sys.modules[n] = st
    sys.modules.pop("atlas4", None)
    import atlas4
    if keymod:
        keymod(atlas4)
    keys = ["%s.%s" % (s, p) for s in SLUGS for p in CORE]
    kb = len(atlas4.Atlas(keys).png) / 1024.0
    print("%-52s %8.2f KB" % (label, kb))
    return kb


old = load("g2r6", "art_g2_r6.bak.py")
new = load("g2r7", "art_g2.py")

base6 = run("round 6, shipping settings", old)
base7 = run("round 7, shipping settings", new)
print("%-52s %+8.2f KB" % ("  round 7 costs", base7 - base6))
print("-" * 62)


def flanks(n):
    def f(a4):
        for s in INNER:
            a4.SIZE_KEY["%s.side" % s] = n
    return f


for n in (40, 38, 36, 34):
    k = run("round 7 + three inner flanks 44 -> %d" % n, new, flanks(n))
    print("%-52s %+8.2f KB" % ("  net against round 6", k - base6))


def front(n):
    def f(a4):
        a4.SIZE["front"] = n
    return f


for n in (88, 86, 84):
    k = run("round 7 + SIZE[front] 92 -> %d" % n, new, front(n))
    print("%-52s %+8.2f KB" % ("  net against round 6", k - base6))


def combo(a4):
    for s in INNER:
        a4.SIZE_KEY["%s.side" % s] = 36
    a4.SIZE["front"] = 88


k = run("COMBO  inner flanks 36 + SIZE[front] 88", new, combo)
print("%-52s %+8.2f KB" % ("  net against round 6", k - base6))
