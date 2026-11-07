_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json,sys
P=_ROOT+'/web/proto/datos/'
def load(f,pre):
    s=open(P+f).read(); s=s[s.index('=')+1:].strip().rstrip(';'); return json.loads(s)
R=load('relato.js','REL'); O=load('observatori.js','OBS'); M=load('metode.js','MET')
def short(o,depth=0,maxl=300):
    s=json.dumps(o,ensure_ascii=False); return s if len(s)<maxl else s[:maxl]+'...'
for name,d in [('REL',R),('MET',M)]:
    print('=====',name)
    for k,v in d.items(): print(k,':',short(v))
print('===== OBS keys')
for k,v in O.items(): print(k,':',short(v,maxl=200))
