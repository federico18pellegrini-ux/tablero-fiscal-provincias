"""Reviewed program identities across the 2027 ONP annex and 2026 PA codes."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import pymupdf
import pandas as pd

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / 'nacion/data/program-sources/crosswalk.json'
KEY = ['jurisdiccion_id', 'servicio_id', 'programa_id']


def norm(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower())


def verify_project_row(path, entry):
    """Read the code, name and amount from the same row of the source table."""
    with pymupdf.open(path) as doc:
        page = doc[entry['page']-1]
        words = page.get_text('words')
        codes = [w for w in words if 95 <= w[0] <= 120 and 145 <= w[1] < 780 and re.fullmatch(r'\d{2}', w[4])]
        found = [w for w in codes if int(w[4]) == entry['project_code']]
        # The same code can appear in different sub-jurisdictions on one page.
        right = 480 if path.name == 'P27J91.pdf' else 350
        found = [w for w in found if any(right <= v[0] < right+90 and abs(v[1]-w[1]) < 2
                 and v[4] == f"{int(entry['project']):,}".replace(',', '.') for v in words)]
        assert len(found) == 1, entry['id']
        y = found[0][1]
        bottom = min((w[1] for w in codes if w[1] > y+2), default=780)
        right = 480 if path.name == 'P27J91.pdf' else 350
        values = [w[4] for w in words if right <= w[0] < right+90 and abs(w[1]-y) < 2 and re.fullmatch(r'[\d.]+', w[4])]
        assert len(values) == 1 and int(values[0].replace('.', '')) == entry['project'], entry['id']
        name_right = 335 if path.name == 'P27J91.pdf' else 267
        label = page.get_textbox(pymupdf.Rect(125, y-1, name_right, bottom-1))
        assert norm(entry['table_name']) in norm(label), (entry['id'], label)


def verify_context(path, context):
    with pymupdf.open(path) as doc:
        words = doc[context['page']-1].get_text('words')
        code = [w for w in words if 105 <= w[0] <= 130 and w[4] == str(context['activity_code'])]
        assert len(code) == 1
        values = [w[4] for w in words if 480 <= w[0] < 550 and abs(w[1]-code[0][1]) < 2]
        assert values == [f"{context['activity_project']:,}".replace(',', '.')]


def select_parts(annual, parts):
    """Union of explicit PA program/activity/project selectors; never fuzzy amounts."""
    selected = pd.Series(False, index=annual.index)
    for part in parts:
        mask = (annual[KEY] == tuple(part['key'])).all(axis=1)
        assert mask.any(), ('Clave sin registros', part['key'])
        if part.get('name'):
            assert {norm(s) for s in annual.loc[mask, 'programa_desc'].unique()} == {norm(part['name'])}
        for operation in ['include', 'exclude']:
            if operation not in part:
                continue
            subset = pd.Series(False, index=annual.index)
            for condition in part[operation]:
                assert set(condition) <= {'subprograma_id', 'proyecto_id', 'actividad_id'}
                item = mask & (annual[list(condition)] == pd.Series(condition)).all(axis=1)
                assert item.any(), ('Actividad sin registros', part['key'], condition)
                subset |= item
            mask &= subset if operation == 'include' else ~subset
        assert not (selected & mask).any(), 'Partes superpuestas'
        selected |= mask
    return annual.loc[selected]


def apply_documented_links(programs, annual):
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    by_id = {p['id']: p for p in programs}
    sources = {s['file']: s for s in evidence['sources']}
    for s in sources.values():
        data = (ROOT / 'nacion' / s['path']).read_bytes()
        assert len(data) == s['bytes'] and hashlib.sha256(data).hexdigest() == s['sha256'], s['file']
    identities = {}
    for names, rows in annual.groupby(['jurisdiccion_desc', 'entidad_desc', 'programa_desc']):
        identities[tuple(map(norm, names))] = {
            tuple(int(v) for v in row)
            for row in rows[KEY].drop_duplicates().itertuples(index=False, name=None)
        }
    overrides = {e['id'] for e in evidence['links'] if e.get('override')}
    withdrawn = set(evidence.get('withdrawn_ids', []))
    for pid in withdrawn | overrides:
        p = by_id[pid]
        # p63 used to be documented; the new evidence replaces that link.
        if pid != 'p63':
            assert p['matched'], pid
        p.update(matched=False, law=None, current=None, accrued=None)
        p.pop('current_functions', None)
    used = set()
    for p in programs:
        if not p['matched']:
            continue
        keys = identities[(norm(p['jurisdiction']), norm(p['entity']), norm(p['name']))]
        rows = select_parts(annual, [{'key':list(k)} for k in keys])
        assert not used.intersection(rows.index), ('Base automática reutilizada', p['id'])
        used.update(rows.index)
    linked = []
    for entry in evidence['links']:
        p = by_id[entry['id']]
        assert not p['matched'] and all(p[k] == entry[k] for k in ['name','entity','jurisdiction','project']), entry['id']
        verify_project_row(ROOT / 'nacion' / sources[entry['source']]['path'], entry)
        parts = entry.get('current_parts') or [{'key':entry['current_key'], 'name':entry['current_name']}]
        g = select_parts(annual, parts)
        assert not used.intersection(g.index), ('Base 2026 reutilizada', entry['id'])
        used.update(g.index)
        for old, new in [('credito_presupuestado','law'),('credito_vigente','current'),('credito_devengado','accrued')]:
            p[new] = round(float(g[old].sum()), 6)
        p.update(matched=True, current_functions=sorted(g.funcion_desc.unique().tolist()),
                 match_method='documented_codes', current_parts=parts, project_code=entry['project_code'],
                 match_note=entry['note'], match_source={'url':sources[entry['source']]['url'],
                    'path':sources[entry['source']]['path'], 'page':entry['page']})
        if len(parts) == 1 and not any(k in parts[0] for k in ['include','exclude']):
            p['current_key'] = parts[0]['key']
        if entry.get('context'):
            verify_context(ROOT / 'nacion' / sources[entry['context']['source']]['path'], entry['context'])
            p['comparison_context'] = entry['context']
        linked.append(p['id'])
    assert len(linked) == len(set(linked))
    reviews = evidence.get('reviews', [])
    for review in reviews + evidence.get('related_reviews', []):
        p = by_id[review['id']]
        p['review'] = review
        assert p['matched'] == (review['status'] == 'comparable'), review['id']
    assert all(p['matched'] or p.get('review') for p in programs)
    groups = []
    for entry in evidence.get('groups', []):
        g = select_parts(annual, entry['current_parts'])
        group = dict(entry, project=sum(by_id[pid]['project'] for pid in entry['program_ids']))
        for old, new in [('credito_presupuestado','law'),('credito_vigente','current'),('credito_devengado','accrued')]:
            group[new] = round(float(g[old].sum()), 6)
        # Context totals overlap their component programs, and never enter a ranking or total.
        group['scope'] = 'Comparación del conjunto; incluye sus programas y no se suma a ellos.'
        groups.append(group)
    return {'reviewed':evidence['reviewed'], 'documented_count':len(linked), 'ids':linked,
            'source':'data/program-sources/crosswalk.json', 'sources':evidence['sources'],
            'reviews':reviews, 'related_reviews':evidence.get('related_reviews', []), 'groups':groups,
            'legal_evidence':evidence.get('legal_evidence', []),
            'investigated_count':len(reviews), 'new_links_count':sum(r['status']=='comparable' for r in reviews),
            'method':'Nombres, actividades y proyectos contrastados con ONP 2026/2027 y PA al 15/09/2026. Cada registro 2026 se usa una sola vez en las comparaciones individuales. Los conjuntos son vistas alternativas y no se suman a sus componentes.'}
