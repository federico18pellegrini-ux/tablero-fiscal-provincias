import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

MANIFEST_FILE = Path('dashboard_manifest.json')
MASTER_FILE = Path('data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv')
CATALOG_FILE = Path('data/reclamos_nacion/catalogo_tipos_reclamo.csv')
DEFLATOR_FILE = Path('deflactor_mensual.csv')
OUTPUT_CSV = Path('outputs/reclamos_nacion_agregado_provincial.csv')
OUTPUT_JSON = Path('dashboard_reclamos_nacion_provincias.json')
OUTPUT_SUMMARY_JSON = Path('outputs/reclamos_nacion_resumen_ba_resto.json')

ROBUST_QUALITIES = {'observado', 'estimado_robusto'}
ALL_QUALITIES = {'observado', 'estimado_robusto', 'proxy', 'no_disponible'}


def normalize_text(value):
    return (value or '').strip()


def parse_float(value):
    raw = normalize_text(value)
    if raw == '':
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def month_key(date_like):
    txt = normalize_text(date_like)
    if len(txt) >= 7:
        return txt[:7]
    return None


def load_deflator_table():
    rows = read_csv(DEFLATOR_FILE)
    table = {}
    for row in rows:
        period = normalize_text(row.get('period'))
        idx = parse_float(row.get('ipc_index'))
        if period and idx:
            table[period] = idx
    return table


def update_amount(row, deflator_table):
    base = parse_float(row.get('monto_nominal'))
    if base is None:
        return None

    explicit = parse_float(row.get('monto_actualizado'))
    if explicit is not None:
        return explicit

    indexador = normalize_text(row.get('indexador')).lower()
    fecha_corte = month_key(row.get('fecha_corte_monto'))

    factor = 1.0
    if indexador in {'sin_actualizacion', 'none', ''}:
        factor = 1.0
    elif indexador == 'ipc_nacional' and fecha_corte in deflator_table:
        latest_month = max(deflator_table)
        latest_idx = deflator_table.get(latest_month)
        cut_idx = deflator_table.get(fecha_corte)
        if latest_idx and cut_idx:
            factor = latest_idx / cut_idx
    else:
        return None

    tasa = parse_float(row.get('tasa_interes'))
    if tasa is not None and tasa > 0:
        factor *= (1 + tasa)

    return base * factor


def robust_share(rows):
    informative = [r for r in rows if normalize_text(r.get('calidad_dato')) in ALL_QUALITIES]
    if not informative:
        return 0.0
    robust = [r for r in informative if normalize_text(r.get('calidad_dato')) in ROBUST_QUALITIES]
    return (len(robust) / len(informative)) * 100


def claim_anchor(row):
    tipo = normalize_text(row.get('tipo_reclamo'))
    sub = normalize_text(row.get('subtipo_reclamo'))
    org = normalize_text(row.get('organismo_nacional'))
    parts = [p for p in [tipo, sub, org] if p]
    return ' · '.join(parts)


def build():
    with MANIFEST_FILE.open(encoding='utf-8') as f:
        manifest = json.load(f)

    province_universe = manifest.get('province_universe', [])
    rows = read_csv(MASTER_FILE)
    _ = read_csv(CATALOG_FILE)
    deflator_table = load_deflator_table()

    grouped = defaultdict(list)
    for row in rows:
        province = normalize_text(row.get('provincia'))
        if province:
            row['monto_actualizado_calculado'] = update_amount(row, deflator_table)
            grouped[province].append(row)

    province_rows = []
    provinces_payload = {}

    for province in province_universe:
        claims = grouped.get(province, [])
        total_reclamada = 0.0
        total_robusta = 0.0
        debt_by_type = defaultdict(float)
        claim_count = len(claims)
        judicialized = 0
        latest_date = None
        observed_anchors = []
        principal_org = None
        observations = []

        for claim in claims:
            amount = claim.get('monto_actualizado_calculado')
            amount = amount if amount is not None else parse_float(claim.get('monto_actualizado'))

            estado = normalize_text(claim.get('estado_reclamo')).lower()
            if 'judicial' in estado:
                judicialized += 1

            cut = normalize_text(claim.get('fecha_corte_monto'))
            if cut:
                try:
                    d = datetime.fromisoformat(cut).date()
                except ValueError:
                    d = None
                if d and (latest_date is None or d > latest_date):
                    latest_date = d

            if amount is not None:
                total_reclamada += amount
                debt_by_type[normalize_text(claim.get('tipo_reclamo'))] += amount
                observed_anchors.append((amount, claim_anchor(claim)))

                if normalize_text(claim.get('calidad_dato')) in ROBUST_QUALITIES:
                    total_robusta += amount

            if not principal_org:
                principal_org = normalize_text(claim.get('organismo_nacional')) or None

            obs = normalize_text(claim.get('observaciones'))
            if obs:
                observations.append(obs)

        principal_type = None
        if debt_by_type:
            principal_type = sorted(debt_by_type.items(), key=lambda kv: kv[1], reverse=True)[0][0]

        observed_anchors.sort(key=lambda x: x[0], reverse=True)
        anchors = [item[1] for item in observed_anchors[:3]]

        methodology_note = (
            'deuda_total_reclamada suma montos actualizados disponibles; deuda_total_robusta incluye '
            'solo calidad observado/estimado_robusto y excluye proxy/no_disponible para evitar doble conteo.'
        )

        qualities = [normalize_text(c.get('calidad_dato')) for c in claims]
        if not claims:
            estado_cobertura = 'sin_carga'
        elif all(q == 'no_disponible' for q in qualities):
            estado_cobertura = 'cobertura_minima'
        elif robust_share(claims) == 0:
            estado_cobertura = 'parcial_proxy'
        else:
            estado_cobertura = 'con_datos'

        payload_row = {
            'provincia': province,
            'deuda_total_reclamada': round(total_reclamada, 2),
            'deuda_total_robusta': round(total_robusta, 2),
            'anclas_principales': anchors,
            'principal_tipo_reclamo': principal_type,
            'principal_organismo_nacional': principal_org,
            'porcentaje_cubierto_con_dato_robusto': round(robust_share(claims), 2),
            'fecha_ultima_actualizacion': latest_date.isoformat() if latest_date else None,
            'observaciones_metodologicas': methodology_note,
            'deuda_por_tipo': {k: round(v, 2) for k, v in debt_by_type.items()},
            'cantidad_de_reclamos': claim_count,
            'cantidad_de_reclamos_judicializados': judicialized,
            'estado_cobertura': estado_cobertura,
            'observaciones': observations[:3],
        }

        province_rows.append(payload_row)
        provinces_payload[province] = payload_row

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open('w', encoding='utf-8', newline='') as f:
        fields = [
            'provincia', 'deuda_total_reclamada', 'deuda_total_robusta', 'anclas_principales',
            'principal_tipo_reclamo', 'principal_organismo_nacional', 'porcentaje_cubierto_con_dato_robusto',
            'fecha_ultima_actualizacion', 'observaciones_metodologicas', 'cantidad_de_reclamos',
            'cantidad_de_reclamos_judicializados', 'estado_cobertura'
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in province_rows:
            row_copy = dict(row)
            row_copy['anclas_principales'] = ' | '.join(row_copy['anclas_principales'])
            writer.writerow({k: row_copy.get(k) for k in fields})

    payload = {
        'source': 'pipeline_reclamos_nacion_v1',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'cutoff_date': date.today().isoformat(),
        'methodology': {
            'deuda_total_reclamada': 'Suma de montos_actualizados disponibles por provincia.',
            'deuda_total_robusta': 'Suma de montos_actualizados con calidad_dato observado o estimado_robusto.',
            'calidad_dato': {
                'observado': 'Monto documentado en fuente primaria con expediente o acto.',
                'estimado_robusto': 'Monto calculado con fórmula homogénea y base trazable.',
                'proxy': 'Aproximación parcial sin base homogénea completa.',
                'no_disponible': 'No existe monto validado al corte.'
            },
            'double_count_guard': 'No sumar reclamos superpuestos por expediente/objeto cuando refieren al mismo hecho generador.'
        },
        'provinces': provinces_payload,
    }

    with OUTPUT_JSON.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')

    ba = provinces_payload.get('Buenos Aires', {})
    resto = {
        'cantidad_provincias': max(0, len(province_rows) - 1),
        'deuda_total_reclamada': round(sum(r['deuda_total_reclamada'] for r in province_rows if r['provincia'] != 'Buenos Aires'), 2),
        'deuda_total_robusta': round(sum(r['deuda_total_robusta'] for r in province_rows if r['provincia'] != 'Buenos Aires'), 2),
        'provincias_con_carga': sum(1 for r in province_rows if r['provincia'] != 'Buenos Aires' and r['cantidad_de_reclamos'] > 0),
    }

    with OUTPUT_SUMMARY_JSON.open('w', encoding='utf-8') as f:
        json.dump({'buenos_aires': ba, 'resto_provincias': resto}, f, ensure_ascii=False, indent=2)
        f.write('\n')

    manifest.setdefault('files', {})['reclamos_nacion_maestra'] = str(MASTER_FILE)
    manifest['files']['reclamos_nacion_catalogo'] = str(CATALOG_FILE)
    manifest['files']['reclamos_nacion_provincial_csv'] = str(OUTPUT_CSV)
    manifest['files']['reclamos_nacion_dashboard_json'] = str(OUTPUT_JSON)
    manifest['files']['reclamos_nacion_resumen'] = str(OUTPUT_SUMMARY_JSON)
    notes = manifest.setdefault('notes', {})
    notes['reclamos_nacion_scope'] = (
        'Matriz Nación→provincias con deuda total reclamada y robusta; distingue observado, estimado robusto, proxy y no disponible.'
    )

    with MANIFEST_FILE.open('w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    build()
