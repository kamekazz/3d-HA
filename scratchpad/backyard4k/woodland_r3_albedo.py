from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');a=s.index('function addRearLakeDetail');b=s.index('\nfunction addBackYard',a);v=s[a:b];v=v.replace('luminance=.185+rng()*.055','luminance=.265+rng()*.055');s=s[:a]+v+s[b:];p.write_text(s,encoding='utf-8')
