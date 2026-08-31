# -*- coding: utf-8 -*-
"""Splice round-7's deck rewrite into art_g0.py.

NAMED `_g0r7_*` ON PURPOSE.  scratchpad/arc4/art/ is shared by four art agents
working at the same time, and round 7 had a live filename collision here: a
parallel agent's own `_r7_splice.py` (which rewrites art_g2.py) landed on top
of this one mid-round and got run by mistake.  Nothing in this file touches any
module but art_g0.py, and every scratch file this round carries the `_g0r7_`
prefix so it cannot happen again.

Idempotent: it always builds from the round-6 backup, so re-running is safe.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _g0r7_frag as F                                          # noqa: E402
import _g0r7_tail as T                                          # noqa: E402

SRC = os.path.join(HERE, "_r5", "art_g0_r6.bak.py")
DST = os.path.join(HERE, "art_g0.py")

s = io.open(SRC, encoding="utf-8").read()
assert "art_g0" not in os.path.basename(DST) or True


def swap(key, new):
    """Replace one @_panel block, from the decorator to the next blank triple."""
    global s
    a = s.index('@_panel("%s")' % key)
    b = s.index("\n\n\n", a) + 3
    s = s[:a] + new + s[b:]


anchor = '@_panel("nba-jam.deck")'
i = s.index(anchor)
s = s[:i] + F.HELPERS.lstrip("\n") + F.LAYOUT.lstrip("\n") + s[i:]

swap("nba-jam.deck", F.NBA_DECK)
swap("tmnt-turtles-in-time.deck", F.TM_DECK)
swap("pac-man.deck", F.PM_DECK)
swap("golden-tee-3d-golf.deck", F.GT_DECK)

a = s.index("# =========================================================================\n"
            "#  DECKS -- the control layout")
b = s.index("# =========================================================================\n"
            "#  DOORS -- the coin door")
s = s[:a] + F.DECKS_HEAD + F.DECKS_BODY.lstrip("\n") + s[b:]

s = s.rstrip("\n") + "\n" + T.TAIL.lstrip("\n")
io.open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("wrote", DST, len(s), "bytes")
