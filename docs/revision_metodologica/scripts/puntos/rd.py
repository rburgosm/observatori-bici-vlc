_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json,sys
D=_ROOT+"/web/proto/datos/"
def L(f):
    t=open(D+f).read(); return json.loads(t[t.index("=")+1:].rstrip().rstrip(";"))
O,Rl,M=L("observatori.js"),L("relato.js"),L("metode.js")
k=O["kpi"]; print({x:k[x] for x in ("tres","n_neg","top","cob","cob_any","per","pl3")})
print("meta esc0", {x:k["meta"]["esc"][0][x] for x in ("año","base","meta","senda_anual","necesaria","concl","senda")})
print("meta esc1", {x:k["meta"]["esc"][1][x] for x in ("año","base","meta","concl","sobre","senda_ult")})
print({x:k["meta"][x] for x in ("previa","previa_ant","max","año_max")})
for n in O["negros"]:
    print(n["n"],n["A"],n["B"],n["por"],n["tres"],n["pl"],n.get("pista"),n["nom"][:45],[ (p["lug"][:25],p["niv"],p["kind"]) for p in n["plan"]][:3])
print("met", {x:M[x] for x in ("cambia_A","igual_sinpeso","cruce_30","cruce_ciudad","pesos","riesgo","uso30")})
print("met plan",M["plan"])
