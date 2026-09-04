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


# ---- 1. bark near-black; undergrowth mass under the west trees
rep('''      new THREE.MeshStandardMaterial({ color: 0x6d4c33, roughness: 1 })));''',
    '''      // Near-black bark (albedo ~0.03). Every tree in this bucket is a bare
      // winter silhouette now (PLANT_TREES is off), and at 0x6d4c33 the
      // west group rendered as "bare white stick geometry lit blue".
      new THREE.MeshStandardMaterial({ color: 0x0c0b0a, roughness: 1 })));''')
rep('''  addBareTree(rng, L.houseW - 12.5, L.houseF + 3.5, 34, trunks);
  addBareTree(rng, L.houseW - 7.5, L.houseF + 11.0, 29, trunks);
  addBareTree(rng, L.houseW - 11.0, L.houseF + 15.5, 26, trunks);''',
    '''  addBareTree(rng, L.houseW - 12.5, L.houseF + 3.5, 34, trunks);
  addBareTree(rng, L.houseW - 7.5, L.houseF + 11.0, 29, trunks);
  addBareTree(rng, L.houseW - 11.0, L.houseF + 15.5, 26, trunks);
  // and a dark undergrowth mass beneath and among those trunks (r 3-5 ft
  // blobs), so the blue landscape light lands on a mass, not on sticks
  addUndergrowth(rng, [
    [L.houseW - 15.0, L.houseF + 1.5, 4.6], [L.houseW - 10.0, L.houseF + 6.0, 3.8],
    [L.houseW - 13.5, L.houseF + 10.5, 4.2], [L.houseW - 7.0, L.houseF + 14.0, 3.4],
    [L.houseW - 12.0, L.houseF + 17.5, 3.6], [L.houseW - 4.5, L.houseF + 9.0, 3.0],
  ], leaves);''')
rep('''// Bare deciduous tree: a trunk and a recursive fork of thinner cylinders,''',
    '''// Dark undergrowth: big low blobs (r 3-5 ft, squashed to ~55%) in a
// near-black green, with the top-lit ramp, for the foot of a tree group.
function addUndergrowth(rng, pts, leaves) {
  for (const [x, z, r] of pts) {
    const g = new THREE.IcosahedronGeometry(r, 1);
    g.scale(0.9 + rng() * 0.3, 0.5 + rng() * 0.12, 0.9 + rng() * 0.3);
    g.rotateY(rng() * 6.283);
    g.translate(x, r * 0.42, z);
    paintNoisy(g, hsl(0.32 + (rng() - 0.5) * 0.04, 0.24, 0.075 + rng() * 0.03), rng, 0.3);
    shadeVertical(g, 0, r * 1.1);
    leaves.push(g);
  }
}

// Bare deciduous tree: a trunk and a recursive fork of thinner cylinders,''')

# ---- 2. walk: one continuous diagonal merging into the drive, joint on the seam
rep('''  const walkEnd = L.padF + 27.0;                 // z 68: where the band's cut meets the drive
  const walkW = L.stepW - 0.4;                   // x 11.6: the landing's west corner
  const walkTopZ = L.stepF + 0.3;                // z 44.8: just off the bottom step
  const bandW = 4.4, bandTop = L.stepF + 13.5;   // z 58: landing -> band
  const fanX = (z) => z <= bandTop
    ? walkW + (L.driveL - bandW - walkW) * Math.max(0, (z - walkTopZ) / (bandTop - walkTopZ))
    : L.driveL - bandW;
  concretePoly([
    [walkW, L.padF + 0.4], [L.driveL, L.padF + 0.4], [L.driveL, walkEnd],
    [L.driveL - bandW, walkEnd - 4.5], [L.driveL - bandW, bandTop], [walkW, walkTopZ],
  ], CONC_Y, beds);                              // same pour as the drive''',
    '''  //    ROUND 10: the band-and-cut ending of round 6 "dead-ended into lawn
  //    with a hard step-off". The west edge is ONE straight diagonal again,
  //    from the steps' west corner all the way to the drive edge at z 72.5
  //    (the same slope the landing had), so the slab merges into the drive
  //    with no lawn between throat and drive, at the drive's own height,
  //    with a control joint scored along the seam at x = driveL.
  const walkW = L.stepW - 0.4;                   // x 11.6: the slab's west corner
  const walkTopZ = L.stepF + 0.3;                // z 44.8: just off the bottom step
  const bandW = 4.4, bandTop = L.stepF + 13.5;   // (x 15.6 at z 58) fixes the diagonal's slope
  const fanSlope = (L.driveL - bandW - walkW) / (bandTop - walkTopZ);
  const walkEnd = walkTopZ + (L.driveL - walkW) / fanSlope;   // z 72.5: where the edge meets the drive
  const fanX = (z) => Math.min(L.driveL, walkW + fanSlope * Math.max(0, z - walkTopZ));
  concretePoly([
    [walkW, L.padF + 0.4], [L.driveL, L.padF + 0.4], [L.driveL, walkEnd], [walkW, walkTopZ],
  ], CONC_Y, beds);                              // same pour as the drive
  addJoint([L.driveL - 0.08, L.padF + 0.4, 0.16, walkEnd - L.padF - 0.4], CONC_Y, beds);''')

# ---- 3. steps: lighter treads, two risers with a shadow line between
rep('''  for (const [zc, zd, h] of [[L.stepF + 0.7, 3.2, 0.92], [L.stepF - 2.0, 2.4, 1.72]]) {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    const step = boxAt(8.6, h, zd, cx, L.lo, zc);
    paintNoisy(step, hsl(0.60, 0.012, 0.54), rng, 0.06); masses.push(step);
    const tread = slab(cx - 4.3, zc - zd / 2, cx + 4.3, zc + zd / 2, L.lo + h + 0.004);
    paintNoisy(tread, hsl(0.60, 0.012, 0.68), rng, 0.04); masses.push(tread);
  }''', '''  // Round 10: treads at L 0.74, risers at 0.58, and a dark nosing shadow
  // line (0.14 ft, L 0.30) along the foot of each riser, so the front reads
  // as two risers and three lit treads rather than one slab.
  for (const [zc, zd, h] of [[L.stepF + 0.7, 3.2, 0.92], [L.stepF - 2.0, 2.4, 1.72]]) {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    const step = boxAt(8.6, h, zd, cx, L.lo, zc);
    paintNoisy(step, hsl(0.60, 0.012, 0.58), rng, 0.06); masses.push(step);
    const tread = slab(cx - 4.3, zc - zd / 2, cx + 4.3, zc + zd / 2, L.lo + h + 0.004);
    paintNoisy(tread, hsl(0.60, 0.012, 0.74), rng, 0.04); masses.push(tread);
  }
  {
    const cx = (L.stepW + L.stepE) / 2 - 0.5;
    // foot of the lower riser, on the walk; foot of the upper riser, on the lower tread
    for (const [z, yy] of [[L.stepF + 2.3, CONC_Y + 0.006], [L.stepF - 0.8, L.lo + 0.92 + 0.008]]) {
      const sh = slab(cx - 4.3, z, cx + 4.3, z + 0.14, yy);
      paint(sh, hsl(0.60, 0.012, 0.30)); masses.push(sh);
    }
  }''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('PATCHED')
