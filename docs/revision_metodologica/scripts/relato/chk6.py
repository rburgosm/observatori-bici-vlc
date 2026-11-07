_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json
from scipy.stats import poisson, nbinom
P=_ROOT+'/web/proto/datos/'
s=open(P+'relato.js').read(); s=s[s.index('=')+1:].strip().rstrip(';'); R=json.loads(s)
sc=R['sc']; a=0.493
out_hi=[d for d in sc if d['N']>poisson.ppf(0.975,d['mu'])]
out_lo=[d for d in sc if d['N']<poisson.ppf(0.025,d['mu'])]
print('sitios',len(sc),'por encima banda Poisson',len(out_hi),'de ellos p<=0.8:',sum(d['p']<=0.8 for d in out_hi),'p<=0.95:',sum(d['p']<=0.95 for d in out_hi),'| por debajo',len(out_lo))
# NB band
def nbq(q,mu): 
    r=1/a; p=r/(r+mu); return nbinom.ppf(q,r,p)
print('fuera banda NB arriba',sum(d['N']>nbq(.975,d['mu']) for d in sc),'abajo',sum(d['N']<nbq(.025,d['mu']) for d in sc))
print('p>0.95:',sum(d['p']>0.95 for d in sc),' 0.8-0.95:',sum(0.8<d['p']<=0.95 for d in sc))
for k in ['Játiva','TIRSO','BALACIART']:
    d=[x for x in sc if k in x['n']][0]; print(d)
