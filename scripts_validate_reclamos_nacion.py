"""Validate provenance, missingness and freshness of published claims outputs."""
import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    subprocess.run([sys.executable, str(Path(__file__).with_name('scripts_build_nacion_reclamos.py')), '--check'], check=True)
