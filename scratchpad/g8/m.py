"""Honest meter: sd AND mean|d1| at NATIVE resolution, with a visual overlay."""
import sys, json
from PIL import Image, ImageDraw

def stats(im, box):
    c = im.crop(box).convert("RGB")
    px = c.load(); w,h = c.size
    lum = [[0.2126*px[x,y][0]+0.7152*px[x,y][1]+0.0722*px[x,y][2] for x in range(w)] for y in range(h)]
    flat = [v for row in lum for v in row]
    n = len(flat); mean = sum(flat)/n
    sd = (sum((v-mean)**2 for v in flat)/n) ** 0.5
    d = []
    for y in range(h):
        for x in range(w-1): d.append(abs(lum[y][x+1]-lum[y][x]))
    for y in range(h-1):
        for x in range(w): d.append(abs(lum[y+1][x]-lum[y][x]))
    md = sum(d)/len(d) if d else 0
    # mean rgb
    R=sum(px[x,y][0] for y in range(h) for x in range(w))/n
    G=sum(px[x,y][1] for y in range(h) for x in range(w))/n
    B=sum(px[x,y][2] for y in range(h) for x in range(w))/n
    return dict(mean=round(mean,1), sd=round(sd,2), d1=round(md,2),
                ratio=round(md/sd,3) if sd>1e-6 else 0.0, n=n,
                rgb=(round(R),round(G),round(B)),
                hex="#%02x%02x%02x"%(round(R),round(G),round(B)))

def run(path, boxes, overlay=None):
    im = Image.open(path)
    out = {}
    for name, box in boxes.items():
        out[name] = stats(im, box)
    if overlay:
        o = im.convert("RGB").copy(); dr = ImageDraw.Draw(o)
        for name, box in boxes.items():
            dr.rectangle(box, outline=(255,0,255), width=3)
            dr.text((box[0]+4, box[1]+4), name, fill=(255,0,255))
        o.save(overlay)
    return out

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    res = run(cfg["path"], {k: tuple(v) for k,v in cfg["boxes"].items()}, cfg.get("overlay"))
    for k,v in res.items():
        print("%-16s mean %6.1f  sd %6.2f  d1 %6.2f  |d1|/sd %5.3f  n %7d  %s" %
              (k, v["mean"], v["sd"], v["d1"], v["ratio"], v["n"], v["hex"]))
