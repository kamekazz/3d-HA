from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index('function addRearLakeDetail(');b=s.index('\nfunction addBackYard(',a);f=s[a:b]
f=f.replace("    const g=new THREE.BufferGeometry();\n    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));", """    // Drooping boughs extend over the water, where their canopy closes the
    // overhead skyline without placing foliage in the camera's walking space.
    for(let b=0;b<3;b++) {
      const end=[x+(b-1)*4.5,y+7.5+rng()*3,z-7-rng()*5];
      limb([x+lean*.3,y+height*.34,z],end,radius*.13,.025,0x404639,masses);
      leafCloud(...end,5.4,2.8,3.4,1800,pos,col,.48);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));""")
# Build the main stem as one continuous, tapered ring mesh: separate capped
# cylinders left black horizontal seams at each change of lean.
old='    for(let i=0;i<4;i++)limb(spine[i],spine[i+1],radius*(1-i*.2),radius*(.8-i*.19),0x45453d,masses);'
new='''    const leader=new THREE.CatmullRomCurve3(spine),stemPos=[],stemUv=[],stemIdx=[];
    for(let ring=0;ring<=28;ring++) {
      const t=ring/28,c=leader.getPoint(t),r=radius*(1-t*.82);
      for(let j=0;j<=36;j++) {
        const angle=j*Math.PI*2/36,relief=1+.035*Math.sin(angle*13+t*5)+.022*Math.sin(angle*23-t*9);
        stemPos.push(c.x+Math.cos(angle)*r*relief,c.y,c.z+Math.sin(angle)*r*relief);stemUv.push(j/36,t*8);
        if(ring<28&&j<36){const k=ring*37+j;stemIdx.push(k,k+37,k+1,k+1,k+37,k+38);}
      }
    }
    const stem=new THREE.BufferGeometry();stem.setAttribute('position',new THREE.Float32BufferAttribute(stemPos,3));
    stem.setAttribute('uv',new THREE.Float32BufferAttribute(stemUv,2));stem.setIndex(stemIdx);stem.computeVertexNormals();
    paintNoisy(stem,color(0x45453d),rng,.33);masses.push(stem);'''
f=f.replace(old,new)
p.write_text(s[:a]+f+s[b:])
