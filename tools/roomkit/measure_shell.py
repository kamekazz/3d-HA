"""Measure the whole-house shell GLB's footprint in world feet.

The shell is a model of the REAL house, so its bounding box is the one piece of
true-scale ground truth we have. The traced room footprints were drawn by hand
and two builders measured them as too deep; this is what to re-trace against.

Reports the shell's world-space bbox alongside the traced rooms' bbox per floor,
so the discrepancy is visible in one place.

    python -m roomkit.measure_shell
"""

import json
import os

from playwright.sync_api import sync_playwright

BASE = os.environ.get("ROOMKIT_BASE", "http://127.0.0.1:5000")

JS = """
async () => {
  const THREE = await import('three');
  const house = await import('/js/house.js');

  house.setLevel('all');                      // House mode loads/shows the shell
  for (let i = 0; i < 80; i++) {
    if (house.getShellRoot()) break;
    await new Promise(r => setTimeout(r, 250));
  }
  const shell = house.getShellRoot();
  if (!shell) return { error: 'shell never loaded' };

  const box = new THREE.Box3().setFromObject(shell);
  const size = box.getSize(new THREE.Vector3());
  const c = box.getCenter(new THREE.Vector3());

  // Flat hardscape (driveway, patio) drags the bbox out; measure the built
  // mass separately by ignoring meshes under 3 ft tall, the same rule
  // environment.js uses to find the house footprint.
  const tall = new THREE.Box3();
  shell.traverse((o) => {
    if (!o.isMesh) return;
    const b = new THREE.Box3().setFromObject(o);
    if (b.max.y - b.min.y >= 3.0) tall.union(b);
  });
  const ts = tall.getSize(new THREE.Vector3());

  return {
    shell_all: { x: [+box.min.x.toFixed(2), +box.max.x.toFixed(2)],
                 z: [+box.min.z.toFixed(2), +box.max.z.toFixed(2)],
                 y: [+box.min.y.toFixed(2), +box.max.y.toFixed(2)],
                 size: [+size.x.toFixed(2), +size.y.toFixed(2), +size.z.toFixed(2)],
                 center: [+c.x.toFixed(2), +c.z.toFixed(2)] },
    shell_built_mass: { x: [+tall.min.x.toFixed(2), +tall.max.x.toFixed(2)],
                        z: [+tall.min.z.toFixed(2), +tall.max.z.toFixed(2)],
                        size: [+ts.x.toFixed(2), +ts.y.toFixed(2), +ts.z.toFixed(2)] },
    config: house.getShellConfig(),
  };
}
"""


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=[
            "--use-gl=angle", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 900, "height": 700})
        page.goto(BASE, wait_until="load", timeout=60000)
        page.wait_for_function("() => !!window.__scene3d", timeout=30000)
        page.wait_for_timeout(3000)
        res = page.evaluate(JS)
        browser.close()
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
