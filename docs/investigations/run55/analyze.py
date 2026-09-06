"""Offline audit of the joined raidtest_events export; no database writes."""
import collections
import csv
from pathlib import Path

path = Path(__file__).with_name("events-run54-run55.tsv")
with path.open() as stream:
    events = list(csv.DictReader(stream, delimiter="\t"))

for run in ("54", "55"):
    rows = [e for e in events if e["run_id"] == run]
    boss_ids = {e["source_guid"] for e in rows if e["event_type"] == "boss_hp"}
    assert len(boss_ids) == 1, (run, boss_ids)
    boss = boss_ids.pop()
    damage = [e for e in rows if e["event_type"] == "damage" and e["target_guid"] == boss]
    print(f"run={run} boss={boss}")
    bins = collections.Counter()
    for e in damage:
        bins[int(e["rel_ms"]) // 10000] += int(e["value"])
    print("damage by 10-second window:", dict(sorted(bins.items())))
    early = [e for e in damage if int(e["rel_ms"]) < 60000]
    print("0-60s damage:", sum(int(e["value"]) for e in early))
    print("deaths:", [(e["rel_ms"], e["source_guid"]) for e in rows if e["event_type"] == "death"])
    positive = [e for e in damage if int(e["value"]) > 0]
    gaps = sorted(((int(b["rel_ms"]) - int(a["rel_ms"]), a["rel_ms"], b["rel_ms"])
                   for a, b in zip(positive, positive[1:])), reverse=True)
    print("largest gaps between positive damage (ms):", gaps[:3])
    previous_hp = None
    changes = []
    for e in rows:
        if e["event_type"] == "boss_hp" and e["value"] != previous_hp:
            changes.append((e["rel_ms"], e["value"]))
            previous_hp = e["value"]
    print("HP transitions:", changes)
