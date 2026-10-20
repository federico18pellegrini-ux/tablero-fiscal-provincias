"""Cierre anual derivado de doce meses oficiales, sin imputación."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from scripts_regenerate_2026 import import_top, manifest_universe, write_csv

ROOT = Path(__file__).resolve().parent


def build():
    source = ROOT / "data/top_sources/top_mensual_2025_12.xlsx"
    rows, coverage = import_top(source, manifest_universe(), 2025)
    assert coverage["La Pampa"] == [f"2025-{m:02}" for m in range(1, 13)]
    values = defaultdict(float)
    for row in rows:
        if row["province"] == "La Pampa":
            values[row["tax"]] += row["value_millions"]
    assert len(values) == 5
    values["Total"] = sum(values.values())
    target = ROOT / "serie_top_1984_2024_normalizado.csv"
    with target.open(encoding="utf-8", newline="") as f:
        existing = list(csv.DictReader(f))
    additions = []
    for tax, value in values.items():
        previous = [r for r in existing if r["province"] == "La Pampa" and r["year"] == "2025" and r["tax"] == tax]
        if previous:
            assert len(previous) == 1 and abs(float(previous[0]["value_millions"]) - value) < .001
        else:
            additions.append(dict(province="La Pampa", source=source.name, year=2025, tax=tax, value_millions=value))
    write_csv(target, list(existing[0]), existing + additions)
    audit = dict(
        date="2026-10-20", province="La Pampa", year=2025,
        source_file=str(source.relative_to(ROOT)).replace("\\", "/"),
        source_url="https://www.argentina.gob.ar/sites/default/files/" + source.name,
        sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        method="Suma de enero a diciembre, pesos corrientes, millones. Cada total mensual concilia con los cinco componentes, tolerancia 0,05 millones. No se sustituye el vacío de la planilla anual por una estimación.",
        months=coverage["La Pampa"], annual_millions=dict(values),
    )
    (ROOT / "data/lapampa_2025_annual.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    build()
