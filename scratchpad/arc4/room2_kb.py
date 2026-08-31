"""Room 2's real payload, per piece, straight off the live DB + the files.

    $PY scratchpad/arc4/room2_kb.py
"""
import os
import sqlite3
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
DB = os.path.join(_ROOT, "backend", "house.db")
UP = os.path.join(_ROOT, "backend", "uploads", "models")

con = sqlite3.connect(DB)
rows = con.execute(
    "SELECT o.name, m.id, m.filename FROM objects o "
    "JOIN models m ON m.id = o.model_id WHERE o.room_id = 2").fetchall()
seen, out, tot = set(), [], 0.0
for name, mid, fn in rows:
    if mid in seen:
        continue
    seen.add(mid)
    p = os.path.join(UP, fn or "")
    if not os.path.exists(p):
        cand = [f for f in os.listdir(UP) if f.startswith("model_%d." % mid)]
        p = os.path.join(UP, cand[0]) if cand else None
    kb = os.path.getsize(p) / 1024.0 if p and os.path.exists(p) else 0.0
    tot += kb
    out.append((kb, name))
out.sort(reverse=True)
for kb, name in out:
    flag = "   << OVER 300 KB PER-PIECE CAP" if kb > 300 else ""
    print("%8.1f KB  %s%s" % (kb, name, flag))
print("-" * 46)
print("%8.1f KB  ROOM 2 TOTAL, %d pieces   (cap 1536.0 KB, %+.1f)"
      % (tot, len(out), tot - 1536.0))
