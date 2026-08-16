import sys, subprocess, os, json
import r17
from ckit import save_and_place
PY = sys.executable
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe import POSES, stats
wall = sys.argv[1]
base = {"n":"#959595","w":"#989898","e":"#ececec","s":"#fafafa"}
for v in [int(x) for x in sys.argv[2:]]:
    c = "#%02x%02x%02x" % (v,v,v)
    sk = dict(base); sk[wall] = c
    r17.SKINS = sk
    save_and_place("Hall2F Wall Wash Skins", r17.piece_skins(sk), 17)
    pose = dict(POSES[17][wall]); pose["fov"]=26; pose["size"]=[800,620]
    png = os.path.join("shots", "sw_%s_%d.png" % (wall, v))
    subprocess.run([PY,"-m","roomkit.shot","--pose-json",json.dumps(pose),
                    "--level","2","--day","--out",os.path.abspath(png)],
                   cwd=TOOLS, check=True, stdout=subprocess.DEVNULL)
    print("  A=%3d -> %s" % (v, stats(png)))
