import json
import sys

for p in sys.argv[1:]:
    txt = open(p).read()
    i = txt.index("{")
    d = json.loads(txt[i:])
    print("---", p)
    print("  on ", d["on"]["meter"], " off", d["off"]["meter"], " delta", d["delta"],
          " ratio", round(d["on"]["meter"]["centre"] / max(d["off"]["meter"]["centre"], .01), 2))
    for tag in ("on", "off"):
        own = [(s["owner"], s["intensity"]) for s in d[tag]["slots"]]
        print("  %-3s slots:" % tag, own)
    print("  at", d["on"]["at"], "night", d["on"]["night"])
