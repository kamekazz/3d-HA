from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index("  localItem('shore', 'Rear far bank and woodland', () => {");b=s.index('\n}\n\nfunction addBackYard',a);far=s[a:b]
end='''    const woodland = new THREE.BufferGeometry();
    woodland.setAttribute('position',new THREE.Float32BufferAttribute(farPos,3));
    woodland.setAttribute('color',new THREE.Float32BufferAttribute(farCol,3));
    woodland.setAttribute('uv',new THREE.Float32BufferAttribute(farPos.leafUVs,2));
    woodland.setAttribute('normal',new THREE.Float32BufferAttribute(farPos.leafNormals,3));
    woodland.userData.rearFoliage=true;woodland.userData.rearOakLeaf=true;woodland.userData.rearFarLeaf=true;woodland.userData.rearSingleLeafSurface=true;props.push(woodland);'''
assert end in far
replacement='''    // Release temporary JS Number arrays after each plant. Typed geometry
    // chunks preserve exact vertex order and are merged by the existing bucket;
    // one huge forest accumulator otherwise exceeds the browser's memory peak.
    const flushFarLeaves=()=>{
      if(!farPos.length)return;
      const woodland = new THREE.BufferGeometry();
      woodland.setAttribute('position',new THREE.Float32BufferAttribute(farPos,3));
      woodland.setAttribute('color',new THREE.Float32BufferAttribute(farCol,3));
      woodland.setAttribute('uv',new THREE.Float32BufferAttribute(farPos.leafUVs,2));
      woodland.setAttribute('normal',new THREE.Float32BufferAttribute(farPos.leafNormals,3));
      woodland.userData.rearFoliage=true;woodland.userData.rearOakLeaf=true;woodland.userData.rearFarLeaf=true;woodland.userData.rearSingleLeafSurface=true;props.push(woodland);
      farPos.length=0;farCol.length=0;farPos.leafUVs.length=0;farPos.leafNormals.length=0;
    };'''
far=far.replace(end,'    flushFarLeaves();',1)
far=far.replace('    const farPos=[], farCol=[];', '    const farPos=[], farCol=[];\n'+replacement,1)
far=far.replace('for(let x=lakeX0;x<lakeX1;x+=2.5+rng()*3.7) {','for(let x=lakeX0;x<lakeX1;x+=2.5+rng()*3.7) {\n      flushFarLeaves();',1)
far=far.replace('for(let x=lakeX0;x<lakeX1;x+=4+rng()*5) {','for(let x=lakeX0;x<lakeX1;x+=4+rng()*5) {\n      flushFarLeaves();',1)
far=far.replace('for(let x=lakeX0-12;x<lakeX1+12;x+=7+rng()*7) {','for(let x=lakeX0-12;x<lakeX1+12;x+=7+rng()*7) {\n      flushFarLeaves();',1)
s=s[:a]+far+s[b:];p.write_text(s)
