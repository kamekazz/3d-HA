# -*- coding: utf-8 -*-
"""Dump every art_g2 panel EXACTLY as atlas4 will pack it (real texel size,
real QUANT), as PNGs, into a directory.

    $PY _r8_dump.py <outdir> [old]

`old` puts scratchpad/arc4/art/_r8old (round 7's art_g2) first on sys.path,
so the same script measures the previous round with no other difference.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..",
                                                "tools")))
if len(sys.argv) > 2 and sys.argv[2] == "old":
    sys.path.insert(0, os.path.join(HERE, "_r8old"))

from PIL import Image  # noqa: E402
import atlas4  # noqa: E402
import art_g2  # noqa: E402

OUT = sys.argv[1]
if not os.path.isdir(OUT):
    os.makedirs(OUT)

SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
meta = {"aspect": {}, "dims": {}}
for s in SLUGS:
    for cls in ("marquee", "front", "side", "deck"):
        key = "%s.%s" % (s, cls)
        w, h = atlas4.dims(key)
        rows = atlas4.render(key, w, h)
        im = Image.new("RGB", (w, h))
        im.putdata([c for r in rows for c in r])
        im.save(os.path.join(OUT, key.replace(".", "__") + ".png"))
        meta["dims"][key] = [w, h]
        meta["aspect"][key] = art_g2.A[s][cls]
meta["xfer"] = dict(art_g2.DECK_XFER)
meta["inset"] = {s: art_g2.FRONT_RECT[s].get("inset_ft") for s in SLUGS}
with open(os.path.join(OUT, "meta.json"), "w") as f:
    json.dump(meta, f, indent=1)
print("dumped", len(meta["dims"]), "panels ->", OUT)
