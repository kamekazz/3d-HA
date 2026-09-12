from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index('function addRearLakeDetail(');b=s.index('\nfunction addBackYard(',a);f=s[a:b]
f=f.replace('join=.22+rng()*.46','join=.29+rng()*.46')
f=f.replace('3.5,2.4,3.2,210,pos,col,.78','3.5,2.4,3.2,340,pos,col,.47')
f=f.replace('if(x<mid+2)for(let b=0;b<5;b++)','if(x<mid-8)for(let b=0;b<5;b++)')
f=f.replace('cy=y+4+rng()*5','cy=y+7+rng()*5')
f=f.replace('4.3,3.2,3.8,700,pos,col,.9','4.3,3.2,3.8,1100,pos,col,.48')
# Narrower leaves have six perimeter points and a raised midrib, rather than a broad diamond.
f=f.replace('[[ -size', '[[-size')
f=f.replace("const verts = [[-size,0,0],[0,size*0.15,size*0.57],[size,0,0],[0,-size*0.12,-size*0.57]]", "const verts = [[-size,0,0],[0,size*0.12,size*0.36],[size,0,0],[0,-size*0.08,-size*0.36]]")
p.write_text(s[:a]+f+s[b:])
