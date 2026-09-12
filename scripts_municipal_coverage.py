"""Inventory presence, periods and actionable municipal data gaps separately."""
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def enrich_coverage(data, cov):
    research = json.loads((ROOT / 'municipios/data/coverage_research.json').read_text(encoding='utf-8'))
    portals = json.loads((ROOT / 'municipios/data/fiscal_search.json').read_text(encoding='utf-8'))
    portals = {r['id']: r for r in portals['municipalities']}
    inventory = {r['id']: r for r in cov['municipalities']}
    matrix = []
    for m in data['municipalities']:
        row = inventory[m['id']]
        b, g = m.get('annualBudget') or {}, m.get('management') or {}
        p = portals[m['id']]
        portal = p.get('accountUrl') or p.get('providedUrl') or ''
        row['portalUrl'] = portal
        row['budgetYear'] = b.get('year')
        row['budgetAsOf'] = b.get('asOf')
        row['budgetOriginal2026'] = b.get('year') == 2026 and b.get('original') is not None
        row['budgetCurrent2026'] = b.get('year') == 2026 and b.get('current') is not None
        row['findings'] = [r for r in research['findings'] if r['id'] == m['id']]
        requests = []

        def item(topic, present, period, request, state=None):
            status = state or ('Incorporado' if present else 'Pendiente')
            matrix.append({'id': m['id'], 'municipio': m['municipio'], 'tema': topic,
                           'estado': status, 'periodo': period or '', 'documentoNecesario': '' if present else request,
                           'portal': portal, 'revision': research['reviewedAt']})
            if not present:
                requests.append({'topic': topic, 'state': status, 'request': request})

        item('Cuenta fiscal comparable', bool(m.get('fiscal')), 'enero–junio 2026',
             'Cuenta ahorro-inversión-financiamiento (CAIF) enero–junio 2026, o ejecuciones por carácter económico conciliadas que excluyan financiamiento.')
        item('Presupuesto original 2026', row['budgetOriginal2026'], str(b.get('year') or ''),
             'Ordenanza de presupuesto 2026 aprobada y total de erogaciones; identificar los organismos incluidos.')
        item('Presupuesto vigente 2026', row['budgetCurrent2026'], b.get('asOf'),
             'Crédito anual vigente 2026 y modificaciones, con fecha de corte y saldo inicial anual.')
        treasury = g.get('treasury') or {}
        item('Saldo de tesorería', bool(treasury), treasury.get('date'),
             'Estado de tesorería conciliado: bancos, efectivo, valores y fondos afectados. El saldo total no equivale a caja libre.')
        item('Caja libre', False, '',
             'Caja de libre disponibilidad conciliada, descontando fondos afectados y obligaciones exigibles.')
        debt = g.get('debt') or {}
        item('Stock de deuda municipal', bool(debt), '2025-12-31' if debt else '',
             'Planilla de deuda consolidada y flotante, contratos, moneda y corte; separar pasivos contables y evitar sumarlos dos veces.')
        item('Calendario futuro de deuda', False, '',
             'Planilla de vencimientos futuros de capital e intereses, por contrato y fecha; separar lo ya pagado del año.')
        item('Deuda con proveedores vencida', False, '',
             'Antigüedad y vencimiento de facturas pendientes, conciliados con la deuda flotante. Pendiente no significa vencida.')
        item('Flujos fiscales mensuales', False, '',
             'Ingresos percibidos y gastos devengados por mes, sin acumulación; necesarios para ajustar cada flujo por IPC.')
        history = g.get('history') or []
        years = sorted({int(r['fin'][:4]) for r in history if r['fin'][5:7] == '12' and r['inicio'][5:7] == '01'})
        complete_history = all(y in years for y in range(2021, 2026))
        item('Cierres fiscales anuales 2021–2025', complete_history, ', '.join(map(str, years)),
             'CAIF de cierre anual 2021–2025 con los mismos organismos; no anualizar semestres.',
             'Incorporado' if complete_history else 'Historia parcial' if history else 'Sin serie anual incorporada')
        item('Transferencias provinciales', bool(m.get('transfers')), '2025-01 a 2026-07', 'Serie mensual por concepto.')
        item('Empleo y salarios privados formales', bool(m.get('employment')), '2019-01 a 2025-12', 'Serie OEDE por departamento.')
        item('Población y condiciones de vida', all(m.get(k) is not None for k in ('poblacion_2022', 'hogares_nbi_2022_pct')), 'Censo 2022', 'Cuadros INDEC/DPE con población, hogares y definiciones.')
        item('Producto municipal', m.get('pbg_constante_2004_2023_ars') is not None, '2021–2023; precios 2004', 'PBG municipal DPE. No reemplazarlo por PBG provincial.')
        item('Delitos registrados', bool(m.get('community', {}).get('crime')), '2024–2025', 'Base SNIC por departamento, hechos y población de referencia.')
        item('Deuda de personas', bool(m.get('community', {}).get('debt')), '2026-07', 'Relevamiento CEC/FES con datos BCRA; no equivale a toda la deuda de los hogares.')
        bank = all(m.get(k) is not None for k in ('prestamos_2024_ars', 'depositos_2024_ars'))
        item('Préstamos y depósitos bancarios', bank, '2024-12',
             'Cifra publicada por localización BCRA/DPE; las reservas estadísticas no se completan con cero.',
             None if bank else 'Reservado o sin cifra de origen')
        industry = m.get('empleo_industrial_dic2025') is not None
        item('Empleo industrial', industry, '2025-12',
             'Dato sectorial OEDE publicado. No reconstruir celdas reservadas por diferencia.',
             None if industry else 'Reservado o sin cifra de origen')
        item('Desempleo, informalidad y pobreza por ingresos', False, '',
             'Encuesta representativa del municipio con metodología y muestra; los datos por aglomerado no representan automáticamente cada partido.', 'Sin serie comparable para 135')
        row['documentsNeeded'] = requests
        row['missing'] = list(dict.fromkeys(row['missing'] + [r['request'] for r in requests if r['topic'] in (
            'Presupuesto original 2026', 'Presupuesto vigente 2026', 'Saldo de tesorería', 'Caja libre',
            'Stock de deuda municipal', 'Calendario futuro de deuda', 'Deuda con proveedores vencida',
            'Flujos fiscales mensuales', 'Cierres fiscales anuales 2021–2025')]))
    topics = list(dict.fromkeys(r['tema'] for r in matrix))
    cov['topics'] = [{'topic': t, 'available': sum(r['estado'] == 'Incorporado' for r in matrix if r['tema'] == t),
                      'total': len(data['municipalities'])} for t in topics]
    cov['research'] = {k: v for k, v in research.items() if k != 'documents'}
    cov['matrix'] = matrix
    cov['commonPending'] = [
        'Caja libre, vencimientos futuros, antigüedad de proveedores y flujos fiscales mensuales: todavía no hay una serie comparable para los 135. Un saldo en tesorería no resuelve esos faltantes.',
        'Tesorería detallada: Las Heras a junio de 2026 y Tigre a diciembre de 2025. El stock de Tigre y los pasivos contables de Las Heras tienen distinto alcance.',
        'Los presupuestos tienen distintos cortes y organismos. Original aprobado y vigente se registran por separado.',
        'La historia fiscal detallada está incorporada para Las Heras y Tigre; en Las Heras falta el cierre anual 2023. Las transferencias mensuales visibles empiezan en 2025, aunque existen archivos oficiales anteriores.',
    ]
    return cov


def matrix_csv(cov):
    stream = io.StringIO(newline='')
    keys = ['id', 'municipio', 'tema', 'estado', 'periodo', 'documentoNecesario', 'portal', 'revision']
    writer = csv.DictWriter(stream, fieldnames=keys, delimiter=';', lineterminator='\n')
    writer.writeheader()
    writer.writerows(cov['matrix'])
    return '\ufeff' + stream.getvalue()
