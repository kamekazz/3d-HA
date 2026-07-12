"""Generate the built-in seamless wall/floor texture presets.

Dev-only, run once (needs Pillow: `pip install pillow` — deliberately NOT in
backend/requirements.txt). Emits 256x256 PNGs into frontend/textures/, which
Flask already serves statically. Textures are near-white and low-contrast so
the room's wall/floor color tints them via material.map * material.color.

Re-runnable: fixed random seed, deterministic output.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
OUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "textures"

random.seed(31337)


def seamless_noise(lo, hi, cell=16):
    """Periodic low-frequency noise: random cell x cell grid tiled 3x3,
    bicubic-upscaled so one full period lands in the center SIZE crop."""
    small = Image.new("L", (cell * 3, cell * 3))
    values = [[random.randint(lo, hi) for _ in range(cell)] for _ in range(cell)]
    for ty in range(3):
        for tx in range(3):
            for y in range(cell):
                for x in range(cell):
                    small.putpixel((tx * cell + x, ty * cell + y), values[y][x])
    scale = SIZE // cell
    big = small.resize((cell * 3 * scale, cell * 3 * scale), Image.BICUBIC)
    off = cell * scale
    return big.crop((off, off, off + SIZE, off + SIZE))


def grain(img, amount, step=1):
    """Fine per-pixel speckle, inherently seamless (independent pixels)."""
    px = img.load()
    for y in range(0, SIZE, step):
        for x in range(0, SIZE, step):
            v = px[x, y]
            if isinstance(v, tuple):
                v = v[0]
            v = max(0, min(255, v + random.randint(-amount, amount)))
            px[x, y] = v
    return img


def to_rgb(gray):
    return gray.convert("RGB")


def plaster():
    return to_rgb(grain(seamless_noise(218, 242, cell=16), 5))


def concrete():
    base = seamless_noise(210, 238, cell=8)
    return to_rgb(grain(base, 9))


def carpet():
    base = seamless_noise(222, 240, cell=32)
    return to_rgb(grain(base, 12))


def brick():
    """Running bond: 4 columns x 8 rows of bricks, alternate rows offset by
    half a brick — periodic by construction."""
    img = Image.new("L", (SIZE, SIZE), 180)  # mortar
    draw = ImageDraw.Draw(img)
    bw, bh, gap = 64, 32, 3
    for row in range(SIZE // bh):
        offset = (bw // 2) if row % 2 else 0
        for col in range(-1, SIZE // bw + 1):
            x0 = col * bw + offset
            y0 = row * bh
            shade = 226 + random.randint(-8, 8)
            draw.rectangle(
                [x0 + gap, y0 + gap, x0 + bw - gap, y0 + bh - gap], fill=shade)
    return to_rgb(grain(img, 6))


def tile():
    """4x4 grid of square tiles with thin grout lines."""
    img = Image.new("L", (SIZE, SIZE), 182)  # grout
    draw = ImageDraw.Draw(img)
    tw, gap = 64, 2
    for row in range(SIZE // tw):
        for col in range(SIZE // tw):
            shade = 236 + random.randint(-4, 4)
            draw.rectangle(
                [col * tw + gap, row * tw + gap,
                 (col + 1) * tw - gap, (row + 1) * tw - gap], fill=shade)
    return to_rgb(grain(img, 3))


def wood():
    """4 vertical planks with darker seams and subtle lengthwise grain.
    Grain columns are per-x (period divides SIZE) so edges wrap."""
    img = Image.new("L", (SIZE, SIZE), 188)  # seams
    px = img.load()
    pw, gap = 64, 2
    plank_shade = [222 + random.randint(-10, 10) for _ in range(SIZE // pw)]
    col_wobble = [random.randint(-6, 6) for _ in range(SIZE)]
    for x in range(SIZE):
        plank = x // pw
        in_seam = (x % pw) < gap or (x % pw) >= pw - gap
        for y in range(SIZE):
            if in_seam:
                continue
            v = plank_shade[plank] + col_wobble[x] + random.randint(-4, 4)
            px[x, y] = max(0, min(255, v))
    return to_rgb(img)


TEXTURES = {
    "plaster": plaster,
    "brick": brick,
    "concrete": concrete,
    "wood": wood,
    "tile": tile,
    "carpet": carpet,
}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in TEXTURES.items():
        path = OUT_DIR / f"{name}.png"
        fn().save(path, optimize=True)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
