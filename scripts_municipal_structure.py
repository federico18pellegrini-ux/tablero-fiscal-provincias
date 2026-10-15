"""Verified-only bridge between the external survey, rankings and reports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def apply_structure(municipalities):
    data = json.loads((ROOT/'municipios/data/structure.json').read_text(encoding='utf-8'))
    register = json.loads((ROOT/'municipios/data/structure_verified.json').read_text(encoding='utf-8'))
    for m in data['municipalities']:
        verified = {}
        for key, observation in [('workforce', m['workforce']), *m['indicators'].items()]:
            if not observation or observation['verification'] != 'primary_document':
                continue
            evidence = register[m['id']][key]
            assert evidence == observation['evidence']
            assert hashlib.sha256((ROOT/'municipios/data'/evidence['file']).read_bytes()).hexdigest() == evidence['sha256']
            for field, value in {**evidence['expected'], **evidence.get('confirmed', {})}.items():
                assert observation[field] == value, (m['id'], key, field)
            if key == 'hcd' and 'numerator' in evidence:
                assert abs(100*evidence['numerator']/evidence['denominator']-observation['value']) < .0051
            verified[key] = observation.copy()
            if key == 'workforce':
                permanent = [v for label,v in observation['categories'] if label == 'permanente']
                verified[key]['permanent'] = permanent[0] if len(permanent) == 1 else None
        municipalities[m['id']]['verifiedStructure'] = verified
    return sum(bool(m['verifiedStructure']) for m in municipalities.values())
