"""Re-tone the Wall Art GLB in place — no rebuild, just its material factors.

The canvas is round 2's work and the round-3 critic passed it ("the painting
itself is close"), so its pigment field is NOT re-derived.  What changed is the
room around it: daylight.js raised the interior light, and more light through
ACES means a brighter, flatter, less saturated canvas.  Metered on the round-4
render against the photo:

    photo  art lum 139.4 / wall 174.5 = 0.799   mean saturation 0.108
    render art lum 202.8 / wall 225.0 = 0.902   mean saturation 0.083

So every baseColorFactor is pulled toward its own luminance-preserving chroma
axis by 1.35 and scaled by 0.67 in linear light.  Reads the GLB's JSON chunk,
rewrites the material array, and writes a new file — the original upload is left
untouched on disk.
"""
import json
import os
import struct
import sys

SRC = sys.argv[1]
DST = sys.argv[2]
CHROMA = 1.35
LEVEL = 0.67
LUM = (0.2126, 0.7152, 0.0722)

with open(SRC, "rb") as fh:
    hdr = fh.read(12)
    jlen, jtag = struct.unpack("<II", fh.read(8))
    js = fh.read(jlen)
    rest = fh.read()

g = json.loads(js.decode("utf-8"))
n = 0
for mat in g.get("materials", []):
    pbr = mat.get("pbrMetallicRoughness")
    if not pbr or "baseColorFactor" not in pbr:
        continue
    c = pbr["baseColorFactor"]
    y = sum(LUM[i] * c[i] for i in range(3))
    out = [max(0.0, min(1.0, (y + (c[i] - y) * CHROMA) * LEVEL)) for i in range(3)]
    pbr["baseColorFactor"] = out + [c[3] if len(c) > 3 else 1.0]
    n += 1

js2 = json.dumps(g, separators=(",", ":")).encode("utf-8")
js2 += b" " * ((-len(js2)) % 4)
total = 12 + 8 + len(js2) + len(rest)
with open(DST, "wb") as fh:
    fh.write(struct.pack("<III", 0x46546C67, 2, total))
    fh.write(struct.pack("<II", len(js2), jtag))
    fh.write(js2)
    fh.write(rest)
print("re-toned %d materials -> %s" % (n, os.path.basename(DST)))
