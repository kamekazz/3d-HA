"""Deterministic synthetic needle/twig alpha atlas; no photographic source."""
from PIL import Image, ImageDraw
from pathlib import Path
import random, math

rng = random.Random(0x50494e45)
im = Image.new('RGBA', (256, 256))
draw = ImageDraw.Draw(im)
draw.line([(127, 250), (125, 163), (130, 86), (128, 8)], fill=(75, 71, 48, 255), width=3)
for j in range(19):
    t = j / 19
    root = (128 + rng.uniform(-3, 3), 231 - t * 212)
    reach = (1 - t * .70) * rng.uniform(56, 99)
    for side in [-1, 1]:
        end = (root[0] + side * reach, root[1] - rng.uniform(18, 47))
        draw.line([root, end], fill=(81, 83, 51, 255), width=2)
        dx, dy = end[0] - root[0], end[1] - root[1]
        mag = math.hypot(dx, dy)
        ax, ay = dx / mag, dy / mag
        for n in range(17):
            along = (n + .3) / 18
            p = (root[0] + dx * along, root[1] + dy * along)
            length = rng.uniform(10, 23) * (1 - along * .37)
            for s in [-1, 1]:
                q = (p[0] + ax * length * .5 - ay * length * s,
                     p[1] + ay * length * .5 + ax * length * s)
                v = rng.uniform(.75, 1.22)
                color = (int(97*v), int(116*v), int(71*v), 255)
                draw.line([p, q], fill=color, width=2)
out = Path(__file__).resolve().parents[2] / 'frontend/textures/rear-conifer-spray.png'
im.save(out, optimize=True)
print(out, out.stat().st_size)
