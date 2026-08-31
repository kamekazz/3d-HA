# -*- coding: utf-8 -*-
"""Recalibrate the per-machine marquee emissive after the first r4 shoot.

glTF `emissiveFactor` is a FLAT add with no texture, so on a marquee that now
carries a drawn title the emissive competes with the artwork instead of lighting
it.  The first pass used the marquee's own light hue at strength 0.2-1.15 and
measured: NBA Jam's crimson caps washed to pink, and the Turtles marquee went to
a flat pale green with the art gone.  Same hues, taken down to a low VALUE and
run at strength ~1, put the glow back where the photographs have it without
bleaching the print.
"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "bsmt", "a2kit.py")
s = io.open(P, encoding="utf-8").read()

NEW = {
    "star-wars-atari":            ("#171410", 0.90),
    "marvel-super-heroes":        ("#2b2118", 1.00),
    "marvel-vs-capcom":           ("#3c2618", 1.00),
    "mortal-kombat":              ("#28304a", 1.00),
    "nba-jam":                    ("#514226", 1.00),
    "tmnt-turtles-in-time":       ("#2e3618", 1.00),
    "east-7-no-machine":          ("#16181c", 0.90),
    "legends-ultimate":           ("#1e222c", 1.00),
    "street-fighter-2-champion-edition": ("#182448", 1.00),
    "time-crisis":                ("#4c4024", 1.00),
    "terminator-2":               ("#23252e", 1.00),
    "ridge-racer":                ("#50441a", 1.00),
    "north-1-graffiti-multicade": ("#16181f", 0.90),
    "pac-man":                    ("#5a4a2a", 1.00),
    "nfl-blitz":                  ("#1b1b24", 0.90),
    "golden-tee-3d-golf":         ("#303c22", 1.00),
}

n = 0
for slug, (col, st) in NEW.items():
    pat = re.compile(r'("%s":\s*)\("#[0-9a-f]{6}", [0-9.]+\)' % re.escape(slug))
    s, k = pat.subn(lambda m: '%s("%s", %.2f)' % (m.group(1), col, st), s)
    n += k
if n != len(NEW):
    raise SystemExit("replaced %d of %d marquee tints" % (n, len(NEW)))

s = s.replace(
    "# a high strength washes the printed title away -- the lit marquees sit at\n"
    "# 0.85-1.15 and the ones the photos show dark sit at 0.22-0.40.",
    "# a high strength washes the printed title away.  MEASURED: the first pass\n"
    "# used each band's own light hue at strength up to 1.15 and NBA Jam's\n"
    "# crimson caps came out pink while the Turtles marquee bleached to flat\n"
    "# green.  So the tint is that marquee's hue taken to a LOW VALUE -- the lit\n"
    "# bands sit around luma 60-85 and the ones the photographs show dark around\n"
    "# 22-30 -- and the strength stays near 1.  The glow reads at night; the\n"
    "# printed title survives the day.")

io.open(P, "w", encoding="utf-8").write(s)
print("marquee tints recalibrated:", n)
