#!/usr/bin/env python3
"""目标切换的摩擦成本：每次换目标要停多久，折算成损失了多少 DPS。

usage: target_switch_cost.py <run_id> [<run_id> ...]

做法：按 bot 的伤害事件流切段——连续打同一个 target_guid 算一段，
两段之间的空档就是「切换成本」（丢目标 → 选目标 → 跑过去 → 转向 → 重新出手）。
把这些空档加起来，按该 bot 活跃时的实际 DPS 折算，就是切换损失的伤害量。
"""
import collections, statistics, subprocess, sys

MYSQL = ["/opt/homebrew/bin/mysql", "-uacore", "-pacore", "-N", "acore_characters", "-e"]
WHO = {796: '坦克', 797: '牧师', 798: '盗贼', 799: '法师', 800: '萨满'}
GAP_MIN_MS = 500      # 小于这个不算切换空档（正常出手间隔）
GAP_MAX_MS = 20000    # 大于这个多半是潜地/阵亡，不算在切换成本里


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.splitlines() if l]


def main(runs):
    rl = ','.join(runs)
    dur = {(int(r[0]), int(r[1])): int(r[2]) for r in
           q(f"SELECT run_id,seq,duration_ms FROM raidtest_attempts WHERE run_id IN ({rl}) AND duration_ms>0;")}
    stream = collections.defaultdict(list)
    for r in q(f"SELECT a.run_id,a.seq,e.source_guid,e.rel_ms,IFNULL(e.target_guid,0),e.value "
               f"FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
               f"AND e.event_type='damage' AND e.source_guid BETWEEN 796 AND 800 ORDER BY 1,2,3,4;"):
        stream[(int(r[0]), int(r[1]), int(r[2]))].append((int(r[3]), int(r[4]), int(r[5])))

    print(f"{'角色':<6}{'切换次数/场':>11}{'  切换空档中位':>13}{'  切换总耗时/场':>14}{'  占全场':>8}"
          f"{'  活跃DPS':>9}{'  切换损失伤害/场':>16}")
    for guid in (798, 799, 800, 796):
        n_sw, gaps_all, lost_ms, active_dps, fights = [], [], [], [], 0
        for (run, seq, g), ev in stream.items():
            if g != guid:
                continue
            fights += 1
            d = dur[(run, seq)]
            switches, lost = 0, 0
            for (t0, tgt0, _), (t1, tgt1, _) in zip(ev, ev[1:]):
                gap = t1 - t0
                if tgt1 != tgt0 and GAP_MIN_MS <= gap <= GAP_MAX_MS:
                    switches += 1
                    gaps_all.append(gap)
                    lost += gap
            total = sum(v for _, _, v in ev)
            # 活跃时间 = 全场 - 切换空档 - 长空窗（潜地/死亡）
            longgaps = sum(t1 - t0 for (t0, _, _), (t1, _, _) in zip(ev, ev[1:]) if t1 - t0 > GAP_MAX_MS)
            active = max(1, d - lost - longgaps)
            n_sw.append(switches); lost_ms.append(lost); active_dps.append(total / (active / 1000))
        if not fights:
            continue
        mdps = statistics.median(active_dps)
        mlost = statistics.median(lost_ms)
        print(f"{WHO[guid]:<6}{statistics.median(n_sw):>11.0f}{statistics.median(gaps_all)/1000:>12.1f}s"
              f"{mlost/1000:>13.0f}s{100*mlost/statistics.median(list(dur.values())):>7.0f}%"
              f"{mdps:>9.0f}{mdps*mlost/1000/1000:>15.0f}k")


if __name__ == '__main__':
    main(sys.argv[1:] or ['514'])
