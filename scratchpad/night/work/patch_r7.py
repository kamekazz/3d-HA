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


# ---- 1. concrete: neutral cool grey, blotchy vertex albedo, tyre lanes, joint heights
rep('''function addConcrete(x0, z0, x1, z1, y, joints, beds) {
  const g = slab(x0, z0, x1, z1, y, 2, 2);
  paint(g, hsl(0.10, 0.02, 0.57));
  beds.push(g);
  const dk = hsl(0.10, 0.02, 0.42).clone();
  for (const [jx, jz, jw, jd] of joints) {
    const j = slab(jx, jz, jx + jw, jz + jd, y + 0.012);
    paint(j, dk);
    beds.push(j);
  }
}''', '''//
// ROUND 7: the pour is NEUTRAL cool grey (the sepia the critics saw was the
// drive spot's warmth), subdivided at ~2.5 ft and painted with a 2-4 ft
// blotch (paintBlotch, +-8%) so it is not a uniform speckle, and `lanes`
// lays two faint darker tyre lanes toward the garage. Heights: base y,
// lanes +0.008, joints +0.016.
const CONC = () => hsl(0.60, 0.012, 0.57);
function paintBlotch(geo, color, cell, amt, rng) {
  const pos = geo.attributes.position, n = pos.count;
  const arr = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const x = pos.getX(i), z = pos.getZ(i);
    const f = 1 + (worldNoise(x + 57, z - 23, cell) - 0.5) * 2 * amt
                + (worldNoise(x - 11, z + 71, cell * 0.45) - 0.5) * amt
                + (rng ? (rng() - 0.5) * 0.04 : 0);
    arr[i * 3] = color.r * f; arr[i * 3 + 1] = color.g * f; arr[i * 3 + 2] = color.b * f;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(arr, 3));
}
function addConcrete(x0, z0, x1, z1, y, joints, beds, lanes = [], rng = null) {
  const g = slab(x0, z0, x1, z1, y, Math.max(2, Math.round((x1 - x0) / 2.5)),
                 Math.max(2, Math.round((z1 - z0) / 2.5)));
  paintBlotch(g, CONC(), 3.2, 0.08, rng);
  beds.push(g);
  for (const [lx, lz0, lz1, lw] of lanes) {
    const l = slab(lx - lw / 2, lz0, lx + lw / 2, lz1, y + 0.008, 2,
                   Math.max(2, Math.round((lz1 - lz0) / 2.5)));
    paintBlotch(l, hsl(0.60, 0.012, 0.535), 3.2, 0.06, rng);
    beds.push(l);
  }
  const dk = hsl(0.60, 0.012, 0.42).clone();
  for (const [jx, jz, jw, jd] of joints) {
    const j = slab(jx, jz, jx + jw, jz + jd, y + 0.016);
    paint(j, dk);
    beds.push(j);
  }
}''')

rep('''  const g = new THREE.ShapeGeometry(shape);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  paint(g, hsl(0.10, 0.02, 0.57));
  beds.push(g);
}''', '''  const g = new THREE.ShapeGeometry(shape);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  paintBlotch(g, CONC(), 3.2, 0.08);
  beds.push(g);
}''')

# drive joints: explicit, plus tyre lanes
rep('''  const joints = [];
  for (let z = L.street - 21.4; z > L.houseF + 6; z -= 12.5) {
    joints.push([L.driveL, z, L.driveR - L.driveL, 0.16]);
  }
  joints.push([(L.driveL + L.driveR) / 2 - 0.08, L.houseF, 0.16, L.street - L.houseF]);''',
    '''  //    ROUND 7: three transverse joints -- 10 ft off the garage, mid-drive,
  //    and the one 21.4 ft short of the kerb the night photo shows.
  const joints = [];
  for (const z of [L.houseF + 10, L.houseF + 29, L.street - 21.4]) {
    joints.push([L.driveL, z, L.driveR - L.driveL, 0.16]);
  }
  joints.push([(L.driveL + L.driveR) / 2 - 0.08, L.houseF, 0.16, L.street - L.houseF]);
  // two faint tyre-worn lanes into the west bay (the car's track, 5.2 ft)
  const laneX = (L.driveL + L.driveR) / 2 - 5.9;
  const lanes = [[laneX - 2.6, L.houseF + 0.5, L.street - 22, 1.5],
                 [laneX + 2.6, L.houseF + 0.5, L.street - 22, 1.5]];''')
rep('''  addConcrete(L.driveL, L.houseF, L.driveR, L.street - 7.6, CONC_Y, joints, beds);''',
    '''  addConcrete(L.driveL, L.houseF, L.driveR, L.street - 7.6, CONC_Y, joints, beds, lanes, rng);''')
rep('''  const jointDk = hsl(0.10, 0.02, 0.42).clone();''',
    '''  const jointDk = hsl(0.60, 0.012, 0.42).clone();''')
rep('''    const j = slab(jx, z, L.driveL - 0.2, z + 0.16, CONC_Y + 0.012);''',
    '''    const j = slab(jx, z, L.driveL - 0.2, z + 0.16, CONC_Y + 0.016);''')
rep('''    paintNoisy(step, hsl(0.10, 0.02, 0.60), rng, 0.06); masses.push(step);''',
    '''    paintNoisy(step, hsl(0.60, 0.012, 0.60), rng, 0.06); masses.push(step);''')

# ---- 2. the rock BAND
rep('''  const stripEnd = L.stepF + 13.5;                        // z 58
  // THREE pale steppers set on a diagonal across the strip (0.9 / 1.45 /
  // 2.0 ft off the walk edge), first, so the pebble field is kept off them
  const stepDiscs = addSteppers(rng, [L.stepF + 5.0, L.stepF + 8.6, L.stepF + 12.2].map((z, i) =>
                                  [fanX(z) - 0.9 - i * 0.55, z]), rockY, beds);
  // the strip: ~3.5 ft of pale river rock along the walk's west edge from
  // the mulch bed to z 58, widening at its far end round the uplight
  addBedPoly(rng, [
    [L.stepW - 0.8, bedF1 - 0.2], [fanX(bedF1 - 0.2), bedF1 - 0.2],
    [fanX(stripEnd), stripEnd], [L.stepW - 1.0, stripEnd + 0.6],
    [L.stepW - 3.4, bedF1 + 1.5], [L.stepW - 3.4, bedF1 - 0.2],
  ], rockY, beds, 11, stepDiscs, 0.22, true);''',
    '''  // ROUND 7: the rock is a BAND now, not a patch -- constant 3 ft width,
  // measured square to the landing's west edge, running with that edge from
  // the foot of the steps (z 47.4) to z 57.5 where the landing meets the
  // drive-side band. Inner edge = the concrete; outer edge = a raised cobble
  // rim against the lawn, so the shape reads when only half of it is lit.
  // Two 18 in round pale steppers sit on its centreline at thirds.
  const stripEnd = L.stepF + 13.0;                        // z 57.5
  const bandTopZ = bedF1 - 0.2;                           // z 47.4
  const ex = L.driveL - bandW - walkW, ez = bandTop - walkTopZ;  // edge direction
  const eL = Math.hypot(ex, ez), nx = -ez / eL, nz = ex / eL;    // unit normal, west
  const BAND_W = 3.0;
  const stepDiscs = addSteppers(rng, [1 / 3, 2 / 3].map((t) => {
    const z = bandTopZ + (stripEnd - bandTopZ) * t;
    return [fanX(z) + nx * BAND_W * 0.5, z + nz * BAND_W * 0.5];
  }), rockY, beds);
  const bandOuter = [[fanX(bandTopZ) + nx * BAND_W, bandTopZ + nz * BAND_W],
                     [fanX(stripEnd) + nx * BAND_W, stripEnd + nz * BAND_W]];
  addBedPoly(rng, [
    [fanX(bandTopZ), bandTopZ], [fanX(stripEnd), stripEnd],
    bandOuter[1], bandOuter[0],
  ], rockY, beds, 11, stepDiscs, 0.22, true);
  // the rim: lawn side and the far end, small stones, slightly proud
  addCobbleRun(rng, [bandOuter[0], bandOuter[1], [fanX(stripEnd), stripEnd]], rockY, beds, 0.62);''')

rep('''function addCobbleRun(rng, pts, y, beds) {
  for (let k = 0; k < pts.length - 1; k++) {
    const [ax, az] = pts[k], [bx, bz] = pts[k + 1];
    const L = Math.hypot(bx - ax, bz - az);
    const n = Math.max(1, Math.round(L / 0.62));
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const r = 0.28 + rng() * 0.24;''',
    '''function addCobbleRun(rng, pts, y, beds, sc = 1) {
  for (let k = 0; k < pts.length - 1; k++) {
    const [ax, az] = pts[k], [bx, bz] = pts[k + 1];
    const L = Math.hypot(bx - ax, bz - az);
    const n = Math.max(1, Math.round(L / (0.62 * sc)));
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n;
      const r = (0.28 + rng() * 0.24) * sc;''')

# ---- 3. leaf litter: drifts, not a field
rep('''function addLeafLitter(rng, n, x0, z0, x1, z1, keep, y, beds) {
  let placed = 0, tries = 0;
  while (placed < n && tries < n * 6) {
    tries++;
    const x = x0 + rng() * (x1 - x0), z = z0 + rng() * (z1 - z0);
    if (!keep(x, z)) continue;''',
    '''// `drifts` are [cx, cz, r, n]: flecks gather round a centre (density
// falling off to the radius) -- loose piles against an edge, never a field.
function addLeafLitter(rng, drifts, keep, y, beds) {
  for (const [cx, cz, rad, n] of drifts) {
  let placed = 0, tries = 0;
  while (placed < n && tries < n * 6) {
    tries++;
    const a = rng() * Math.PI * 2, d = rng() * rng() * rad;
    const x = cx + Math.cos(a) * d, z = cz + Math.sin(a) * d * 0.8;
    if (!keep(x, z)) continue;''')
rep('''    paint(g, hsl(0.08 + rng() * 0.06, 0.16 + rng() * 0.16, 0.34 + rng() * 0.20));
    beds.push(g);
    placed++;
  }
}''', '''    paint(g, hsl(0.08 + rng() * 0.06, 0.16 + rng() * 0.16, 0.34 + rng() * 0.20));
    beds.push(g);
    placed++;
  }
  }
}''')
rep('''  addLeafLitter(rng, 260, L.houseW - 4, bedF1, L.driveL, L.street - 12.5, (x, z) => {
    if (z < bedF1 + 0.3 && x < L.stepW - 0.6) return false;      // the mulch bed
    if (z < stripEnd + 1.0 && x > L.stepW - 3.8) return false;    // the strip
    return x < fanX(z) - 0.3;                                    // never the walk
  }, L.lo + 0.02, beds);''',
    '''  // (round 7: ~100 flecks in five drifts against the bed edge and the
  // band's lawn side; the 260-fleck field read as a brown plane with a
  // hard edge along the drive)
  addLeafLitter(rng, [
    [L.houseW + 6, bedF1 + 2.2, 3.6, 24], [L.houseW - 0.5, bedF1 + 1.8, 3.0, 16],
    [L.stepW - 4.2, L.stepF + 7.5, 2.6, 22], [L.stepW - 1.5, L.stepF + 13.5, 2.6, 20],
    [L.stepW - 6.5, L.stepF + 12, 2.2, 14],
  ], (x, z) => {
    if (z < bedF1 + 0.3 && x < L.stepW - 0.6) return false;       // the mulch bed
    if (z < stripEnd + 1.4 && x > fanX(z) + nx * (BAND_W + 0.4)) return false; // the band
    return x < fanX(z) - 0.3;                                     // never the walk
  }, L.lo + 0.02, beds);''')

# ---- 4. dry grass tufts in the bed
rep('''  addGrassClump(rng, L.stepW - 1.2, bedF0 + 1.9, mulchY, leaves, true);''',
    '''  addGrassClump(rng, L.stepW - 1.2, bedF0 + 1.9, mulchY, leaves, true);
  // and four dry tufts between and behind the mums, so the bed is a mass
  // of clumps rather than three balls in a row
  for (const [tx, tz] of [[L.stepW - 7.6, bedF0 + 1.5], [L.stepW - 5.4, bedF0 + 1.3],
                          [L.stepW - 3.4, bedF0 + 1.7], [L.stepW - 5.3, bedF0 + 4.4]]) {
    addGrassClump(rng, tx, tz, mulchY, leaves, true);
  }''')

# ---- 5. horizon-hiding hedge masses
rep('''  addBoxwood(rng, L.houseW - 8.0, L.padF + 2.5, 1.6, L.lo, leaves, 'euonymus', true);
  addBoxwood(rng, L.houseW - 5.0, L.padF + 4.5, 1.3, L.lo, leaves, 'juniper', true);''',
    '''  addBoxwood(rng, L.houseW - 8.0, L.padF + 2.5, 1.6, L.lo, leaves, 'euonymus', true);
  addBoxwood(rng, L.houseW - 5.0, L.padF + 4.5, 1.3, L.lo, leaves, 'juniper', true);
  // 8c. Dark hedge masses that BURY the horizon at both frame edges (the
  //     whole-frame critic: "no flat ground plane meets a flat sky"). From
  //     night_front the eye is 4 ft up, so anything under ~5 ft cannot cross
  //     the horizon line; these are 6.5-8 ft. West: a diagonal run on the
  //     lawn beyond the bed; east: a line up the garage's east flank.
  addHedgeMass(rng, [[L.houseW - 4.0, L.padF + 11], [L.houseW - 13.0, L.padF + 22]], 6.5, leaves);
  addHedgeMass(rng, [[L.padE + 4.0, L.houseF + 3.5], [L.padE + 9.5, L.houseF - 11]], 8.0, leaves);''')
rep('''// Bare deciduous tree: a trunk and a recursive fork of thinner cylinders,''',
    '''// A dark clipped hedge run between two world points: overlapping blobs
// r = h/2, so the mass is h tall, with the top-lit / dark-base ramp.
function addHedgeMass(rng, [[ax, az], [bx, bz]], h, leaves) {
  const L = Math.hypot(bx - ax, bz - az), n = Math.max(2, Math.round(L / (h * 0.55)));
  for (let i = 0; i <= n; i++) {
    const t = i / n, r = h / 2 * (0.92 + rng() * 0.16);
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(0.85 + rng() * 0.2, 1.0, 0.85 + rng() * 0.2);
    g.rotateY(rng() * 6.283);
    const x = ax + (bx - ax) * t + (rng() - 0.5) * 0.8, z = az + (bz - az) * t + (rng() - 0.5) * 0.8;
    g.translate(x, r * 0.9, z);
    paintNoisy(g, hsl(0.33 + (rng() - 0.5) * 0.04, 0.30, 0.11 + rng() * 0.04), rng, 0.3);
    shadeVertical(g, 0, r * 1.9);
    leaves.push(g);
  }
}

// Bare deciduous tree: a trunk and a recursive fork of thinner cylinders,''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('PATCHED')
