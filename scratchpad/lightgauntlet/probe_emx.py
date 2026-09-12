"""Per-material proof for windowlight.js: what every tracked object's emissive
actually holds at noon and at midnight, read off the live materials.

  * At noon it asserts BYTE EXACTNESS against `__orig` -- the day claim is
    "this module writes nothing at nightFactor 0", and comparing the materials
    is a stronger statement than diffing a frame, which the renderer only
    reproduces to about 1 sRGB level run to run.
  * At night it prints the emitted linear luminance (lum(emissive) x
    emissiveIntensity) per (object, material), with the module enabled and
    disabled, which is the before/after for one offender.

    python probe_emx.py            # every tracked object
    python probe_emx.py Kitchen    # substring filter on the object name
"""
import json, sys
from playwright.sync_api import sync_playwright

READY = """
async () => {
  const objects = await import('/js/objects.js');
  const roots = [...objects.objects3d.values()];
  return { total: roots.length, loaded: roots.filter(r => r.children.length > 0).length };
}
"""

DUMP = """
async () => {
  const THREE = await import('three');
  const objects = await import('/js/objects.js');
  const lum = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
  const c = new THREE.Color();
  const out = [];
  for (const root of objects.objects3d.values()) {
    const per = new Map();
    root.traverse((ch) => {
      if (!ch.isMesh) return;
      const origs = ch.userData.__orig ||
        (ch.parent?.isMesh ? ch.parent.userData.__orig : null);
      if (!origs) return;
      const mats = Array.isArray(ch.material) ? ch.material : [ch.material];
      mats.forEach((m, i) => {
        const o = origs[i];
        if (!m.emissive || !o || o.emissive === null) return;
        const live = lum(c.setHex(m.emissive.getHex())) * m.emissiveIntensity;
        const auth = lum(c.setHex(o.emissive)) * o.emissiveIntensity;
        const k = m.name || '?';
        const p = per.get(k) || { name: k, live: 0, auth: 0, exact: true };
        p.live = Math.max(p.live, live);
        p.auth = Math.max(p.auth, auth);
        if (m.emissive.getHex() !== o.emissive ||
            m.emissiveIntensity !== o.emissiveIntensity) p.exact = false;
        per.set(k, p);
      });
    });
    if (per.size) out.push({ object: root.userData.name, id: root.userData.objectId,
                             bound: !!root.userData.entityId, mats: [...per.values()] });
  }
  return out;
}
"""

SIM = """
async ({ light, wl }) => {
  const dl = await import('/js/daylight.js');
  window.__windowlight.setEnabled(wl);
  window.__daylight.simulate(light);
  for (let i = 0; i < 400; i++) await new Promise(r => setTimeout(r, 8));
  return { night: window.__windowlight.night() };
}
"""

DAY = {"elevation": 42, "azimuth": 155, "condition": "sunny"}
NIGHT = {"elevation": -18, "azimuth": 0, "condition": "clear-night"}
filt = sys.argv[1] if len(sys.argv) > 1 else ""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    p = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
    p.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    p.wait_for_function("() => !!window.__scene3d", timeout=30000)
    p.wait_for_timeout(4000)
    for _ in range(60):
        st = p.evaluate(READY)
        if st["total"] and st["loaded"] >= st["total"]: break
        p.wait_for_timeout(1000)
    print("objects", st)

    frames = {}
    for tag, light, wl in (("day_on", DAY, True), ("day_off", DAY, False),
                           ("night_off", NIGHT, False), ("night_on", NIGHT, True)):
        print(tag, p.evaluate(SIM, {"light": light, "wl": wl}))
        frames[tag] = p.evaluate(DUMP)
    b.close()

def index(rows):
    return {(r["object"], m["name"]): dict(m, bound=r["bound"]) for r in rows for m in r["mats"]}

day_on, night_on, night_off = index(frames["day_on"]), index(frames["night_on"]), index(frames["night_off"])

bad = [k for k, v in day_on.items() if not v["exact"]]
print("\nDAY: %d (object, material) emissive records live; %d differ from __orig"
      % (len(day_on), len(bad)))
for k in bad[:20]: print("   MISMATCH", k)

print("\nNIGHT emitted linear luminance, module OFF -> ON  (only where it moved)")
print("%-30s %-14s %9s %9s %9s" % ("object", "material", "authored", "before", "after"))
rows = []
for k, v in night_on.items():
    before = night_off.get(k, {}).get("live", 0)
    if abs(before - v["live"]) < 1e-6: continue
    if filt and filt.lower() not in k[0].lower(): continue
    rows.append((before, k[0], k[1], v["auth"], before, v["live"]))
rows.sort(reverse=True)
for _, o, m, auth, before, after in rows:
    print("%-30s %-14s %9.4f %9.4f %9.4f" % (o[:30], m[:14], auth, before, after))
print(len(rows), "materials moved")
