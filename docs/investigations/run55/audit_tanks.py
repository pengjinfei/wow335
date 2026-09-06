"""Recompute tank diagnostic summaries from exported event TSV(s)."""
import collections
import csv
import sys

for path in sys.argv[1:]:
    with open(path) as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    keys = {(e['run_id'], e['attempt_id']) for e in rows}
    for run, attempt in sorted(keys, key=lambda pair: tuple(map(int, pair))):
        events = [e for e in rows if e['run_id'] == run and e['attempt_id'] == attempt]
        bosses = {e['source_guid'] for e in events if e['event_type'] == 'boss_hp'}
        assert len(bosses) == 1, (run, bosses)
        boss = bosses.pop()
        tanks = sorted({e['source_guid'] for e in events if e['detail'].startswith('tank_state:')}, key=int)
        print('run', run, 'attempt', attempt, 'boss', boss)
        for guid in tanks:
            own = [e for e in events if e['source_guid'] == guid]
            damage = [e for e in own if e['event_type'] == 'damage' and e['target_guid'] == boss]
            spells = [e for e in own if e['event_type'] == 'spell' and e['target_guid'] == boss]
            states = [e for e in own if e['detail'].startswith('tank_state:')]
            print('tank', guid, 'hits', len(damage), 'damage', sum(int(e['value']) for e in damage),
                  'last_damage_ms', max((int(e['rel_ms']) for e in damage), default=None),
                  'boss_spell_events', len(spells))
            print('engines', dict(collections.Counter(e['detail'].split()[0] for e in states)))
            print('damage_by_30s', dict(sorted(collections.Counter({
                period: sum(int(e['value']) for e in damage if int(e['rel_ms']) // 30000 == period)
                for period in {int(e['rel_ms']) // 30000 for e in damage}
            }).items())))
            ownership = [e for e in own if e['detail'].startswith('tank_ownership:')]
            print('ownership', dict(collections.Counter(e['detail'] for e in ownership)))
        print('boss_victim_samples', dict(collections.Counter(e['target_guid'] for e in events
              if e['detail'].startswith('boss_state:combat=true'))))
