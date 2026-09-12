from pathlib import Path
p=Path('frontend/js/environment.js')
s=p.read_text(); a=s.index('function addRearLakeDetail('); b=s.index('\nfunction addBackYard(',a); f=s[a:b]
f=f.replace('const bedY = L.lo + 0.32;', 'const bedY = L.lo + 0.72;')
f=f.replace('    addBedPoly(rng, [...edgePts, ...backPts.reverse()], bedY, beds, 1.9, [], 0.14, true);\n    // A mixed two-stone rim sits in the grass, rather than a straight curb.\n    addCobbleRun(rng, edgePts, bedY - 0.035, beds, 0.7);\n    addCobbleRun(rng, edgePts.map(([x,z]) => [x,z-0.43]), bedY - 0.025, beds, 0.63);', '''    // Fine mixed aggregate has its own repeating material; the front gravel
    // material and its UV scale are untouched. Raised individual pebbles catch
    // light over a dense, shaded stone matrix at approximately one-inch scale.
    const canvas=document.createElement('canvas'); canvas.width=canvas.height=1024;
    const ctx=canvas.getContext('2d'); ctx.fillStyle='#696964';ctx.fillRect(0,0,1024,1024);
    for(let i=0;i<29000;i++) {
      const x=rng()*1024,z=rng()*1024,r=1.4+rng()*4.5,shade=90+rng()*88;
      ctx.fillStyle=`rgb(${shade+4},${shade+3},${shade})`;
      ctx.beginPath();ctx.ellipse(x,z,r,r*(.45+rng()*.4),rng()*6.28,0,Math.PI*2);ctx.fill();
      ctx.strokeStyle='rgba(45,44,38,.35)';ctx.lineWidth=.8;ctx.stroke();
    }
    const aggregate=new THREE.CanvasTexture(canvas); aggregate.colorSpace=THREE.SRGBColorSpace;
    aggregate.wrapS=aggregate.wrapT=THREE.RepeatWrapping; aggregate.anisotropy=8;
    const mat=new THREE.MeshStandardMaterial({map:aggregate,bumpMap:aggregate,bumpScale:.025,roughness:1,color:0xb8b6af});
    mat.addEventListener('dispose',()=>aggregate.dispose());
    const gravel=new THREE.Mesh(ribbon(nearX0,nearX1,lawnEdge,x=>shore(x)+2.6,bedY,bedY-.18,180),mat);
    gravel.name='rear-shore-fine-gravel';gravel.receiveShadow=true;gravel.userData.ownGeometry=true;yard.add(gravel);
    for(let x=nearX0;x<nearX1;x+=.24+rng()*.16)for(let row=0;row<2;row++) {
      const r=.10+rng()*.13,g=new THREE.IcosahedronGeometry(r,1);
      g.scale(.8+rng()*.6,.45+rng()*.3,.75+rng()*.45);
      g.rotateY(rng()*6.28);g.translate(x+(rng()-.5)*.2,bedY-.02,lawnEdge(x)-row*.29+(rng()-.5)*.24);
      const tint=new THREE.Color().setHSL(.08+rng()*.09,.04+rng()*.17,.32+rng()*.27,THREE.SRGBColorSpace);
      paintNoisy(g,tint,rng,.17);beds.push(g);
    }''')
f=f.replace('r0 > 0.3 ? 16 : 9, 5','r0 > 0.3 ? 26 : 10, 8')
start=f.index('  const matureTree = ');end=f.index("\n  localItem('shore', 'Rear far bank",start)
f=f[:start]+'''  const matureTree = (x, z, radius, height, lean) => localItem('tree', 'Rear mature broadleaf', () => {
    const y=bedY-.20,pos=[],col=[];
    // A continuous bent leader remains visible above secondary branch joins.
    const spine=Array.from({length:5},(_,i)=>[x+lean*i/4+Math.sin(i*1.7)*radius*.4,y+height*i/4,z+Math.sin(i*1.1)*.6]);
    for(let i=0;i<4;i++)limb(spine[i],spine[i+1],radius*(1-i*.2),radius*(.8-i*.19),0x45453d,masses);
    for(let i=0;i<6;i++) {
      const ang=rng()*6.28;
      limb([x,y+.28,z],[x+Math.cos(ang)*radius*2.2,y-.06,z+Math.sin(ang)*radius*2.2],radius*.20,.025,0x49483e,masses);
    }
    for(let b=0;b<11;b++) {
      const angle=b*2.399+rng()*.8,join=.22+rng()*.46;
      const origin=[x+lean*join,y+height*join,z+Math.sin(join*4)*.5];
      const reach=4+rng()*7;
      const tip=[origin[0]+Math.cos(angle)*reach,origin[1]+2+rng()*5,origin[2]+Math.sin(angle)*reach];
      const bend=origin.map((v,i)=>(v+tip[i])*.5+(i===1?-.4:(rng()-.5)*1.1));
      limb(origin,bend,radius*(.20+rng()*.2),radius*.14,0x44483c,masses);
      limb(bend,tip,radius*.14,.045,0x414639,masses);
      for(let t=0;t<4;t++) {
        const ta=angle+(t-1.5)*.75;
        const end=[tip[0]+Math.cos(ta)*(2+rng()*2),tip[1]+(rng()-.4)*3,tip[2]+Math.sin(ta)*(2+rng()*2)];
        limb(tip,end,.055,.014,0x3e4437,masses);
        leafCloud(...end,3.5,2.4,3.2,210,pos,col,.78);
      }
    }
    // Low irregular boughs toward the western woodland obscure the left-hand
    // water; the eastern opening stays broad as in photographs 05 and 11.
    if(x<mid+2)for(let b=0;b<5;b++) {
      const cx=x+(rng()-.5)*10,cy=y+4+rng()*5,cz=z-1-rng()*5;
      leafCloud(cx,cy,cz,4.3,3.2,3.8,700,pos,col,.9);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(pos.length/3*2),2));
    g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);
  });
  // Unequal gaps, diameters, lean and bank offsets follow the multiple reference
  // views: old trunks west, a thin central group, and two larger eastern trees.
  for(const [offset,r,h,lean,dz] of [[-48,.65,30,-1.2,-1],[-36,.85,31,.8,1],[-27,.50,29,-1.1,-2],
      [-19,.72,33,-1.7,2.5],[-13,.62,31,-.8,2],[-7,.33,30,.7,-1],[-1,.18,28,.2,1],
      [2,.16,29,-.5,.5],[8,.35,31,.9,-.4],[16,.67,35,1.5,1.4],[21,.5,33,1.7,-1.5],
      [31,.75,34,-.8,.4],[44,.7,31,.4,-2]]) {
    const x=mid+offset;matureTree(x,shore(x)+2.5+dz,r,h,lean);
  }
''' + f[end:]
f=f.replace('4.5,4.0,3.5,140,farPos,farCol,3.1','5.7,4.4,4.5,500,farPos,farCol,1.4')
p.write_text(s[:a]+f+s[b:])
