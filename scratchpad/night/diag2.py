import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from roomkit.shot import SETUP_JS, load_poses
from playwright.sync_api import sync_playwright
JS = """
async () => {
  const THREE = await import('three');
  const { scene, camera, renderer } = window.__scene3d;
  let drive = null, porch = null;
  scene.traverse((o) => { if (o.name === 'eaveLight:drive') drive = o; if (!porch && o.name === 'eaveLight:porch') porch = o; });
  const gl = renderer.getContext();
  const px = (wx, wy, wz) => {
    const v = new THREE.Vector3(wx, wy, wz).project(camera);
    const x = Math.round((v.x * 0.5 + 0.5) * gl.drawingBufferWidth), y = Math.round((v.y * 0.5 + 0.5) * gl.drawingBufferHeight);
    const buf = new Uint8Array(4); gl.readPixels(x, y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, buf); return [x, y, buf[0], buf[1], buf[2]];
  };
  const shot = (label) => { renderer.render(scene, camera); return { label, drive45: px(33, 0.3, 45), drive60: px(30, 0.3, 62), walk: px(15, 0.3, 50) }; };
  const out = [];
  const i0 = drive.intensity;
  out.push(shot('as-is drive=' + i0.toFixed(0)));
  drive.intensity = 0; out.push(shot('drive off'));
  drive.intensity = 3000; out.push(shot('drive 3000'));
  drive.intensity = i0; drive.angle = Math.PI / 2 - 0.01; out.push(shot('drive angle 89deg'));
  drive.angle = 1.0;
  const p0 = porch.intensity; porch.intensity = 0; out.push(shot('porch off')); porch.intensity = p0;
  // brute-force: a fresh spot added now
  const s = new THREE.SpotLight(0xffffff, 3000, 0, 1.0, 0.4, 2); s.position.set(33, 12.6, 33); s.target.position.set(33, 0, 58); scene.add(s); scene.add(s.target);
  out.push(shot('extra fresh spot 3000'));
  scene.remove(s); scene.remove(s.target);
  const pl = new THREE.PointLight(0xffffff, 300, 0, 2); pl.position.set(33, 12.6, 40); scene.add(pl); out.push(shot('extra point 300')); scene.remove(pl);
  return { out, numSpots: scene.children.filter(o => o.isSpotLight).length, rendererInfo: renderer.info.render };
}
"""
pose = load_poses()["night_front"]
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
    pg = b.new_page(viewport={"width": 900, "height": 1200})
    pg.goto("http://127.0.0.1:5000", wait_until="load", timeout=60000)
    pg.wait_for_function("() => !!window.__scene3d", timeout=30000); pg.wait_for_timeout(2500)
    args = {"pose": pose, "level": "all", "light": {"elevation": -18, "azimuth": 0, "condition": "clear-night"}, "markers": False, "cutaway": True}
    pg.evaluate(SETUP_JS, args); pg.wait_for_timeout(3000)
    print(json.dumps(pg.evaluate(JS), indent=1)); b.close()
