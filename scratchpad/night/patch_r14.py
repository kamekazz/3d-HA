ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()

def block(s, start, end, new):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + new + s[j:]

# ---------------------------------------------------------------- constants
rep = [
("const LED_COLOR = new THREE.Color(0xffe9c4);   // warm white, ~2700K",
 "const LED_COLOR = new THREE.Color(0xffc58f);   // ~2700K amber-white, like the photo's bulbs"),
("const HALO_SIZE = 1.1;        // ft; screen size clamped in the shader", "const HALO_SIZE = 0.7;        // ft; screen size clamped in the shader"),
("const AMBER_HALO = 0.4;       // the bed fixtures are smaller lamps", "const AMBER_HALO = 0.3;       // the bed fixtures are smaller lamps"),
("const WASH_COLOR = [1.0, 0.74, 0.46];          // linear rgb of the siding wash",
 "const WASH_COLOR = [1.0, 0.56, 0.30];          // linear rgb of the siding wash (~3000K)\nconst CLAPBOARD = 5 / 12;                      // ft; the siding course spacing\nconst GLASS_NIGHT = new THREE.Color(0x0c0c0e);  // unlit window glass after dark"),
("const PORCH_INTENSITY = 40;", "const PORCH_INTENSITY = 36;"),
("    const light = new THREE.PointLight(0xffb870, 0, PORCH_RANGE, 2);", "    const light = new THREE.PointLight(0xffb46b, 0, PORCH_RANGE, 2);"),
("const STEP_POOL = { pos: [14.0, 4.0, 47.0], intensity: 75, range: 16, color: 0xffc080 };",
 "// Sits over the rock strip so the cobbles and steppers beside the walk read\n// (x 3..12, z 44..58 at ~60/255) and the walk at the steps stays ~100.\nconst STEP_POOL = { pos: [7.0, 6.0, 51.0], intensity: 70, range: 18, color: 0xffb46b };"),
("const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 62], intensity: 2200,\n                     angle: 0.6, penumbra: 0.5, range: 56, color: 0xffd2a0 };",
 "// Higher and further back with a wider, softer cone: the same total on the\n// concrete without the hot ellipse round the car that a tight cone drew.\nconst DRIVE_SPOT = { pos: [33, 16, 26], target: [33, 0, 66], intensity: 2600,\n                     angle: 0.95, penumbra: 0.8, range: 66, color: 0xffbe80 };"),
# ------------------------------------------------------------- LEDs
("  const haloBright = dots.map(() => 0.75 + 0.5 * rnd());", "  const haloBright = dots.map(() => 0.9 + 0.2 * rnd());"),
("  // +-25% per-LED brightness, seeded so the string never twinkles between builds",
 "  // +-10% per-LED brightness, seeded so the string never twinkles between builds"),
("      const n = Math.max(1, Math.round(len / LED_SPACING));\n      for (let k = 0; k <= n; k++) {\n        pushDot(new THREE.Vector3().lerpVectors(a, b, k / n).add(off));\n      }",
 "      const n = Math.max(1, Math.round(len / LED_SPACING));\n      for (let k = 0; k <= n; k++) {\n        // a little spacing jitter on the interior bulbs (+-6% of a gap)\n        const jit = (k === 0 || k === n) ? 0 : (jitter() - 0.5) * 0.12;\n        pushDot(new THREE.Vector3().lerpVectors(a, b, (k + jit) / n).add(off));\n      }"),
("  const dots = [];\n  const pushDot = (v) => {",
 "  const dots = [];\n  let jseed = 11;\n  const jitter = () => { jseed = (jseed * 16807) % 2147483647; return jseed / 2147483647; };\n  const pushDot = (v) => {"),
("        gl_PointSize = clamp(ps, 6.0, 40.0);", "        gl_PointSize = clamp(ps, 4.0, 24.0);"),
("        float core = smoothstep(0.32, 0.05, d);\n        float skirt = pow(max(0.0, 1.0 - d), 1.2) * 0.6;\n        // the core overshoots 1.0 on purpose: additive onto lit siding it must\n        // still clip to white, or the dot is just a pinhead riding on the wash\n        vec3 c = mix(vColor, vec3(1.0), core * 0.8) * (core * 1.9 + skirt);",
 "        float core = smoothstep(0.30, 0.05, d);\n        float skirt = pow(max(0.0, 1.0 - d), 1.4) * 0.45;\n        // the core overshoots 1.0 on purpose: additive onto lit siding it must\n        // still clip, or the dot is just a pinhead riding on the wash -- but\n        // it clips through the amber, so the bulb reads 2700K, not 6500K\n        vec3 c = mix(vColor, vec3(1.0), core * 0.55) * (core * 1.9 + skirt);"),
# ------------------------------------------------------------- lit window: curtain gradient
("  ctx.fillStyle = '#ffeec8';\n  ctx.fillRect(0, 0, 32, 128);\n  ctx.fillStyle = 'rgba(110, 70, 30, 0.6)';\n  for (let y = 2; y < 128; y += 7) ctx.fillRect(0, y, 32, 2);\n  // brighter where the lamp is, near the top\n  const grad = ctx.createLinearGradient(0, 0, 0, 128);\n  grad.addColorStop(0, 'rgba(255,255,240,0.35)');\n  grad.addColorStop(1, 'rgba(255,200,140,0)');",
 "  ctx.fillStyle = '#ffe2b0';\n  ctx.fillRect(0, 0, 32, 128);\n  ctx.fillStyle = 'rgba(110, 70, 30, 0.6)';\n  for (let y = 2; y < 128; y += 7) ctx.fillRect(0, y, 32, 2);\n  // a curtain: the lamp is up near the ceiling, the blind's foot is in shadow\n  const grad = ctx.createLinearGradient(0, 0, 0, 128);\n  grad.addColorStop(0, 'rgba(255,250,230,0.45)');\n  grad.addColorStop(0.35, 'rgba(255,220,170,0)');\n  grad.addColorStop(1, 'rgba(40,20,5,0.7)');"),
# ------------------------------------------------------------- wash material + tick
("  washMat = new THREE.MeshBasicMaterial({\n    vertexColors: true, transparent: true, opacity: 0,\n    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,\n    toneMapped: false,\n  });\n  const wash = new THREE.Mesh(buildWashGeometry(local), washMat);",
 "  washMat = makeWashMaterial();\n  const wash = new THREE.Mesh(buildWashGeometry(local), washMat);"),
("  washMat.opacity = night;\n  washMat.visible = on;", "  washMat.uniforms.uOpacity.value = night;\n  washMat.visible = on;\n  // unlit glass is near-black after dark: the shell's window material is a\n  // sky-blue map that reads as flat cyan panes at night\n  for (const g of glass) g.m.color.copy(g.orig).lerp(GLASS_NIGHT, night * 0.92);"),
("let windowMat = null;", "let windowMat = null;\nlet glass = [];            // [{m, orig}] the shell's transparent (window) materials"),
("function build(shell) {\n  dispose();",
 "function build(shell) {\n  dispose();\n  // the shell's transparent materials are its window glass (and a pond);\n  // collected BEFORE our own transparent meshes are added\n  glass = [];\n  const seen = new Set();\n  shell.traverse((o) => {\n    if (!o.isMesh) return;\n    for (const m of (Array.isArray(o.material) ? o.material : [o.material])) {\n      if (m && m.transparent && m.color && !seen.has(m)) { seen.add(m); glass.push({ m, orig: m.color.clone() }); }\n    }\n  });"),
("function dispose() {\n  if (!group) return;",
 "function dispose() {\n  for (const g of glass) g.m.color.copy(g.orig); // hand the shell its glass back\n  glass = [];\n  if (!group) return;"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

# ------------------------------------------------------------- WASHES table
NEW_WASHES = r'''const R2 = Math.SQRT1_2;
const WASHES = [
  // ---- walls. Lit siding: a bright band in the first foot under the bulbs,
  // then a cubic decay, scalloped into a pool under each bulb and cut by the
  // clapboard shadow lines (the shader does all of that -- see makeWashMaterial).
  // front gable rakes (field z 29.6, rake trim z 30.53)
  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 6, alpha: 0.8, clampY: 24.2, clap: true },
  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 6, alpha: 0.8, clampY: 24.2, clap: true },
  // main gable rakes (field z 26.9, trim z 27.7)
  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 6, alpha: 0.6, clap: true },
  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 6, alpha: 0.6, clampY: 23.8, clap: true },
  // the second-floor walls above the porch roof: a faint lift, no pools
  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 2, alpha: 0.1, scallop: false, clap: true },
  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 2, alpha: 0.1, scallop: false, clap: true },
  // garage front wall (z 29.8) under its eave
  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 6, alpha: 0.75, clap: true },
  // east wall of the main house (x 20.6-20.9) under the side eave
  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 5, alpha: 0.6, clap: true },
  // the porch fascia board itself, lit by its own string
  { a: [-7.6, 12.95, 41.42], b: [20.9, 12.95, 41.42], down: [0, -1, 0], width: 0.55, alpha: 0.5 },
  // ---- soffits: the underside of every overhang, lit from the bulbs hanging
  // just below it -- the "lit interior" of the gables. Strips run inward from
  // the fascia edge, a hair under the roof sheet, and pool under each bulb.
  { a: [-8.2, 26.27, 30.7], b: [1.74, 36.38, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },
  { a: [1.74, 36.38, 30.7], b: [11.67, 26.27, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },
  { a: [2.3, 36.95, 27.9], b: [6.656, 41.39, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },
  { a: [6.656, 41.39, 27.9], b: [21.519, 26.27, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },
  { a: [20.6, 13.0, 30.68], b: [48.0, 13.0, 30.68], down: [0, 0, -1], width: 0.9, alpha: 0.9, soffit: true },
  { a: [21.55, 26.27, 27.9], b: [21.55, 26.27, -12.0], down: [-1, 0, 0], width: 0.95, alpha: 0.8, soffit: true },
  // the porch ceiling's front band (the ceiling plane is at y 12.6)
  { a: [-7.615, 12.55, 41.3], b: [20.928, 12.55, 41.3], down: [0, 0, -1], width: 1.6, alpha: 0.6, soffit: true },
];

'''
s = block(s, "const R2 = Math.SQRT1_2;", "// ----------------------------------------------------------- real lights", NEW_WASHES)

# ------------------------------------------------------------- geometry + shader
NEW_BUILDER = r'''function buildWashGeometry(local) {
  const pos = [], col = [], dist = [], along = [], params = [], idx = [];
  const c = WASH_COLOR;
  for (const w of WASHES) {
    const a = local(w.a), b = local(w.b);
    const down = new THREE.Vector3(...w.down).normalize();
    const len = a.distanceTo(b);
    const segs = Math.max(2, Math.ceil(len / 0.75));
    const rows = 4; // the profile is evaluated per fragment; rows only carry the plane
    const alpha = w.alpha ?? 0.7;
    // pools sit under the bulbs, so the scallop period is the run's real gap
    // (RUNS fits a whole number of gaps into each edge, so it is len / n)
    const spacing = w.scallop === false ? 0 : len / Math.max(1, Math.round(len / LED_SPACING));
    const base = pos.length / 3;
    for (let i = 0; i <= segs; i++) {
      const p = new THREE.Vector3().lerpVectors(a, b, i / segs);
      for (let r = 0; r <= rows; r++) {
        const t = r / rows;
        _v.copy(p).addScaledVector(down, w.width * t);
        if (w.clampY !== undefined && _v.y < w.clampY) _v.y = w.clampY;
        pos.push(_v.x, _v.y, _v.z);
        col.push(c[0], c[1], c[2], alpha);
        dist.push(w.width * t);
        along.push(len * i / segs);
        params.push(w.width, spacing, w.clap ? 1 : 0, w.soffit ? 1 : 0);
      }
    }
    for (let i = 0; i < segs; i++) {
      for (let r = 0; r < rows; r++) {
        const p0 = base + i * (rows + 1) + r;
        const p1 = p0 + rows + 1;
        idx.push(p0, p1, p0 + 1, p0 + 1, p1, p1 + 1);
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 4));
  g.setAttribute('aDist', new THREE.Float32BufferAttribute(dist, 1));
  g.setAttribute('aAlong', new THREE.Float32BufferAttribute(along, 1));
  g.setAttribute('aParams', new THREE.Float32BufferAttribute(params, 4));
  g.setIndex(idx);
  return g;
}

// The wash is what the bulbs put on the house. Per fragment, in feet:
//   profile  -- rises over the first half foot under the edge (the fascia's
//               own shadow), holds for a foot, then falls off as a cube, so
//               the wall is dim grey again by mid-height;
//   pools    -- a gaussian under each bulb along the run, so the fascia and
//               soffit read as a chain of warm pools rather than a strip;
//   courses  -- a shadow line at the foot of every 5 in clapboard course, so
//               the band reads as lit siding and not a glow sheet.
// Additive, premultiplied, tone-mapping bypassed like the halos.
function makeWashMaterial() {
  return new THREE.ShaderMaterial({
    uniforms: { uOpacity: { value: 0 }, uCourse: { value: CLAPBOARD } },
    vertexShader: `
      attribute float aDist; attribute float aAlong; attribute vec4 aParams;
      varying vec4 vColor; varying float vDist; varying float vAlong; varying float vWorldY;
      varying vec4 vParams;
      void main() {
        vColor = color; vDist = aDist; vAlong = aAlong; vParams = aParams;
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vWorldY = wp.y;
        gl_Position = projectionMatrix * viewMatrix * wp;
      }`,
    fragmentShader: `
      uniform float uOpacity; uniform float uCourse;
      varying vec4 vColor; varying float vDist; varying float vAlong; varying float vWorldY;
      varying vec4 vParams;
      void main() {
        float W = vParams.x; float spacing = vParams.y;
        bool soffit = vParams.w > 0.5;
        float d = vDist;
        float band = soffit ? 0.35 : 1.0;
        float rise = soffit ? 1.0 : smoothstep(0.0, 0.45, d);
        float decay = d < band ? 1.0
          : pow(max(0.0, 1.0 - (d - band) / max(0.01, W - band)), soffit ? 1.6 : 3.0);
        float p = rise * decay;
        if (spacing > 0.0) {
          float a = (fract(vAlong / spacing) - 0.5) * spacing;   // ft to the nearest bulb
          float sigma = soffit ? 0.6 : 0.85;
          float pool = exp(-(a * a) / (2.0 * sigma * sigma));
          p *= soffit ? (0.3 + 0.7 * pool) : (0.5 + 0.5 * pool);
        }
        if (vParams.z > 0.5) {
          float f = fract(vWorldY / uCourse);
          p *= 1.0 - 0.5 * (1.0 - smoothstep(0.0, 0.22, f));
        }
        vec3 c = vColor.rgb * (vColor.a * p * uOpacity);
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
}

'''
s = block(s, "function buildWashGeometry(local) {", "// Screen-space halo:", NEW_BUILDER)
open(p, 'w', encoding='utf-8').write(s)

# ------------------------------------------------------------- roomlights: warm exteriors
p = ROOT + r"\frontend\js\roomlights.js"
s = open(p, encoding='utf-8').read()
rep = [
("const EXTERIOR_BASE = 70;\nconst EXTERIOR_RANGE = 34;         // ft",
 "const EXTERIOR_BASE = 70;\nconst EXTERIOR_RANGE = 34;         // ft\n// The coach lamps and floods on the facade are ~3000K in every photograph; a\n// white bulb reports rgb 255,255,255 to HA, which lit them 6500K here.\nconst EXTERIOR_WARM = new THREE.Color(0xffb46b);"),
("    } else if (isExterior(p.owner)) {\n      p.light.color.copy(p.owner.color);",
 "    } else if (isExterior(p.owner)) {\n      p.light.color.copy(p.owner.color).lerp(EXTERIOR_WARM, 0.75);"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
