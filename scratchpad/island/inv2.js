(async () => {
  const THREE = await import('three');
  const env = window.__scene3d.scene.getObjectByName('environment');
  const out = []; const b = new THREE.Box3();
  env.traverse(o => { if (o.parent && (o.userData?.yardKey || o.name) && o.visible) { b.setFromObject(o); if (!b.isEmpty() && b.max.z > 70 && b.min.y > -3 && b.max.y < 3) out.push({ n: o.name || o.userData.yardKey, k: o.userData?.yardKind, box: [b.min.x, b.min.z, b.max.x, b.max.z, b.max.y].map(v => +v.toFixed(1)) }); } });
  return out;
})()
