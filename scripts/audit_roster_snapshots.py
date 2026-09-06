#!/usr/bin/env python3
"""Summarize pre-pull character snapshots; fingerprints ignore run/GUID and row order."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(path):
    rows = [line.split('\t') for line in path.read_text().splitlines()]
    values = {r[0]: r[1] for r in rows if len(r) == 2}
    errors = [r[1] for r in rows if r[0] == 'error']
    if values.get('valid') != '1':
        errors.append('snapshot did not pass preflight')
    canonical = sorted('\t'.join(r) for r in rows if r[0] in {
        'fixture_version', 'spec', 'level', 'talent', 'glyph', 'spell', 'item', 'profession'})
    return {
        'file': str(path), 'spec': values.get('spec'),
        'run': values.get('run'), 'attempt': values.get('attempt'), 'guid': values.get('guid'),
        'talent_points': int(values.get('talent_points', 0)),
        'glyphs': sum(r[0] == 'glyph' and r[2] != '0' for r in rows),
        'items': sum(r[0] == 'item' for r in rows),
        'fingerprint': hashlib.sha256('\n'.join(canonical).encode()).hexdigest(),
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshots', nargs='+', type=Path)
    args = parser.parse_args()
    reports = [audit(path) for path in args.snapshots]
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    return int(any(report['errors'] for report in reports))


if __name__ == '__main__':
    raise SystemExit(main())
