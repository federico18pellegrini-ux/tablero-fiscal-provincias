#!/usr/bin/env python3
"""Sincroniza en el HTML los factores de deflación auditados del CSV."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
CSV = ROOT / "deflactor_mensual.csv"


def replace_constant(text: str, name: str, value: dict[str, float]) -> str:
    replacement = f"const {name} = {json.dumps(value, ensure_ascii=False, sort_keys=True)};"
    updated, count = re.subn(rf"const {name} = \{{.*?\}};", replacement, text, count=1)
    if count != 1:
        raise ValueError(f"No se pudo reemplazar {name}")
    return updated


def main() -> None:
    with CSV.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    monthly = {row["period"]: float(row["factor_to_latest"]) for row in rows}
    annual = {
        period[:4]: factor
        for period, factor in monthly.items()
        if period.endswith("-12")
    }
    latest_year = max(monthly)[0:4]
    annual[latest_year] = 1.0

    text = HTML.read_text(encoding="utf-8")
    old_year_match = re.search(r"const YEAR_DEFLATOR = (\{.*?\});", text)
    if not old_year_match:
        raise ValueError("No se encontró YEAR_DEFLATOR")
    own_revenue_year = json.loads(old_year_match.group(1))
    for year in list(own_revenue_year):
        if year in annual:
            own_revenue_year[year] = annual[year]
        elif int(year) < 2011:
            own_revenue_year[year] = float(own_revenue_year[year]) * 1.026

    text = replace_constant(text, "YEAR_DEFLATOR", own_revenue_year)
    text = replace_constant(text, "DEFLACTOR_MONTH", monthly)
    text = replace_constant(text, "DEFLACTOR_YEAR", annual)
    HTML.write_text(text, encoding="utf-8")
    print(f"HTML sincronizado: {len(monthly)} meses, base {max(monthly)}")


if __name__ == "__main__":
    main()
