#!/usr/bin/env python3
"""Construye la capa federal comparable de resultados de gobierno.

Fuentes oficiales:
- SNIC 2024-2025: tasa de víctimas de homicidio doloso.
- Aprender Secundaria 2024: Lengua, Matemática y participación.
- DEIS 2024: mortalidad infantil y población proyectada.
- INDEC Censo 2022: hogares con NBI y tipologías seleccionadas.
- DNAP 2024: gasto APNF por finalidad y función.

El archivo final separa resultado, contexto estructural y esfuerzo fiscal. No
calcula causalidad ni un ranking compuesto de gestión.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import tempfile
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
OUTPUT_JSON = ROOT / "data/government_results_provinces.json"
OUTPUT_CSV = ROOT / "data/government_results/official_metrics.csv"
LEGACY_PBA = ROOT / "data/government_results_pba.json"

SNIC_API = "https://apis.datos.gob.ar/series/api/series"
SNIC_PAGE = "https://www.argentina.gob.ar/seguridad/estadisticascriminales"
APRENDER_PAGE = "https://www.argentina.gob.ar/educacion/evaluacion-informacion-educativa/aprender/aprender-2024/informes-jurisdiccionales-de-aprender-secundaria-2024"
APRENDER_BASE = "https://www.argentina.gob.ar/sites/default/files/2025/07"
DEIS_URL = "https://www.argentina.gob.ar/sites/default/files/serie_5_nro_68_anuario_vitales_v4_revisada_ok.pdf"
NBI_URL = "https://www.indec.gob.ar/ftp/cuadros/sociedad/serie_nbi_2022.xlsx"
SPENDING_URL = "https://www.argentina.gob.ar/sites/default/files/gfyf_apnf_2024_-_trim._iv_1.xlsx"
SPENDING_PAGE = "https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/gastos-por"


PROVINCES: list[dict[str, str]] = [
    {"name": "Buenos Aires", "code": "06", "aprender": "buenos_aires_2024.pdf"},
    {"name": "CABA", "code": "02", "aprender": "ciudad_autonoma_de_buenos_aires_2024.pdf"},
    {"name": "Catamarca", "code": "10", "aprender": "catamarca_2024.pdf"},
    {"name": "Chaco", "code": "22", "aprender": "chaco_2024.pdf"},
    {"name": "Chubut", "code": "26", "aprender": "chubut_2024.pdf"},
    {"name": "Corrientes", "code": "18", "aprender": "corrientes_2024.pdf"},
    {"name": "Córdoba", "code": "14", "aprender": "cordoba_2024.pdf"},
    {"name": "Entre Ríos", "code": "30", "aprender": "entre_rios_2024.pdf"},
    {"name": "Formosa", "code": "34", "aprender": "formosa_2024.pdf"},
    {"name": "Jujuy", "code": "38", "aprender": "jujuy_2024.pdf"},
    {"name": "La Pampa", "code": "42", "aprender": "la_pampa_2024.pdf"},
    {"name": "La Rioja", "code": "46", "aprender": "la_rioja_2024.pdf"},
    {"name": "Mendoza", "code": "50", "aprender": "mendoza_2024.pdf"},
    {"name": "Misiones", "code": "54", "aprender": "misiones_2024.pdf"},
    {"name": "Neuquén", "code": "58", "aprender": "neuquen_2024.pdf"},
    {"name": "Río Negro", "code": "62", "aprender": "rio_negro_2024.pdf"},
    {"name": "Salta", "code": "66", "aprender": "salta_2024.pdf"},
    {"name": "San Juan", "code": "70", "aprender": "san_juan_2024.pdf"},
    {"name": "San Luis", "code": "74", "aprender": "san_luis_2024.pdf"},
    {"name": "Santa Cruz", "code": "78", "aprender": "santa_cruz_2024.pdf"},
    {"name": "Santa Fe", "code": "82", "aprender": "santa_fe_2024.pdf"},
    {"name": "Santiago del Estero", "code": "86", "aprender": "santiago_del_estero_2024.pdf"},
    {"name": "Tierra del Fuego", "code": "94", "aprender": "tierra_del_fuego_2024.pdf"},
    {"name": "Tucumán", "code": "90", "aprender": "tucuman_2024.pdf"},
]


ALIASES = {
    "Ciudad Autónoma de Buenos Aires": "CABA",
    "Ciud. Aut. de Buenos Aires": "CABA",
    "Ciud. Aut. Bs. As.": "CABA",
    "Sgo. del Estero": "Santiago del Estero",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur": "Tierra del Fuego",
}


def normalize_province(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return ALIASES.get(text, text)


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 tablero-fiscal-provincias"})
    with urllib.request.urlopen(request, timeout=90) as response:
        destination.write_bytes(response.read())


def decimal_es(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def format_decimal(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def format_money_per_capita(value: float) -> str:
    rounded = round(value / 1000)
    return f"$ {rounded:,.0f} mil".replace(",", ".")


def fetch_security(province: dict[str, str]) -> dict[str, Any]:
    series_id = f"t_snic_1_victimas_{province['code']}"
    url = f"{SNIC_API}?ids={series_id}&start_date=2024-01-01&limit=10"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 tablero-fiscal-provincias"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    values = {row[0][:4]: float(row[1]) for row in payload.get("data", []) if row[1] is not None}
    if not {"2024", "2025"}.issubset(values):
        raise ValueError(f"SNIC incompleto para {province['name']}: {values}")
    change = (values["2025"] / values["2024"] - 1) * 100 if values["2024"] else None
    return {
        "security_rate_2024": values["2024"],
        "security_rate_2025": values["2025"],
        "security_change_pct": change,
        "source_security": url,
    }


def extract_text(reader: PdfReader) -> str:
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def first_match(pattern: str, text: str, label: str) -> re.Match[str]:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"No se pudo extraer {label}")
    return match


def parse_aprender(pdf_path: Path, source_url: str) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    if len(reader.pages) < 21:
        raise ValueError(f"Aprender con páginas insuficientes: {pdf_path.name}")
    text = extract_text(reader)
    results = first_match(
        r"En el caso de.{0,320}?porcentajes son\s+(\d+,\d+)% y (\d+,\d+)% respectivamente",
        text,
        f"resultados Aprender en {pdf_path.name}",
    )
    language_2022 = first_match(
        r"En 2022 el porcentaje.{0,260}?era de\s+(\d+,\d+)%",
        text,
        f"Lengua 2022 en {pdf_path.name}",
    )
    math_2022 = first_match(
        r"En tanto, en 2022.{0,180}?(\d+,\d+)%",
        text,
        f"Matemática 2022 en {pdf_path.name}",
    )
    participation_page = reader.pages[10].extract_text() or ""
    students = first_match(
        r"(\d[\d.]*) estudiantes \((\d+,\d+)%\)",
        participation_page,
        f"participación estudiantil en {pdf_path.name}",
    )
    schools = first_match(
        r"(\d[\d.]*) escuelas \((\d+,\d+)%\)",
        participation_page,
        f"participación de escuelas en {pdf_path.name}",
    )
    return {
        "education_language_high_2024": decimal_es(results.group(1)),
        "education_math_high_2024": decimal_es(results.group(2)),
        "education_language_high_2022": decimal_es(language_2022.group(1)),
        "education_math_high_2022": decimal_es(math_2022.group(1)),
        "education_student_participation_pct": decimal_es(students.group(2)),
        "education_school_participation_pct": decimal_es(schools.group(2)),
        "source_education": source_url,
    }


def parse_health(pdf_path: Path) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    reader = PdfReader(str(pdf_path))
    history_text = reader.pages[122].extract_text() or ""
    population_text = reader.pages[153].extract_text() or ""
    expected = {province["name"] for province in PROVINCES}
    history: dict[str, dict[str, float]] = {}
    population: dict[str, int] = {}
    for line in history_text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        for source_name in ["Ciud. Aut. de Buenos Aires", *[p["name"] for p in PROVINCES if p["name"] != "CABA"]]:
            if not clean.startswith(source_name + " "):
                continue
            province = normalize_province(source_name)
            values = re.findall(r"\d+,\d+", clean[len(source_name):])
            if len(values) != 12:
                raise ValueError(f"Historia DEIS incompleta para {province}: {values}")
            floats = [decimal_es(value) for value in values]
            history[province] = {"2022": floats[-3], "2023": floats[-2], "2024": floats[-1]}
            break
    for line in population_text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        population_names = [
            "Ciud. Aut. Bs. As.",
            "Sgo. del Estero",
            *[p["name"] for p in PROVINCES if p["name"] not in {"CABA", "Santiago del Estero"}],
        ]
        for source_name in population_names:
            if not clean.startswith(source_name + " "):
                continue
            province = normalize_province(source_name)
            total = re.search(r"\s(\d{1,3}(?:\.\d{3})+)\s", clean[len(source_name):] + " ")
            if not total:
                raise ValueError(f"Población DEIS incompleta para {province}: {clean}")
            population[province] = int(total.group(1).replace(".", ""))
            break
    if set(history) != expected:
        raise ValueError(f"Cobertura DEIS historia: faltan {sorted(expected - set(history))}")
    if set(population) != expected:
        raise ValueError(f"Cobertura DEIS población: faltan {sorted(expected - set(population))}")
    return history, population


def parse_nbi(path: Path) -> dict[str, dict[str, float]]:
    dataframe = pd.read_excel(path, sheet_name="NBI_Hogares%", header=None)
    expected = {province["name"] for province in PROVINCES}
    output: dict[str, dict[str, float]] = {}
    for _, row in dataframe.iloc[5:].iterrows():
        province = normalize_province(row.iloc[0])
        if province not in expected:
            continue
        output[province] = {
            "nbi_households_pct_2010": float(row.iloc[1]),
            "nbi_households_pct_2022": float(row.iloc[9]),
            "nbi_housing_pct_2022": float(row.iloc[11]),
            "nbi_sanitary_pct_2022": float(row.iloc[12]),
            "nbi_overcrowding_pct_2022": float(row.iloc[13]),
        }
    if set(output) != expected:
        raise ValueError(f"Cobertura NBI: faltan {sorted(expected - set(output))}")
    return output


def parse_spending(path: Path, population: dict[str, int]) -> dict[str, dict[str, float]]:
    dataframe = pd.read_excel(path, sheet_name="IV TRIM 2024 PARA PUBLICAR", header=None)
    header = dataframe.iloc[8]
    columns = {normalize_province(value): index for index, value in header.items()}
    concepts = {str(dataframe.iloc[row_index, 0]).strip(): row_index for row_index in range(9, 24)}
    concept_map = {
        "spend_security_pc_2024": "Servicios de seguridad",
        "spend_health_pc_2024": "Salud",
        "spend_education_culture_pc_2024": "Educación y cultura",
        "spend_social_assistance_pc_2024": "Promoción y asistencia social",
    }
    output: dict[str, dict[str, float]] = {}
    for province in (item["name"] for item in PROVINCES):
        column = columns.get(province)
        if column is None:
            raise ValueError(f"DNAP sin columna para {province}")
        values: dict[str, float] = {}
        for field, concept in concept_map.items():
            amount_millions = float(dataframe.iloc[concepts[concept], column])
            values[field] = amount_millions * 1_000_000 / population[province]
        output[province] = values
    return output


def rank_map(rows: list[dict[str, Any]], field: str, lower_is_better: bool, eligible_field: str | None = None) -> tuple[dict[str, int | None], int]:
    eligible = [
        row for row in rows
        if row.get(field) is not None and (eligible_field is None or bool(row.get(eligible_field)))
    ]
    ordered = sorted(eligible, key=lambda row: float(row[field]), reverse=not lower_is_better)
    ranks: dict[str, int | None] = {row["province"]: None for row in rows}
    previous: float | None = None
    previous_rank = 0
    for position, row in enumerate(ordered, start=1):
        value = float(row[field])
        if previous is None or not math.isclose(value, previous, abs_tol=1e-9):
            previous_rank = position
            previous = value
        ranks[row["province"]] = previous_rank
    return ranks, len(eligible)


def pct_change(current: float, previous: float) -> float | None:
    return (current / previous - 1) * 100 if previous else None


def result_metric(
    *, metric_id: str, label: str, value: float, display: str, period: str,
    direction: str, rank: int | None, rank_total: int, source_title: str,
    source_url: str, interpretation: str, change: float | None = None,
    change_unit: str = "pct", comparison_period: str | None = None,
    status: str = "auditado",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": metric_id,
        "label": label,
        "value": value,
        "display": display,
        "period": period,
        "direction": direction,
        "rank": rank,
        "rank_total": rank_total,
        "status": status,
        "source_title": source_title,
        "source_url": source_url,
        "interpretation": interpretation,
    }
    if change is not None:
        payload["change"] = change
        payload["change_unit"] = change_unit
        payload["comparison_period"] = comparison_period
    return payload


def build_payload(rows: list[dict[str, Any]], local_pba: dict[str, Any]) -> dict[str, Any]:
    ranks: dict[str, tuple[dict[str, int | None], int]] = {
        "security": rank_map(rows, "security_rate_2025", True),
        "language": rank_map(rows, "education_language_high_2024", False, "education_rank_eligible"),
        "math": rank_map(rows, "education_math_high_2024", False, "education_rank_eligible"),
        "health": rank_map(rows, "health_infant_mortality_2024", True),
        "nbi": rank_map(rows, "nbi_households_pct_2022", True),
        "housing": rank_map(rows, "nbi_housing_pct_2022", True),
        "sanitary": rank_map(rows, "nbi_sanitary_pct_2022", True),
    }
    provinces: dict[str, Any] = {}
    for row in rows:
        province = row["province"]
        security_change = row["security_change_pct"]
        security_verb = "bajó" if security_change < 0 else "subió" if security_change > 0 else "no cambió"
        education_status = "auditado" if row["education_rank_eligible"] else "parcial"
        education_note = (
            f"La participación estudiantil fue {format_decimal(row['education_student_participation_pct'])}%. "
            + ("Se muestra el dato, pero se excluye del ranking por baja participación." if not row["education_rank_eligible"] else "El ranking conserva esta cobertura visible.")
        )
        health_change = pct_change(row["health_infant_mortality_2024"], row["health_infant_mortality_2023"])
        health_verb = "bajó" if health_change is not None and health_change < 0 else "subió" if health_change is not None and health_change > 0 else "no cambió"
        nbi_change_pp = row["nbi_households_pct_2022"] - row["nbi_households_pct_2010"]
        pillars = [
            {
                "id": "security",
                "label": "Seguridad",
                "question": "¿Bajó la violencia letal?",
                "indicator_type": "resultado",
                "status": "auditado",
                "metrics": [
                    result_metric(
                        metric_id="homicide_rate", label="Víctimas de homicidio doloso",
                        value=row["security_rate_2025"], display=f"{format_decimal(row['security_rate_2025'])} cada 100.000",
                        period="2025", direction="lower_is_better",
                        rank=ranks["security"][0][province], rank_total=ranks["security"][1],
                        change=security_change, comparison_period="vs. 2024",
                        source_title="SNIC - estadísticas criminales provinciales",
                        source_url=row["source_security"],
                        interpretation=f"La tasa {security_verb} {format_decimal(abs(security_change))}% frente a 2024. Es el indicador de seguridad más comparable entre provincias, aunque no resume robos ni percepción de inseguridad.",
                    ),
                    result_metric(
                        metric_id="homicide_rate_previous", label="Tasa del año anterior",
                        value=row["security_rate_2024"], display=f"{format_decimal(row['security_rate_2024'])} cada 100.000",
                        period="2024", direction="context_required", rank=None, rank_total=24,
                        source_title="SNIC - estadísticas criminales provinciales", source_url=row["source_security"],
                        interpretation="Base utilizada para calcular la variación interanual.",
                    ),
                ],
            },
            {
                "id": "education",
                "label": "Educación",
                "question": "¿Cuántos estudiantes alcanzan los aprendizajes esperados?",
                "indicator_type": "resultado",
                "status": education_status,
                "quality_note": education_note,
                "metrics": [
                    result_metric(
                        metric_id="language_high", label="Lengua · satisfactorio o avanzado",
                        value=row["education_language_high_2024"], display=f"{format_decimal(row['education_language_high_2024'])}%",
                        period="Aprender Secundaria 2024", direction="higher_is_better",
                        rank=ranks["language"][0][province], rank_total=ranks["language"][1],
                        change=row["education_language_high_2024"] - row["education_language_high_2022"], change_unit="pp",
                        comparison_period="vs. Aprender 2022",
                        source_title="Aprender Secundaria 2024 - informe jurisdiccional", source_url=row["source_education"],
                        interpretation=f"{format_decimal(row['education_language_high_2024'])} de cada 100 estudiantes alcanzaron los dos niveles superiores en Lengua.", status=education_status,
                    ),
                    result_metric(
                        metric_id="math_high", label="Matemática · satisfactorio o avanzado",
                        value=row["education_math_high_2024"], display=f"{format_decimal(row['education_math_high_2024'])}%",
                        period="Aprender Secundaria 2024", direction="higher_is_better",
                        rank=ranks["math"][0][province], rank_total=ranks["math"][1],
                        change=row["education_math_high_2024"] - row["education_math_high_2022"], change_unit="pp",
                        comparison_period="vs. Aprender 2022",
                        source_title="Aprender Secundaria 2024 - informe jurisdiccional", source_url=row["source_education"],
                        interpretation="Mide el porcentaje que alcanzó desempeño satisfactorio o avanzado en Matemática.", status=education_status,
                    ),
                ],
                "participation": {
                    "students_pct": row["education_student_participation_pct"],
                    "schools_pct": row["education_school_participation_pct"],
                    "rank_eligible": row["education_rank_eligible"],
                },
            },
            {
                "id": "health",
                "label": "Salud",
                "question": "¿Mejoró la supervivencia durante el primer año de vida?",
                "indicator_type": "resultado",
                "status": "auditado",
                "metrics": [
                    result_metric(
                        metric_id="infant_mortality", label="Mortalidad infantil",
                        value=row["health_infant_mortality_2024"], display=f"{format_decimal(row['health_infant_mortality_2024'])} cada 1.000",
                        period="2024", direction="lower_is_better",
                        rank=ranks["health"][0][province], rank_total=ranks["health"][1],
                        change=health_change, comparison_period="vs. 2023",
                        source_title="DEIS - Estadísticas Vitales 2024", source_url=DEIS_URL,
                        interpretation=f"La tasa {health_verb} {format_decimal(abs(health_change or 0))}% frente a 2023. En provincias pequeñas conviene mirar también el promedio trianual porque pocos casos pueden mover mucho el porcentaje.",
                    ),
                    result_metric(
                        metric_id="infant_mortality_three_year", label="Promedio 2022-2024",
                        value=row["health_infant_mortality_avg_2022_2024"], display=f"{format_decimal(row['health_infant_mortality_avg_2022_2024'])} cada 1.000",
                        period="promedio 2022-2024", direction="lower_is_better", rank=None, rank_total=24,
                        source_title="DEIS - Estadísticas Vitales 2024", source_url=DEIS_URL,
                        interpretation="Suaviza la volatilidad anual y permite una lectura más estable.",
                    ),
                ],
            },
            {
                "id": "social",
                "label": "Condiciones sociales",
                "question": "¿Qué proporción de hogares tenía carencias estructurales?",
                "indicator_type": "contexto_estructural",
                "status": "auditado",
                "metrics": [
                    result_metric(
                        metric_id="nbi_households", label="Hogares con al menos una NBI",
                        value=row["nbi_households_pct_2022"], display=f"{format_decimal(row['nbi_households_pct_2022'])}%",
                        period="Censo 2022", direction="lower_is_better",
                        rank=ranks["nbi"][0][province], rank_total=ranks["nbi"][1],
                        change=nbi_change_pp, change_unit="pp", comparison_period="vs. Censo 2010",
                        source_title="INDEC - Necesidades Básicas Insatisfechas", source_url=NBI_URL,
                        interpretation=f"El porcentaje bajó {format_decimal(abs(nbi_change_pp))} puntos frente al Censo 2010. Es una condición estructural: no debe atribuirse por sí sola al gobierno actual.",
                    ),
                    result_metric(
                        metric_id="nbi_overcrowding", label="Hacinamiento crítico",
                        value=row["nbi_overcrowding_pct_2022"], display=f"{format_decimal(row['nbi_overcrowding_pct_2022'])}%",
                        period="Censo 2022", direction="lower_is_better", rank=None, rank_total=24,
                        source_title="INDEC - Necesidades Básicas Insatisfechas", source_url=NBI_URL,
                        interpretation="Hogares con más de tres personas por cuarto.",
                    ),
                ],
            },
            {
                "id": "infrastructure",
                "label": "Vivienda y saneamiento",
                "question": "¿Qué déficits habitacionales básicos persisten?",
                "indicator_type": "contexto_estructural",
                "status": "auditado",
                "metrics": [
                    result_metric(
                        metric_id="nbi_housing", label="Vivienda inconveniente",
                        value=row["nbi_housing_pct_2022"], display=f"{format_decimal(row['nbi_housing_pct_2022'])}%",
                        period="Censo 2022", direction="lower_is_better",
                        rank=ranks["housing"][0][province], rank_total=ranks["housing"][1],
                        source_title="INDEC - Necesidades Básicas Insatisfechas", source_url=NBI_URL,
                        interpretation="Hogares en viviendas precarias, habitaciones de inquilinato o espacios no destinados originalmente a vivienda.",
                    ),
                    result_metric(
                        metric_id="nbi_sanitary", label="Sin inodoro",
                        value=row["nbi_sanitary_pct_2022"], display=f"{format_decimal(row['nbi_sanitary_pct_2022'])}%",
                        period="Censo 2022", direction="lower_is_better",
                        rank=ranks["sanitary"][0][province], rank_total=ranks["sanitary"][1],
                        source_title="INDEC - Necesidades Básicas Insatisfechas", source_url=NBI_URL,
                        interpretation="Es un piso severo de déficit sanitario; no equivale a la falta de cloacas de red.",
                    ),
                ],
            },
            {
                "id": "effort",
                "label": "Esfuerzo presupuestario asociado",
                "question": "¿Cuánto gastó la provincia por habitante en estas funciones?",
                "indicator_type": "esfuerzo_fiscal",
                "status": "auditado",
                "quality_note": "Pesos corrientes de 2024 por habitante. Sirve para comparar esfuerzo, no demuestra que el gasto haya causado el resultado.",
                "metrics": [
                    {"id": "spend_security_pc", "label": "Seguridad", "value": row["spend_security_pc_2024"], "display": format_money_per_capita(row["spend_security_pc_2024"]), "period": "2024", "status": "auditado"},
                    {"id": "spend_health_pc", "label": "Salud", "value": row["spend_health_pc_2024"], "display": format_money_per_capita(row["spend_health_pc_2024"]), "period": "2024", "status": "auditado"},
                    {"id": "spend_education_pc", "label": "Educación y cultura", "value": row["spend_education_culture_pc_2024"], "display": format_money_per_capita(row["spend_education_culture_pc_2024"]), "period": "2024", "status": "auditado"},
                    {"id": "spend_social_pc", "label": "Promoción y asistencia social", "value": row["spend_social_assistance_pc_2024"], "display": format_money_per_capita(row["spend_social_assistance_pc_2024"]), "period": "2024", "status": "auditado"},
                ],
                "source_title": "DNAP - Gasto por finalidad y función APNF 2024",
                "source_url": SPENDING_PAGE,
            },
        ]
        provinces[province] = {
            "province": province,
            "pillars": pillars,
            "local_detail": local_pba.get("pillars", []) if province == "Buenos Aires" else [],
        }
    return {
        "schema_version": 1,
        "generated_at": date.today().isoformat(),
        "province_universe": [province["name"] for province in PROVINCES],
        "methodology": "Capa federal comparable. Separa resultados recientes, contexto estructural y esfuerzo presupuestario. Cada indicador conserva su período, fuente, dirección y elegibilidad para ranking.",
        "rank_rules": {
            "method": "ranking de competencia: 1 + cantidad de jurisdicciones con resultado estrictamente mejor; los empates comparten posición",
            "direction": "homicidios, mortalidad infantil y privaciones: menor es mejor; aprendizaje: mayor es mejor",
            "education": "se publica el dato de las 24 jurisdicciones, pero se excluye del ranking cuando respondió menos del 50% de la matrícula del marco",
            "no_composite": "no se calcula un ranking general de gobierno ni se atribuye causalidad entre gasto y resultado",
        },
        "sources": {
            "security": {"period": "2025", "url": SNIC_PAGE, "coverage": "24/24"},
            "education": {"period": "2024", "url": APRENDER_PAGE, "coverage": "24/24 con participación visible"},
            "health": {"period": "2024", "url": DEIS_URL, "coverage": "24/24"},
            "social_and_housing": {"period": "2022", "url": NBI_URL, "coverage": "24/24", "type": "contexto estructural"},
            "spending": {"period": "2024", "url": SPENDING_PAGE, "coverage": "24/24", "type": "esfuerzo fiscal APNF"},
        },
        "provinces": provinces,
    }


def main() -> None:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="government-results-") as temporary:
        temp = Path(temporary)
        vitales = temp / "deis_vitales_2024.pdf"
        nbi = temp / "serie_nbi_2022.xlsx"
        spending = temp / "gasto_finalidad_funcion_2024.xlsx"
        download(DEIS_URL, vitales)
        download(NBI_URL, nbi)
        download(SPENDING_URL, spending)
        health, population = parse_health(vitales)
        nbi_data = parse_nbi(nbi)
        spending_data = parse_spending(spending, population)
        for province in PROVINCES:
            name = province["name"]
            education_url = f"{APRENDER_BASE}/{province['aprender']}"
            education_pdf = temp / province["aprender"]
            try:
                download(education_url, education_pdf)
            except Exception:
                if name != "Santiago del Estero":
                    raise
                education_url = education_url.replace("www.argentina.gob.ar", "back.argentina.gob.ar")
                download(education_url, education_pdf)
            row: dict[str, Any] = {"province": name}
            row.update(fetch_security(province))
            row.update(parse_aprender(education_pdf, education_url))
            row.update({
                "health_infant_mortality_2022": health[name]["2022"],
                "health_infant_mortality_2023": health[name]["2023"],
                "health_infant_mortality_2024": health[name]["2024"],
                "health_infant_mortality_avg_2022_2024": sum(health[name].values()) / 3,
                "population_2024": population[name],
                "source_health": DEIS_URL,
            })
            row.update(nbi_data[name])
            row.update(spending_data[name])
            row.update({
                "education_rank_eligible": row["education_student_participation_pct"] >= 50,
                "source_social": NBI_URL,
                "source_spending": SPENDING_URL,
            })
            rows.append(row)
    if len(rows) != 24 or {row["province"] for row in rows} != {item["name"] for item in PROVINCES}:
        raise ValueError("La base federal no cubre exactamente las 24 jurisdicciones")
    local_pba = json.loads(LEGACY_PBA.read_text(encoding="utf-8"))
    payload = build_payload(rows, local_pba)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = list(rows[0].keys())
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Resultados federales: {len(rows)} jurisdicciones")
    print(f"Educación elegible para ranking: {sum(bool(row['education_rank_eligible']) for row in rows)}/24")
    print(f"JSON: {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"CSV auditable: {OUTPUT_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
