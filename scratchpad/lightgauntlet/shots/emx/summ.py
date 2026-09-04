import json,glob,sys
def load(f):
    s=open(f).read(); return json.loads(s[s.index('{'):])
for f in sorted(glob.glob(sys.argv[1] if len(sys.argv)>1 else '*.json')):
    try: d=load(f)
    except Exception as e: print(f,'ERR',e); continue
    on,off=d['on'],d['off']; mo,mf=on['meter'],off['meter']
    print('%-20s ON mean=%6.1f ctr=%6.1f p95=%5.1f | OFF mean=%6.1f ctr=%6.1f p95=%5.1f | ctr ratio=%5.2f | off slots=%d | at %s / %s' % (
        f, mo['mean'],mo['centre'],mo['p95'], mf['mean'],mf['centre'],mf['p95'],
        mo['centre']/max(mf['centre'],1e-9), len(off['slots']), on['at'], off['at']))
