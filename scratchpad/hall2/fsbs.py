"""Photo floor crop beside the same region of the render, both at one scale."""
import os
import sys
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"

PAIRS = [
    ("doors1", "two_closed_white_doors_1.jpg", (40, 330, 340, 590),
     "p_doors1.png", (200, 960, 800, 1180)),
    ("stairs", "hallway_looking_towards_stairs.jpg", (20, 400, 340, 600),
     "p_stairs.png", (180, 840, 820, 1180)),
    ("runner", "hallway_with_white_runner_rug.jpg", (250, 330, 450, 560),
     "p_runner.png", (560, 800, 830, 1140)),
]

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "floor_"
    for (nm, pf, pb, rf, rb) in PAIRS:
        a = Image.open(os.path.join(P, pf)).convert("RGB").crop(pb)
        b = Image.open(os.path.join(S, tag + rf)).convert("RGB").crop(rb)
        H = 420
        a = a.resize((int(a.width * H / a.height), H), Image.LANCZOS)
        b = b.resize((int(b.width * H / b.height), H), Image.LANCZOS)
        out = Image.new("RGB", (a.width + b.width + 12, H), (20, 20, 20))
        out.paste(a, (0, 0))
        out.paste(b, (a.width + 12, 0))
        out.save(os.path.join(OUT, f"sbs_{tag}{nm}.png"))
        print("sbs_%s%s.png  PHOTO | RENDER" % (tag, nm))
