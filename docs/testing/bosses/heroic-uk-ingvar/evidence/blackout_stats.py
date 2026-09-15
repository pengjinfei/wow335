#!/usr/bin/env python3
"""因格瓦尔：后排「整段不出手」的逐场口径（视线丢失的行为代价）。

背景（2026-09-15 run528/seq4）：法师站在 (220.97,-324.55) 一动不动 84s→98s **零伤害**，
同一窗口它对坦克 `los=false`、治疗也连续 10 个 tick `no actions executed`、坦克无治疗被磨死。
视线一断，后排既不治、不解、也不打，而且**不会自己挪一步**——所有"去接近他"的动作
都以 `party member to heal/dispel` 为目标，而那个值正是被视线过滤掉的那一个。

口径：
- 存活期 = [首次出手, min(自己的死亡时刻, 本场结束)]，死后不计（死后采样陷阱）。
- 出手 = 该角色作为 source 的 damage / heal / spell 事件任意一条（HoT 跳动也算，
  所以这个口径是**保守**的：真实空窗只会更长）。
- **必须扣掉 P1→P2 的转阶段**：因格瓦尔第一阶段打死后趴地复活，这段时间谁都打不到，
  每一场都会给每个人制造一段 15–25 秒的假空窗（第一版口径就是这么被污染的）。
  做法：把「至少有一个人对 boss 造成伤害」的那些秒当作战斗活跃秒，
  空窗只计落在活跃秒里的部分。
- 报 `活跃期空窗秒合计（≥3s 的段）` 与 `最长活跃期空窗`。

用法：blackout_stats.py <run_id> [...]
"""
import subprocess, sys
from collections import defaultdict

MYSQL = "/opt/homebrew/opt/mysql@8.4/bin/mysql"

def q(sql):
    out = subprocess.run([MYSQL, "-uroot", "-N", "--batch", "-e", sql],
                         capture_output=True, text=True, check=True).stdout
    return [l.split("\t") for l in out.splitlines() if l]

def main(runs):
    ids = ",".join(runs)
    cls = dict(q("SELECT guid, class FROM acore_characters.characters WHERE guid BETWEEN 791 AND 795;"))
    names = {"2": "坦克", "5": "治疗", "4": "盗贼", "8": "法师", "7": "萨满"}
    watch = [(g, names[c]) for g, c in sorted(cls.items()) if c in ("5", "8", "4", "7")]
    attempts = q(f"""SELECT id, run_id, seq, result, deaths FROM acore_characters.raidtest_attempts
                     WHERE run_id IN ({ids}) ORDER BY run_id, seq;""")
    hdr = " ".join(f"{n+'空窗/最长':>13}" for _, n in watch)
    print(f"{'run/seq':>9} {'result':>7} {'死':>2} {hdr}")
    for aid, run_id, seq, result, deaths in attempts:
        if result == "aborted":
            continue
        # 战斗活跃秒：至少有人对 boss 造成伤害的那些秒（扣掉 P1→P2 转阶段）
        active = {int(r) // 1000 for (r,) in q(
            f"""SELECT rel_ms FROM acore_characters.raidtest_events
                WHERE attempt_id={aid} AND event_type='damage' AND target_guid=60;""")}
        cells = []
        for guid, _name in watch:
            acts = sorted({int(r) // 1000 for (r,) in q(
                f"""SELECT rel_ms FROM acore_characters.raidtest_events
                    WHERE attempt_id={aid} AND source_guid={guid}
                    AND event_type IN ('damage','spell') ;""")}
                | {int(r) // 1000 for (r,) in q(
                f"""SELECT rel_ms FROM acore_characters.raidtest_events
                    WHERE attempt_id={aid} AND source_guid={guid} AND detail LIKE 'heal:%';""")})
            death = q(f"""SELECT MIN(rel_ms) FROM acore_characters.raidtest_events
                          WHERE attempt_id={aid} AND event_type='death' AND source_guid={guid};""")
            dead_s = int(death[0][0]) // 1000 if death and death[0][0] not in ("NULL", None) else None
            if not acts:
                cells.append(f"{'-':>13}")
                continue
            end = dead_s if dead_s is not None else acts[-1]
            total = longest = 0
            for a, b in zip(acts, acts[1:]):
                if a >= end:
                    break
                live = sum(1 for s2 in range(a + 1, min(b, end)) if s2 in active)
                if live >= 3:
                    total += live
                    longest = max(longest, live)
            cells.append(f"{str(total)+'/'+str(longest):>13}")
        print(f"{run_id+'/'+seq:>9} {result:>7} {deaths:>2} " + " ".join(cells))

if __name__ == "__main__":
    main(sys.argv[1:])
