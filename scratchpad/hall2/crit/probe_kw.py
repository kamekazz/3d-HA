import os, sys, importlib
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2")
import kneewall as K
from roomkit.glb import Material, _rgb
from roomkit.place import place

KEY = {
 "WM":"#ff0000",   # face skins
 "WG":"#00ff00",   # cap top
 "CORE":"#0000ff",
 "CAPF":"#ffff00", # cap nose hall
 "CAPW":"#ff00ff", # cap nose well
 "BANDF":"#00ffff",
 "BANDW":"#ff8000",
 "BBM":"#8000ff",
 "BBT":"#004000",
 "BBCAP":"#808000",
 "ENDM":"#ff80c0",
 "UND":"#000000",
}
for k,v in KEY.items():
    m = getattr(K, k)
    m.color = _rgb(v); m.roughness=1.0; m.metallic=0.0; m.emissive=_rgb(v); m.emissive_strength=1.0
mod = K.build()
p = os.path.join(r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\glb","kw_probe.glb")
mod.save(p)
lo,hi = mod.bounds()
place(K.NAME, p, 17, pos=((lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2), rot_y_deg=0.0, scale=1.0)
print("ok")
