"""Register a floor-plan image to world coords and draw a labelled ft grid."""
import sys, json
from PIL import Image, ImageDraw

def main(plan, out, ax, bx_, ay, by, rooms, crop, sc):
    im = Image.open(plan).convert("RGB")
    d = ImageDraw.Draw(im)
    P = lambda wx, wz: (ax + bx_*wx, ay + by*wz)
    for (name, x0, x1, z0, z1, col) in rooms:
        p0 = P(x0, z0); p1 = P(x1, z1)
        d.rectangle([min(p0[0],p1[0]), min(p0[1],p1[1]),
                     max(p0[0],p1[0]), max(p0[1],p1[1])], outline=col, width=3)
        d.text((min(p0[0],p1[0])+4, min(p0[1],p1[1])+4), name, fill=col)
    # 1 ft ticks inside the first room
    (name, x0, x1, z0, z1, col) = rooms[0]
    for i in range(int(x1-x0)+1):
        p = P(x0+i, z0); q = P(x0+i, z1)
        d.line([p, q], fill=(255,120,0), width=1)
        if i % 2 == 0: d.text((p[0]-6, p[1]-16), str(i), fill=(255,60,0))
    for i in range(int(z1-z0)+1):
        p = P(x0, z0+i); q = P(x1, z0+i)
        d.line([p, q], fill=(0,140,255), width=1)
        if i % 2 == 0: d.text((p[0]+2, p[1]-6), str(i), fill=(0,90,255))
    c = im.crop(crop).resize(((crop[2]-crop[0])*sc, (crop[3]-crop[1])*sc), Image.LANCZOS)
    c.save(out); print(c.size)

if __name__ == "__main__":
    exec(open(sys.argv[1]).read())
