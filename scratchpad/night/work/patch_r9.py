import io
p = 'frontend/js/environment.js'
s = io.open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s[:4000] else '\n'


def rep(old, new, count=1):
    global s
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = s.count(old)
    assert n == count, ('MATCH COUNT %d for: %s' % (n, old[:90]))
    s = s.replace(old, new)


# ---- 1. mums: rust / burnt orange MOUNDS, not saturated red points
rep('''function addMum(rng, x, z, r, y, leaves, hue = 0.09, sat = 0.80, light = 0.46) {
  lumpyMass(rng, x, z, r, y, leaves, 0.78, () =>''',
    '''// Round 9: a flatter dome (sq 0.60) and muted tints -- the saturated
// 0.80-sat gold/red read as "red dots in a row" from 40 ft.
function addMum(rng, x, z, r, y, leaves, hue = 0.07, sat = 0.60, light = 0.40) {
  lumpyMass(rng, x, z, r, y, leaves, 0.60, () =>''')
rep('''  addMum(rng, L.stepW - 6.4, bedF0 + 3.4, 1.05, mulchY, leaves, 0.105, 0.85, 0.46); // gold
  addMum(rng, L.stepW - 4.3, bedF0 + 2.6, 1.0, mulchY, leaves, 0.045, 0.72, 0.30); // rust''',
    '''  addMum(rng, L.stepW - 6.4, bedF0 + 3.4, 1.2, mulchY, leaves, 0.075, 0.62, 0.40); // burnt orange
  addMum(rng, L.stepW - 4.3, bedF0 + 2.6, 1.1, mulchY, leaves, 0.045, 0.55, 0.32); // rust
  // and green low shrubs mixed through the dried clumps, so the bed is not a
  // row of one thing
  addBoxwood(rng, L.houseW + 3.2, bedF0 + 3.6, 0.85, mulchY, leaves, 'boxwood', true);
  addBoxwood(rng, L.houseW + 8.4, bedF0 + 1.6, 0.95, mulchY, leaves, 'juniper', true);''')
rep('''    addMum(rng, px, pz, 0.62, L.lo + 0.47, leaves, 0.03, 0.62, 0.27);''',
    '''    addMum(rng, px, pz, 0.62, L.lo + 0.47, leaves, 0.04, 0.50, 0.30);''')
rep('''  addMum(rng, L.driveL + 1.0, L.houseF + 2.2, 0.95, L.lo + 1.05, leaves, 0.085, 0.85, 0.46);''',
    '''  addMum(rng, L.driveL + 1.0, L.houseF + 2.2, 0.95, L.lo + 1.05, leaves, 0.075, 0.65, 0.42);''')

# ---- 2. the band: flat at grade, obviously linear
rep('''  ], rockY, beds, 11, stepDiscs, 0.22, true);
  // the rim: the lawn side ONLY, small stones, slightly proud. Round 7 ran
  // it round the far end too and from 40 ft the two runs closed into "a
  // perfectly circular rock ring".
  addCobbleRun(rng, [bandOuter[0], bandOuter[1]], rockY, beds, 0.62);''',
    '''  ], rockY, beds, 13, stepDiscs, 0.17, true);
  // The lawn-side edge: a dark 0.3 ft trench line under a run of SMALL flat
  // stones (sc 0.42). Round 8's rim stones were 0.5 ft cobbles and the
  // band's near end read as "a single rock pile"; the band must stay flat
  // at grade with two parallel edges, and the dark line is what draws the
  // outer edge straight.
  {
    const [[ax, az], [bx, bz]] = bandOuter;
    const L2 = Math.hypot(bx - ax, bz - az), ang = Math.atan2(-(bz - az), bx - ax);
    const trench = boxAt(L2, 0.03, 0.32, (ax + bx) / 2, rockY - 0.01, (az + bz) / 2, ang);
    paint(trench, hsl(0.07, 0.25, 0.20)); beds.push(trench);
  }
  addCobbleRun(rng, [bandOuter[0], bandOuter[1]], rockY, beds, 0.42);''')

# ---- 3. platform: treads lighter than risers
rep('''  for (const [zc, zd, h] of [[L.stepF + 0.7, 3.2, 0.92], [L.stepF - 2.0, 2.4, 1.72]]) {
    const step = boxAt(8.6, h, zd, (L.stepW + L.stepE) / 2 - 0.5, L.lo, zc);
    paintNoisy(step, hsl(0.60, 0.012, 0.60), rng, 0.06); masses.push(step);
  }''', '''  // Round 9: the TREAD is a separate, lighter top plate (L 0.68 over the
  // riser box's 0.54) so tread and riser read as two planes under a wash.
  for (const [zc, zd, h] of [[L.stepF + 0.7, 3.2, 0.92], [L.stepF - 2.0, 2.4, 1.72]]) {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    const step = boxAt(8.6, h, zd, cx, L.lo, zc);
    paintNoisy(step, hsl(0.60, 0.012, 0.54), rng, 0.06); masses.push(step);
    const tread = slab(cx - 4.3, zc - zd / 2, cx + 4.3, zc + zd / 2, L.lo + h + 0.004);
    paintNoisy(tread, hsl(0.60, 0.012, 0.68), rng, 0.04); masses.push(tread);
  }''')

# ---- 4. background tree line
rep('''  addBoxwood(rng, L.houseW - 8.0, L.padF + 2.5, 1.6, L.lo, leaves, 'euonymus', true);
  addBoxwood(rng, L.houseW - 5.0, L.padF + 4.5, 1.3, L.lo, leaves, 'juniper', true);
  // 8c.''', '''  addBoxwood(rng, L.houseW - 8.0, L.padF + 2.5, 1.6, L.lo, leaves, 'euonymus', true);
  addBoxwood(rng, L.houseW - 5.0, L.padF + 4.5, 1.3, L.lo, leaves, 'juniper', true);
  // 8d. The BACKGROUND tree line: bare crowns behind and beside the house
  //     that show above the garage ridge (18.2 ft) at right and behind the
  //     porch roof at left from night_front -- the photograph's sky is not
  //     a void, it has silhouettes bleeding into a low glow. An irregular
  //     row: beside the house (x outside the block) at z -12..-30, behind
  //     it (x across the block) at z -32..-44 so nothing stands in a room;
  //     30-45 ft tall, 9-14 ft apart, plus two big crowns east of the
  //     garage. About 1,500 five-sided cylinders in the one bark draw call.
  for (let x = L.houseW - 24; x < L.padE + 26; x += 9 + rng() * 5) {
    const inBlock = x > L.houseW - 3 && x < L.padE + 3;
    const z = inBlock ? L.blockN - 8 - rng() * 12 : L.wingN - 1 - rng() * 18;
    addBareTree(rng, x + (rng() - 0.5) * 3, z, 30 + rng() * 15, trunks);
  }
  addBareTree(rng, L.padE + 11.5, L.houseF + 6.5, 42, trunks);
  addBareTree(rng, L.padE + 19.5, L.houseF - 5.5, 38, trunks);
  // 8c.''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('PATCHED')
