#!/usr/bin/env python3
"""Build the PBA governor brief from audited 1816 inputs.

The inputs are deliberately small and reviewable. Values copied from charts must
carry evidence_status=visual_and_table_verified before they can reach the UI.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SNAPSHOTS = ROOT / "data/1816/pba_fiscal_snapshots.csv"
RANKING = ROOT / "data/1816/ranking_1t26.csv"
OUTPUT = ROOT / "dashboard_governor_brief.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def number(row: dict[str, str], field: str) -> float:
    return float(row[field])


def validate_snapshot(row: dict[str, str]) -> None:
    income = number(row, "total_income_m")
    spending = number(row, "primary_spending_m")
    primary = number(row, "primary_result_m")
    interest = number(row, "interest_m")
    financial = number(row, "financial_result_m")
    if abs((income - spending) - primary) > 1:
        raise ValueError(f"{row['period']}: primary result does not reconcile")
    if abs((primary + interest) - financial) > 1:
        raise ValueError(f"{row['period']}: financial result does not reconcile")
    if row["evidence_status"] != "visual_and_table_verified":
        raise ValueError(f"{row['period']}: chart values need visual verification")


def main() -> None:
    snapshots = read_csv(SNAPSHOTS)
    if [row["period"] for row in snapshots] != ["2025-Q4", "2026-Q1"]:
        raise ValueError("Expected ordered snapshots 2025-Q4 and 2026-Q1")
    for row in snapshots:
        validate_snapshot(row)

    ranking = read_csv(RANKING)
    if len(ranking) != 23 or {int(row["general_rank"]) for row in ranking} != set(range(1, 24)):
        raise ValueError("The latest 1816 ranking must contain exactly ranks 1-23")
    latest = snapshots[-1]
    previous = snapshots[-2]
    pba_rank = next(row for row in ranking if row["province"] == "Buenos Aires")
    if int(pba_rank["general_rank"]) != int(latest["general_rank"]):
        raise ValueError("PBA rank differs between the snapshot and ranking table")

    payload = {
        "province": "Buenos Aires",
        "as_of": latest["report_cutoff"],
        "status": "se_deteriora",
        "headline": "El trimestre todavía deja margen primario, pero la Provincia gasta más de lo que ingresa en la mirada anual.",
        "plain_language_verdict": (
            "La Provincia no está sin recursos: recauda casi la mitad de sus ingresos no previsionales por cuenta propia. "
            "El problema es que el gasto supera a los ingresos y los intereses agrandan el déficit."
        ),
        "key_metrics": [
            {
                "id": "financial_ltm",
                "label": "Resultado financiero",
                "value": number(latest, "financial_result_pct"),
                "unit": "% de ingresos",
                "window": "últimos 12 meses",
                "comparison": round(number(latest, "financial_result_pct") - number(previous, "financial_result_pct"), 1),
                "comparison_unit": "p.p. vs 4T25",
                "signal": "red",
                "interpretation": "Por cada $100 que ingresaron, faltaron $6,60 después de intereses.",
            },
            {
                "id": "quarter_financial",
                "label": "Resultado del 1T",
                "value": number(latest, "quarter_financial_pct"),
                "unit": "% de ingresos",
                "window": "enero-marzo 2026",
                "comparison": round(number(latest, "quarter_financial_pct") - number(latest, "quarter_comparator_financial_pct"), 1),
                "comparison_unit": "p.p. vs 1T25",
                "signal": "red",
                "interpretation": "El primario fue positivo, pero los intereses llevaron el trimestre a déficit.",
            },
            {
                "id": "debt_income",
                "label": "Deuda / ingresos",
                "value": number(latest, "debt_income_pct"),
                "unit": "%",
                "window": "último dato homogéneo",
                "comparison": round(number(latest, "debt_income_pct") - number(previous, "debt_income_pct"), 1),
                "comparison_unit": "p.p. vs 4T25",
                "signal": "amber",
                "interpretation": "La relación bajó, pero PBA sigue última entre las 23 jurisdicciones comparadas.",
            },
            {
                "id": "general_rank",
                "label": "Ranking fiscal",
                "value": int(latest["general_rank"]),
                "unit": f"de {latest['universe']}",
                "window": "últimos 12 meses",
                "comparison": int(latest["general_rank"]) - int(previous["general_rank"]),
                "comparison_unit": "puesto vs 4T25",
                "signal": "amber",
                "interpretation": "Perdió un lugar: del puesto 15 al 16.",
            },
        ],
        "risks": [
            {
                "title": "Déficit persistente",
                "evidence": "Resultado financiero de -6,6% de los ingresos en los últimos 12 meses.",
                "political_meaning": "Reduce margen para salarios, obra y respuesta ante una emergencia.",
            },
            {
                "title": "Ingresos débiles frente al gasto",
                "evidence": "En el 1T26 los ingresos reales cayeron 0,8% y el gasto primario creció 2,0% interanual.",
                "political_meaning": "Sin corrección, la brecha vuelve a presionar caja y financiamiento.",
            },
            {
                "title": "Deuda todavía condicionante",
                "evidence": "Deuda equivalente a 45,2% de los ingresos; puesto 23 de 23 en este indicador.",
                "political_meaning": "La baja del ratio ayuda, pero no resuelve vencimientos ni exposición financiera.",
            },
        ],
        "decisions": [
            {
                "horizon": "30 días",
                "action": "Cerrar un parte semanal de caja, salarios, aguinaldo y vencimientos.",
                "why": "El informe fiscal no contiene saldo de Tesorería ni calendario 90/180 días.",
            },
            {
                "horizon": "90 días",
                "action": "Fijar un límite real al gasto primario y proteger servicios esenciales y obra prioritaria.",
                "why": "El gasto crece por encima de los ingresos y el capital bajó de 8,4% a 8,1% del gasto comparable.",
            },
            {
                "horizon": "180 días",
                "action": "Separar la negociación con Nación del plan de ordenamiento propio.",
                "why": "La autonomía es alta para el conjunto provincial, pero no alcanza para absorber déficit e intereses.",
            },
        ],
        "missing_for_decision": [
            "Caja disponible consolidada y fondos con afectación específica",
            "Cobertura exacta de salarios y aguinaldo",
            "Vencimientos de capital e intereses a 90 y 180 días",
            "Compromisos salariales y de proveedores ya devengados",
        ],
        "methodology": {
            "quarter_vs_ltm": "El trimestre mide la coyuntura; los últimos 12 meses muestran la tendencia estructural. No se mezclan.",
            "facts_inferences_actions": "Las cifras son hechos publicados; su lectura política es una inferencia; las decisiones son propuestas.",
            "ranking_universe": "23 jurisdicciones con información homogénea. La Pampa no integra el informe.",
            "money_unit": "Millones de pesos corrientes en las tablas absolutas.",
        },
        "sources": [
            {"report": "Provincias 4T25", "pages": [7, 8, 23, 27], "cutoff": previous["report_cutoff"]},
            {"report": "Provincias 1T26", "pages": [7, 8, 23, 27], "cutoff": latest["report_cutoff"]},
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {OUTPUT.name} built from {len(snapshots)} snapshots and {len(ranking)} ranked provinces")


if __name__ == "__main__":
    main()
