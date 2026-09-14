#!/usr/bin/env python3
"""阿努巴拉克：潜地窗口分解（每场三次潜地的起止、时长，以及潜地期输出落在大型召唤物身上的比例）。

usage: submerge_windows.py <run_id> [<run_id> ...]

用途：boss 在 75/50/25 三个血线潜地，`EVENT_EMERGE` 是 60 秒；但杀光「大型召唤物」
（守卫 29216 / 毒疗者 29217，英雄第一次 2 只、第二三次 4 只）会把出土改成 5 秒
（core `boss_anubarak.cpp::SummonedCreatureDies`）。本脚本用「对 boss 的伤害事件出现 >12 秒空档」
切出潜地窗口，回答两件事：潜地占了全场多少时间、提前出土的机制有没有在生效。
"""
import collections, statistics, subprocess, sys

MYSQL = ["/opt/homebrew/bin/mysql", "-uacore", "-pacore", "-N", "acore_characters", "-e"]
BOSS = 104
LARGE = (29216, 29217)
PLAYERS = set(range(796, 801))


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [line.split('\t') for line in out.splitlines() if line]


def main(runs):
    rl = ','.join(runs)
    dmg = collections.defaultdict(list)
    for r in q(f"SELECT a.run_id,a.seq,e.rel_ms,e.source_guid,IFNULL(e.target_guid,0),IFNULL(e.actor_entry,0),e.value "
               f"FROM raidtest_events e JOIN raidtest_attempts a ON a.id=e.attempt_id "
               f"WHERE a.run_id IN ({rl}) AND a.result<>'aborted' AND e.event_type='damage';"):
        run, seq, ms, src, tgt, entry, val = (int(x) for x in r)
        dmg[(run, seq)].append((ms / 1000, src, tgt, entry, val))

    by_phase = collections.defaultdict(list)
    for key in sorted(dmg):
        ev = sorted(dmg[key])
        entry_of = {src: e for _, src, _, e, _ in ev if e and src not in PLAYERS}
        bt = [t for t, _, tgt, _, _ in ev if tgt == BOSS]
        if not bt:
            continue
        wins = [(a, b) for a, b in zip(bt, bt[1:]) if b - a > 12]
        line = []
        for i, (a, b) in enumerate(wins):
            large = other = 0
            for t, src, tgt, _, val in ev:
                if a - 3 <= t <= b + 3 and src in PLAYERS and tgt not in PLAYERS and tgt != BOSS:
                    if entry_of.get(tgt) in LARGE:
                        large += val
                    else:
                        other += val
            share = 100 * large / max(1, large + other)
            by_phase[i + 1].append((b - a, share))
            line.append(f"p{i+1} {a:.0f}→{b:.0f} ({b-a:.0f}s, 大怪占比 {share:.0f}%)")
        print(f"{key[0]}/{key[1]}: " + '  '.join(line))

    print()
    total = 0
    for ph in sorted(by_phase):
        lens = [x[0] for x in by_phase[ph]]
        shares = [x[1] for x in by_phase[ph]]
        total += statistics.median(lens)
        print(f"第{ph}次潜地：n={len(lens)} 时长中位 {statistics.median(lens):.0f}s "
              f"（60 秒是不杀大怪的上限，5 秒是杀光后的下限）大怪吃掉的输出中位 {statistics.median(shares):.0f}%")
    print(f"三次潜地合计中位 ≈ {total:.0f}s")


if __name__ == '__main__':
    main(sys.argv[1:] or ['493'])
