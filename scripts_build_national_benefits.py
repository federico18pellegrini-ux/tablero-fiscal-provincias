"""Rebuild monthly entitlements from archived official IMSS text, not budget totals."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'nacion/data/benefit-sources'
OUTPUT = ROOT / 'nacion/data/benefits.json'


def amount(text, pattern):
    matches = re.findall(pattern + r'\s*\$\s*([\d. ]+)', text, re.M | re.I)
    if len(matches) != 1:
        raise ValueError(f'Expected one amount for {pattern}: {matches}')
    return int(re.sub(r'\D', '', matches[0]))


def build():
    sources = json.loads((SOURCES / 'sources.json').read_text(encoding='utf-8'))
    ipc_path = ROOT / 'nacion/data/gestion/ipc_observado.json'
    ipc = {r['periodo']: r['indice'] for r in json.loads(ipc_path.read_text(encoding='utf-8'))}
    rows, corrections = [], []
    for source in sources['sources']:
        raw = (SOURCES / source['text_file']).read_bytes().replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == source['text_sha256']
        if source.get('archived_pdf'):
            assert hashlib.sha256((SOURCES / source['archived_pdf']).read_bytes()).hexdigest() == source['sha256']
        text = raw.decode('utf-8')
        period = source['period']
        month_names = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        if period == '2025-07':
            assert 'Durante el mes de julio de 2025' in text and 'Resolución ANSES 251/2025' in text
            corrections.append({'period': period, 'field': 'period', 'printed': 'Junio 2025', 'corrected': 'Julio 2025',
                                'reason': 'Encabezado repetido de junio; archivo, nota 2 y resolución 251/2025 corresponden a julio.',
                                'verification': 'https://www.anses.gob.ar/noticias/en-julio-las-jubilaciones-pensiones-y-asignaciones-aumentaran-150-por-ciento'})
        else:
            assert re.search(month_names[int(period[5:]) - 1] + r'\s*' + period[:4], text[:300], re.I), period
        minimum = amount(text, r'^\s*Haber mínimo SIPA')
        if period == '2024-03':
            # The same PDF's decree footnote gives $134,445.30; its headline rounds incorrectly.
            assert '$134.445,30' in text and minimum == 134446
            corrections.append({'period': period, 'field': 'minimum', 'printed': minimum,
                                'corrected': 134445, 'reason': 'Redondeo del importe exacto de la nota 3: $134.445,30.'})
            minimum = 134445
        if period == '2023-12':
            bonus = amount(text, r'^')  # December footnote puts the amount alone at line start.
            auh = amount(text, r'^\s*Hijo/a \(tramo 1\) y AUH')
        else:
            bonus = amount(text, r'^\s*(?:Bono Extraordinario Previsional|Ayuda económica previsional)\d*')
            auh = amount(text, r'^\s*AUH y AUE')
            printed_total = amount(text, r'^\s*Haber mínimo SIPA con (?:bono extraordinario previsional|Ayuda económica previsional)')
            if printed_total != minimum + bonus:
                corrections.append({'period': period, 'printed_total': printed_total, 'calculated_total': minimum + bonus,
                                    'reason': 'Se suman los componentes publicados; no se reproduce el total inconsistente de la tabla.'})
        assert 0 < minimum < 1_000_000 and 0 < bonus < 100_000 and 0 < auh < 300_000
        rows.append({'period': period, 'minimum': minimum, 'bonus': bonus, 'minimum_bonus': minimum + bonus,
                     'auh': auh, 'ipc': ipc.get(period), 'source': source['url']})
    rows.sort(key=lambda r: r['period'])
    assert len(rows) == len({r['period'] for r in rows}) == 32
    return {'meta': {'reviewed': sources['retrieved'], 'unit': 'ARS por mes · importes publicados redondeados al peso',
                     'publisher': sources['publisher'], 'source': sources['index_url'],
                     'latest_nominal': rows[-1]['period'], 'latest_real': max(r['period'] for r in rows if r['ipc']),
                     'missing_months': ['2024-01', '2024-02'],
                     'ipc_sha256': hashlib.sha256(ipc_path.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
                     'method': 'Variación real = (monto final / monto inicial) / (IPC final / IPC inicial) - 1. IPC nacional observado. No se usa inflación proyectada en las prestaciones.',
                     'scope': 'Mínima con bono completo para quien cumple el tope. AUH general: derecho mensual al 100%, no depósito neto ni adicional por zona. No incluye aguinaldo.',
                     'corrections': corrections}, 'rows': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    if args.check:
        assert json.loads(OUTPUT.read_text(encoding='utf-8')) == result, 'Benefits out of date'
    else:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'IMSS: {len(result["rows"])} meses; IPC observado hasta {result["meta"]["latest_real"]}.')
