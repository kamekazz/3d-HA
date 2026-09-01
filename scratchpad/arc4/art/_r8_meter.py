import os, sys, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_g2


def panel(key, n=256):
    buf = [[(0, 0, 0)] * n for _ in range(n)]
    art_g2.PANELS[key](buf, 0, 0, n)
    return [c for r in buf for c in r]


def stat(key):
    px = panel(key)
    lum = sorted(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px)
    return (sum(lum) / len(lum), statistics.pstdev(lum),
            lum[len(lum) // 4], lum[len(lum) // 2], lum[3 * len(lum) // 4])


base = stat("time-crisis.deck")
print("%-38s %-38s" % ("panel", "mean    sd     p25    med    p75   med/TC"))
for s in ("legends-ultimate", "street-fighter-2-champion-edition",
          "time-crisis", "terminator-2"):
    m, sd, a, b, c = stat(s + ".deck")
    print("%-38s %6.1f %6.1f %6.1f %6.1f %6.1f   %.3f"
          % (s, m, sd, a, b, c, b / base[3]))
print()
print("PHOTO medians (docs/photos-jpg): T2/TC 0.386 (v4 5), 0.511 (v4 4);"
      " CE/TC 1.26 (v4 4)")
