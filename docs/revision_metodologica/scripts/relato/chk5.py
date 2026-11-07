_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json,unicodedata
P=_ROOT+'/web/proto/datos/'
s=open(P+'observatori.js').read(); s=s[s.index('=')+1:].strip().rstrip(';'); O=json.loads(s)
norm=lambda x: unicodedata.normalize("NFD",str(x)).encode("ascii","ignore").decode().upper()
FALTAN={"Tres Cruces - Campos Crespo (cruce, peaton)":["TRES CRUCES","CAMPOS CRESPO"],"Av. Peris y Valero (punto, peaton)":["PERIS Y VALERO"],
"C/ Xativa (calle, act)":["XATIVA|JATIVA"],"Peset Aleixandre - Cami de Montcada":["PESET","MONTCADA|MONCADA"],"Giorgeta - Jesus":["GIORGETA","JESUS"],
"Gral Aviles - Luis Bunuel":["GENERAL AVILES","BUNUEL"],"Germanias/Castellon":["GERMANIAS","CASTELLON"],"Ronda Norte":["RONDA NORTE"]}
for n in O['negros']:
    tx=[norm(u[0] if isinstance(u,list) else u) for u in n['ubis']]+[norm(n['nom'])]
    hits=[k for k,cl in FALTAN.items() if any(all(any(a in t for a in c.split('|')) for c in cl) for t in tx)]
    if hits: print(n['nom'][:45],'pl=',n['pl'],'->',hits)
