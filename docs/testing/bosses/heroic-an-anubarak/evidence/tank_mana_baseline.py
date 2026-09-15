#!/usr/bin/env python3
"""保护骑续蓝闭环的「改前/改后」口径。

usage: tank_mana_baseline.py <run_id> [<run_id> ...]

闭环（WLK 3.3.5 防骑）：庇护祝福（招架/躲闪/格挡回 2% 最大法力，proc 57319）
+ 精神协调（受治疗返蓝）+ 神圣恳求（54428）常驻、由圣光守护 2/2（proc 63521）刷新。
本脚本量四件事：恳求放了几次、庇护祝福 proc 了几次、坦克法力什么时候见底、
以及见底后群体仇恨（奉献 48819 / 神圣之盾 48952 / 正义之锤 53595）还剩多少。
"""
import statistics, subprocess, sys

MYSQL = ["/opt/homebrew/bin/mysql", "-uacore", "-pacore", "-N", "acore_characters", "-e"]
TANK = 796
SPELLS = {54428: '神圣恳求', 63521: '圣光守护proc', 57319: '庇护祝福回蓝proc',
          48819: '奉献', 48952: '神圣之盾', 53595: '正义之锤', 53408: '智慧审判',
          20166: '智慧之印', 61411: '正义之盾'}


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.splitlines() if l]


def main(runs):
    rl = ','.join(runs)
    n = len(q(f"SELECT id FROM raidtest_attempts WHERE run_id IN ({rl}) AND duration_ms>0;"))
    if not n:
        print("no attempts"); return
    print(f"fights={n}")
    print("--- 坦克技能次数/场")
    counts = {int(r[0]): int(r[1]) for r in
              q(f"SELECT e.spell_id,COUNT(*) FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id "
                f"WHERE a.run_id IN ({rl}) AND e.event_type='spell' AND e.source_guid={TANK} "
                f"AND e.spell_id IN ({','.join(str(s) for s in SPELLS)}) GROUP BY 1;")}
    for sid, name in SPELLS.items():
        print(f"  {name:<14} {counts.get(sid,0)/n:6.1f}")
    print("--- 坦克法力")
    # 口径：必须剔除坦克死后的采样——bot 阵亡后法力就是 0，不剔的话「蓝见底」会把「被打死」算成「没蓝」。
    death = {(int(r[0]), int(r[1])): int(r[2]) for r in
             q(f"SELECT a.run_id,a.seq,MIN(e.rel_ms) FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id "
               f"WHERE a.run_id IN ({rl}) AND e.event_type='death' AND e.source_guid={TANK} GROUP BY 1,2;")}
    floors = {}
    for r in q(f"SELECT a.run_id,a.seq,e.rel_ms,"
               f"CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(e.detail,'power=',-1),'/',1) AS UNSIGNED) "
               f"FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id WHERE a.run_id IN ({rl}) "
               f"AND e.event_type='state' AND e.source_guid={TANK} AND e.detail LIKE 'resource:%';"):
        key = (int(r[0]), int(r[1]))
        if key in death and int(r[2]) >= death[key] - 1000:
            continue
        floors[key] = min(floors.get(key, 10 ** 9), int(r[3]))
    if floors:
        vals = sorted(floors.values())
        print(f"  活着时的法力地板：中位 {statistics.median(vals):.0f}，最低 {vals[0]}（{len(vals)} 场）")
    late = {int(r[0]): int(r[1]) for r in
            q(f"SELECT e.spell_id,COUNT(*) FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id "
              f"WHERE a.run_id IN ({rl}) AND e.event_type='spell' AND e.source_guid={TANK} AND e.rel_ms>200000 "
              f"AND e.spell_id IN (48819,48952,53595) GROUP BY 1;")}
    print("--- 200 秒之后的群体仇恨（次/场）")
    for sid in (48819, 48952, 53595):
        print(f"  {SPELLS[sid]:<14} {late.get(sid,0)/n:6.1f}")


if __name__ == '__main__':
    main(sys.argv[1:] or ['505'])
