from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');s=s.replace('idx.push(k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2);','idx.push(k,k+1,k+sides+1,k+1,k+sides+2,k+sides+1);');p.write_text(s,encoding='utf-8')
