"""Recompute run56–59 observer validation from the local TSV export."""
import collections
import csv
from pathlib import Path
import re

with Path(__file__).with_name('events-run56-run59.tsv').open() as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))

# Main-tank GUIDs verified against force-recreate logs for these four runs.
for run, main_tank in [('56', '656'), ('57', '666'), ('58', '676'), ('59', '686')]:
    events = [e for e in rows if e['run_id'] == run]
    boss_ids = {e['source_guid'] for e in events if e['event_type'] == 'boss_hp'}
    assert len(boss_ids) == 1, (run, boss_ids)
    boss = boss_ids.pop()
    damage = [e for e in events if e['event_type'] == 'damage' and e['target_guid'] == boss]
    positive = [e for e in damage if int(e['value']) > 0]
    gaps = [int(b['rel_ms']) - int(a['rel_ms']) for a, b in zip(positive, positive[1:])]
    tank = [e for e in damage if e['source_guid'] == main_tank]
    print('run', run, 'first60_damage', sum(int(e['value']) for e in positive if int(e['rel_ms']) < 60000),
          'max_positive_gap_ms', max(gaps, default=0), 'main_tank_hits', len(tank),
          'main_tank_damage', sum(int(e['value']) for e in tank))
    states = [e for e in events if e['detail'].startswith('boss_state:')]
    print('unreachable_samples', sum('unreachable=true' in e['detail'] for e in states),
          'boss_spell_evades', sum(e['event_type'] == 'spell' and e['target_guid'] == boss
                                  and re.search(r' miss=6(?: |$)', e['detail']) is not None for e in events),
          'cast_cancels', sum(e['detail'].startswith('cast_cancel:') for e in events))
    print('combat_victims', dict(collections.Counter(e['target_guid'] for e in states
                                                    if e['detail'].startswith('boss_state:combat=true'))))
    print('boss_deaths', [(e['rel_ms'], e['target_guid']) for e in events
                         if e['event_type'] == 'death' and e['source_guid'] == boss and e['actor_entry'] == '16011'])
