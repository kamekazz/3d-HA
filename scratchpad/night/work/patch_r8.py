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


# ---- 1. joints as grooves with a lighter chamfer (shared helper)
rep('''  const dk = hsl(0.60, 0.012, 0.42).clone();
  for (const [jx, jz, jw, jd] of joints) {
    const j = slab(jx, jz, jx + jw, jz + jd, y + 0.016);
    paint(j, dk);
    beds.push(j);
  }
}''', '''  for (const j of joints) addJoint(j, y, beds);
}
// A control joint that reads at 40 ft: a 0.10 ft groove 12% darker than the
// pour, flanked by two 0.07 ft chamfers 10% lighter. `rect` is [x, z, w, d]
// with the thin dimension 0.16 (the old solid dark stripe), which is where
// the groove is centred.
const JOINT_DK = () => hsl(0.60, 0.012, 0.50), JOINT_LT = () => hsl(0.60, 0.012, 0.63);
function addJoint([jx, jz, jw, jd], y, beds) {
  const along = jw >= jd ? 'x' : 'z';                 // the long axis
  const cz = jz + jd / 2, cx = jx + jw / 2;
  const strip = (off, w, col, yy) => {
    const g = along === 'x'
      ? slab(jx, cz + off - w / 2, jx + jw, cz + off + w / 2, yy)
      : slab(cx + off - w / 2, jz, cx + off + w / 2, jz + jd, yy);
    paint(g, col); beds.push(g);
  };
  strip(-0.085, 0.07, JOINT_LT(), y + 0.014);
  strip(0.085, 0.07, JOINT_LT(), y + 0.014);
  strip(0, 0.10, JOINT_DK(), y + 0.016);
}''')
rep('''  const jointDk = hsl(0.60, 0.012, 0.42).clone();
  for (let z = walkTopZ + 4.5; z < walkEnd - 3; z += 5.5) {
    const jx = fanX(z) + 0.15;
    const j = slab(jx, z, L.driveL - 0.2, z + 0.16, CONC_Y + 0.016);
    paint(j, jointDk); beds.push(j);
  }''', '''  for (let z = walkTopZ + 4.5; z < walkEnd - 3; z += 5.5) {
    const jx = fanX(z) + 0.15;
    addJoint([jx, z, L.driveL - 0.2 - jx, 0.16], CONC_Y, beds);
  }''')

# ---- 2. the band: no rim round the far end (it read as a circular ring)
rep('''  // the rim: lawn side and the far end, small stones, slightly proud
  addCobbleRun(rng, [bandOuter[0], bandOuter[1], [fanX(stripEnd), stripEnd]], rockY, beds, 0.62);''',
    '''  // the rim: the lawn side ONLY, small stones, slightly proud. Round 7 ran
  // it round the far end too and from 40 ft the two runs closed into "a
  // perfectly circular rock ring".
  addCobbleRun(rng, [bandOuter[0], bandOuter[1]], rockY, beds, 0.62);''')

# ---- 3. the porch-west bed: dried hydrangea / mum clumps, no geese
rep('''  const SP = ['boxwood', 'boxwood', 'euonymus', 'juniper', 'yew'];
  for (let x = L.houseW - 0.6; x < L.stepW - 10.5; x += 1.55 + rng() * 0.85) {
    addBoxwood(rng, x, bedF0 + 1.2 + rng() * 1.5, 0.9 + rng() * 1.2, mulchY,
               leaves, SP[Math.floor(rng() * SP.length)]);
  }
  for (let x = L.houseW + 1.5; x < L.stepW - 11; x += 3.4 + rng() * 2.4) {
    addPerennial(rng, x, bedF1 - 1.4 - rng() * 0.9, mulchY, leaves,
                 4 + Math.floor(rng() * 4), 2.6);
  }''', '''  // ROUND 8: the porch's WEST half is a long low bed of DRIED hydrangea and
  // mum clumps (muted rust / straw / cream, the night photograph's November
  // bed), not the July boxwood-and-salvia row -- five varied clumps with
  // straw tufts between, and a scatter of irregular cobbles along the
  // mulch's front edge.
  const DRIED = ['cream', 'straw', 'rust', 'straw', 'cream', 'rust'];
  let di = 0;
  for (let x = L.houseW - 0.2; x < L.stepW - 10.5; x += 2.6 + rng() * 1.2) {
    addDriedClump(rng, x, bedF0 + 1.4 + rng() * 2.2, 1.05 + rng() * 0.55, mulchY,
                  leaves, DRIED[di++ % DRIED.length]);
    if (rng() < 0.6) addGrassClump(rng, x + 1.3, bedF0 + 0.9 + rng() * 1.2, mulchY, leaves, true);
  }
  for (let x = L.houseW - 0.8; x < L.stepW - 1.5; x += 0.9 + rng() * 0.9) {
    const r = 0.16 + rng() * 0.16;
    const c = new THREE.IcosahedronGeometry(r, 0);
    c.scale(1 + rng() * 0.5, 0.55, 1 + rng() * 0.5);
    c.rotateY(rng() * 6.283);
    c.translate(x, mulchY + r * 0.2, bedF1 - 0.35 - rng() * 0.5);
    paint(c, hsl(0.58 + rng() * 0.05, 0.05, 0.36 + rng() * 0.3)); beds.push(c);
  }''')
rep('''  // the two cast geese, west of the porch steps
  addGoose(rng, L.stepW - 3.6, bedF1 - 0.9, mulchY, 0.5, props);
  addGoose(rng, L.stepW - 2.6, bedF1 - 1.3, mulchY, 0.9, props);''',
    '''  // (the two cast geese are gone from the night frame: with the pot beside
  // them they read as "three identical candle lanterns" from 40 ft)''')
rep('''  addUplightCan(L.driveR + 0.9, L.houseF + 5.9, L.lo + 0.04, props);
  addUplightCan(L.driveR + 1.1, L.houseF + 9.2, L.lo + 0.04, props);''',
    '''  // (no fixture cans here: the only can in the yard is the one at the rock
  // band's end -- repeated identical fixtures were the round-7 tell)''')

# the dried clump helper, next to addMum
rep('''// The lumpy dome itself: `sq` squashes the whole mass, `tint()` gives each''',
    '''// A dried hydrangea / spent mum clump: the same lumpy dome in muted
// November colours -- cream (papery hydrangea heads), straw, rust.
const DRIED_TINT = {
  cream: [0.10, 0.22, 0.60], straw: [0.12, 0.34, 0.50], rust: [0.045, 0.48, 0.33],
};
function addDriedClump(rng, x, z, r, y, leaves, kind = 'straw') {
  const [h, sat, l] = DRIED_TINT[kind] || DRIED_TINT.straw;
  lumpyMass(rng, x, z, r, y, leaves, 0.72, () =>
    hsl(h + (rng() - 0.5) * 0.03, sat, l + (rng() - 0.5) * 0.14), 0.40);
}
// The lumpy dome itself: `sq` squashes the whole mass, `tint()` gives each''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('PATCHED')
