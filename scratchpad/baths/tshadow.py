from bkit import *
from bkit import Model, Material, Part, save_here, bx

m = Model()
OP  = Material("tst_opaque", "#121211", roughness=0.99, metallic=0.0)
TR6 = Material("tst_a60", "#121211", roughness=0.99, metallic=0.0, opacity=0.60)
TR6H= Material("tst_a60h", "#121211", roughness=0.99, metallic=0.0, opacity=0.60)
GRY = Material("tst_grey", "#3a3a38", roughness=0.99, metallic=0.0, opacity=0.60)

def quad_at(mat, x0, x1, y, z0, z1):
    m.add(Part([(x0,y,z0),(x1,y,z0),(x1,y,z1),(x0,y,z1)],
               [(0,2,1),(0,3,2)]), mat)

quad_at(OP,   0.0, 0.8, 0.050, 0.0, 2.0)   # A opaque    @0.05
quad_at(TR6,  1.0, 1.8, 0.050, 0.0, 2.0)   # B alpha .60 @0.05
quad_at(TR6H, 2.0, 2.8, 0.300, 0.0, 2.0)   # C alpha .60 @0.30
quad_at(GRY,  3.0, 3.8, 0.050, 0.0, 2.0)   # D grey a.60 @0.05
save_here("Master Bath Test Strip", m, 16)
