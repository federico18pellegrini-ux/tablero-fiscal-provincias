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
    # An annual flow cannot be deflated accurately with a December index.
    # Annual real series remain unavailable until monthly flows are matched.
    annual = {}
    own_revenue_year = {}
    text = HTML.read_text(encoding="utf-8")
    text = replace_constant(text, "YEAR_DEFLATOR", own_revenue_year)
    text = replace_constant(text, "DEFLACTOR_MONTH", monthly)
    text = replace_constant(text, "DEFLACTOR_YEAR", annual)
    HTML.write_text(text, encoding="utf-8")
    print(f"HTML sincronizado: {len(monthly)} meses, último mes {max(monthly)}; base junio 2026")


if __name__ == "__main__":
    main()
