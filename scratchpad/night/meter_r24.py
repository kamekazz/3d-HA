import sys
from PIL import Image, ImageStat
im = Image.open(sys.argv[1]); ren = im.convert('L'); rgb = im.convert('RGB')
def m(img, x, y, w, h): return ImageStat.Stat(img.crop((x, y, x+w, y+h))).mean[0]
T = [
 ("drive at garage door",      (820, 745, 40, 12), 45),
 ("drive at car nose (R)",     (760, 752, 30, 12), 35),
 ("drive beside car flank",    (760, 820, 30, 30), 20),
 ("drive 5 ft behind car",     (600, 930, 60, 30), 12),
 ("drive mid-frame row 900",   (430, 900, 60, 40), 6),
 ("drive bottom edge",         (430, 1150, 100, 40), 2),
 ("walk at steps",             (400, 720, 40, 40), 104),
 ("walk fan mid",              (420, 780, 30, 30), 60),
 ("walk meets drive",          (445, 860, 30, 30), 25),
 ("rock band",                 (330, 760, 30, 30), 40),
 ("lawn W of rocks",           (200, 800, 40, 40), 5),
 ("lawn far W",                (100, 900, 40, 40), 4),
 ("lawn E of drive",           (860, 900, 30, 30), 4),
 ("steps (treads+risers)",     (420, 718, 50, 20), 85),
 ("garage wall under sconce",  (760, 660, 20, 20), 139),
 ("garage door face",          (700, 660, 60, 30), 150),
 ("siding at foundation",      (790, 705, 20, 12), 20),
 ("gable s1 (rake)",           (297, 462, 8, 6), 78),
 ("gable s2",                  (297, 476, 8, 6), 147),
 ("gable s3",                  (297, 490, 8, 6), 176),
 ("gable s4",                  (297, 504, 8, 6), 99),
 ("gable s5 (window head)",    (297, 518, 8, 6), 51),
 ("car rear face",             (600, 780, 60, 30), 8),
 ("car tyre bottoms",          (500, 880, 40, 15), 6),
 ("porch ceiling",             (220, 605, 80, 8), 142),
]
print("%-28s %7s %7s %6s" % ("patch", "render", "target", "ratio"))
for name, (x, y, w, h), t in T:
    v = m(ren, x, y, w, h); r = v / max(t, 1)
    print("%-28s %7.0f %7.0f %6.2f%s" % (name, v, t, r, "" if 0.8 <= r <= 1.2 else "  <-- off"))
def rgbm(x, y, w, h): return tuple(round(v) for v in ImageStat.Stat(rgb.crop((x, y, x+w, y+h))).mean)
print("blue rgb: porch W column", rgbm(262, 600, 10, 60), "| W end wall", rgbm(280, 560, 20, 40), "| far-left trees", rgbm(60, 500, 60, 120), "| shrubs under trees", rgbm(60, 640, 80, 40))
