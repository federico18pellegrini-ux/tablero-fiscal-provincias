#!/usr/bin/env python3
"""Sincroniza fallbacks embebidos con los archivos publicados.

GitHub Pages carga primero CSV/JSON externos. Estos fallbacks evitan que una
falla de red o caché vuelva a mostrar cifras antiguas.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"


def csv_rows(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as source:
        rows: list[dict[str, object]] = list(csv.DictReader(source))
    numeric_fields = {
        "year",
        "value_millions",
        "amortization_ars_m",
        "interest_ars_m",
        "total_service_ars_m",
    }
    for row in rows:
        for field in numeric_fields:
            if field not in row or row[field] in (None, ""):
                continue
            value = str(row[field])
            row[field] = int(float(value)) if field == "year" else float(value)
    return rows


def replace_constant(text: str, name: str, payload: object) -> str:
    replacement = f"const {name} = {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))};"
    updated, count = re.subn(
        rf"^const {name}\s*=.*?;\s*$",
        replacement,
        text,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    if count != 1:
        raise ValueError(f"No se encontró {name}")
    return updated


def main() -> None:
    text = HTML.read_text(encoding="utf-8")
    payloads = {
        "EMBEDDED_MANIFEST": json.loads((ROOT / "dashboard_manifest.json").read_text(encoding="utf-8")),
        "EMBEDDED_TOP_M": csv_rows(ROOT / "top_mensual_2026_normalizado.csv"),
        "EMBEDDED_INFO2026": csv_rows(ROOT / "informacion_consolidada_2026_normalizado.csv"),
        "EMBEDDED_PBA_DEBT_PROFILE": json.loads((ROOT / "data/debt/pba_debt_profile_2026q1.json").read_text(encoding="utf-8")),
        "EMBEDDED_PBA_DEBT_SCHEDULE": csv_rows(ROOT / "data/debt/pba_debt_service_schedule_2026_2041.csv"),
        "EMBEDDED_GOVERNMENT_RESULTS": json.loads((ROOT / "data/government_results_pba.json").read_text(encoding="utf-8")),
        "EMBEDDED_RECLAMOS_NACION": json.loads((ROOT / "dashboard_reclamos_nacion_provincias.json").read_text(encoding="utf-8")),
    }
    for name, payload in payloads.items():
        text = replace_constant(text, name, payload)
    HTML.write_text(text, encoding="utf-8")
    print("Fallbacks sincronizados:", ", ".join(payloads))


if __name__ == "__main__":
    main()
