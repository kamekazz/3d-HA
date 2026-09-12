from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');a=s.index('function addRearLakeDetail');b=s.index('\nfunction addBackYard',a);v=s[a:b]
needle='''    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));'''
insert='''    // Broad lateral crowns reach back over the bank. Unequal crown heights
    // and drooping outside shoots leave scalloped water/sky openings beneath.
    for(let b=0;b<3;b++) {
      const spread=(b-1)*4.8+(rng()-.5)*3;
      const end=[x+spread,y+9.5+rng()*7,z+1+(rng()-.5)*5];
      const origin=[x+lean*.37,y+height*.37,z];
      branch([origin,[(origin[0]+end[0])*.5,end[1]+1,(z+end[2])*.5],end],radius*.22,.025,masses);
      leafCloud(...end,4.5+rng()*1.7,2.7+rng()*1.7,3.2+rng(),1000,pos,col,.51);
    }
'''
assert needle in v;v=v.replace(needle,insert+needle,1)
# distant leaf packets use a smaller, double-sided lens to bound the draw cost
v=v.replace('for(let edge=0;edge<6;edge++)for(const k of [edge,(edge+1)%6,6,6,(edge+1)%6,edge]) {','''const indices=scale>1?[0,2,3,0,3,5,3,2,0,5,3,0]:Array.from({length:6},(_,edge)=>[edge,(edge+1)%6,6,6,(edge+1)%6,edge]).flat();
        for(const k of indices) {''')
v=v.replace('4.5,300,farPos,farCol,1.4','4.5,1100,farPos,farCol,2.4')
s=s[:a]+v+s[b:];p.write_text(s,encoding='utf-8')
