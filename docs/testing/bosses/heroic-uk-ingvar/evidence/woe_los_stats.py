#!/usr/bin/env python3
"""因格瓦尔 Woe Strike(59735) / 解咒视线 的逐场口径。

口径（沿用 2026-09-10 run332 那一轮，便于跨轮比较）：
- `curse_watch` 是 mod-raidtest 观测器每秒一次的只读采样：被诅咒者身上有可解诅咒时，
  记录每个会「解除诅咒」(475) 的成员自己的判据（sees/picks/los/距离）。
- **无视线秒** = 采样行里 `los=false` 的条数（不是时长积分；一秒一条）。
  **只算解咒者还活着的行**（`curer_alive=true`）：解咒者死后 `los` 恒为 false，
  把死后行算进去会把「没解成」和「已经团灭」混为一谈（LESSONS 口径陷阱之一：死后采样）。
  死后行单列为 `死后`，不参与任何判据。
- **有视线仍选不出** = `los=true` 且 `picks=0`。
- **正常选出** = `picks!=0`。
- Woe 上身 = boss 施放 59735 的次数；Woe proc = 59736 施放次数（被治疗者→治疗者）。
- **反射伤害** = 与某次 59736 同刻（±60ms）落在同一目标身上的 damage 事件之和。
  观测器把这类伤害记为 spell_id=0，只看伤害表会误判成普攻。

用法：woe_los_stats.py <run_id> [<run_id> ...]
"""
import subprocess, sys, re
from collections import defaultdict

MYSQL = "/opt/homebrew/opt/mysql@8.4/bin/mysql"

def q(sql):
    out = subprocess.run([MYSQL, "-uroot", "-N", "--batch", "-e", sql],
                         capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.splitlines() if line]

def main(runs):
    ids = ",".join(runs)
    attempts = q(f"""SELECT id, run_id, seq, result, deaths, duration_ms, boss_hp_min
                     FROM acore_characters.raidtest_attempts
                     WHERE run_id IN ({ids}) ORDER BY run_id, seq;""")
    print(f"{'run/seq':>9} {'result':>7} {'死':>2} {'时长s':>6} "
          f"{'无视线秒':>8} {'有视线没选出':>12} {'正常选出':>8} {'死后':>4} "
          f"{'Woe上身':>7} {'Woe proc':>8} {'反射伤害':>8}")
    agg = defaultdict(int)
    for aid, run_id, seq, result, deaths, dur, hpmin in attempts:
        if result == "aborted":
            continue
        rows = q(f"""SELECT detail FROM acore_characters.raidtest_events
                     WHERE attempt_id={aid} AND detail LIKE 'curse_watch:%';""")
        no_los = ok_no_pick = picked = dead = 0
        for (d,) in rows:
            los = re.search(r" los=(\w+)", d)
            pk = re.search(r" picks=(\d+)", d)
            alive = re.search(r"curer_alive=(\w+)", d)
            if not los or not pk:
                continue
            if alive and alive.group(1) != "true":
                dead += 1
                continue
            if los.group(1) != "true":
                no_los += 1
            elif pk.group(1) == "0":
                ok_no_pick += 1
            else:
                picked += 1
        apply_n = int(q(f"""SELECT COUNT(*) FROM acore_characters.raidtest_events
                            WHERE attempt_id={aid} AND event_type='spell' AND spell_id=59735;""")[0][0])
        procs = q(f"""SELECT rel_ms, target_guid FROM acore_characters.raidtest_events
                      WHERE attempt_id={aid} AND event_type='spell' AND spell_id=59736;""")
        dmgs = q(f"""SELECT id, rel_ms, target_guid, value FROM acore_characters.raidtest_events
                     WHERE attempt_id={aid} AND event_type='damage';""")
        by_t = defaultdict(list)
        for did, rel, tgt, val in dmgs:
            by_t[tgt].append((int(rel), int(did), int(val)))
        hit = {}
        for rel, tgt in procs:
            rel = int(rel)
            for drel, did, val in by_t.get(tgt, ()):
                if abs(drel - rel) <= 60:
                    hit[did] = val
        reflect = sum(hit.values())
        print(f"{run_id+'/'+seq:>9} {result:>7} {deaths:>2} {int(dur)/1000:>6.0f} "
              f"{no_los:>8} {ok_no_pick:>12} {picked:>8} {dead:>4} "
              f"{apply_n:>7} {len(procs):>8} {reflect:>8}")
        agg[result] += 1
        agg["no_los_" + ("kill" if result == "kill" else "fail")] += no_los
    print("\n合计:", dict(agg))

if __name__ == "__main__":
    main(sys.argv[1:])
