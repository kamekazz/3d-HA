import os
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
os.makedirs(OUT, exist_ok=True)


def crop(f, box, name, s=3):
    im = Image.open(os.path.join(P, f)).crop(box)
    im = im.resize((im.width * s, im.height * s), Image.LANCZOS)
    im.save(os.path.join(OUT, name))
    print(name, im.size)


crop("two_closed_white_doors_1.jpg", (0, 320, 450, 600), "d1_floor.png")
crop("two_closed_white_doors_2.jpg", (0, 330, 450, 600), "d2_floor.png")
crop("hallway_with_white_runner_rug.jpg", (0, 380, 220, 600), "run_floorL.png")
crop("hallway_looking_towards_stairs.jpg", (0, 400, 250, 600), "st_floorL.png")
crop("hallway_looking_towards_stairs.jpg", (140, 300, 330, 420), "st_floorFar.png", 4)
