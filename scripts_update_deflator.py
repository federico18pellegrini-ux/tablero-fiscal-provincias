#!/usr/bin/env python3
"""Actualiza el deflactor mensual con IPC oficial y una base explícita."""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PATH = ROOT / "deflactor_mensual.csv"
BASE_PERIOD = "2026-06"
OFFICIAL_IPC_MOM = {
    "2026-01": 0.029,
    "2026-02": 0.029,
    "2026-03": 0.034,
    "2026-04": 0.026,
    "2026-05": 0.021,
    "2026-06": 0.019,
}


def main() -> None:
    with PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    by_period = {row["period"]: row for row in rows}
    for period, rate in OFFICIAL_IPC_MOM.items():
        row = by_period.setdefault(
            period,
            {"period": period, "ipc_mom": "", "ipc_index": "", "factor_to_latest": ""},
        )
        row["ipc_mom"] = f"{rate:.6f}"

    ordered = [by_period[period] for period in sorted(by_period) if period <= BASE_PERIOD]
    if not ordered or ordered[-1]["period"] != BASE_PERIOD:
        raise ValueError(f"Falta el período base {BASE_PERIOD}")

    first_index = float(ordered[0]["ipc_index"] or 100)
    ordered[0]["ipc_index"] = f"{first_index:.6f}"
    for previous, current in zip(ordered, ordered[1:]):
        rate = float(current["ipc_mom"])
        current_index = float(previous["ipc_index"]) * (1 + rate)
        current["ipc_index"] = f"{current_index:.6f}"

    latest_index = float(ordered[-1]["ipc_index"])
    for row in ordered:
        row["factor_to_latest"] = f"{latest_index / float(row['ipc_index']):.6f}"

    with PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["period", "ipc_mom", "ipc_index", "factor_to_latest"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(ordered)

    print(f"Deflactor actualizado: {len(ordered)} períodos, base {BASE_PERIOD}=1")


if __name__ == "__main__":
    main()
