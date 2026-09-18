"""Official OPC supplements, transcribed from identified tables and sealed originals."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_updates(initial, current):
    data = json.loads((ROOT / 'nacion/data/management-sources/evidence.json').read_text(encoding='utf-8'))
    for source in data['sources']:
        raw = (ROOT / 'nacion' / source['path']).read_bytes()
        assert len(raw) == source['bytes']
        assert hashlib.sha256(raw).hexdigest() == source['sha256'], source['path']
    acts = data['modifications']['acts']
    assert len(acts) == len({r['id'] for r in acts}) == 5
    assert [r['date'] for r in acts] == sorted(r['date'] for r in acts)
    net = sum(r['spending_ars_millions'] for r in acts)
    residual = current - initial - net
    # Five published, independently rounded totals: at most 0.5 million per act.
    assert abs(residual) <= 2.5, 'Normas y cambio neto no concilian'
    data['modifications']['reconciliation'] = {
        'initial': initial, 'current': current, 'net': current-initial,
        'acts_total': net, 'rounding_residual': residual,
        'tolerance_ars_millions': 2.5,
    }
    d = data['debt']
    assert [r['period'] for r in d['months']] == [f'2026-{m:02}' for m in range(8,13)]
    for key in ('ars_thousand_millions', 'fx_usd_millions'):
        assert all(r[key] >= 0 for r in d['months'])
        difference = d['totals'][key] - sum(r[key] for r in d['months'])
        assert abs(difference) <= 3, 'Revisar redondeo del perfil OPC'
        d['totals'][key+'_rounding_difference'] = difference
    assert d['stock_cutoff'] == '2026-07-31'
    return data
