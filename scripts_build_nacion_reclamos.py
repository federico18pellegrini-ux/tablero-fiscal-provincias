"""Build documentary evidence, never an inferred receivables balance."""
import argparse
import csv
import io
import json
import math
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
EVIDENCE_FILE = ROOT / 'data/reclamos_nacion/evidencia_verificada.json'
KINDS = {'reclamo', 'acuerdo', 'anticipo', 'credito_compensable', 'pago', 'sin_monto'}
QUALIFIERS = {'exacto', 'aproximado', 'mas_de', 'rango'}


def validate_evidence(data, universe):
    errors = []
    if data.get('schema_version') != 2:
        errors.append('schema_version debe ser 2')
    try:
        reviewed = date.fromisoformat(data['reviewed_at'])
    except (ValueError, KeyError, TypeError):
        errors.append('reviewed_at inválido')
        reviewed = date.min
    if set(data.get('provinces', {})) != set(universe):
        errors.append('Deben estar las 24 jurisdicciones, sin omisiones ni extras')
    seen = set()
    for province, payload in data.get('provinces', {}).items():
        if payload.get('saldo_actual_verificado') is not None:
            errors.append(f'{province}: esta versión no verifica saldos corrientes conciliados')
        if not payload.get('pending'):
            errors.append(f'{province}: falta explicar qué queda pendiente')
        for record in payload.get('records', []):
            label = f'{province}/{record.get("id")}'
            if not record.get('id') or record['id'] in seen:
                errors.append(f'{label}: id ausente o duplicado')
            seen.add(record.get('id'))
            if record.get('kind') not in KINDS:
                errors.append(f'{label}: tipo inválido')
            if not record.get('title') or not record.get('explanation'):
                errors.append(f'{label}: falta título o explicación')
            for key in ['published_at', 'valuation_date']:
                value = record.get(key)
                if key == 'valuation_date' and value is None:
                    continue
                try:
                    if date.fromisoformat(value) > reviewed:
                        errors.append(f'{label}: fecha posterior a revisión')
                except (TypeError, ValueError):
                    errors.append(f'{label}: {key} inválida')
            source = record.get('source', {})
            host = urlparse(source.get('url', '')).hostname or ''
            if not source.get('institution') or not source.get('title') or not source.get('url', '').startswith('https://') or not host.endswith(('.gob.ar', '.gov.ar')):
                errors.append(f'{label}: requiere documento oficial identificado')
            amount = record.get('amount')
            if record.get('amount_basis') not in {None, 'mensual'} or (record.get('amount_basis') and amount is None):
                errors.append(f'{label}: base temporal del importe inválida')
            if amount is None:
                if record.get('kind') != 'sin_monto':
                    errors.append(f'{label}: importe requerido para este tipo')
                continue
            value = amount.get('value')
            valid = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0
            if not valid:
                errors.append(f'{label}: monto debe ser positivo y finito')
            if amount.get('currency') not in {'ARS', 'USD'} or amount.get('qualifier') not in QUALIFIERS:
                errors.append(f'{label}: moneda o calificador inválido')
            if amount.get('qualifier') == 'rango':
                upper = amount.get('upper')
                if not isinstance(upper, (int, float)) or not math.isfinite(upper) or not valid or upper <= value:
                    errors.append(f'{label}: rango inválido')
            parts = record.get('components', [])
            if parts:
                values = [part.get('value') for part in parts]
                if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in values):
                    errors.append(f'{label}: componente inválido')
                elif valid and abs(sum(values) - value) > 0.01:
                    errors.append(f'{label}: componentes no concilian con total publicado')
    return errors


def build_payload(data, universe):
    errors = validate_evidence(data, universe)
    if errors:
        raise ValueError('\n'.join(errors))
    provinces = {}
    for name in universe:
        item = data['provinces'][name]
        records = item['records']
        provinces[name] = {
            **item, 'provincia': name,
            'coverage': 'con_montos_publicados' if any(r['amount'] is not None for r in records) else ('documento_sin_monto' if records else 'pendiente_documentacion'),
            'latest_publication': max((r['published_at'] for r in records), default=None),
        }
    return {
        'schema_version': 2, 'reviewed_at': data['reviewed_at'],
        'latest_publication': max((p['latest_publication'] for p in provinces.values() if p['latest_publication']), default=None),
        'methodology': data['methodology'], 'provinces': provinces,
        'coverage': {
            'jurisdictions': len(provinces),
            'with_amounts': sum(p['coverage'] == 'con_montos_publicados' for p in provinces.values()),
            'documents_without_amounts': sum(p['coverage'] == 'documento_sin_monto' for p in provinces.values()),
            'pending_documentation': sum(p['coverage'] == 'pendiente_documentacion' for p in provinces.values()),
            'verified_current_balances': 0,
        },
    }


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def csv_text(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def build_outputs(data, universe):
    payload = build_payload(data, universe)
    rows, provincial_rows = [], []
    for name, item in payload['provinces'].items():
        provincial_rows.append({'provincia': name, 'cobertura': item['coverage'], 'saldo_actual_verificado': None, 'ultima_publicacion': item['latest_publication'], 'documentos': len(item['records']), 'pendiente': item['pending']})
        for record in item['records']:
            amount = record['amount'] or {}
            rows.append({
                'provincia': name, 'id': record['id'], 'tipo': record['kind'], 'concepto': record['title'],
                'monto': amount.get('value'), 'monto_hasta': amount.get('upper'), 'moneda': amount.get('currency'), 'calificador': amount.get('qualifier'),
                'fecha_publicacion': record['published_at'], 'fecha_valuacion': record.get('valuation_date'),
                'periodo': record.get('period', ''), 'explicacion': record['explanation'],
                'organismo': record['source']['institution'], 'documento': record['source']['title'], 'url': record['source']['url'],
                'componentes_incluidos': json.dumps(record.get('components', []), ensure_ascii=False),
            })
    fields = ['provincia', 'id', 'tipo', 'concepto', 'monto', 'monto_hasta', 'moneda', 'calificador', 'fecha_publicacion', 'fecha_valuacion', 'periodo', 'explicacion', 'organismo', 'documento', 'url', 'componentes_incluidos']
    return {
        'dashboard_reclamos_nacion_provincias.json': json_text(payload),
        'data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv': csv_text(rows, fields),
        'data/reclamos_nacion/reclamos_nacion_buenos_aires_caso_testigo.csv': csv_text([r for r in rows if r['provincia'] == 'Buenos Aires'], fields),
        'outputs/reclamos_nacion_agregado_provincial.csv': csv_text(provincial_rows, ['provincia', 'cobertura', 'saldo_actual_verificado', 'ultima_publicacion', 'documentos', 'pendiente']),
        'outputs/reclamos_nacion_resumen_ba_resto.json': json_text({'schema_version': 2, 'reviewed_at': data['reviewed_at'], 'coverage': payload['coverage'], 'nota': 'No se calcula un total nacional: difieren conceptos, monedas, fechas y estados de reconocimiento.'}),
        'outputs/reclamos_nacion_buenos_aires_resumen.json': json_text(payload['provinces']['Buenos Aires']),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads(EVIDENCE_FILE.read_text(encoding='utf-8'))
    universe = json.loads((ROOT / 'dashboard_manifest.json').read_text(encoding='utf-8'))['province_universe']
    for path, content in build_outputs(data, universe).items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Desactualizado: {path}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8', newline='\n')
    print('OK: evidencia y derivados de reclamos Nación, 24 jurisdicciones; sin saldos inferidos.')


if __name__ == '__main__':
    main()
