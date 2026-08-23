import os, sys
from fm import stats
SH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shots"))
tag = sys.argv[1] if len(sys.argv) > 1 else "floor2_base_"
print(f"=== RENDER {tag} ===")
stats(f"{SH}/{tag}p_doors2.png", 380, 990, 740, 1190, "R d2 floor near")
stats(f"{SH}/{tag}p_doors2.png", 430, 950, 700, 1010, "R d2 floor mid")
stats(f"{SH}/{tag}p_doors2.png", 830, 1050, 890, 1190, "R d2 WALL/base R")
print()
stats(f"{SH}/{tag}p_stairs.png", 255, 870, 330, 1150, "R st floor L strip")
stats(f"{SH}/{tag}p_stairs.png", 560, 850, 650, 990,  "R st floor R strip")
stats(f"{SH}/{tag}p_stairs.png", 420, 810, 530, 860,  "R st floor far")
stats(f"{SH}/{tag}p_stairs.png", 750, 300, 860, 600,  "R st WALL right")
print()
stats(f"{SH}/{tag}p_runner.png", 620, 900, 700, 1000, "R rn floor R")
stats(f"{SH}/{tag}p_runner.png", 400, 830, 520, 862,  "R rn floor far")
stats(f"{SH}/{tag}p_runner.png", 700, 250, 800, 550,  "R rn WALL right")
