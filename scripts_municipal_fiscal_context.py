"""Keep historical originals and secondary observations outside the common ranking."""
import hashlib
import json
import math
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def apply_fiscal_context(municipalities, path, valid_location):
    audit = json.loads(path.read_text(encoding='utf-8'))
    verified = date.fromisoformat(audit['verifiedAt'])
    for m in municipalities.values():
        m.pop('fiscalHistory', None)
        m.pop('fiscalSupplement', None)
    seen = set()
    for kind in ['history', 'supplements']:
        for r in audit[kind]:
            ident = r['id']
            key = (kind, ident, r['fin'])
            if ident not in municipalities or key in seen or date.fromisoformat(r['fin']) > verified:
                raise ValueError('Invalid fiscal context period or municipality')
            seen.add(key)
            if not r.get('documents'):
                raise ValueError('Missing fiscal context source')
            for d in r['documents']:
                if not valid_location(d) or not d.get('url','').startswith('https://') or not re.fullmatch(r'[a-f0-9]{64}',d.get('sha256','')) or d.get('sha256')=='0'*64 or d.get('bytes',0)<=0:
                    raise ValueError('Invalid fiscal context source')
                if d.get('archive'):
                    archive = ROOT / d['archive']
                    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != d['sha256']:
                        raise ValueError('Invalid fiscal context source')
                elif kind=='history':
                    raise ValueError('Missing historical original')
            m = municipalities[ident]
            if kind == 'history':
                start, end = date.fromisoformat(r['inicio']), date.fromisoformat(r['fin'])
                latest = max((f['fin'] for f in [m.get('fiscal'), m.get('fiscalOther')] if f), default='0001-01-01')
                if start > end or r['fin'] >= latest or start.year != end.year or start.month != 1 or start.day > 5 or end.month != 12 or end.day < 30:
                    raise ValueError('Historical fiscal context must be an older annual account')
                a = {k: Decimal(v) for k, v in r['amounts'].items()}
                errors = [a['ingresos_corrientes']+a['ingresos_capital']-a['ingresos_totales'],
                          a['gastos_corrientes']+a['gastos_capital']-a['gastos_totales'],
                          a['ingresos_totales']-a['gastos_totales']-a['resultado_financiero']]
                if not all(v.is_finite() for v in a.values()) or any(abs(v)>Decimal('.01') for v in errors):
                    raise ValueError('Unreconciled historical fiscal context')
                f = {**{k:v for k,v in r.items() if k not in ['id','amounts']}, **{k:float(v) for k,v in a.items()}}
                ratio = lambda num, den: float(a[num]/a[den]*100) if a[den] else None
                f.update(resultado_sobre_ingresos_pct=ratio('resultado_financiero','ingresos_totales'),
                         capital_sobre_gasto_pct=ratio('gastos_capital','gastos_totales'),
                         ahorro_corriente=float(a['ingresos_corrientes']-a['gastos_corrientes']),
                         personal_sobre_gasto_corriente_pct=None,
                         capital_por_habitante_base2022_ars_corrientes=float(a['gastos_capital'])/m['poblacion_2022'],
                         url=r['documents'][0]['url'])
                m.setdefault('fiscalHistory', []).append(f)
            else:
                if m.get('fiscalSupplement') or r.get('sourceType')!='secondary_credit_report' or r.get('unit')!='ARS_millions' or r.get('priceBasis')!='nominal' or r.get('precision')!='rounded_to_millions' or not r.get('provider') or not r.get('note'):
                    raise ValueError('Invalid secondary fiscal context scope')
                if not date.fromisoformat(r['fin']) <= date.fromisoformat(r['publishedAt']) <= verified:
                    raise ValueError('Invalid secondary fiscal context date')
                required = {'ingresos_operativos','ingresos_capital','gastos_operativos','gastos_capital','personal','resultado_financiero'}
                a = r['figures']
                if set(a)!=required or any(type(v) is not int or not math.isfinite(v) for v in a.values()):
                    raise ValueError('Invalid rounded secondary fiscal figures')
                if abs(a['ingresos_operativos']+a['ingresos_capital']-a['gastos_operativos']-a['gastos_capital']-a['resultado_financiero'])>3:
                    raise ValueError('Secondary fiscal rounding exceeds the source precision')
                # The published result is retained, including its rounding residual.
                # None of these observations overwrite fiscal or fiscalOther.
                m['fiscalSupplement'] = {k:v for k,v in r.items() if k!='id'}
    return audit
