"""Render art_g0.PANELS to (a) a real 4x4 atlas PNG and (b) a labelled preview
sheet where every panel is shown AT ITS TRUE QUAD ASPECT -- i.e. what the
cabinet actually shows once the square tile is stretched onto the quad.
Also reports per-panel mean and mean|d1| so the tone claims are measured."""
import os
import sys
import zlib
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import art_g0 as A                                        # noqa: E402

TILE = A.TILE
ORDER = [
    "star-wars-atari.side", "star-wars-atari.marquee",
    "star-wars-atari.front", "star-wars-atari.deck",
    "nba-jam.side", "nba-jam.marquee", "nba-jam.front", "nba-jam.deck",
    "street-fighter-2-champion-edition.side",
    "street-fighter-2-champion-edition.marquee",
    "street-fighter-2-champion-edition.front",
    "street-fighter-2-champion-edition.deck",
    "north-1-graffiti-multicade.side", "north-1-graffiti-multicade.marquee",
    "north-1-graffiti-multicade.front", "north-1-graffiti-multicade.deck",
]
assert sorted(ORDER) == sorted(A.PANELS), "ORDER/PANELS mismatch"

N = 4
W = N * TILE
px = [[(0, 0, 0)] * W for _ in range(W)]
stats = []
for i, key in enumerate(ORDER):
    col, row = i % N, i // N
    A.PANELS[key](px, col * TILE, row * TILE, TILE)
    tot = 0.0
    d1 = 0.0
    cnt = 0
    for y in range(TILE):
        rr = px[row * TILE + y]
        prev = None
        for x in range(TILE):
            p = rr[col * TILE + x]
            lum = 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]
            tot += lum
            if prev is not None:
                d1 += abs(lum - prev)
                cnt += 1
            prev = lum
    stats.append((key, tot / float(TILE * TILE), d1 / float(cnt)))


def write_png(path, img):
    h = len(img)
    w = len(img[0])
    raw = bytearray()
    for row in img:
        raw.append(0)
        for p in row:
            raw.append(p[0])
            raw.append(p[1])
            raw.append(p[2])

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    out = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(out)


atlas = os.path.join(HERE, "atlas_g0.png")
write_png(atlas, px)
abytes = os.path.getsize(atlas)
print("atlas 4x4 @%d = %dx%d, %d bytes" % (TILE, W, W, abytes))

from PIL import Image, ImageDraw                          # noqa: E402

im = Image.new("RGB", (W, W))
im.putdata([p for row in px for p in row])

# lay the 16 panels out at true aspect: sides / fronts tall, marquees / decks
# wide.  Four columns, one machine per column, so a machine reads as a set.
CELL_W, CELL_H = 300, 330
PAD = 16
CAP = 26
MACHINES = ["star-wars-atari", "nba-jam",
            "street-fighter-2-champion-edition", "north-1-graffiti-multicade"]
ZONES = ["side", "marquee", "front", "deck"]
sheet_w = PAD + 4 * (CELL_W + PAD)
sheet_h = PAD + 4 * (CELL_H + CAP + PAD)
sheet = Image.new("RGB", (sheet_w, sheet_h), (16, 16, 18))
d = ImageDraw.Draw(sheet)
for r, zone in enumerate(ZONES):
    for c, mach in enumerate(MACHINES):
        key = "%s.%s" % (mach, zone)
        i = ORDER.index(key)
        col, row = i % N, i // N
        t = im.crop((col * TILE, row * TILE, (col + 1) * TILE,
                     (row + 1) * TILE))
        a = A.ASPECT[key]
        if a >= 1.0:
            w = CELL_W
            h = max(8, int(round(CELL_W / a)))
            if h > CELL_H:
                h = CELL_H
                w = int(round(CELL_H * a))
        else:
            h = CELL_H
            w = max(8, int(round(CELL_H * a)))
        t = t.resize((w, h), Image.LANCZOS)
        x = PAD + c * (CELL_W + PAD) + (CELL_W - w) // 2
        y = PAD + r * (CELL_H + CAP + PAD) + (CELL_H - h) // 2
        sheet.paste(t, (x, y))
        d.rectangle([x - 1, y - 1, x + w, y + h], outline=(96, 96, 104))
        cy = PAD + r * (CELL_H + CAP + PAD) + CELL_H + 3
        d.text((PAD + c * (CELL_W + PAD), cy),
               "%s  %s  (aspect %.2f)" % (str(i).rjust(2), zone.upper(), a),
               fill=(226, 226, 232))
        d.text((PAD + c * (CELL_W + PAD), cy + 11), mach[:40],
               fill=(140, 140, 150))
sheet.save(os.path.join(HERE, "preview_g0.png"))

with open(os.path.join(HERE, "preview_g0_captions.txt"), "w") as f:
    f.write("art_g0 preview -- one MACHINE per column, one ZONE per row.\n")
    f.write("Every panel is shown at its TRUE quad aspect (the square tile as\n")
    f.write("it lands on the cabinet), not as the square atlas tile.\n")
    f.write("tile %d px; 4x4 atlas of these 16 tiles = %d bytes\n\n"
            % (TILE, abytes))
    f.write("index  panel                                          aspect"
            "   mean   mean|d1|\n")
    for i, (key, mean, d1) in enumerate(stats):
        f.write("%5d  %-46s %5.2f  %6.1f   %5.2f\n"
                % (i, key, A.ASPECT[key], mean, d1))
    f.write("\nWHAT EACH PANEL CLAIMS\n")
    for k in ORDER:
        f.write("- %s\n    %s\n" % (k, A.NOTES[k]))

for key, mean, d1 in stats:
    print("%-46s a %5.2f  mean %6.1f  |d1| %5.2f"
          % (key, A.ASPECT[key], mean, d1))
print("preview -> preview_g0.png (+ _captions.txt)")
