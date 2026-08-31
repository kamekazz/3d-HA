"""Splice the round-7 deck rewrite into art_g1.py.  Bottom-up so the earlier
line numbers stay valid.  Run once; art_g1_r6.bak.py is the pre-edit file."""
import io
import os

H = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(H, "..", "art_g1.py")


def rd(n):
    return io.open(os.path.join(H, n), encoding="utf-8").read().rstrip("\n")


src = io.open(T, encoding="utf-8").read().split("\n")

# (1-indexed inclusive start, end, replacement)  -- applied bottom-up
JOBS = [
    (645, 660, rd("p_helpers.py")),
    (862, 890, rd("p_msh.py")),
    (1112, 1141, rd("p_mvc.py")),
    (1353, 1387, rd("p_mk.py")),
    (1556, 1580, rd("p_blitz.py")),
    (1761, 1858, rd("p_decks.py")),
]

# sanity: check each range starts where we think it does
EXPECT = {645: "def _socket(", 862: "def _msh_deck(", 1112: "def _mvc_deck(",
          1353: "def _mk_deck(", 1556: "def _blitz_deck(", 1761: "def _row("}
for a, b, _ in JOBS:
    assert src[a - 1].startswith(EXPECT[a]), (a, src[a - 1][:40])

for a, b, txt in sorted(JOBS, reverse=True):
    src[a - 1:b] = txt.split("\n")

io.open(T, "w", encoding="utf-8", newline="\n").write("\n".join(src))
print("spliced ->", os.path.abspath(T), len(src), "lines")
