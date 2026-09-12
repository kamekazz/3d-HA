from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index('    // At this distance crown interiors supply opaque');b=s.index('    // Low, broken water-edge scrub',a);s=s[:a]+s[b:];s=s.replace('        farCore(...tip,width*.64,crownY,width*.58);\n','',1);s=s.replace('rank===0?750:1050,farPos,farCol,rank===0?1.0:1.3)', 'rank===0?1600:2400,farPos,farCol,rank===0?1.0:1.3)',1)
s=s.replace('rearFarOakMat = null, rearFarVolumeMat = null;', 'rearFarOakMat = null;',1)
a=s.index('        const volumes=selected.filter(g=>g.userData?.rearFarVolume);');b=s.index("        leafMesh.name=distant?'rear-distant-oak-leaves'",a)
s=s[:a]+"        const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(selected),false),mat);\n"+s[b:]
p.write_text(s)
