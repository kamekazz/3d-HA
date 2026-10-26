(async () => {
  const THREE = await import('three');
  const env = window.__scene3d.scene.getObjectByName('environment');
  const out = [];
  const b = new THREE.Box3();
  const mats = new Map();
  for (const root of env.children) {
    const list = root.isGroup && !root.userData?.kind ? root.children : [root];
    for (const o of list) {
      b.setFromObject(o);
      let verts = 0, meshes = 0; const ms = new Set();
      o.traverse(m => { if (m.isMesh || m.isPoints || m.isLineSegments) { meshes++; verts += m.geometry?.attributes?.position?.count || 0; for (const mm of [].concat(m.material)) ms.add(mm?.type + ':' + (mm?.name || '') + ':' + (mm?.uuid||'').slice(0,4)); } });
      out.push({ name: o.name, kind: o.userData?.kind, yk: o.userData?.yardKind, key: o.userData?.yardKey,
        vis: o.visible, verts, meshes, box: b.isEmpty() ? null : [b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z].map(v => Math.round(v)), mats: [...ms].slice(0, 4) });
    }
  }
  return out;
})()
