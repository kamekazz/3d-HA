import json, sys, os
for p in sorted(sys.argv[1:]):
    t = open(p, encoding='utf-8', errors='replace').read()
    i = t.find('{\n  "room"')
    if i < 0: print(p, "NO JSON:", t[:120].replace('\n',' ')); continue
    d = json.loads(t[i:])
    o, f = d['on']['meter'], d['off']['meter']
    print('%-30s night=%-6s ON mean=%-6s centre=%-6s p95=%-5s | OFF mean=%-6s centre=%-6s p95=%-5s at=%s'
          % (os.path.basename(p).replace('.json',''), d['off']['night'],
             o['mean'], o['centre'], o['p95'], f['mean'], f['centre'], f['p95'], d['off']['at']))
