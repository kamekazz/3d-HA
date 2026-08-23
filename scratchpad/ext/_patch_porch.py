import io, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'f_porch.py')
s = io.open(p, encoding='utf-8').read()


def rep(old, new):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new, 1)


rep('''WREATH = Material("wreath", "#33452f", roughness=1.0, metallic=0.0)
RIBBON = Material("wreath_ribbon", "#8d2f30", roughness=0.9, metallic=0.0)''',
    '''# The wreath on this door is NOT a green ring. "Front of the house.jpg"
# (x 780-820, y 610-700; enlarged in scratchpad/ext/p_porch.png at 790-870)
# shows a dark-red STARBURST -- radiating twigs, no visible foliage ring --
# about 22 inches across. Round 1 built a green torus with a red tab.
WREATH = Material("wreath_red", "#7d2b2c", roughness=0.95, metallic=0.0)
WREATH_DK = Material("wreath_red_dk", "#54191c", roughness=0.95, metallic=0.0)
RIBBON = Material("wreath_ribbon", "#3a3436", roughness=0.9, metallic=0.0)''')

rep('''def _urn(m, x, z):
    m.add(cyl(0.62, 1.55, 12, r_top=0.80), WHITE, at=(x, 0, z))
    m.add(cyl(0.86, 0.14, 12), WHITE, at=(x, 1.52, z))
    # white flowers spilling over the rim, clipped topiary above
    for a in range(8):
        t = a / 8 * math.tau
        m.add(cyl(0.30, 0.26, 6), BLOOM,
              at=(x + math.cos(t) * 0.66, 1.58, z + math.sin(t) * 0.66))
    add_box(m, LEAF, 0.20, 1.1, 0.20, x, 1.7, z)
    m.add(cyl(0.62, 0.90, 10, r_top=0.50), LEAF, at=(x, 1.80, z))
    m.add(cyl(0.44, 0.70, 10, r_top=0.30), LEAF, at=(x, 2.80, z))''',
    '''def _ball(m, mat, r, x, y, z, seg=12):
    """Sphere-ish blob from three stacked truncated cones.

    roomkit.glb has no sphere, and the porch topiaries in the photographs are
    clipped BALLS on a stem -- round 1 stacked two plain cones, which read as
    a pair of green traffic cones rather than as topiary."""
    m.add(cyl(r * 0.55, r * 0.62, seg, r_top=r), mat, at=(x, y, z))
    m.add(cyl(r, r * 0.76, seg, r_top=r * 0.94), mat, at=(x, y + r * 0.62, z))
    m.add(cyl(r * 0.94, r * 0.62, seg, r_top=r * 0.42), mat,
          at=(x, y + r * 1.38, z))


def _urn(m, x, z):
    m.add(cyl(0.62, 1.55, 12, r_top=0.80), WHITE, at=(x, 0, z))
    m.add(cyl(0.86, 0.14, 12), WHITE, at=(x, 1.52, z))
    # white flowers spilling over the rim, clipped topiary above
    for a in range(8):
        t = a / 8 * math.tau
        m.add(cyl(0.30, 0.26, 6), BLOOM,
              at=(x + math.cos(t) * 0.66, 1.58, z + math.sin(t) * 0.66))
    add_box(m, LEAF, 0.17, 2.9, 0.17, x, 1.66, z)          # stem
    _ball(m, LEAF, 0.62, x, 1.72, z)
    _ball(m, LEAF, 0.46, x, 3.10, z)''')

rep('''def wreath():
    m = Model()
    # torus() is built in the XZ plane; stand it up so it faces the street
    m.add(tor(0.92, 0.24, 20, 8), WREATH, rot_x=math.pi / 2)
    add_box(m, RIBBON, 0.30, 0.62, 0.12, 0, 0.86, 0.10)
    return m''',
    '''def wreath():
    """Dark-red starburst: radiating twigs off a small hub, no foliage ring.

    Built in the XY plane facing +Z (the street): each twig is a thin box
    rotated about Z, so the whole thing is 44 boxes and ~10 KB.
    """
    m = Model()
    n = 26
    for i in range(n):
        a = i / n * math.tau
        # alternate lengths and tones so it reads as twigs, not as a wheel
        ln = 0.94 if i % 2 == 0 else 0.72
        if i % 5 == 0:
            ln = 1.05
        mat = WREATH if i % 3 else WREATH_DK
        r = ln / 2 + 0.10
        m.add(box(0.055, ln, 0.055, anchor="center"), mat,
              at=(math.cos(a) * r, math.sin(a) * r, 0.02),
              rot_z=(math.pi / 2 - a))
    m.add(cyl(0.20, 0.10, 12), WREATH_DK, at=(0, -0.05, 0.0), rot_x=math.pi / 2)
    # the small dark hanger over the top rail of the door
    add_box(m, RIBBON, 0.16, 0.46, 0.10, 0, 0.98, 0.02)
    return m''')

rep('from kit import Model, Material, add_box, OUT',
    'from kit import Model, Material, add_box, OUT\nfrom roomkit.glb import box')

rep('("Frontyard Door Wreath", wreath(), DOOR_X, DOOR_Z + 0.30, PORCH_Y + 5.05, 0),',
    '("Frontyard Door Wreath", wreath(), DOOR_X, DOOR_Z + 0.34, PORCH_Y + 5.35, 0),')

io.open(p, 'w', encoding='utf-8').write(s)
print('ok')
