"""Crop + meter floor patches out of a render or a photo."""
import os
import sys
import numpy as np
from PIL import Image

OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
os.makedirs(OUT, exist_ok=True)


def go(path, box, name, s=3):
    im = Image.open(path).convert("RGB")
    a = np.array(im.crop(box)).astype(float)
    g = a.mean(axis=2)
    print(f"{name:22s} {box}  mean={g.mean():6.1f} sd={g.std():5.2f} "
          f"|d1|x={np.abs(np.diff(g,axis=1)).mean():5.2f} "
          f"|d1|y={np.abs(np.diff(g,axis=0)).mean():5.2f} "
          f"rgb=({a[:,:,0].mean():.0f},{a[:,:,1].mean():.0f},{a[:,:,2].mean():.0f})")
    c = im.crop(box)
    c = c.resize((c.width * s, c.height * s), Image.LANCZOS)
    c.save(os.path.join(OUT, name + ".png"))


if __name__ == "__main__":
    S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
    tag = sys.argv[1] if len(sys.argv) > 1 else "floorbase_"
    go(f"{S}\\{tag}p_runner.png", (620, 800, 780, 900), f"{tag}run_R", 3)
    go(f"{S}\\{tag}p_runner.png", (380, 800, 500, 880), f"{tag}run_L", 3)
    go(f"{S}\\{tag}p_stairs.png", (250, 950, 600, 1150), f"{tag}st_near", 2)
    go(f"{S}\\{tag}p_doors1.png", (250, 990, 700, 1190), f"{tag}d1_floor", 2)
    # wall reference
    go(f"{S}\\{tag}p_runner.png", (700, 400, 820, 520), f"{tag}wall_E", 2)
