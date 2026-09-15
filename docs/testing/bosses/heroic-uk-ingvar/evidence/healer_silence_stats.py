#!/usr/bin/env python3
"""因格瓦尔：治疗「有人残血却一个动作都没执行」的逐场口径。

背景（2026-09-15 run528/seq4 发现）：坦克 65.3s→96.5s **一次治疗都没收到**，
从满血 24,394 被磨死；同期治疗的引擎日志连续 10 个 tick 是 `no actions executed`，
连 `PUSH:flash heal on party` 都没有——不是被 multiplier 归零（那会留下 PUSH 行），
是 `party member to heal` 直接返回空。同一秒法师对坦克 `los=false`。

口径：
- 采样来自观测器每秒一次的 `heal_actions:` 引擎轨迹（需 `AiPlayerbot.LogInGroupOnly = 0`），
  同一秒被切成多片，按 rel_ms 拼回。
- **静默秒** = 该秒治疗的轨迹里没有任何 `A:<含 heal/flash/renew/prayer/penance/shield> - OK`，
  且当秒**坦克存活且血量 < 70%**。治疗死后的秒全部剔除（死后采样）。
- 另记 `no_action` = 轨迹里出现 `no actions executed`（引擎整 tick 空转）的静默秒。

用法：healer_silence_stats.py <run_id> [...]
"""
import subprocess, sys, re
from collections import defaultdict

MYSQL = "/opt/homebrew/opt/mysql@8.4/bin/mysql"
HEAL_OK = re.compile(r"A:([^|]*?(?:heal|flash|renew|prayer|penance|shield|mending)[^|]*?) - OK")

def q(sql):
    out = subprocess.run([MYSQL, "-uroot", "-N", "--batch", "-e", sql],
                         capture_output=True, text=True, check=True).stdout
    return [l.split("\t") for l in out.splitlines() if l]

def main(runs):
    ids = ",".join(runs)
    attempts = q(f"""SELECT id, run_id, seq, result, deaths FROM acore_characters.raidtest_attempts
                     WHERE run_id IN ({ids}) ORDER BY run_id, seq;""")
    # 角色：paladin=tank, priest=heal（roster normal5-v1 固定五人）
    roles = dict(q("""SELECT guid, class FROM acore_characters.characters WHERE guid BETWEEN 791 AND 795;"""))
    tank = next(g for g, c in roles.items() if c == "2")
    healer = next(g for g, c in roles.items() if c == "5")
    print(f"tank={tank} healer={healer}")
    print(f"{'run/seq':>9} {'result':>7} {'死':>2} {'坦克残血秒':>10} {'其中治疗静默':>12} "
          f"{'整tick空转':>10} {'最长连续':>8}")
    for aid, run_id, seq, result, deaths in attempts:
        if result == "aborted":
            continue
        # 坦克每秒血量
        hp = {}
        for rel, d in q(f"""SELECT rel_ms, detail FROM acore_characters.raidtest_events
                            WHERE attempt_id={aid} AND source_guid={tank} AND detail LIKE 'resource:hp=%';"""):
            m = re.match(r"resource:hp=(\d+)/(\d+)", d)
            if m and int(m.group(2)):
                hp[int(rel) // 1000] = int(m.group(1)) / int(m.group(2))
        # 治疗死亡时刻
        dead = q(f"""SELECT MIN(rel_ms) FROM acore_characters.raidtest_events
                     WHERE attempt_id={aid} AND event_type='death' AND source_guid={healer};""")
        dead_s = int(dead[0][0]) // 1000 if dead and dead[0][0] not in ("NULL", None) else 10 ** 9
        # 治疗每秒引擎轨迹（分片拼回）
        trace = defaultdict(str)
        for rel, d in q(f"""SELECT rel_ms, detail FROM acore_characters.raidtest_events
                            WHERE attempt_id={aid} AND source_guid={healer} AND detail LIKE 'heal_actions:%'
                            ORDER BY rel_ms, id;"""):
            trace[int(rel) // 1000] += re.sub(r"^heal_actions:\d+:", "", d)
        low = silent = idle = 0
        run_len = best = 0
        for s in sorted(trace):
            if s >= dead_s or hp.get(s, 1.0) >= 0.70:
                run_len = 0
                continue
            low += 1
            if HEAL_OK.search(trace[s]):
                run_len = 0
                continue
            silent += 1
            run_len += 1
            best = max(best, run_len)
            if "no actions executed" in trace[s]:
                idle += 1
        print(f"{run_id+'/'+seq:>9} {result:>7} {deaths:>2} {low:>10} {silent:>12} {idle:>10} {best:>8}")

if __name__ == "__main__":
    main(sys.argv[1:])
