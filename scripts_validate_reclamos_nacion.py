import csv
import json
from pathlib import Path

from scripts_build_nacion_reclamos import validate_master_row

MANIFEST_FILE = Path('dashboard_manifest.json')
MASTER_FILE = Path('data/reclamos_nacion/reclamos_nacion_provincias_maestra.csv')


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def main():
    with MANIFEST_FILE.open(encoding='utf-8') as f:
        manifest = json.load(f)
    province_universe = manifest.get('province_universe', [])

    rows = read_csv(MASTER_FILE)
    errors = []
    for idx, row in enumerate(rows, start=2):
        row_errors = validate_master_row(row, province_universe)
        for err in row_errors:
            errors.append(f'fila {idx}: {err}')

    if errors:
        print('ERROR: validación fallida')
        for error in errors:
            print(f'- {error}')
        raise SystemExit(1)

    print(f'OK: {len(rows)} filas validadas sin errores en {MASTER_FILE}')


if __name__ == '__main__':
    main()
