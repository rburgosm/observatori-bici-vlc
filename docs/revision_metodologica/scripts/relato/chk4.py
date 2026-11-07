_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json
P=_ROOT+'/web/proto/datos/'
s=open(P+'observatori.js').read(); s=s[s.index('=')+1:].strip().rstrip(';'); O=json.loads(s)
n=O['negros']; print(len(n), 'keys:', list(n[0].keys()))
for x in n: print(x['nom'][:40], x.get('n'), x.get('pista'), x.get('k'), x.get('pl'), x.get('tres'))
print('ciudad k', O['ciudad']['k'])
print(O['kpi'].get('pl3'), O['kpi'].get('amb_solo'))
