"""Retrieve the exact official sources pinned by the national dashboard manifest.
Refuses changed bytes instead of silently rebuilding a new vintage.
"""
import argparse, hashlib, json, urllib.request, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cache',type=Path,required=True);args=ap.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'nacion/data/sources.json').read_text('utf-8'))
    for s in manifest:
        target=args.cache/s['file']
        if not target.exists():
            with urllib.request.urlopen(s['url'],timeout=90) as r:content=r.read()
            if hashlib.sha256(content).hexdigest()!=s['sha256']:raise ValueError(f"Source changed: {s['file']}. Use the archived 2026-09-17 snapshot or review a new vintage.")
            target.write_bytes(content)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=s['sha256']:raise ValueError(f"Hash mismatch: {target.name}")
        if target.suffix=='.zip':
            with zipfile.ZipFile(target) as z:
                for name in z.namelist():
                    if '/' in name or '\\' in name:raise ValueError('Unexpected archive path')
                    (args.cache/name).write_bytes(z.read(name))
    (args.cache/'manifest.json').write_text(json.dumps(manifest,indent=2),'utf-8')
    print(f'Verified {len(manifest)} original sources.')
if __name__=='__main__':main()
