#!/usr/bin/env python3
"""Draft a dungeon route from the world DB and the playerbots travel-node graph.

Usage: routegen.py <map_id> <travel node chain, comma separated> <out file> [--link 12] [--side 30]
                   [--overrides overrides/<map>-<name>.txt]

- Skeleton: playerbots_travelnode_path points along the given node chain (entrance -> boss -> ... -> last boss),
  downsampled to about one node every 15 yd.
- Packs: hostile, non-critter, non-flying spawns on the map, joined by creature_formations (same floor) and by
  distance (<= --link yd, |dz| < 6). (Marking every pack with a waypoint walker as a side pack skipped the forge
  room workers, who walk between anvils, and the leader pulled the room at once - run 1782.) Each pack is placed at its nearest skeleton point; packs farther than --side yd from
  the skeleton are marked side=1 (optional to clear).
- Bosses: packs holding a creature with a boss_* script or named like a node of the travel chain
  (dungeon bosses are rank 1 in creature_template, so rank does not tell).
The output is a draft: pull spots, patrol handling and special segments are filled in by hand or from a recording.
"""
import argparse, collections, math, subprocess

MYSQL = ['/opt/homebrew/opt/mysql@8.4/bin/mysql', '-uacore', '-pacore', '-N', '-B']


def query(db, sql):
    out = subprocess.run(MYSQL + [db, '-e', sql], capture_output=True, text=True, check=True).stdout
    return [line.split('\t') for line in out.strip().split('\n') if line]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('map_id', type=int)
    ap.add_argument('chain')
    ap.add_argument('out')
    ap.add_argument('--link', type=float, default=12.0)
    ap.add_argument('--side', type=float, default=30.0)
    ap.add_argument('--overrides', help='hand fixes: lines "pack <spawnId> [along=<yd>] [side=<0|1>] [boss=0] [sent=1]" and '
                    '"object <along> <x> <y> <z> entry=<go entry>"')
    a = ap.parse_args()
    overrides = {}
    objects = []  # "object|summoned <along> <x> <y> <z> entry=<...>" lines, copied as written
    ignored = set()  # "ignore-entry <entry>": creatures that are not cleared (cannot die until a boss does)
    if a.overrides:
        for line in open(a.overrides):
            fields = line.split('#', 1)[0].split()
            if len(fields) >= 2 and fields[0] == 'pack':
                overrides[int(fields[1])] = dict(f.split('=', 1) for f in fields[2:])
            elif fields and fields[0] in ('object', 'summoned', 'drop', 'boss'):
                objects.append(line.split('#', 1)[0].strip() + ('  # ' + line.split('#', 1)[1].strip() if '#' in line else ''))
            elif len(fields) >= 2 and fields[0] == 'ignore-entry':
                ignored.add(int(fields[1]))
    chain = [int(x) for x in a.chain.split(',')]

    names = {int(r[0]): r[1] for r in query('acore_playerbots',
             f"SELECT id, name FROM playerbots_travelnode WHERE id IN ({a.chain})")}
    skel = []
    for s, t in zip(chain, chain[1:]):
        pts = query('acore_playerbots', f"SELECT x, y, z FROM playerbots_travelnode_path "
                    f"WHERE node_id={s} AND to_node_id={t} ORDER BY nr")
        if not pts:
            # Only the other direction is stored for some links (Nexus: Anomalus -> Telestra); walk it backwards.
            pts = query('acore_playerbots', f"SELECT x, y, z FROM playerbots_travelnode_path "
                        f"WHERE node_id={t} AND to_node_id={s} ORDER BY nr DESC")
        if not pts:
            raise SystemExit(f'no travel path {s} -> {t} in either direction')
        skel += [tuple(map(float, p)) for p in pts]
    cum = [0.0]
    for i in range(1, len(skel)):
        cum.append(cum[-1] + math.dist(skel[i - 1], skel[i]))

    rows = query('acore_world', f"""
        SELECT c.guid, c.id, t.name, t.rank, c.position_x, c.position_y, c.position_z, IFNULL(f.leaderGUID, 0), t.ScriptName,
               c.MovementType
        FROM creature c JOIN creature_template t ON t.entry = c.id
        LEFT JOIN creature_template_movement m ON m.CreatureId = t.entry
        LEFT JOIN creature_formations f ON f.memberGUID = c.guid
        WHERE c.map = {a.map_id} AND t.npcflag = 0 AND (t.unit_flags & 0x2) = 0 AND t.type <> 8
          AND IFNULL(m.Flight, 0) = 0 AND t.faction NOT IN (35, 31, 188)""")
    spawns = [dict(guid=int(r[0]), entry=int(r[1]), name=r[2], rank=int(r[3]),
                   p=(float(r[4]), float(r[5]), float(r[6])), leader=int(r[7]),
                   script=r[8] if len(r) > 8 else '', patrol=len(r) > 9 and r[9] == '2') for r in rows
              if int(r[1]) not in ignored]
    parent = {s['guid']: s['guid'] for s in spawns}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_guid = {s['guid']: s for s in spawns}
    # Formations join only on one floor: a patrolling leader spawned on the floor above (Utgarde Keep geist 125874
    # at z 109 over a pack at z 66) otherwise drags the whole pack's target out of reach.
    for s in spawns:
        leader = by_guid.get(s['leader'])
        if leader and abs(leader['p'][2] - s['p'][2]) < 6:
            parent[find(s['guid'])] = find(s['leader'])
    # "pack <spawnId> split=1": that spawn's formation is a pack of its own, not joined by distance to its neighbours
    # (Ahn'kahet: a patrol walks through a static squad; joined, the pack could not be pulled on its own).
    def formation(s):
        return s['leader'] or s['guid']
    split = {formation(by_guid[g]) for g, fix in overrides.items() if fix.get('split') == '1' and g in by_guid}
    for i, s in enumerate(spawns):
        for t in spawns[i + 1:]:
            if (formation(s) in split or formation(t) in split) and formation(s) != formation(t):
                continue
            if math.dist(s['p'], t['p']) <= a.link and abs(s['p'][2] - t['p'][2]) < 6:
                parent[find(s['guid'])] = find(t['guid'])
    groups = collections.defaultdict(list)
    for s in spawns:
        groups[find(s['guid'])].append(s)

    boss_names = {n for n in names.values()}
    items = []
    for members in groups.values():
        c = tuple(sum(s['p'][i] for s in members) / len(members) for i in range(3))
        j = min(range(len(skel)), key=lambda i: math.dist(skel[i], c))
        radius = max(math.dist(s['p'], c) for s in members)
        bosses = [s for s in members if s['name'] in boss_names or s['script'].startswith('boss_')]
        along, off = cum[j], math.dist(skel[j], c)
        sent = False
        hold = ''
        pull = ''
        frm = ''
        nocc = False
        for s in members:
            fix = overrides.get(s['guid'])
            if fix:
                along = float(fix.get('along', along))
                if 'side' in fix:
                    off = 0.0 if fix['side'] == '0' else a.side + 1.0
                if 'boss' in fix:
                    bosses = [] if fix['boss'] == '0' else bosses
                sent = sent or fix.get('sent') == '1'
                hold = fix.get('hold', hold)
                pull = fix.get('pull', pull)
                frm = fix.get('from', frm)
                nocc = nocc or fix.get('cc') == '0'
        items.append((along, off, c, radius, members, bosses, sent, hold, pull, frm, nocc))
    items.sort(key=lambda it: it[0])

    with open(a.out, 'w') as out:
        out.write(f"# Route draft for map {a.map_id}, generated by tools/route-gen/routegen.py\n")
        out.write(f"# chain: {' -> '.join(names.get(n, str(n)) for n in chain)}; "
                  f"skeleton {cum[-1]:.0f} yd, {len(spawns)} hostile spawns, {len(items)} packs\n")
        out.write("# node <along_yd> <x> <y> <z>\n# pack <along_yd> <x> <y> <z> radius=<yd> side=<0|1> elite=<n> "
                  "spawns=<guid,...> # names\n# boss <along_yd> <x> <y> <z> radius=<yd> entry=<entry,...> spawns=<guid,...> # names\n")
        def write_item(item):
            along, off, c, radius, members, bosses, sent, hold, pull, frm, nocc = item
            extra = ((' sent=1' if sent else '') + (f' hold={hold}' if hold else '') + (f' pull={pull}' if pull else '')
                     + (f' from={frm}' if frm else '') + (' cc=0' if nocc else ''))
            label = ', '.join(f"{v}x{k}" for k, v in collections.Counter(s['name'] for s in members).items())
            if bosses:
                out.write(f"boss {along:.0f} {c[0]:.1f} {c[1]:.1f} {c[2]:.1f} radius={radius:.1f} "
                          f"entry={','.join(str(s['entry']) for s in bosses)} "
                          f"spawns={','.join(str(s['guid']) for s in members)}{extra} # {label}\n")
            else:
                elite = sum(1 for s in members if s['rank'] >= 1)
                out.write(f"pack {along:.0f} {c[0]:.1f} {c[1]:.1f} {c[2]:.1f} radius={radius:.1f} "
                          f"side={int(off > a.side)} elite={elite} "
                          f"spawns={','.join(str(s['guid']) for s in members)}{extra} # {label}\n")

        next_node = 0.0
        pi = 0
        for i, p in enumerate(skel):
            while pi < len(items) and items[pi][0] <= cum[i]:
                write_item(items[pi])
                pi += 1
            if cum[i] >= next_node or i == len(skel) - 1:
                out.write(f"node {cum[i]:.0f} {p[0]:.1f} {p[1]:.1f} {p[2]:.1f}\n")
                next_node = cum[i] + 15.0
        # Items an override placed past the last node (a final boss back at the hub) go at the end.
        while pi < len(items):
            write_item(items[pi])
            pi += 1
        # Objects to use (the loader orders every line by along).
        for line in objects:
            out.write(line + "\n")
    print(f"wrote {a.out}: {len(items)} packs, skeleton {cum[-1]:.0f} yd")


if __name__ == '__main__':
    main()
