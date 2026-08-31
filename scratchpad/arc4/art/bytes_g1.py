"""What group 1's panels actually cost in the shared atlas PNG."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\bsmt")

from roomkit.glb import png_rgb                                 # noqa: E402
import art_g1 as G                                              # noqa: E402

keys = list(G.PANELS)
for tile in (96, 128, 192, 256):
    ncol = 5
    nrow = (len(keys) + ncol - 1) // ncol
    W, H = ncol * tile, nrow * tile
    px = [[(0, 0, 0)] * W for _ in range(H)]
    for i, k in enumerate(keys):
        G.PANELS[k](px, (i % ncol) * tile, (i // ncol) * tile, tile)
    b = png_rgb(px)
    tot = sum(sum(p) for row in px for p in row) / (3.0 * W * H)
    print("tile %3d  atlas %4dx%4d  %8.1f KB  mean %.1f"
          % (tile, W, H, len(b) / 1024.0, tot))
    if tile == 192:
        open(os.path.join(HERE, "atlas_g1_192.png"), "wb").write(b)

# for reference: what round 3's own atlas costs and meters
try:
    import a2kit
    a = a2kit.ART_TEX
    print("\nround-3 a2kit atlas (256x256, 16 tiles): %.1f KB"
          % (len(a) / 1024.0))
except Exception as e:                                          # noqa: BLE001
    print("\n(a2kit not importable here: %s)" % e)
