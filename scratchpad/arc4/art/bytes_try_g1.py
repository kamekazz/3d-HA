import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import png_rgb                                 # noqa: E402
import art_g1 as G                                              # noqa: E402

keys = list(G.PANELS)


def build(tile):
    ncol = 5
    nrow = (len(keys) + ncol - 1) // ncol
    W, H = ncol * tile, nrow * tile
    px = [[(0, 0, 0)] * W for _ in range(H)]
    for i, k in enumerate(keys):
        G.PANELS[k](px, (i % ncol) * tile, (i // ncol) * tile, tile)
    return px


for t in (192, 256):
    print("as-is        tile %d  %.1f KB" % (t, len(png_rgb(build(t))) / 1024))

G.Cv.noise = lambda *a, **k: None
for t in (192, 256):
    print("noise off    tile %d  %.1f KB" % (t, len(png_rgb(build(t))) / 1024))


def blitq(q, amp):
    def blit(self, px, ox, oy, tile):
        B = G._BAYER
        for y in range(tile):
            row = self.b[y]
            orow = px[oy + y]
            by = B[y & 3]
            for x in range(tile):
                n = (by[x & 3] - 7.5) * amp
                p = row[x]
                orow[ox + x] = tuple(
                    G._clamp8(round((c + n) / q) * q) for c in p)
    return blit


for q, amp in ((12, 1.4), (16, 1.9), (24, 2.8)):
    G.Cv.blit = blitq(q, amp)
    for t in (192, 256):
        print("q%-2d noiseoff tile %d  %.1f KB"
              % (q, t, len(png_rgb(build(t))) / 1024))
