"""Rebuild deflators from official national indices; no unverified historical splice."""
import csv
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE_PERIOD='2026-06'
def main():
    path=ROOT/'data/ipc_national_index.csv'
    if len(sys.argv)>1:
        import pandas as pd
        d=pd.read_excel(sys.argv[1],sheet_name='Índices IPC Cobertura Nacional',header=None)
        if d.iloc[5,0]!='Total nacional' or d.iloc[9,0]!='Nivel general':raise ValueError('INDEC layout changed')
        rows=[{'period':d.iloc[5,c].strftime('%Y-%m'),'ipc_index':float(d.iloc[9,c])} for c in range(1,len(d.columns)) if hasattr(d.iloc[5,c],'strftime')]
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['period','ipc_index'],lineterminator='\n');w.writeheader();w.writerows(rows)
    with path.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    base=next(float(r['ipc_index']) for r in rows if r['period']==BASE_PERIOD)
    previous=None
    for r in rows:
        index=float(r['ipc_index']);r['ipc_mom']='' if previous is None else f'{index/previous-1:.8f}';r['factor_to_latest']=f'{base/index:.10f}';previous=index
    with (ROOT/'deflactor_mensual.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['period','ipc_mom','ipc_index','factor_to_latest'],lineterminator='\n');w.writeheader();w.writerows(rows)
    print(f"INDEC: {len(rows)} months; base {BASE_PERIOD}; latest {rows[-1]['period']}")
if __name__=='__main__':main()
