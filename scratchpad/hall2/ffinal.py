"""Final metering: clean, object-free floor patches only, render downsampled
to the photographs' 450x600 so mean|d1| is compared at one resolution."""
import sys
import numpy as np
from PIL import Image

P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"


def row(path, box, label, half=False):
    im = Image.open(path).convert("RGB").crop(box)
    if half:
        im = im.resize((max(2, im.width // 2), max(2, im.height // 2)), Image.LANCZOS)
    a = np.array(im).astype(float)
    g = a.mean(axis=2)
    dx = np.abs(np.diff(g, axis=1)).mean()
    print(f"{label:26s} n={g.size:5d} mean={g.mean():6.1f} sd={g.std():5.2f} "
          f"|d1|x={dx:5.2f} |d1|y={np.abs(np.diff(g,axis=0)).mean():5.2f} "
          f"|d1|/sd={dx/max(g.std(),1e-6):5.3f} "
          f"rgb=({a[:,:,0].mean():.0f},{a[:,:,1].mean():.0f},{a[:,:,2].mean():.0f})")
    return g.mean()


PH_WALL = [("hallway_with_white_runner_rug.jpg", (355, 300, 430, 400), "PH runner wall E"),
           ("hallway_looking_towards_stairs.jpg", (350, 200, 430, 320), "PH stairs wall E"),
           ("two_closed_white_doors_1.jpg", (370, 180, 440, 330), "PH doors1 wall R")]
PH_FLOOR = [("hallway_with_white_runner_rug.jpg", (20, 440, 120, 570), "PH runner floor nearL"),
            ("hallway_looking_towards_stairs.jpg", (40, 480, 150, 590), "PH stairs floor nearL"),
            ("hallway_looking_towards_stairs.jpg", (150, 300, 210, 330), "PH stairs floor far"),
            ("two_closed_white_doors_1.jpg", (150, 400, 300, 500), "PH doors1 alcove"),
            ("two_closed_white_doors_2.jpg", (150, 470, 300, 560), "PH doors2 alcove")]

RN_WALL = [("p_runner", (705, 860, 755, 1000), "RN runner wall E"),
           ("p_stairs", (760, 620, 860, 760), "RN stairs wall E"),
           ("p_doors1", (55, 250, 135, 700), "RN doors1 wall L")]
RN_FLOOR = [("p_runner", (632, 1000, 700, 1120), "RN runner floor R"),
            ("p_runner", (400, 822, 560, 862), "RN runner floor far"),
            ("p_stairs", (400, 825, 555, 875), "RN stairs floor far"),
            ("p_stairs", (545, 940, 600, 1060), "RN stairs floor R"),
            ("p_doors1", (470, 1060, 890, 1195), "RN doors1 alcove")]

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "floor_"
    print("===== PHOTOGRAPHS (450x600 native) =====")
    pw = [row(f"{P}\\{f}", b, l) for (f, b, l) in PH_WALL]
    pf = [row(f"{P}\\{f}", b, l) for (f, b, l) in PH_FLOOR]
    print(f"  floor/wall  runner {pf[0]/pw[0]:.3f} | stairs {pf[1]/pw[1]:.3f} "
          f"{pf[2]/pw[1]:.3f} | doors {pf[3]/pw[2]:.3f} {pf[4]/pw[2]:.3f}")
    print()
    print(f"===== RENDER {tag} (downsampled to 450x600) =====")
    rw = [row(f"{S}\\{tag}{p}.png", b, l, True) for (p, b, l) in RN_WALL]
    rf = [row(f"{S}\\{tag}{p}.png", b, l, True) for (p, b, l) in RN_FLOOR]
    print(f"  floor/wall  runner {rf[0]/rw[0]:.3f} {rf[1]/rw[0]:.3f} | "
          f"stairs {rf[2]/rw[1]:.3f} {rf[3]/rw[1]:.3f} | doors {rf[4]/rw[2]:.3f}")
