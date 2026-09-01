"""Pack only art_g2's own panels, old vs new, so the byte delta is this
module's and not the other three agents'.

    $PY scratchpad/arc4/art/_r8_bytes.py            # round 8 (shipping)
    $PY scratchpad/arc4/art/_r8_bytes.py old        # round 7 (the .bak)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                                "tools")))
if len(sys.argv) > 1 and sys.argv[1] == "old":
    sys.path.insert(0, os.path.join(HERE, "_r8old"))
import atlas4  # noqa: E402

MINE = ["legends-ultimate", "street-fighter-2-champion-edition",
        "time-crisis", "terminator-2"]
keys = atlas4.keys_for(MINE)
a = atlas4.Atlas(keys)
print("%s   %d panels   %.2f KB" % (a, len(keys), len(a.png) / 1024.0))
for k in ("street-fighter-2-champion-edition.deck", "terminator-2.deck",
          "time-crisis.deck", "legends-ultimate.front",
          "terminator-2.front", "street-fighter-2-champion-edition.front"):
    one = atlas4.Atlas([k])
    print("   %-42s %s  %.2f KB" % (k, atlas4.dims(k), len(one.png) / 1024.0))
