import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from roomkit.shot import SETUP_JS, load_poses
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const THREE = await import('three');
  const { scene } = window.__scene3d;
  const out = { debug: window.__eavelights?.debug(), spots: [], drive: null, night: window.__daylight?.state().current.nightFactor };
  scene.updateMatrixWorld(true);
  scene.traverse((o) => {
    if (o.isSpotLight) {
      const p = new THREE.Vector3(); o.getWorldPosition(p);
      const t = new THREE.Vector3(); o.target.getWorldPosition(t);
      out.spots.push({ name: o.name, intensity: o.intensity, pos: p.toArray().map(v => +v.toFixed(1)), target: t.toArray().map(v => +v.toFixed(1)), angle: o.angle, distance: o.distance, decay: o.decay, targetInScene: !!o.target.parent, visible: o.visible });
    }
  });
  const rc = new THREE.Raycaster(new THREE.Vector3(33, 20, 50), new THREE.Vector3(0, -1, 0));
  const h = rc.intersectObjects(scene.children, true).filter(x => x.object.visible)[0];
  if (h) { const m = h.object.material; out.drive = { name: h.object.name, y: +h.point.y.toFixed(2), type: m.type, color: m.color?.getHexString(), emissive: m.emissive?.getHexString(), emissiveIntensity: m.emissiveIntensity, vertexColors: m.vertexColors, roughness: m.roughness, envMapIntensity: m.envMapIntensity }; }
  return out;
}
"""
pose = load_poses()["night_front"]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    pg = b.new_page(viewport={"width": 900, "height": 1200})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type in ("error", "warning") else None)
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(2500)
    args = {"pose": pose, "level": "all", "light": {"elevation": -18, "azimuth": 0, "condition": "clear-night"}, "markers": False, "cutaway": True}
    pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(3000)
    print(json.dumps(pg.evaluate(JS), indent=1)); print("errors:", errs[:8]); b.close()
