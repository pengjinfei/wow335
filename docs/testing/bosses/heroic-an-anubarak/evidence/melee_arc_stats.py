#!/usr/bin/env python3
"""近战是否站在 boss 正面锥里（阿努巴拉克践踏 = 正面 120°、15 码）。

usage: melee_arc_stats.py <run_id> [<run_id> ...]

boss 的朝向没有入库，用「boss → 主坦方向」当朝向的代理：boss 始终面向仇恨目标，
践踏读条期还会 SetInFront + DisableRotate 锁死朝向（见 ANTriggers.h 注释）。
于是每个采样点算 angle(boss→某人) 与 angle(boss→坦克) 的夹角，≤60° 且距离 ≤15 码即判定「在锥内」。
最后用实际被践踏命中的时刻反验这个代理是否可信。
"""
import math, statistics, subprocess, sys, collections

MYSQL = ["/opt/homebrew/bin/mysql", "-uacore", "-pacore", "-N", "acore_characters", "-e"]
BOSS, TANK = 104, 796
WHO = {796: '坦克', 797: '牧师', 798: '盗贼', 799: '法师', 800: '萨满'}
CONE_DEG, CONE_YD = 60.0, 15.0


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.splitlines() if l]


def main(runs):
    rl = ','.join(runs)
    pos = collections.defaultdict(dict)          # (run,seq,ms) -> guid -> (x,y)
    for r in q(f"SELECT a.run_id,a.seq,e.rel_ms,e.source_guid,e.detail FROM raidtest_events e "
               f"JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
               f"AND e.event_type='state' AND e.detail LIKE 'pos:%';"):
        x, y, _ = r[4][4:].split(',')
        pos[(int(r[0]), int(r[1]), int(r[2]))][int(r[3])] = (float(x), float(y))

    inarc = collections.Counter(); total = collections.Counter()
    arc_at = collections.defaultdict(list)
    for key, units in pos.items():
        if BOSS not in units or TANK not in units:
            continue
        bx, by = units[BOSS]; tx, ty = units[TANK]
        if math.hypot(tx - bx, ty - by) < 0.5:
            continue
        face = math.atan2(ty - by, tx - bx)
        for guid, (px, py) in units.items():
            if guid == BOSS:
                continue
            dx, dy = px - bx, py - by
            dist = math.hypot(dx, dy)
            delta = math.degrees(abs((math.atan2(dy, dx) - face + math.pi) % (2 * math.pi) - math.pi))
            total[guid] += 1
            if delta <= CONE_DEG and dist <= CONE_YD:
                inarc[guid] += 1
            arc_at[(key[0], key[1], guid)].append((key[2], delta, dist))

    print(f"采样点 {len(pos)} 个（每秒一次）")
    print(f"{'角色':<6}{'在正面锥内的时间占比':>16}{'  中位夹角':>10}{'  中位距 boss':>12}")
    for guid in sorted(total):
        vals = [d for k, lst in arc_at.items() if k[2] == guid for _, d, _ in lst]
        dists = [x for k, lst in arc_at.items() if k[2] == guid for _, _, x in lst]
        print(f"{WHO.get(guid, guid):<6}{100*inarc[guid]/total[guid]:>15.0f}%{statistics.median(vals):>11.0f}°{statistics.median(dists):>12.1f}")

    print("\n--- 反验：boss 打到玩家 >=8k 的时刻，该玩家当时是否被判定在锥内")
    ok = bad = 0
    for r in q(f"SELECT a.run_id,a.seq,e.rel_ms,e.target_guid,e.value FROM raidtest_events e "
               f"JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
               f"AND e.event_type='damage' AND e.source_guid={BOSS} AND e.target_guid BETWEEN 796 AND 800 "
               f"AND e.value>=8000 ORDER BY 1,2,3;"):
        run, seq, ms, guid, val = int(r[0]), int(r[1]), int(r[2]), int(r[3]), int(r[4])
        near = [(abs(t - ms), d, dist) for t, d, dist in arc_at.get((run, seq, guid), []) if abs(t - ms) <= 1500]
        if not near:
            continue
        _, delta, dist = min(near)
        hit = delta <= CONE_DEG and dist <= CONE_YD
        ok += hit; bad += (not hit)
        print(f"  {run}/{seq} t={ms//1000:>3}s {WHO[guid]:<4} {val:>6} 夹角 {delta:>3.0f}° 距离 {dist:>4.1f}  {'锥内' if hit else '锥外?'}")
    print(f"  代理可信度：{ok}/{ok+bad} 次命中落在判定的锥内")


if __name__ == '__main__':
    main(sys.argv[1:] or ['514'])
