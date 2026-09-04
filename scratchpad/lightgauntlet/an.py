import json,sys
sys.path.insert(0,'.')
from probe2 import series,stats
d=json.load(sys.stdin)
for e in d:
    f=e['file']
    print('fix %g fill %g slab %g'%(e['fixture'],e['fill'],e['slab']), stats(f))
    print('   wall .10-.18', series(f,.10,.18,.05,.95,9))
    print('   mid  .40-.48', series(f,.40,.48,.05,.95,9))
    print('   floor.75-.85', series(f,.75,.85,.05,.95,9))
