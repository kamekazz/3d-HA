"""One line per (room, k) out of level.py's report json."""
import json
import sys

HDR = ("%-22s %5s %6s %6s %6s %6s %6s %7s %6s %6s %6s %6s" %
       ("report", "k", "lens", "wall", "ratio", "p99", "p99.9", "max", "mean",
        "cen_on", "cen_of", "lit:un"))


def show(path):
    d = json.load(open(path))
    tag = path.split("/")[-1].replace("_report.json", "")
    off = d["off"]["centre"]
    for s in d["sweep"]:
        print("%-22s %5g %6s %6s %6s %6s %6s %7s %6s %6s %6s %6s" % (
            tag, s["k"], s.get("lens_median", "-"), s.get("wall_median", "-"),
            s.get("ratio", "-"), s["nonlens_p99"], s["nonlens_p999"],
            s["nonlens_max"], s["mean"], s["centre"], off,
            round(s["centre"] / max(off, .01), 2)))


if __name__ == "__main__":
    print(HDR)
    for p in sys.argv[1:]:
        show(p)
