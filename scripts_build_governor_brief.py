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
            "Buenos Aires tiene recursos, escala económica y capacidad de gestión: recauda por su cuenta casi la mitad de sus "
            "ingresos no previsionales. Aun así, hoy gasta más de lo que le entra, paga cada vez más intereses y los ingresos vienen "
            "recuperándose más despacio que el gasto. La salida no es un ajuste indiscriminado sobre la salud, la educación, la "
            "seguridad, los salarios y la actividad, ni una pelea federal sin estrategia. Hay que ordenar la caja, cuidar los servicios "
            "y la obra que realmente hacen falta, reclamar por las vías institucionales los recursos que debe Nación y fortalecer la "
            "producción bonaerense. El problema urgente es financiero; la respuesta tiene que ser gradual, productiva y federal."
        ),
        "federal_metrics": {
            "national_tax_share_pct": number(latest, "national_tax_share_pct"),
            "autonomy_ex_ss_pct": number(latest, "autonomy_ex_ss_pct"),
            "ron_per_capita_vs_average_pct": 37,
            "ron_per_capita_rank": 23,
            "ron_per_capita_universe": 23,
        },
        "federal_reading": (
            "Buenos Aires hace un esfuerzo fiscal propio importante, pero sigue muy condicionada por el esquema federal. "
            "Recauda por sí misma el 48,5% de sus ingresos no previsionales, mientras que los impuestos de origen nacional "
            "representan el 39,3% de los ingresos totales en los últimos 12 meses al 31 de marzo de 2026. A la vez, recibe por "
            "habitante apenas 37 cuando el promedio comparable recibe 100 y queda 23 de 23 entre las provincias. Eso muestra "
            "una desventaja estructural en el reparto por habitante."
        ),
        "federal_conclusion": (
            "Hay un problema federal real que debe reclamarse y cuantificarse, pero estos datos no alcanzan para atribuirle a Nación "
            "todo el déficit provincial. Las series de 2026 tienen cortes distintos y la matriz de reclamos todavía cubre sólo una "
            "parte del universo. La posición más sólida es defender los recursos bonaerenses con firmeza y datos, mientras la "
            "Provincia ordena su caja y el ritmo del gasto."
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
                "measurement": "Ratio nominal · acumulado móvil · sin desestacionalizar",
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
                "measurement": "Ratio nominal · trimestre · sin desestacionalizar",
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
                "measurement": "Stock / ingresos nominales · sin desestacionalizar",
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
                "measurement": "Indicador relativo · universo de 23 jurisdicciones",
                "interpretation": "Perdió un lugar: del puesto 15 al 16.",
            },
        ],
        "risks": [
            {
                "title": "La caja anual no alcanza para cubrir todo el gasto",
                "evidence": "En 12 meses se gastaron $106,60 por cada $100 ingresados: faltaron $2,70 antes de intereses y otros $3,90 después.",
                "political_meaning": "Por qué importa: si se repite, obliga a postergar pagos, obra o servicios, o a buscar financiamiento más caro.",
            },
            {
                "title": "El gasto crece más rápido que los ingresos",
                "evidence": "En el 1T26 los ingresos reales cayeron 0,8% y el gasto primario real creció 2,0% contra el 1T25. Son variaciones interanuales reales, no desestacionalizadas.",
                "political_meaning": "Por qué importa: la inflación puede hacer subir los montos nominales y ocultar que el poder de compra de los recursos está cayendo.",
            },
            {
                "title": "La deuda bajó, pero todavía condiciona decisiones",
                "evidence": "Equivale a 45,2% de los ingresos y ubica a PBA 23 de 23 en este indicador comparativo.",
                "political_meaning": "Por qué importa: una mejora del ratio no demuestra que haya caja para aguinaldo y vencimientos; esos datos todavía faltan.",
            },
        ],
        "decisions": [
            {
                "horizon": "30 días",
                "action": "Instalar una mesa semanal de caja y prioridades.",
                "why": "Ordenar cada pago por fecha y criticidad: salarios y aguinaldo, salud, educación, seguridad, proveedores pyme y obra estratégica. Sin saldo de Tesorería y vencimientos no debe prometerse cobertura.",
            },
            {
                "horizon": "90 días",
                "action": "Defender los recursos bonaerenses por vías institucionales.",
                "why": "Consolidar cada deuda de Nación, cuantificar su efecto por municipio y servicio, y avanzar por gestión administrativa, CFI y justicia. Retener unilateralmente coparticipación no es una herramienta operativa ni jurídicamente prudente.",
            },
            {
                "horizon": "180 días",
                "action": "Acordar un programa productivo y de gasto con resultados medibles.",
                "why": "Revisar compras y programas de bajo impacto, mejorar cumplimiento tributario sin subir alícuotas de forma general y concentrar la inversión en empleo, pymes e infraestructura que amplíe la base económica.",
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
