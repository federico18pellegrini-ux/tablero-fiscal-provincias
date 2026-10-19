"""Refresh observed CPI and the remaining geometric scenario, preserving August price base."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def scenario(ipc,anchor='2026-08'):
    observed=max(k for k in ipc if k.startswith('2026-'));month=int(observed[-2:]);indices=dict(ipc)
    dec26=ipc['2025-12']*1.29
    for m in range(month+1,13):indices[f'2026-{m:02}']=ipc[observed]*(dec26/ipc[observed])**((m-month)/(12-month))
    for m in range(1,13):indices[f'2027-{m:02}']=dec26*1.18**(m/12)
    averages={str(y):sum(indices[f'{y}-{m:02}'] for m in range(1,13))/12 for y in range(2023,2028)}
    return observed,indices,averages,{y:ipc[anchor]/v for y,v in averages.items()}

def main():
    ipc={r['period']:float(r['ipc_index']) for r in csv.DictReader((ROOT/'data/ipc_national_index.csv').read_text().splitlines())}
    p=ROOT/'nacion/data/budget.json';d=json.loads(p.read_text(encoding='utf-8'));observed,indices,averages,factors=scenario(ipc)
    d['deflator'].update(observed_through=observed,annual_factors=factors,annual_average_index=averages,monthly_index={k:v for k,v in indices.items() if k>='2026-01'},method='IPC INDEC observado hasta septiembre 2026. Proyección propia desde octubre: variación mensual constante hasta alcanzar los supuestos ONP de diciembre (29% en 2026; 18% en 2027). Montos anuales divididos por IPC promedio anual y multiplicados por IPC agosto 2026. No usa IPC de diciembre como deflactor anual.')
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
