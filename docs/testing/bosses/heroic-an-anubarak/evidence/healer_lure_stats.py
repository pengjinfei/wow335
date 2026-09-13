#!/usr/bin/env python3
"""量化"治疗被小怪引出平台"：按 attempt 统计各成员跑到 y>280（北侧坡道，小怪刷新点方向）的次数、
治疗离开前 3 秒执行的动作、以及打过治疗的小怪多久后转打坦克。只查库，不跑场。
用法：python3 healer_lure_stats.py 469 470 471 473 477
"""
import subprocess, sys, re, collections
RUNS = ",".join(sys.argv[1:]) or "477"
NAMES = {796: 'tank', 797: 'priest', 798: 'rogue', 799: 'mage', 800: 'shaman'}
PRIEST, TANK = 797, 796

def q(sql, db='acore_characters'):
    p = subprocess.run(['mysql', '-uacore', '-pacore', '-N', db, '-e', sql], capture_output=True, text=True)
    if p.returncode:
        sys.exit(p.stderr)
    return [l.split('\t') for l in p.stdout.strip().split('\n') if l]

def positions(aid, g):
    out = []
    for t, d in q(f"SELECT rel_ms,detail FROM raidtest_events WHERE attempt_id={aid} AND event_type='state' "
                  f"AND source_guid={g} AND detail LIKE 'pos:%' ORDER BY rel_ms"):
        x, y, z = map(float, d[4:].split(','))
        out.append((int(t), x, y, z))
    return out

def episodes(pos):
    eps, inside = [], True
    for t, x, y, z in pos:
        if y > 280 and inside:
            eps.append(t); inside = False
        elif y <= 270:
            inside = True
    return eps

tot = collections.defaultdict(collections.Counter)
print("attempt | result | 北上次数(成员:开始秒) | 牧师离开前后 3 秒 OK 动作 | 牧师死亡秒")
for aid, run, seq, res in q(f"SELECT id,run_id,seq,result FROM raidtest_attempts WHERE run_id IN ({RUNS}) "
                             f"AND result IN ('kill','wipe','timeout') ORDER BY id"):
    death = q(f"SELECT MIN(rel_ms) FROM raidtest_events WHERE attempt_id={aid} AND event_type='death' AND source_guid={PRIEST}")[0][0]
    death = None if death == 'NULL' else int(death)
    parts, priest_eps = [], []
    for g in NAMES:
        eps = [e for e in episodes(positions(aid, g)) if not (death and e > death)]  # 死后尸体/灵魂移动不算
        tot[res][NAMES[g]] += len(eps)
        if eps:
            parts.append(f"{NAMES[g]}:{[e // 1000 for e in eps]}")
        if g == PRIEST:
            priest_eps = eps
    acts = []
    for e in priest_eps:
        for t, d in q(f"SELECT rel_ms,detail FROM raidtest_events WHERE attempt_id={aid} AND event_type='state' "
                      f"AND detail LIKE 'heal_actions%' AND rel_ms BETWEEN {e - 13000} AND {e - 7000} ORDER BY rel_ms"):
            acts += [f"{t // 1000 if isinstance(t, int) else int(t) // 1000}:{a}" for a in re.findall(r'A:([^|]*?) - OK', d)]
    print(f"{run}/{seq} {res:7} | {' '.join(parts) or '-'} | {acts or '-'} | {death // 1000 if death else '-'}")
print("按结果汇总（死亡前的北上次数）：")
for res, c in tot.items():
    print("  ", res, dict(c))

print("\n打过治疗的小怪：类型、总伤害、平均多久后转去打坦克")
by = collections.defaultdict(list)
for aid, in q(f"SELECT id FROM raidtest_attempts WHERE run_id IN ({RUNS}) AND result IN ('kill','wipe','timeout')"):
    per = collections.defaultdict(list)
    for t, s, tg, ent, v in q(f"SELECT rel_ms,source_guid,target_guid,actor_entry,value FROM raidtest_events "
                              f"WHERE attempt_id={aid} AND event_type='damage' AND source_guid NOT BETWEEN 796 AND 800 ORDER BY rel_ms"):
        per[(int(s), int(ent))].append((int(t), int(tg), int(v)))
    for (s, ent), lst in per.items():
        ph = [t for t, tg, v in lst if tg == PRIEST]
        if not ph:
            continue
        f = min(ph)
        later = [t for t, tg, v in lst if tg == TANK and t > f]
        by[ent].append(((min(later) - f) / 1000 if later else None, sum(v for t, tg, v in lst if tg == PRIEST)))
for ent, lst in sorted(by.items()):
    handed = [s for s, _ in lst if s is not None]
    print(f"  entry {ent}: 只数={len(lst)} 对治疗总伤={sum(d for _, d in lst) // 1000}k "
          f"转打坦克={len(handed)}/{len(lst)} 平均 {sum(handed) / len(handed) if handed else 0:.1f} 秒")
