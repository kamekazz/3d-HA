"""Round-2 textures for room 7.

The round-1 critic's single named gap: "every hero surface in this room is built
as a collage of axis-aligned boxes when the toolchain already supports the
textured quad that would fix it".  This module is that fix.  Everything here
returns raw PNG bytes for `roomkit.glb.Material(tex=...)`, to be mapped with
`uv_quad`.

Two kinds of texture live here:

* **Procedural** (clock dial, posters, deck graphics, signage, door leaf, floor
  sheen).  Drawn with PIL primitives at print scale, so letterforms and dial
  ticks are anti-aliased rather than blocked out of geometry.
* **Photo-derived albedo** for the KIES banner.  The banner is a photographic
  print of a split front/rear BMW M4 render with a paint-splatter ground; there
  is no honest way to draw that from primitives.  It is rectified out of
  `Garage v3 1.jpg` with a four-point perspective solve, then the photograph's
  own lighting is DIVIDED OUT (a wide gaussian estimates the illumination field
  and the image is normalised against it) so what is mapped is an albedo, not a
  lit image the renderer would then light a second time.  This is texture
  baking, and it is declared in rooms/7.json.
"""
import io
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

PHOTOS = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg"
FONTDIR = r"C:\Windows\Fonts"


def _png(im, colors=0):
    """PIL image -> PNG bytes.  `colors` quantises to a palette, which is what
    keeps a 512 px photographic tile inside the per-piece KB cap."""
    if colors:
        im = im.convert("RGB").quantize(colors=colors, method=Image.MAXCOVERAGE)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def _font(name, size):
    for cand in (name, "arialbd.ttf", "arial.ttf"):
        p = os.path.join(FONTDIR, cand)
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _centre(d, xy, text, font, fill, spacing=0):
    """Draw `text` centred on xy, optionally letter-spaced."""
    if not spacing:
        w = d.textlength(text, font=font)
        d.text((xy[0] - w / 2.0, xy[1]), text, font=font, fill=fill)
        return
    w = sum(d.textlength(c, font=font) for c in text) + spacing * (len(text) - 1)
    x = xy[0] - w / 2.0
    for c in text:
        d.text((x, xy[1]), c, font=font, fill=fill)
        x += d.textlength(c, font=font) + spacing


# ------------------------------------------------------------- KIES banner
# The vinyl's four corners in Garage v3 1.jpg (1200x1600), read off a
# 20-px-gridded 3x crop.  The banner's right edge lands within ~0.2 ft of the
# NE corner, which is what fixes its width on the wall.
#
# The top edge slopes DOWN to the east and the bottom edge UP, because the
# camera stands at room-local x 4.4 -- west of the banner -- at 5.1 ft, so the
# banner's top (7.4 ft) is above the horizon and its bottom (1.2 ft) below it,
# and both converge as the wall recedes.  Getting that backwards is what tilted
# the KIES baseline in the first two attempts; the check is that the wordmark's
# baseline comes out level and the car's centre split comes out vertical.
BANNER_QUAD = [(417, 532), (609, 546), (611, 772), (417, 801)]   # TL TR BR BL


def banner_png(w=440, h=600, colors=190):
    src = Image.open(os.path.join(PHOTOS, "Garage v3 1.jpg")).convert("RGB")
    q = BANNER_QUAD
    data = (q[0][0], q[0][1], q[3][0], q[3][1],
            q[2][0], q[2][1], q[1][0], q[1][1])          # nw sw se ne
    im = src.transform((w, h), Image.QUAD, data, Image.BICUBIC)

    # --- divide the photograph's own illumination back out ------------------
    ill = im.convert("L").filter(ImageFilter.GaussianBlur(radius=w * 0.16))
    ip = ill.load()
    px = im.load()
    n = w * h
    mean = sum(ip[x, y] for y in range(h) for x in range(w)) / float(n)
    for y in range(h):
        for x in range(w):
            k = mean / max(24.0, ip[x, y])
            r, g, b = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)),
                        min(255, int(b * k)))

    # mild denoise then a light unsharp: the source is a 208 px JPEG crop, and
    # its block noise both reads as grain at 1:1 and triples the PNG.
    im = im.filter(ImageFilter.MedianFilter(3))
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=95, threshold=3))

    # re-normalise so the vinyl white lands at the value measured off the
    # photograph (the banner's clean white meters 200 against the north wall's
    # 167) with the factor colour carrying the rest.
    st = im.convert("L").getextrema()
    lo, hi = st
    if hi - lo > 20:
        px = im.load()
        for y in range(h):
            for x in range(w):
                r, g, b = px[x, y]
                f = 248.0 / hi
                px[x, y] = (min(255, int(r * f)), min(255, int(g * f)),
                            min(255, int(b * f)))
    return _png(im, colors)


# -------------------------------------------------------- LIQUI MOLY clock
def clock_png(s=320):
    im = Image.new("RGB", (s, s), (232, 233, 234))
    d = ImageDraw.Draw(im)
    c = s / 2.0
    d.ellipse([2, 2, s - 3, s - 3], fill=(206, 209, 212))          # bezel
    d.ellipse([10, 10, s - 11, s - 11], fill=(238, 240, 241))
    d.ellipse([18, 18, s - 19, s - 19], fill=(252, 252, 251))      # dial
    f_num = _font("arial.ttf", int(s * 0.085))
    for i in range(60):
        a = 2 * math.pi * i / 60.0 - math.pi / 2
        r1 = c - 26
        r0 = c - (38 if i % 5 == 0 else 32)
        wid = 3 if i % 5 == 0 else 1
        d.line([c + r0 * math.cos(a), c + r0 * math.sin(a),
                c + r1 * math.cos(a), c + r1 * math.sin(a)],
               fill=(46, 48, 51), width=wid)
    for i in range(1, 13):
        a = 2 * math.pi * i / 12.0 - math.pi / 2
        r = c - 52
        t = str(i)
        tw = d.textlength(t, font=f_num)
        d.text((c + r * math.cos(a) - tw / 2, c + r * math.sin(a) - s * 0.048),
               t, font=f_num, fill=(38, 40, 43))
    # the LIQUI MOLY block: white type knocked out of red, on a dark ground
    bx0, bx1 = c - s * 0.235, c + s * 0.245
    d.rectangle([bx0, c - s * 0.115, bx1, c - s * 0.005], fill=(20, 22, 25))
    d.rectangle([bx0, c + s * 0.005, bx1, c + s * 0.115], fill=(198, 26, 32))
    f_lg = _font("arialbd.ttf", int(s * 0.095))
    _centre(d, (c + s * 0.005, c - s * 0.112), "LIQUI", f_lg, (250, 250, 250))
    _centre(d, (c + s * 0.005, c + s * 0.002), "MOLY", f_lg, (250, 250, 250))
    # hands
    for (ang, ln, wd) in ((-0.62, c * 0.52, 7), (2.35, c * 0.74, 5)):
        d.line([c, c, c + ln * math.cos(ang), c + ln * math.sin(ang)],
               fill=(26, 28, 31), width=wd)
    d.line([c, c, c + c * 0.66 * math.cos(1.1), c + c * 0.66 * math.sin(1.1)],
           fill=(186, 34, 32), width=3)
    d.ellipse([c - 7, c - 7, c + 7, c + 7], fill=(30, 32, 35))
    return _png(im, 96)


# ------------------------------------------------------- KIES cabinet poster
def kies_poster_png(w=260, h=380):
    im = Image.new("RGB", (w, h), (247, 247, 245))
    d = ImageDraw.Draw(im)
    _centre(d, (w * 0.5, h * 0.055), "KIES", _font("arialbd.ttf", int(h * 0.115)),
            (26, 28, 31))
    _centre(d, (w * 0.5, h * 0.185), "MOTORSPORTS",
            _font("arial.ttf", int(h * 0.036)), (86, 90, 95), spacing=h * 0.012)
    # a silver coupe photographed three-quarter, blocked as soft tone bands
    y0 = int(h * 0.27)
    d.rectangle([w * 0.06, y0, w * 0.94, h * 0.82], fill=(228, 231, 234))
    body = [(w * 0.10, h * 0.70), (w * 0.14, h * 0.55), (w * 0.30, h * 0.47),
            (w * 0.46, h * 0.40), (w * 0.68, h * 0.41), (w * 0.86, h * 0.50),
            (w * 0.90, h * 0.66), (w * 0.86, h * 0.73), (w * 0.12, h * 0.74)]
    d.polygon(body, fill=(168, 176, 186))
    d.polygon([(w * 0.34, h * 0.47), (w * 0.50, h * 0.415), (w * 0.66, h * 0.425),
               (w * 0.70, h * 0.49)], fill=(58, 64, 72))
    for cx in (w * 0.28, w * 0.76):
        d.ellipse([cx - w * 0.085, h * 0.64, cx + w * 0.085, h * 0.79],
                  fill=(34, 36, 40))
        d.ellipse([cx - w * 0.045, h * 0.673, cx + w * 0.045, h * 0.757],
                  fill=(178, 182, 186))
    d.rectangle([w * 0.06, h * 0.82, w * 0.94, h * 0.86], fill=(206, 210, 214))
    _centre(d, (w * 0.5, h * 0.90), "kiesmotorsports.com",
            _font("arial.ttf", int(h * 0.038)), (120, 124, 129))
    return _png(im, 64)


# ------------------------------------------------------------ PARKING ONLY
def parking_png(w=200, h=260):
    im = Image.new("RGB", (w, h), (246, 246, 244))
    d = ImageDraw.Draw(im)
    d.rectangle([4, 4, w - 5, h - 5], outline=(40, 42, 46), width=3)
    # the M tricolour bar
    for i, c in enumerate(((52, 96, 168), (28, 32, 40), (176, 34, 38))):
        d.rectangle([w * 0.30 + i * w * 0.13, h * 0.11,
                     w * 0.30 + (i + 1) * w * 0.13, h * 0.165], fill=c)
    _centre(d, (w * 0.5, h * 0.28), "PARKING", _font("arialbd.ttf", int(h * 0.115)),
            (28, 30, 34))
    _centre(d, (w * 0.5, h * 0.44), "ONLY", _font("arialbd.ttf", int(h * 0.115)),
            (28, 30, 34))
    for i, t in enumerate(("ALL OTHERS", "WILL BE TOWED")):
        _centre(d, (w * 0.5, h * (0.64 + i * 0.10)), t,
                _font("arial.ttf", int(h * 0.062)), (96, 100, 105))
    return _png(im, 16)


# --------------------------------------------------------- framed art prints
def rainbow_png(w=180, h=230, seed=3):
    """The two tie-dye prints north of the TV: a rainbow smear on black."""
    im = Image.new("RGB", (w, h), (14, 15, 17))
    d = ImageDraw.Draw(im)
    band = ((214, 52, 44), (232, 140, 40), (238, 214, 62), (86, 178, 84),
            (58, 150, 206), (78, 86, 176))
    rnd = _R(seed)
    for i, c in enumerate(band):
        for k in range(9):
            t = k / 8.0
            x = w * (0.16 + 0.62 * t) + rnd.f(-6, 6)
            y = h * (0.72 - 0.46 * t) + i * h * 0.052 + rnd.f(-5, 5)
            r = w * (0.16 - 0.05 * t)
            d.ellipse([x - r, y - r * 0.62, x + r, y + r * 0.62], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(radius=w * 0.035))
    return _png(im, 48)


def wave_png(w=200, h=150, seed=9):
    """The blue ocean-wave canvas above the M badge."""
    im = Image.new("RGB", (w, h), (232, 236, 238))
    d = ImageDraw.Draw(im)
    rnd = _R(seed)
    for i in range(26):
        t = i / 25.0
        c = (int(28 + 120 * t), int(58 + 130 * t), int(96 + 120 * t))
        y = h * (0.30 + 0.62 * t)
        pts = [(x, y + math.sin(x / w * 6.2 + t * 4) * h * 0.06 + rnd.f(-2, 2))
               for x in range(0, w + 1, 10)]
        d.line(pts, fill=c, width=int(h * 0.09))
    d.polygon([(0, 0), (w, 0), (w, h * 0.34), (0, h * 0.30)], fill=(238, 241, 243))
    im = im.filter(ImageFilter.GaussianBlur(radius=1.6))
    return _png(im, 48)


# -------------------------------------------------------- skate deck graphics
def deck_png(kind, w=150, h=560, seed=5):
    """A hung deck's top graphic.  `kind`: 'city' or 'swirl' (photo 1's pair)."""
    rnd = _R(seed)
    if kind == "city":
        im = Image.new("RGB", (w, h), (24, 42, 68))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, h * 0.30], fill=(46, 92, 140))
        for i in range(16):                                   # skyline
            x = i * w / 16.0
            hh = rnd.f(0.10, 0.30)
            d.rectangle([x, h * (0.42 - hh), x + w / 16.0 + 1, h * 0.46],
                        fill=(18, 26, 40))
        d.rectangle([0, h * 0.46, w, h * 0.62], fill=(150, 168, 186))
        d.polygon([(w * 0.10, h * 0.60), (w * 0.26, h * 0.53),
                   (w * 0.74, h * 0.53), (w * 0.90, h * 0.60),
                   (w * 0.90, h * 0.66), (w * 0.10, h * 0.66)],
                  fill=(60, 108, 172))
        for cx in (w * 0.26, w * 0.74):
            d.ellipse([cx - w * 0.10, h * 0.625, cx + w * 0.10, h * 0.665],
                      fill=(20, 22, 26))
        d.rectangle([0, h * 0.70, w, h * 0.80], fill=(88, 160, 96))
        d.rectangle([0, h * 0.86, w, h], fill=(180, 60, 52))
    else:
        im = Image.new("RGB", (w, h), (246, 246, 246))
        d = ImageDraw.Draw(im)
        # black-and-white marbled swirl: wide sine bands running the length
        for i in range(-3, 14):
            base = h * (i / 10.0)
            pts, back = [], []
            for k in range(0, 21):
                u = k / 20.0
                x = w * u
                off = h * 0.075 * math.sin(u * 5.4 + i * 0.8) \
                    + h * 0.035 * math.sin(u * 11.0 + i)
                pts.append((x, base + off))
                back.append((x, base + off + h * 0.052))
            d.polygon(pts + back[::-1], fill=(20, 20, 22))
    d = ImageDraw.Draw(im)
    d.ellipse([-w * 0.5, -h * 0.055, w * 1.5, h * 0.055], fill=(228, 229, 231))
    d.ellipse([-w * 0.5, h * 0.945, w * 1.5, h * 1.055], fill=(228, 229, 231))
    return _png(im, 40)


def mirror_car_png(kind, w=150, h=430):
    """One of the two oval car mirrors flanking the service door (photo 1)."""
    im = Image.new("RGB", (w, h), (238, 241, 244))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h * 0.28, w, h * 0.74],
                fill=(140, 162, 190) if kind == "blue" else (96, 100, 106))
    body = (24, 52, 116) if kind == "blue" else (196, 200, 205)
    d.polygon([(w * 0.08, h * 0.62), (w * 0.12, h * 0.50), (w * 0.30, h * 0.44),
               (w * 0.52, h * 0.40), (w * 0.76, h * 0.43), (w * 0.92, h * 0.52),
               (w * 0.92, h * 0.63), (w * 0.08, h * 0.65)], fill=body)
    d.polygon([(w * 0.32, h * 0.445), (w * 0.52, h * 0.408),
               (w * 0.70, h * 0.435), (w * 0.72, h * 0.485),
               (w * 0.34, h * 0.49)], fill=(30, 34, 40))
    for cx in (w * 0.26, w * 0.74):
        d.ellipse([cx - w * 0.10, h * 0.585, cx + w * 0.10, h * 0.665],
                  fill=(26, 28, 32))
        d.ellipse([cx - w * 0.055, h * 0.605, cx + w * 0.055, h * 0.645],
                  fill=(176, 180, 184))
    _centre(d, (w * 0.5, h * 0.09), "BMW", _font("arialbd.ttf", int(h * 0.062)),
            (34, 37, 42))
    _centre(d, (w * 0.5, h * 0.80), "M4 COMPETITION",
            _font("arial.ttf", int(h * 0.034)), (52, 56, 62))
    d.ellipse([2, 2, w - 3, h - 3], outline=(150, 154, 160), width=5)
    return _png(im, 40)


# --------------------------------------------------- sectional door leaf face
DOOR_GRAIN = 24.0


def door_png(w=512, h=256, seed=17):
    """Value field for the white sectional leaf.

    Round 1 shipped this face at mean |delta| 0.00 -- algebraically flat paint
    on the largest surface in the room.  A real steel door is brightest at the
    top (it faces the header light), carries a shallow pillow across every
    section and picks up vertical wash streaks and a dirt gradient at the
    bottom rail.  One repeat covers the WHOLE leaf, so v maps section joints.
    """
    rnd = _R(seed)
    secs = 4
    lat = [[rnd.f(-1, 1) for _ in range(19)] for _ in range(13)]
    # a fine lattice too: round 2's first door still metered mean|delta| 0.14
    # against the photograph's 3.91-4.57, because the only variation in it was
    # smooth gradients.  A real steel leaf has an embossed stucco face.
    fn = 250
    fine = [[rnd.f(-1, 1) for _ in range(fn + 1)] for _ in range(fn + 1)]
    rows = []
    for y in range(h):
        t = y / float(h)                      # 0 = top of the leaf
        row = []
        # section-local coordinate, 0..1 within each of the four sections
        s = (t * secs) % 1.0
        for x in range(w):
            u = x / float(w)
            v = 252.0
            v -= 26.0 * t ** 1.5                       # top-lit gradient
            v += 5.0 * math.sin(math.pi * s)           # pillow across a section
            if s < 0.028 or s > 0.972:                 # section joint
                v -= 30.0
            v -= 5.0 * math.cos(math.pi * (u - 0.5))   # slight barrel across
            # low-frequency wash: bilinear over a coarse lattice
            gx, gy = u * 18, t * 12
            i0, j0 = int(gx), int(gy)
            fx, fy = gx - i0, gy - j0
            fx = fx * fx * (3 - 2 * fx)
            fy = fy * fy * (3 - 2 * fy)
            nv = (lat[j0][i0] * (1 - fx) * (1 - fy)
                  + lat[j0][i0 + 1] * fx * (1 - fy)
                  + lat[j0 + 1][i0] * (1 - fx) * fy
                  + lat[j0 + 1][i0 + 1] * fx * fy)
            v += nv * 4.0
            # embossed stucco face: a fine value-noise field plus a shallow
            # horizontal rib at roughly 2 in centres
            gx2, gy2 = (u * fn) % fn, (t * fn * 0.55) % fn
            i2, j2 = int(gx2), int(gy2)
            f2x, f2y = gx2 - i2, gy2 - j2
            f2x = f2x * f2x * (3 - 2 * f2x)
            f2y = f2y * f2y * (3 - 2 * f2y)
            v += DOOR_GRAIN * (fine[j2][i2] * (1 - f2x) * (1 - f2y)
                        + fine[j2][i2 + 1] * f2x * (1 - f2y)
                        + fine[j2 + 1][i2] * (1 - f2x) * f2y
                        + fine[j2 + 1][i2 + 1] * f2x * f2y)
            v += 2.2 * math.sin(t * 150.0 * math.pi)
            if t > 0.90:                               # grime at the bottom rail
                v -= (t - 0.90) * 130.0
            row.append(max(0, min(255, int(round(v)))))
        rows.append(row)
    im = Image.new("L", (w, h))
    im.putdata([v for r in rows for v in r])
    return _png(im)


# -------------------------------------------------------------- tiny helper
class _R:
    """The same LCG roomkit.glb uses, so a texture is reproducible."""

    def __init__(self, seed=1):
        self.s = seed & 0xFFFFFFFF

    def n(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def f(self, a, b):
        return a + (b - a) * self.n()


if __name__ == "__main__":
    out = os.path.dirname(os.path.abspath(__file__))
    for name, fn in (("banner", banner_png), ("clock", clock_png),
                     ("kies_poster", kies_poster_png), ("parking", parking_png),
                     ("rainbow", rainbow_png), ("wave", wave_png),
                     ("door", door_png)):
        b = fn()
        open(os.path.join(out, "tex_%s.png" % name), "wb").write(b)
        print("  %-14s %7.1f KB" % (name, len(b) / 1024.0))
    for k in ("city", "swirl"):
        b = deck_png(k)
        open(os.path.join(out, "tex_deck_%s.png" % k), "wb").write(b)
        print("  deck %-9s %7.1f KB" % (k, len(b) / 1024.0))
    for k in ("blue", "silver"):
        b = mirror_car_png(k)
        open(os.path.join(out, "tex_mir_%s.png" % k), "wb").write(b)
        print("  mirror %-7s %7.1f KB" % (k, len(b) / 1024.0))
