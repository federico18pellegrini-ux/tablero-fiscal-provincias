#!/usr/bin/env python3
"""Valida trazabilidad de recaudación propia 2026 publicada en insumos del tablero."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOP_FILE = ROOT / 'top_mensual_2026_normalizado.csv'
REAL_DYN_FILE = ROOT / 'dashboard_real_dynamics_inputs.csv'
OUT_FILE = ROOT / 'outputs' / 'top_2026_traceability_report.csv'


def load_top_totals() -> dict[tuple[str, str], float]:
    totals: dict[tuple[str, str], float] = defaultdict(float)
    with TOP_FILE.open(encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh):
            province = row['province']
            period = row['period']
            try:
                value = float(row['value_millions'])
            except (TypeError, ValueError):
                continue
            totals[(province, period)] += value
    return totals


def load_published_own_revenue() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with REAL_DYN_FILE.open(encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh):
            if row.get('metric') != 'own_revenue':
                continue
            if not row.get('current_nominal_millions'):
                continue
            rows.append(row)
    return rows


def main() -> int:
    totals = load_top_totals()
    published = load_published_own_revenue()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    mismatches = 0
    with OUT_FILE.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow([
            'province', 'period', 'published_millions', 'reconstructed_millions',
            'delta_millions', 'delta_pct', 'source_current', 'status'
        ])
        for row in published:
            province = row['province']
            period = row['period']
            published_value = float(row['current_nominal_millions'])
            reconstructed = totals.get((province, period), 0.0)
            delta = published_value - reconstructed
            delta_pct = (delta / reconstructed * 100.0) if reconstructed else None
            status = 'ok' if abs(delta) < 1e-6 else 'mismatch'
            if status == 'mismatch':
                mismatches += 1
            writer.writerow([
                province,
                period,
                f'{published_value:.6f}',
                f'{reconstructed:.6f}',
                f'{delta:.6f}',
                '' if delta_pct is None else f'{delta_pct:.6f}',
                row.get('source_current', ''),
                status,
            ])

    print(f'Reporte generado: {OUT_FILE}')
    print(f'Filas auditadas: {len(published)}')
    print(f'Diferencias: {mismatches}')
    return 1 if mismatches else 0


if __name__ == '__main__':
    raise SystemExit(main())
