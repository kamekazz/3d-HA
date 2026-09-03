"""Mean luminance (0-255) of named patches in the render and in the photo scaled to 900x1200."""
import sys, json
from PIL import Image, ImageStat
ren = Image.open(sys.argv[1]).convert("L")
ph = Image.open("../../demo/exterior_night.jpg").convert("L").resize((900, 1200), Image.LANCZOS)
patches = json.loads(sys.argv[2])   # {name: [[rx,ry,w,h],[px,py,w,h]]}
print("%-28s %8s %8s" % ("patch", "render", "photo"))
for name, (r, p) in patches.items():
    a = ImageStat.Stat(ren.crop((r[0], r[1], r[0]+r[2], r[1]+r[3]))).mean[0]
    b = ImageStat.Stat(ph.crop((p[0], p[1], p[0]+p[2], p[1]+p[3]))).mean[0]
    print("%-28s %8.1f %8.1f" % (name, a, b))
