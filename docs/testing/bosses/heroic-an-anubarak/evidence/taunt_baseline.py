#!/usr/bin/env python3
"""阿努巴拉克：小怪打非坦克的「改前口径」量化。

usage: taunt_baseline.py <run_id> [<run_id> ...]

输出四块：
  1. 每场承伤来源分解（boss / 守卫 / 毒疗者 / 掠夺者 …）与落点（坦克 vs 非坦克）
  2. 大型召唤物「从不打坦克」的比例、在非坦克身上的停留时长
  3. 圣骑士嘲讽（62124 制裁之手 / 31789 正义防御）的用量与对上述段落的 5 秒覆盖率
  4. 牧师首次蓝 <500 的时刻、结果分布
口径与 run 483–493 一致，改动后用同一脚本对比。
"""
import collections, statistics, subprocess, sys

MYSQL = ["/opt/homebrew/bin/mysql", "-uacore", "-pacore", "-N", "acore_characters", "-e"]
TANK = 796
PLAYERS = set(range(796, 801))
NAME = {29120: 'boss', 29216: 'guardian', 29217: 'venomancer', 29213: 'darter',
        29214: 'assassin', 29209: 'skitterer'}
LARGE = (29216, 29217, 29213)
TAUNTS = (62124, 31789)


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [line.split('\t') for line in out.splitlines() if line]


def main(runs):
    rl = ','.join(runs)
    attempts = q(f"SELECT a.run_id,a.seq,a.result,ROUND(a.duration_ms/1000),a.boss_hp_min "
                 f"FROM raidtest_attempts a WHERE a.run_id IN ({rl}) AND a.result<>'aborted' ORDER BY 1,2;")
    fights = {(int(r[0]), int(r[1])): r[2] for r in attempts}
    n = len(fights)
    if not n:
        print("no attempts"); return
    dmg = q(f"SELECT a.run_id,a.seq,e.rel_ms,e.source_guid,IFNULL(e.target_guid,0),IFNULL(e.actor_entry,0),e.value "
            f"FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id "
            f"WHERE a.run_id IN ({rl}) AND e.event_type='damage';")
    taunts = collections.defaultdict(list)
    for r in q(f"SELECT a.run_id,a.seq,e.rel_ms,e.spell_id FROM raidtest_events e "
               f"JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
               f"AND e.event_type='spell' AND e.source_guid={TANK} AND e.spell_id IN {TAUNTS};"):
        taunts[(int(r[0]), int(r[1]))].append((int(r[2]) / 1000, int(r[3])))

    taken = collections.Counter(); taken_nt = collections.Counter()
    per_add = collections.defaultdict(list)
    for r in dmg:
        run, seq, ms, src, tgt, entry, val = (int(x) for x in r)
        if (run, seq) not in fights:
            continue
        if tgt in PLAYERS and src not in PLAYERS:
            key = NAME.get(entry, entry)
            taken[key] += val
            if tgt != TANK:
                taken_nt[key] += val
            if entry in LARGE:
                per_add[(run, seq, src, entry)].append((ms / 1000, tgt, val))

    print(f"fights={n}  kills={sum(1 for v in fights.values() if v=='kill')}  "
          f"wipes={sum(1 for v in fights.values() if v=='wipe')}  "
          f"timeouts={sum(1 for v in fights.values() if v=='timeout')}")
    print("\n--- 每场承伤（k/场，括号内为落在非坦克身上的部分）")
    tot = sum(taken.values())
    for k, v in taken.most_common():
        print(f"  {str(k):<12} {v/n/1000:7.1f}k  ({taken_nt[k]/n/1000:6.1f}k 非坦)  {100*v/tot:4.1f}%")
    print(f"  {'合计':<12} {tot/n/1000:7.1f}k  ({sum(taken_nt.values())/n/1000:6.1f}k 非坦 = "
          f"{100*sum(taken_nt.values())/tot:.0f}%)")

    print("\n--- 大型召唤物：是否被坦克接走")
    print(f"{'怪':<11} {'刷出':>6} {'打过非坦':>8} {'从不打坦':>8} {'段/场':>7} {'停留中位':>9} {'停留p90':>8} "
          f"{'非坦伤害/场':>11} {'5秒内有嘲讽':>11}")
    for entry in LARGE:
        spawned = touched = never = 0
        lat, segs, seg_cov, nt_dmg = [], 0, 0, 0
        for (run, seq, guid, e), ev in per_add.items():
            if e != entry:
                continue
            spawned += 1
            ev.sort()
            nt = [x for x in ev if x[1] != TANK]
            if not nt:
                continue
            touched += 1
            nt_dmg += sum(x[2] for x in nt)
            tl = sorted(taunts.get((run, seq), []))
            seg = None
            for t, tgt, val in ev:
                if tgt != TANK:
                    if seg is None:
                        seg = t
                else:
                    if seg is not None:
                        lat.append(t - seg); segs += 1
                        if any(seg - 1 <= x[0] <= seg + 5 for x in tl):
                            seg_cov += 1
                        seg = None
            if seg is not None:
                never += 1
                lat.append(ev[-1][0] - seg); segs += 1
                if any(seg - 1 <= x[0] <= seg + 5 for x in tl):
                    seg_cov += 1
        if not lat:
            continue
        print(f"{NAME[entry]:<11} {spawned:>6} {touched:>8} {never:>8} {segs/n:>7.1f} "
              f"{statistics.median(lat):>8.1f}s {sorted(lat)[int(.9*len(lat))]:>7.1f}s "
              f"{nt_dmg/n/1000:>10.1f}k {100*seg_cov/segs:>10.0f}%")

    hor = sum(1 for k in taunts for x in taunts[k] if x[1] == 62124)
    rd = sum(1 for k in taunts for x in taunts[k] if x[1] == 31789)
    print(f"\n坦克嘲讽用量：制裁之手 {hor/n:.1f} 次/场、正义防御 {rd/n:.1f} 次/场"
          f"（两个 8 秒冷却，满打满算约 {2*sum(int(r[3]) for r in attempts)/n/8:.0f} 次/场）")

    oom = q(f"SELECT a.run_id,a.seq,ROUND(MIN(e.rel_ms)/1000) FROM raidtest_events e "
            f"JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
            f"AND e.event_type='state' AND e.source_guid=797 AND e.detail LIKE 'resource:%' "
            f"AND CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.detail,'power=',-1),'/',1) AS UNSIGNED)<500 GROUP BY 1,2;")
    if oom:
        ts = [int(r[2]) for r in oom]
        print(f"牧师首次蓝<500：{len(ts)}/{n} 场，中位 {statistics.median(ts):.0f}s，均值 {sum(ts)/len(ts):.0f}s")


if __name__ == '__main__':
    main(sys.argv[1:] or ['483'])
