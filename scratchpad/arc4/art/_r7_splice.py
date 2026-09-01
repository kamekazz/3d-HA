# -*- coding: utf-8 -*-
"""Paste the round-7 deck artwork + geometry contract into art_g2.py.

    $PY scratchpad/arc4/art/_r7_splice.py

Idempotent: re-running replaces the same four functions and the same spec
block again.  A backup of the pre-round-7 file is art_g2_r6.bak.py.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _r7_decks as D          # noqa: E402
import _r7_head as HD          # noqa: E402
import _r7_spec as S           # noqa: E402

# ALWAYS start from the pre-round-7 file, so re-running can never stack a
# second copy of the helper block on top of the first.
P = os.path.join(HERE, "art_g2.py")
BAK = os.path.join(HERE, "art_g2_r6.bak.py")
src = open(BAK, encoding="utf-8").read()

_NEXT = re.compile(r"\n(?=def |# =====|PANELS = |# ----+ geometry spec)")


def fn_span(s, name, nth=1):
    idx = -1
    for _ in range(nth):
        idx = s.index("\ndef %s(" % name, idx + 1)
    start = idx + 1
    m = _NEXT.search(s, start + 10)
    return start, m.start() + 1


def replace_fn(s, name, text, nth=1):
    a, b = fn_span(s, name, nth)
    return s[:a] + text.lstrip("\n").rstrip() + "\n\n\n" + s[b:]


# 1. the four deck paint functions.  t2_deck is defined twice (round 4's
#    legacy copy at the top of the file, then round 5's); replace the SECOND,
#    which is the one Python binds and PANELS uses.
src = replace_fn(src, "lu_deck", D.LU)
src = replace_fn(src, "ce_deck", D.CE)
src = replace_fn(src, "tc_deck", D.TC)
src = replace_fn(src, "t2_deck", D.T2, nth=2)

# 2. the shared round-7 helpers, inserted just before the Legends Ultimate
#    banner so every deck function can see them.
ANCH = "_LU_BLACK = "
src = src[:src.index(ANCH)] + D.HELPERS.lstrip("\n") + src[src.index(ANCH):]

# 3. the geometry spec block.
a = src.index("# " + "-" * 62 + " geometry spec")
b = src.index("# The printed front panel's own rect")
src = src[:a] + S.SPEC.lstrip("\n") + src[b:]

# 4. the round-7 section of the module docstring.
DOC = "WHAT CHANGED FROM ROUND 4, AND WHY"
src = src.replace(DOC, HD.HEAD + DOC, 1)

open(P, "w", encoding="utf-8").write(src)
print("spliced ->", P, len(src), "bytes")
