from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');a=s.index('function addRearLakeDetail');b=s.index('\nfunction addBackYard',a);v=s[a:b]
v=v.replace('y+9.5+rng()*7,z+1+(rng()-.5)*5','y+8.2+rng()*5.2,z+1+(rng()-.5)*5')
v=v.replace('const origin=[x+lean*.37,y+height*.37,z];','const origin=[x+lean*.27,y+height*(.20+rng()*.10),z];')
v=v.replace('4.5+rng()*1.7,2.7+rng()*1.7,3.2+rng(),1000,pos,col,.51','4.5+rng()*2.4,2.5+rng()*1.9,3.2+rng(),1900,pos,col,.45')
s=s[:a]+v+s[b:];p.write_text(s,encoding='utf-8')
