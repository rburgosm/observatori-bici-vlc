_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json,unicodedata,re,pandas as pd
D=_ROOT+"/web/proto/datos/"
t=open(D+"observatori.js").read(); O=json.loads(t[t.index("=")+1:].rstrip().rstrip(";"))
def norm(x): return unicodedata.normalize("NFD", str(x)).encode("ascii", "ignore").decode().upper()
EXTRA={"Tres Cruces - Campos Crespo":["TRES CRUCES","CAMPOS CRESPO"],"C/ Xàtiva":["C/ XATIVA|C/ JATIVA"],
 "Peset Aleixandre - Camí de Montcada":["PESET","MONTCADA|MONCADA"],"Giorgeta - Jesús":["GIORGETA","JESUS"],
 "Av. de Peris y Valero":["PERIS Y VALERO"],"Gran Vía Germanías a la altura de C/ Castellón":["GERMANIAS"],
 "Ronda Norte":["RONDA NORD|RONDA NORTE"]}
lug=pd.read_csv(_ROOT+"/data/processed/pdsv_lugares.csv").set_index("nombre")
neg=[n for n in O["negros"] if not n.get("zona")]
new=[]
for n in neg:
    tx=[norm(u) for u,_ in n["ubis"]]+[norm(n["nom"])]
    hits=[]
    for k,cl in EXTRA.items():
        if any(all(any(a in s for a in c.split("|")) for c in cl) for s in tx):
            tl=lug.loc[k,"tipo_lugar"]; tl=tl if isinstance(tl,str) else tl.iloc[0]
            hits.append((k,"lugar" if tl.startswith("cruce") else "calle"))
    pl=n["pl"]
    if hits:
        pl2=1 if (pl==1 or any(h[1]=="lugar" for h in hits)) else 2
    else: pl2=pl
    if hits: print(n["nom"][:50],"pl",pl,"->",pl2,hits)
    new.append(pl2)
print("antes", {k:sum(n["pl"]==k for n in neg) for k in (1,2,0)}, "después", {k:new.count(k) for k in (1,2,0)})
# also: all ubis of top30 that contain Ronda interior streets (Anillo ciclista)
ANI=r"C/ COLON|C/ XATIVA|GUILLEM DE CASTRO|C/ JUSTICIA|PG CIUDADELA|C/ BLANQUERIAS|PL TETUAN|C/ PINTOR LOPEZ|PG PECHINA"
print("en Ronda Interior (anillo ciclista):",[n["nom"][:40] for n in neg if any(re.search(ANI,norm(u)) for u,_ in n["ubis"]+[[n["nom"],0]])])
