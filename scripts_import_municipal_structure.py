"""Import an attributed external municipal survey, never as verified fiscal accounts.

Usage: python scripts_import_municipal_structure.py --snapshot-dir DIRECTORY
The downloaded JS assignments are parsed as JSON, never executed.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def assignment(path, variable):
    raw = path.read_bytes()
    value = json.loads(raw.decode('utf-8-sig').split(variable + '=', 1)[1].strip().rstrip(';'))
    return value, hashlib.sha256(raw).hexdigest()


def build(folder):
    data, data_hash = assignment(folder / 'data.js', 'window.MUNI')
    sources, source_hash = assignment(folder / 'fuentes.js', 'window.MUNI_FUENTES')

    def source(index):
        indices = index if isinstance(index, list) else [index]
        result = []
        for i in indices:
            if not isinstance(i, int) or not 0 <= i < len(sources):
                continue
            s = sources[i]
            if not s[2].startswith(('http://', 'https://')):
                continue
            result.append(dict(organization=s[0], title=s[1], url=s[2], surveyConsultedAt=s[3], official=bool(s[4])))
        return result

    rows = []
    for m in data['list']:
        row = dict(id=m['cod'], municipality=m['nombre'], indicators={}, workforce=None, decisions=[])
        for key in ('flo', 'hcd', 'pub'):
            value = m['d'].get(key)
            if value is None:
                continue
            refs = source(value[2])
            if not refs or not all(s['official'] for s in refs):
                continue
            row['indicators'][key] = dict(value=value[0], period=value[1], sources=refs,
                                          verification='external_survey')
        e = m.get('emp')
        if e and e.get('t') in ('o', 'c', 'x'):
            refs = source(e.get('f'))
            if refs and all(s['official'] for s in refs) and not e.get('no'):
                row['workforce'] = dict(type=e['t'], period=e['per'], total=e.get('v'),
                                        categories=e.get('cat', []), sources=refs,
                                        verification='external_survey')
        # Link to decisions without repeating unverified allegations or monetary sanctions.
        decisions = {(s[2], s[4]) for s in m.get('sen', []) if len(s) > 4
                     and s[0].startswith('htc_') and s[4].startswith('https://sistemas.htc.gba.gov.ar/')}
        row['decisions'] = [dict(year=y, url=url) for y, url in sorted(decisions, reverse=True)]
        rows.append(row)
    verified = json.loads((ROOT / 'municipios/data/structure_verified.json').read_text(encoding='utf-8'))
    for row in rows:
        for key, evidence in verified.get(row['id'], {}).items():
            observation = row['workforce'] if key == 'workforce' else row['indicators'][key]
            assert all(observation.get(field) == value for field, value in evidence['expected'].items()), 'Recheck changed observation against primary document'
            assert hashlib.sha256((ROOT / 'municipios/data' / evidence['file']).read_bytes()).hexdigest() == evidence['sha256']
            observation['verification'] = 'primary_document'
            observation['evidence'] = evidence
    assert len(rows) == 135 and len({m['id'] for m in rows}) == 135
    return dict(version=1, importedAt='2026-10-14', source='https://municipiosargentinos.net/',
                sourceFiles={'data.js': data_hash, 'fuentes.js': source_hash},
                verification='external_survey',
                note='Relevamiento de Municipios Argentinos con enlaces a documentos oficiales. '
                     'Los importes y dotaciones todavía no tienen contraste independiente integral. '
                     'No integran los rankings fiscales verificados ni los informes PDF.',
                coverage={**{k: sum(k in m['indicators'] for m in rows) for k in ('flo', 'hcd', 'pub')},
                          'workforce': sum(m['workforce'] is not None for m in rows),
                          'decisions': sum(bool(m['decisions']) for m in rows)}, municipalities=rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot-dir', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.snapshot_dir)
    (ROOT / 'municipios/data/structure.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['coverage']))
