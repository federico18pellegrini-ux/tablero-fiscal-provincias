"""Reviewed program identities across the 2027 ONP annex and 2026 PA codes."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import pymupdf

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
    used = set()
    for p in programs:
        if not p['matched']:
            continue
        used.update(identities[(norm(p['jurisdiction']), norm(p['entity']), norm(p['name']))])
    linked = []
    for entry in evidence['links']:
        p = by_id[entry['id']]
        assert not p['matched'] and all(p[k] == entry[k] for k in ['name','entity','jurisdiction','project']), entry['id']
        verify_project_row(ROOT / 'nacion' / sources[entry['source']]['path'], entry)
        key = tuple(entry['current_key'])
        assert key not in used, ('Base 2026 reutilizada', key)
        used.add(key)
        g = annual[(annual[KEY] == key).all(axis=1)]
        assert len(g) and {norm(s) for s in g.programa_desc.unique()} == {norm(entry['current_name'])}, entry['id']
        for old, new in [('credito_presupuestado','law'),('credito_vigente','current'),('credito_devengado','accrued')]:
            p[new] = round(float(g[old].sum()), 6)
        p.update(matched=True, current_functions=sorted(g.funcion_desc.unique().tolist()),
                 match_method='documented_codes', current_key=list(key), project_code=entry['project_code'],
                 match_note=entry['note'], match_source={'url':sources[entry['source']]['url'],
                    'path':sources[entry['source']]['path'], 'page':entry['page']})
        if entry.get('context'):
            verify_context(ROOT / 'nacion' / sources[entry['context']['source']]['path'], entry['context'])
            p['comparison_context'] = entry['context']
        linked.append(p['id'])
    assert len(linked) == len(set(linked))
    return {'reviewed':evidence['reviewed'], 'documented_count':len(linked), 'ids':linked,
            'source':'data/program-sources/crosswalk.json', 'sources':evidence['sources'],
            'method':'Nombres y códigos contrastados con los fascículos ONP 2027 y el registro PA 2026. Cada base 2026 se usa una sola vez; cambios de alcance sin equivalencia completa siguen sin comparación.'}
