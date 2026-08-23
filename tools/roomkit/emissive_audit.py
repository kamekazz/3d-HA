"""Audit every placed GLB for emissive on ROOM-SCALE surfaces, by emitting AREA.

    python -m roomkit.emissive_audit

Run it before you report a room, and any time a critic says "that is emissive".

A recessed can lens and a 480 sq ft ceiling plane are both "emissive material on
an object called Ceiling". Only one is forbidden. The discriminator is the area
of the geometry actually carrying the emissive material, so that is what this
measures - in square feet, after the glTF metre->foot conversion.

ROOM-BRIEF: emissive belongs on a fixture the photograph shows, at the size the
photograph shows it. Never on a wall, skin, trim run, ceiling or floor.
"""
import json, os, sqlite3, struct
import numpy as np

ROOT = r'C:\Users\Manuel\Desktop\Pro\3d HA'
MODELS = os.path.join(ROOT, 'backend', 'uploads', 'models')
FT = 3.28084          # glTF is metres, the world is feet
THRESHOLD_SQFT = 12.0  # a fixture is small; anything this big is a surface

con = sqlite3.connect(os.path.join(ROOT, 'backend', 'house.db'))
rows = list(con.execute(
    "SELECT o.name, o.model_id, r.id, r.name, o.scale "
    "FROM objects o JOIN rooms r ON r.id = o.room_id"))

def load(path):
    with open(path, 'rb') as f:
        magic, _, _ = struct.unpack('<III', f.read(12))
        if magic != 0x46546C67:
            return None, None
        clen, _ = struct.unpack('<II', f.read(8))
        js = json.loads(f.read(clen).decode('utf-8'))
        blen, _ = struct.unpack('<II', f.read(8))
        return js, f.read(blen)

def accessor(g, buf, i):
    a = g['accessors'][i]
    bv = g['bufferViews'][a['bufferView']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    n = a['count']
    ncomp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5125: '<u4', 5123: '<u2', 5121: '<u1', 5126: '<f4'}[a['componentType']]
    return np.frombuffer(buf, dtype=np.dtype(dt), count=n * ncomp, offset=off).reshape(n, ncomp)

def tri_area(v, idx):
    a, b, c = v[idx[:, 0]], v[idx[:, 1]], v[idx[:, 2]]
    return float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() * 0.5)

findings = []
for oname, mid, rid, rname, oscale in rows:
    p = os.path.join(MODELS, 'model_%d.glb' % mid)
    if not os.path.exists(p):
        continue
    try:
        g, buf = load(p)
    except Exception:
        continue
    if not g:
        continue
    s = (oscale or 1.0) ** 2
    for mesh in g.get('meshes', []):
        for prim in mesh.get('primitives', []):
            mi = prim.get('material')
            if mi is None:
                continue
            mat = g['materials'][mi]
            ef = mat.get('emissiveFactor')
            if not ef or max(ef) <= 0.001:
                continue
            stren = mat.get('extensions', {}).get(
                'KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
            if 'POSITION' not in prim.get('attributes', {}) or 'indices' not in prim:
                continue
            v = accessor(g, buf, prim['attributes']['POSITION']).astype(float)
            idx = accessor(g, buf, prim['indices']).reshape(-1, 3).astype(int)
            sqft = tri_area(v, idx) * FT * FT * s
            if sqft >= THRESHOLD_SQFT:
                findings.append((sqft, rid, rname, oname, mid,
                                 mat.get('name', '?'), max(ef), stren))

findings.sort(reverse=True)
print('EMISSIVE ON ROOM-SCALE SURFACES  (emitting area >= %.0f sq ft)' % THRESHOLD_SQFT)
print('%9s  %-4s %-17s %-26s %-8s %-10s %6s %6s' %
      ('sq ft', 'room', 'room name', 'object', 'model', 'material', 'factor', 'stren'))
print('-' * 100)
for sqft, rid, rname, oname, mid, mat, ef, stren in findings:
    print('%9.1f  %-4s %-17s %-26s %-8s %-10s %6.3f %6.2f'
          % (sqft, rid, rname[:17], oname[:26], mid, mat[:10], ef, stren))
print()
print('%d room-scale emissive surfaces, across %d rooms'
      % (len(findings), len({f[1] for f in findings})))
inscope = [f for f in findings if f[1] in (1, 2, 3, 7, 11)]
print('%d of them in this run\'s five rooms (1,2,3,7,11)' % len(inscope))
