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
OUTPUT_BA_CASE_CSV = Path('data/reclamos_nacion/reclamos_nacion_buenos_aires_caso_testigo.csv')
OUTPUT_BA_SUMMARY_JSON = Path('outputs/reclamos_nacion_buenos_aires_resumen.json')

ROBUST_QUALITIES = {'observado', 'estimado_robusto'}
ALL_QUALITIES = {'observado', 'estimado_robusto', 'proxy', 'no_disponible'}
ALLOWED_INDEXERS = {'ipc_nacional', 'sin_actualizacion', 'none', ''}
ALLOWED_CURRENCIES = {'ARS', 'USD', 'EUR'}
ALLOWED_STATUS = {
    'administrativo',
    'judicializado',
    'acuerdo_parcial',
    'cerrado',
    'pendiente_relevamiento',
}


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


def is_iso_date(value):
    txt = normalize_text(value)
    if txt == '':
        return False
    try:
        datetime.fromisoformat(txt)
        return True
    except ValueError:
        return False


def validate_master_row(row, province_universe):
    errors = []
    provincia = normalize_text(row.get('provincia'))
    if provincia == '':
        errors.append('provincia: obligatorio')
    elif province_universe and provincia not in province_universe:
        errors.append(f'provincia: fuera de universo ({provincia})')

    tipo = normalize_text(row.get('tipo_reclamo'))
    if tipo == '':
        errors.append('tipo_reclamo: obligatorio')

    expediente = normalize_text(row.get('expediente_o_causa'))
    if expediente == '':
        errors.append('expediente_o_causa: obligatorio')

    estado = normalize_text(row.get('estado_reclamo')).lower()
    if estado and estado not in ALLOWED_STATUS:
        errors.append(f'estado_reclamo: inválido ({estado})')

    calidad = normalize_text(row.get('calidad_dato'))
    if calidad and calidad not in ALL_QUALITIES:
        errors.append(f'calidad_dato: inválida ({calidad})')

    moneda = normalize_text(row.get('moneda'))
    if moneda and moneda not in ALLOWED_CURRENCIES:
        errors.append(f'moneda: inválida ({moneda})')

    indexador = normalize_text(row.get('indexador')).lower()
    if indexador not in ALLOWED_INDEXERS:
        errors.append(f'indexador: inválido ({indexador})')

    periodo_desde = normalize_text(row.get('periodo_desde'))
    periodo_hasta = normalize_text(row.get('periodo_hasta'))
    if periodo_desde and not is_iso_date(periodo_desde):
        errors.append(f'periodo_desde: fecha inválida ({periodo_desde})')
    if periodo_hasta and not is_iso_date(periodo_hasta):
        errors.append(f'periodo_hasta: fecha inválida ({periodo_hasta})')
    if periodo_desde and periodo_hasta and periodo_desde > periodo_hasta:
        errors.append('periodo_desde > periodo_hasta')

    fecha_corte = normalize_text(row.get('fecha_corte_monto'))
    if fecha_corte and not is_iso_date(fecha_corte):
        errors.append(f'fecha_corte_monto: fecha inválida ({fecha_corte})')

    monto_nominal = parse_float(row.get('monto_nominal'))
    monto_actualizado = parse_float(row.get('monto_actualizado'))
    tasa_interes = parse_float(row.get('tasa_interes'))
    if monto_nominal is not None and monto_nominal < 0:
        errors.append('monto_nominal: debe ser >= 0')
    if monto_actualizado is not None and monto_actualizado < 0:
        errors.append('monto_actualizado: debe ser >= 0')
    if tasa_interes is not None and (tasa_interes < 0 or tasa_interes > 5):
        errors.append('tasa_interes: fuera de rango [0, 5]')

    if calidad in {'observado', 'estimado_robusto'} and monto_actualizado is None and monto_nominal is None:
        errors.append('monto: obligatorio para calidad observado/estimado_robusto')
    if monto_actualizado is None and monto_nominal is not None and fecha_corte == '':
        errors.append('fecha_corte_monto: obligatoria cuando hay monto_nominal sin monto_actualizado')

    return errors


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


def claim_dedup_key(row):
    expediente = normalize_text(row.get('expediente_o_causa')).lower()
    if expediente:
        return f'expediente::{expediente}'
    provincia = normalize_text(row.get('provincia')).lower()
    tipo = normalize_text(row.get('tipo_reclamo')).lower()
    subtipo = normalize_text(row.get('subtipo_reclamo')).lower()
    organismo = normalize_text(row.get('organismo_nacional')).lower()
    return f'fallback::{provincia}::{tipo}::{subtipo}::{organismo}'


def deduplicate_claims(claims):
    unique = {}
    for claim in claims:
        key = claim_dedup_key(claim)
        current = unique.get(key)
        if current is None:
            unique[key] = claim
            continue

        current_amount = current.get('monto_actualizado_calculado')
        candidate_amount = claim.get('monto_actualizado_calculado')
        current_quality = normalize_text(current.get('calidad_dato'))
        candidate_quality = normalize_text(claim.get('calidad_dato'))

        if candidate_amount is not None and current_amount is None:
            unique[key] = claim
        elif candidate_amount is not None and current_amount is not None:
            if candidate_quality in ROBUST_QUALITIES and current_quality not in ROBUST_QUALITIES:
                unique[key] = claim
            elif candidate_quality == current_quality and candidate_amount > current_amount:
                unique[key] = claim

    return list(unique.values())


def aggregate_province_claims(claims):
    deduped_claims = deduplicate_claims(claims)
    total_reclamada = 0.0
    total_robusta = 0.0
    debt_by_type = defaultdict(float)
    claim_count = len(deduped_claims)
    judicialized = 0
    latest_date = None
    observed_anchors = []
    principal_org = None
    observations = []

    for claim in deduped_claims:
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

    robust_pct = round(robust_share(deduped_claims), 2)
    missing_amounts = any(
        normalize_text(c.get('calidad_dato')) in ROBUST_QUALITIES and c.get('monto_actualizado_calculado') is None
        for c in deduped_claims
    )
    coverage_insufficient = (
        claim_count > 0 and (
            robust_pct < 100
            or missing_amounts
            or total_reclamada == 0
        )
    )

    if not deduped_claims:
        estado_cobertura = 'sin_carga'
    elif coverage_insufficient:
        estado_cobertura = 'cobertura_insuficiente'
    else:
        estado_cobertura = 'con_datos'

    return {
        'deuda_total_reclamada': round(total_reclamada, 2),
        'deuda_total_robusta': round(total_robusta, 2),
        'anclas_principales': anchors,
        'principal_tipo_reclamo': principal_type,
        'principal_organismo_nacional': principal_org,
        'porcentaje_cubierto_con_dato_robusto': robust_pct,
        'fecha_ultima_actualizacion': latest_date.isoformat() if latest_date else None,
        'deuda_por_tipo': {k: round(v, 2) for k, v in debt_by_type.items()},
        'cantidad_de_reclamos': claim_count,
        'cantidad_de_reclamos_judicializados': judicialized,
        'estado_cobertura': estado_cobertura,
        'cobertura_insuficiente': coverage_insufficient,
        'observaciones': observations[:3],
    }


def select_amount_for_export(claim):
    calculated = claim.get('monto_actualizado_calculado')
    if calculated is not None:
        return round(calculated, 2)
    updated = parse_float(claim.get('monto_actualizado'))
    if updated is not None:
        return round(updated, 2)
    nominal = parse_float(claim.get('monto_nominal'))
    if nominal is not None:
        return round(nominal, 2)
    return None


def build_ba_case_outputs(ba_claims):
    deduped = deduplicate_claims(ba_claims)
    sorted_claims = sorted(
        deduped,
        key=lambda c: (
            normalize_text(c.get('tipo_reclamo')),
            normalize_text(c.get('expediente_o_causa')),
        ),
    )

    OUTPUT_BA_CASE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_BA_CASE_CSV.open('w', encoding='utf-8', newline='') as f:
        fields = [
            'provincia',
            'tipo_reclamo',
            'organismo_nacional',
            'expediente_o_referencia',
            'monto',
            'fecha_corte',
            'calidad_dato',
            'observaciones',
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for claim in sorted_claims:
            writer.writerow(
                {
                    'provincia': normalize_text(claim.get('provincia')),
                    'tipo_reclamo': normalize_text(claim.get('tipo_reclamo')),
                    'organismo_nacional': normalize_text(claim.get('organismo_nacional')),
                    'expediente_o_referencia': normalize_text(claim.get('expediente_o_causa')),
                    'monto': select_amount_for_export(claim),
                    'fecha_corte': normalize_text(claim.get('fecha_corte_monto')),
                    'calidad_dato': normalize_text(claim.get('calidad_dato')),
                    'observaciones': normalize_text(claim.get('observaciones')),
                }
            )

    with_amount = [c for c in sorted_claims if select_amount_for_export(c) is not None]
    by_quality = defaultdict(int)
    by_type = defaultdict(float)
    for claim in sorted_claims:
        quality = normalize_text(claim.get('calidad_dato')) or 'no_informado'
        by_quality[quality] += 1
        amount = select_amount_for_export(claim)
        if amount is not None:
            by_type[normalize_text(claim.get('tipo_reclamo'))] += amount

    total_reclamado = round(sum(select_amount_for_export(c) or 0.0 for c in sorted_claims), 2)
    total_robusto = round(
        sum(
            (select_amount_for_export(c) or 0.0)
            for c in sorted_claims
            if normalize_text(c.get('calidad_dato')) in ROBUST_QUALITIES
        ),
        2,
    )

    summary_payload = {
        'provincia': 'Buenos Aires',
        'fecha_corte_reporte': max((normalize_text(c.get('fecha_corte_monto')) for c in sorted_claims), default=''),
        'cantidad_reclamos': len(sorted_claims),
        'cantidad_reclamos_con_monto': len(with_amount),
        'deuda_total_reclamada': total_reclamado,
        'deuda_total_robusta': total_robusto,
        'conteo_por_calidad_dato': dict(by_quality),
        'deuda_con_monto_por_tipo_reclamo': {k: round(v, 2) for k, v in by_type.items()},
        'nota': 'Caso testigo BA armado con evidencia disponible en el repositorio; donde la evidencia no cuantifica, se conserva calidad proxy o no_disponible.',
    }
    OUTPUT_BA_SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_BA_SUMMARY_JSON.open('w', encoding='utf-8') as f:
        json.dump(summary_payload, f, ensure_ascii=False, indent=2)
        f.write('\n')


def build():
    with MANIFEST_FILE.open(encoding='utf-8') as f:
        manifest = json.load(f)

    province_universe = manifest.get('province_universe', [])
    rows = read_csv(MASTER_FILE)
    _ = read_csv(CATALOG_FILE)
    deflator_table = load_deflator_table()

    validation_errors = []
    for idx, row in enumerate(rows, start=2):
        errs = validate_master_row(row, province_universe)
        for err in errs:
            validation_errors.append(f'fila {idx}: {err}')

    if validation_errors:
        joined = '\n'.join(validation_errors[:30])
        total = len(validation_errors)
        extra = '' if total <= 30 else f'\n... {total - 30} errores adicionales'
        raise ValueError(f'Validación fallida de tabla maestra ({total} errores):\n{joined}{extra}')

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
        aggregate = aggregate_province_claims(claims)

        methodology_note = (
            'deuda_total_reclamada suma montos actualizados disponibles; deuda_total_robusta incluye '
            'solo calidad observado/estimado_robusto y excluye proxy/no_disponible para evitar doble conteo.'
        )

        payload_row = {
            'provincia': province,
            'deuda_total_reclamada': aggregate['deuda_total_reclamada'],
            'deuda_total_robusta': aggregate['deuda_total_robusta'],
            'deuda_nacion_con_provincia': {
                'status': 'pendiente_diseno_funcional',
                'ready_for_render': False,
                'component_key': 'deuda_nacion_con_provincia',
                'cards': [],
                'last_update': aggregate['fecha_ultima_actualizacion'],
            },
            'anclas_principales': aggregate['anclas_principales'],
            'principal_tipo_reclamo': aggregate['principal_tipo_reclamo'],
            'principal_organismo_nacional': aggregate['principal_organismo_nacional'],
            'porcentaje_cubierto_con_dato_robusto': aggregate['porcentaje_cubierto_con_dato_robusto'],
            'fecha_ultima_actualizacion': aggregate['fecha_ultima_actualizacion'],
            'observaciones_metodologicas': methodology_note,
            'deuda_por_tipo': aggregate['deuda_por_tipo'],
            'cantidad_de_reclamos': aggregate['cantidad_de_reclamos'],
            'cantidad_de_reclamos_judicializados': aggregate['cantidad_de_reclamos_judicializados'],
            'estado_cobertura': aggregate['estado_cobertura'],
            'cobertura_insuficiente': aggregate['cobertura_insuficiente'],
            'observaciones': aggregate['observaciones'],
        }

        province_rows.append(payload_row)
        provinces_payload[province] = payload_row

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open('w', encoding='utf-8', newline='') as f:
        fields = [
            'provincia', 'deuda_total_reclamada', 'deuda_total_robusta', 'anclas_principales',
            'principal_tipo_reclamo', 'principal_organismo_nacional', 'porcentaje_cubierto_con_dato_robusto',
            'fecha_ultima_actualizacion', 'observaciones_metodologicas', 'cantidad_de_reclamos',
            'cantidad_de_reclamos_judicializados', 'estado_cobertura', 'cobertura_insuficiente'
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
        'integration_ready': {
            'selector_keys': ['deuda_total_reclamada', 'deuda_total_robusta'],
            'future_block_key': 'deuda_nacion_con_provincia',
            'future_block_status': 'pendiente_diseno_funcional',
        },
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
        'example_buenos_aires': {
            'title': 'Ejemplo de salida para Buenos Aires',
            'province': 'Buenos Aires',
            'selector_preview': {
                'deuda_total_reclamada': provinces_payload.get('Buenos Aires', {}).get('deuda_total_reclamada'),
                'deuda_total_robusta': provinces_payload.get('Buenos Aires', {}).get('deuda_total_robusta'),
            },
            'ui_hint': 'Mostrar dos tarjetas: Total reclamado y Total robusto, más un callout de cobertura.',
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
    build_ba_case_outputs(grouped.get('Buenos Aires', []))

    manifest.setdefault('files', {})['reclamos_nacion_maestra'] = str(MASTER_FILE)
    manifest['files']['reclamos_nacion_catalogo'] = str(CATALOG_FILE)
    manifest['files']['reclamos_nacion_provincial_csv'] = str(OUTPUT_CSV)
    manifest['files']['reclamos_nacion_dashboard_json'] = str(OUTPUT_JSON)
    manifest['files']['reclamos_nacion_resumen'] = str(OUTPUT_SUMMARY_JSON)
    manifest['files']['reclamos_nacion_ba_caso_testigo'] = str(OUTPUT_BA_CASE_CSV)
    manifest['files']['reclamos_nacion_ba_resumen'] = str(OUTPUT_BA_SUMMARY_JSON)
    notes = manifest.setdefault('notes', {})
    notes['reclamos_nacion_scope'] = (
        'Matriz Nación→provincias con deuda total reclamada y robusta; distingue observado, estimado robusto, proxy y no disponible.'
    )

    with MANIFEST_FILE.open('w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write('\n')


if __name__ == '__main__':
    build()
