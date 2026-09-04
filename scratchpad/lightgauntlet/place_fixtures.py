import json
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.place import place  # noqa: E402

G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glb")

JOBS = [
    ("Flush Dome Ceiling", "flush_dome_ceiling.glb", (2.5, 7.55, 2.0)),
    ("Pendant Shade", "pendant_shade.glb", (2.5, 5.80, 6.0)),
    ("Vanity Bar", "vanity_bar.glb", (7.0, 5.50, 0.6)),
    ("Shop Strip Light", "shop_strip_light.glb", (10.5, 7.65, 5.0)),
]

if __name__ == "__main__":
    room = int(sys.argv[1]) if len(sys.argv) > 1 else 27
    for name, f, pos in JOBS:
        print(name, json.dumps(place(name, os.path.join(G, f), room, pos=pos)))
