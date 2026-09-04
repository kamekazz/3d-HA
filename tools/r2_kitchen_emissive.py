"""Why the Kitchen's UNLIT frame meters 47 when the Living Room's meters 3.

roomkit.emissive_audit says the kitchen cabinetry carries emissive on its own
materials -- `white` 0.178, `trim` 0.153, `whitelo` 0.093 -- over ~1000 sq ft of
cabinet face across models 40/65/66/69. Those are vertical surfaces pointed at
the camera, unlike the ceilings that carry the same trick everywhere else and
are cut away. This shoots the room with its lights OFF twice, the second time
with that emissive zeroed in the page, and meters the pair. Nothing is written.
"""
import json
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")
OUT = "../scratchpad/lightgauntlet/shots/kitchen_emissive"

SETUP = """
async ({ roomId, level, entityIds }) => {
  const house = await import('/js/house.js');
  const focus = await import('/js/focus.js');
  const state = await import('/js/state.js');
  const { camera, controls, renderer, scene } = window.__scene3d;
  if (focus.getFocusedRoomId() === roomId) focus.exitFocus({ flyBack: false });
  house.setLevel(level);
  await new Promise(r => setTimeout(r, 900));
  window.__daylight?.simulate({ elevation: -18, azimuth: 0, condition: 'clear-night' });
  for (const id of entityIds) {
    state.applyState(id, { entity_id: id, state: 'off', attributes: { brightness: null } });
  }
  focus.enterFocus(roomId, { frame: false });
  await new Promise(r => setTimeout(r, 700));
  const THREE = await import('three');
  const mesh = house.roomMeshes.get(roomId);
  const box = new THREE.Box3().setFromObject(mesh);
  const c = box.getCenter(new THREE.Vector3());
  const s = box.getSize(new THREE.Vector3());
  const sceneMod = await import('/js/scene.js');
  controls.enableDamping = false;
  camera.clearViewOffset();
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.fov = 70; camera.near = 0.05; camera.updateProjectionMatrix();
  const P = { x: c.x, y: box.min.y + 5.0, z: c.z + s.z * 0.34 };
  const T = { x: c.x, y: box.min.y + 3.6, z: c.z - s.z * 0.4 };
  sceneMod.flyTo(P, T);
  for (let i = 0; i < 200; i++) { await new Promise(r => requestAnimationFrame(r)); }
  camera.position.set(P.x, P.y, P.z); controls.target.set(T.x, T.y, T.z);
  camera.lookAt(T.x, T.y, T.z);
  for (const el of document.querySelectorAll('body > *:not(#scene-container)')) el.style.display = 'none';
  window.__cutaway?.setEnabled(true); window.__cutaway?.settle();
  for (const id of entityIds) {
    state.applyState(id, { entity_id: id, state: 'off', attributes: { brightness: null } });
  }
  camera.updateProjectionMatrix();
  renderer.render(scene, camera);
  return true;
}
"""

# Zero the emissive on the room's own big surfaces, in the page only.
KILL = """
async (roomId) => {
  const objects = await import('/js/objects.js');
  const house = await import('/js/house.js');
  const { camera, renderer, scene } = window.__scene3d;
  const hits = [];
  for (const [id, root] of objects.objects3d) {
    if (root.userData.roomId !== undefined && root.userData.roomId !== roomId) continue;
    root.traverse((c) => {
      if (!c.isMesh) return;
      const mats = Array.isArray(c.material) ? c.material : [c.material];
      for (const m of mats) {
        if (!m || !m.emissive) continue;
        const lum = m.emissive.r * .3 + m.emissive.g * .59 + m.emissive.b * .11;
        if (lum * (m.emissiveIntensity ?? 1) < 0.005) continue;
        hits.push((m.name || '?') + ' ' + lum.toFixed(3));
        m.emissive.setRGB(0, 0, 0);
        m.needsUpdate = true;
      }
    });
  }
  renderer.render(scene, camera);
  return hits.slice(0, 40);
}
"""


def meter(path):
    from PIL import Image
    im = Image.open(path).convert("L")
    w, h = im.size
    full = list(im.getdata())
    box = im.crop((int(w * .2), int(h * .2), int(w * .8), int(h * .8)))
    bd = list(box.getdata())
    return {"mean": round(sum(full) / len(full), 1),
            "centre": round(sum(bd) / len(bd), 1),
            "p95": sorted(full)[int(len(full) * .95)]}


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader", "--hide-scrollbars"])
        page = b.new_page(viewport={"width": 1000, "height": 750}, device_scale_factor=1)
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout=None if False else page.wait_for_timeout
        page.wait_for_timeout(6000)
        ids = page.evaluate("""async (r) => {
            const rl = await import('/js/roomlights.js');
            const ids = new Set([...rl.getRoomLightIds(r)]);
            for (const f of (window.__roomlights?.fixtures() || [])) if (f.roomId === r) ids.add(f.entityId);
            return [...ids]; }""", 6)
        arg = {"roomId": 6, "level": 1, "entityIds": ids}
        page.evaluate(SETUP, arg)
        page.wait_for_timeout(1500)
        page.evaluate(SETUP, arg)
        page.wait_for_timeout(400)
        page.screenshot(path=OUT + "_with.png")
        hits = page.evaluate(KILL, 6)
        page.wait_for_timeout(400)
        page.screenshot(path=OUT + "_without.png")
        b.close()
    print(json.dumps({"entities": ids, "emissive_materials_zeroed": hits,
                      "off_with_emissive": meter(OUT + "_with.png"),
                      "off_without_emissive": meter(OUT + "_without.png")}, indent=2))


if __name__ == "__main__":
    main()
