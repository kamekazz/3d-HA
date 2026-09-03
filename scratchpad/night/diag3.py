import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from roomkit.shot import SETUP_JS, load_poses
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const THREE = await import('three');
  const { scene, camera, renderer } = window.__scene3d;
  let drive = null; scene.traverse((o) => { if (o.name === 'eaveLight:drive') drive = o; });
  const gl = renderer.getContext();
  const W = gl.drawingBufferWidth, H = gl.drawingBufferHeight;
  const pts = { drive_L_800: [440, 800], drive_R_780: [800, 780], drive_L_1000: [450, 1000], drive_R_900: [820, 900], walk_720: [420, 720], lawn_820: [200, 820] };
  const read = () => { renderer.render(scene, camera); const o = {}; for (const [k, [x, y]] of Object.entries(pts)) { const b = new Uint8Array(4); gl.readPixels(x, H - y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, b); o[k] = b[0]; } return o; };
  const out = {};
  const i0 = drive.intensity; out['drive ' + i0.toFixed(0)] = read();
  drive.intensity = 0; out['drive 0'] = read();
  drive.intensity = 3000; out['drive 3000'] = read();
  drive.intensity = i0;
  const pl = new THREE.PointLight(0xffd2a0, 380, 0, 2); pl.position.set(33, 12.6, 33); scene.add(pl); out['+point 380 at spot pos'] = read(); scene.remove(pl);
  // what surface is under the drive pixels?
  const rc = new THREE.Raycaster(); rc.setFromCamera(new THREE.Vector2(440 / W * 2 - 1, -(800 / H * 2 - 1)), camera);
  const hs = rc.intersectObjects(scene.children, true).filter(h => { let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; } return true; }).slice(0, 3);
  out.under_L_800 = hs.map(h => ({ name: h.object.name, root: (() => { let o = h.object; while (o.parent && o.parent !== scene) o = o.parent; return o.name; })(), pt: h.point.toArray().map(v => +v.toFixed(2)), mat: h.object.material?.type, col: h.object.material?.color?.getHexString(), vc: h.object.material?.vertexColors }));
  const t = new THREE.Vector3(); drive.target.getWorldPosition(t); const p = new THREE.Vector3(); drive.getWorldPosition(p);
  out.spot = { pos: p.toArray(), target: t.toArray(), angle: drive.angle, penumbra: drive.penumbra, distance: drive.distance, decay: drive.decay };
  out.cam = camera.position.toArray().map(v => +v.toFixed(1));
  return out;
}
"""
pose = load_poses()["night_front"]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    pg = b.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=1)
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(2500)
    args = {"pose": pose, "level": "all", "light": {"elevation": -18, "azimuth": 0, "condition": "clear-night"}, "markers": False, "cutaway": True}
    pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(3000); pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(500)
    print(json.dumps(pg.evaluate(JS), indent=1)); b.close()
