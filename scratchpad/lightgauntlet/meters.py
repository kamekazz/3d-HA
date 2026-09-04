import json, sys
for p in sys.argv[1:]:
    t = open(p).read()
    d = json.loads(t[t.index('{'):])
    o, f = d['on']['meter'], d['off']['meter']
    print('%-34s night=%-6s ON mean=%-6s centre=%-6s p95=%-5s | OFF mean=%-6s centre=%-6s p95=%-5s'
          % (p.split('/')[-1].replace('.json',''), d['off']['night'],
             o['mean'], o['centre'], o['p95'], f['mean'], f['centre'], f['p95']))
