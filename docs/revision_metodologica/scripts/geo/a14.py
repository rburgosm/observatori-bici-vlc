_ROOT = __import__('os').path.abspath(__import__('os').path.join(__file__, *['..'] * 5))  # raíz del proyecto
import json, pandas as pd
d=pd.DataFrame(json.load(open(_ROOT+'/data/raw/siniestros/siniestros-de-trafico-2022-2025.json')))
d['y']=d.FECHA.str[:4].astype(int); d=d[d.y<=2025]; d=d[~d.drop(columns='_id').duplicated()]
u=d.UNIDADES_IMPLICADAS
bv=u.str.contains('VMP|BICICLETA'); v=u.str.contains('VMP'); b=u.str.contains('BICICLETA'); moto=u.str.contains('MOTOCICLETA|CICLOMOTOR'); peat=u.str.contains('PEAT')
t=pd.DataFrame({'total':d.groupby('y').size(),'bv':bv.groupby(d.y).sum(),'vmp':v.groupby(d.y).sum(),'bici':b.groupby(d.y).sum(),'moto':moto.groupby(d.y).sum(),'peaton':peat.groupby(d.y).sum(),'no_bv':(~bv).groupby(d.y).sum()})
t['bv_share']=(t.bv/t.total).round(4)
print(t.to_string()); print((t.loc[2025]/t.loc[2022]-1).round(3).to_dict())
h=d['TIPO GRAVEDAD']!='SIN HERIDOS'
print('con heridos: bv', (bv&h).groupby(d.y).sum().to_dict(), 'no bv', ((~bv)&h).groupby(d.y).sum().to_dict())
