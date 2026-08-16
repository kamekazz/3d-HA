from bkit import *
from bkit import Model, Material, Part, save_here, soft_shadow, bx
import bkit

m = Model()
TR6 = Material("t2_a60", "#121211", roughness=0.99, metallic=0.0, opacity=0.60)
m.add(Part([(0,0.05,0),(0.8,0.05,0),(0.8,0.05,2.0),(0,0.05,2.0)],
           [(0,2,1),(0,3,2)]), TR6)
# same helper the pieces use, no clamping, no smooth ambiguity
soft_shadow(m, 2.6, 1.0, 0.7, 0.7, strength=0.58, spill=0.6)
# and a variant with smooth=False by hand
m.save(r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\baths\glb\t2.glb")
print(m.bounds())
import sys; sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.place import place
print(place("Master Bath Test Strip", r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\baths\glb\t2.glb", 16,
            pos=(2.2, 0.05, 5.6), rot_y_deg=0, scale=1.0))
