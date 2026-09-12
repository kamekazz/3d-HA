from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text()
s=s.replace("    const clusterCount=Math.ceil(count/28); positions.leafNormals ||= [];\n    const indices=[0,1,6,1,2,6,2,3,6,3,4,6,4,5,6,5,0,6];", "    if(scale<=1)count=Math.ceil(count*1.25);\n    const clusterCount=Math.ceil(count/28); positions.leafNormals ||= [];\n    const edges=scale<=1?8:6;\n    const indices=Array.from({length:edges},(_,i)=>[i,(i+1)%edges,edges]).flat();",1)
s=s.replace("const size=(.25+rng()*.18)*scale;", "const size=(.25+rng()*.18)*scale*(scale<=1?.78:1);",1)
s=s.replace("const local=[[-size,0,0],[-size*.47,-size*.09,size*.42],[size*.28,-size*.10,size*.45],\n          [size,0,0],[size*.28,-size*.08,-size*.45],[-size*.47,-size*.06,-size*.42],[0,size*.105,0]];", "const local=scale<=1?[[-size,0,0],[-size*.66,-size*.06,size*.30],[-size*.13,-size*.08,size*.45],\n          [size*.52,-size*.07,size*.33],[size,0,0],[size*.52,-size*.08,-size*.33],\n          [-size*.13,-size*.09,-size*.45],[-size*.66,-size*.06,-size*.30],[0,size*.105,0]]\n          :[[-size,0,0],[-size*.47,-size*.09,size*.42],[size*.28,-size*.10,size*.45],\n          [size,0,0],[size*.28,-size*.08,-size*.45],[-size*.47,-size*.06,-size*.42],[0,size*.105,0]];",1)
s=s.replace("const light=k===6?1.06:1;colors.push", "const light=k===edges?1.06:1;colors.push",1)
needle="    // The western side has low branches and a thick shaded understory; the"
new="""    // North-reaching secondary boughs create several depths at the water
    // window, with drooping tips below the main crown's higher scallops.
    if(radius>.58)for(let b=0;b<2;b++) {
      const end=[x+(b?1:-1)*(4+rng()*3),y+8.3+rng()*2.6,z-6-rng()*4];
      const origin=[x+lean*.4,y+height*.40,z];
      branch([origin,[(x+end[0])*.5,end[1]+3.5,z-4],end],radius*.26,.018,masses);
      leafCloud(...end,4.4,3.3,3.5,1700,pos,col,.86);
    }
"""+needle
s=s.replace(needle,new,1)
s=s.replace('one six-triangle surface','one curved surface',1)
p.write_text(s)
