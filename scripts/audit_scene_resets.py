#!/usr/bin/env python3
"""Validate declared scene reset snapshots and compare their reproducible state."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def audit(path, spawns, map_id, difficulty):
    rows = list(csv.DictReader(path.open(), delimiter='\t'))
    errors = []
    actual = [int(row['spawn']) for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != spawns:
        errors.append('reset scope differs from the expected unique spawn set')
    for row in rows:
        if int(row['map']) != map_id or int(row['difficulty']) != difficulty:
            errors.append(f"wrong map/difficulty for spawn {row['spawn']}")
        if int(row['health']) <= 0 or row['health'] != row['max_health'] or row['combat'] != '0':
            errors.append(f"not alive/full/idle: spawn {row['spawn']}")
    if len({row['instance'] for row in rows}) != 1:
        errors.append('snapshot spans multiple instances or is empty')
    keys = ('spawn', 'entry', 'health', 'max_health', 'combat', 'map', 'difficulty', 'x', 'y', 'z')
    canonical = '\n'.join(sorted('\t'.join(row[key] for key in keys) for row in rows))
    return {'file': str(path), 'spawns': sorted(actual), 'errors': errors,
            'fingerprint': hashlib.sha256(canonical.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spawns', required=True, help='comma-separated exact DB spawn IDs')
    parser.add_argument('--map-id', required=True, type=int)
    parser.add_argument('--difficulty', required=True, type=int)
    parser.add_argument('--require-identical', action='store_true', help='also reject native stat differences')
    parser.add_argument('snapshots', nargs='+', type=Path)
    args = parser.parse_args()
    expected = {int(value) for value in args.spawns.split(',')}
    results = [audit(path, expected, args.map_id, args.difficulty) for path in args.snapshots]
    identical = len({row['fingerprint'] for row in results}) == 1
    valid = not any(row['errors'] for row in results)
    print(json.dumps({'valid_reset_scope': valid, 'identical_reset_state': identical, 'snapshots': results}, indent=2))
    return int(not valid or (args.require_identical and not identical))


if __name__ == '__main__':
    raise SystemExit(main())
