#!/usr/bin/env python3
"""因格瓦尔：Dreadful Roar(59734) 每一记的全队影响与"垫血窗口"口径。

机制：60 码半径覆盖整个平台、**2 秒读条**、一记打全队 25k–31k 外加 8 秒恐惧，没有站位解法。
观测器把 boss 的 cast 事件记在**结算那一刻**（detail 里带 `cast_ms=2000`），
所以可以垫血的窗口是 `[t_hit - 2000, t_hit)`。

每一记记录：
- 命中前各成员血量百分比（取 t_hit 前 3 秒内最后一次 `resource:` 采样）；
- 该记对各成员的伤害（与 cast 同毫秒、来源为 boss 的 damage 事件）；
- 命中后是否有人在 8 秒内阵亡；
- **致死余量**：命中前血量减去该记伤害，若 ≤0 记为"这一记本可致死"。

用法：roar_impact.py <run_id> [...]
"""
import subprocess, sys, re
from collections import defaultdict

MYSQL = "/opt/homebrew/opt/mysql@8.4/bin/mysql"
ROAR = 59734

def q(s):
    return [l.split("\t") for l in subprocess.run([MYSQL,"-uroot","-N","--batch","-e",s],
            capture_output=True,text=True,check=True).stdout.splitlines() if l]

def main(runs):
    ids = ",".join(runs)
    cls = dict(q("SELECT guid,class FROM acore_characters.characters WHERE guid BETWEEN 791 AND 795;"))
    name = {"2":"坦克","5":"治疗","4":"盗贼","8":"法师","7":"萨满"}
    members = [(g, name[c]) for g, c in sorted(cls.items())]
    tot_roars = tot_lethal = tot_deaths = 0
    hp_pre_all = []
    for aid, run, seq, res in q(f"""SELECT id,run_id,seq,result FROM acore_characters.raidtest_attempts
                                    WHERE run_id IN ({ids}) AND result<>'aborted' ORDER BY run_id,seq;"""):
        roars = [int(r) for (r,) in q(f"""SELECT rel_ms FROM acore_characters.raidtest_events
                                          WHERE attempt_id={aid} AND event_type='spell' AND spell_id={ROAR}
                                          ORDER BY rel_ms;""")]
        hp = defaultdict(list)
        for g, d, r in q(f"""SELECT source_guid,detail,rel_ms FROM acore_characters.raidtest_events
                             WHERE attempt_id={aid} AND detail LIKE 'resource:hp=%' ORDER BY rel_ms;"""):
            m = re.match(r"resource:hp=(\d+)/(\d+)", d)
            if m and int(m.group(2)):
                hp[g].append((int(r), 100.0*int(m.group(1))/int(m.group(2))))
        deaths = {g: int(t) for g, t in q(f"""SELECT source_guid,MIN(rel_ms) FROM acore_characters.raidtest_events
                                              WHERE attempt_id={aid} AND event_type='death' GROUP BY source_guid;""")}
        for t in roars:
            dmg = {g: int(v) for g, v in q(f"""SELECT target_guid,SUM(value) FROM acore_characters.raidtest_events
                                               WHERE attempt_id={aid} AND event_type='damage' AND source_guid=60
                                               AND rel_ms={t} GROUP BY target_guid;""")}
            cells, lethal = [], 0
            for g, nm in members:
                if g in deaths and deaths[g] <= t:
                    cells.append(f"{nm}:-")
                    continue
                pre = next((p for r, p in reversed(hp[g]) if t-3000 <= r <= t), None)
                d = dmg.get(g, 0)
                if pre is None:
                    cells.append(f"{nm}:?")
                    continue
                hp_pre_all.append(pre)
                maxhp = d / max(pre/100.0, 1e-6) if False else None
                # 致死余量用百分比表示：该记伤害占最大生命的比例需要血量样本换算
                cells.append(f"{nm}:{pre:.0f}%-{d}")
                if d and pre and d >= pre/100.0 * _maxhp(hp, g, aid, q):
                    lethal += 1
            died = [nm for g, nm in members if g in deaths and t <= deaths[g] <= t+8000]
            tot_roars += 1
            tot_lethal += lethal
            tot_deaths += len(died)
            print(f"{run}/{seq} t={t/1000:6.1f}s  " + "  ".join(cells) +
                  (f"   →8秒内阵亡: {','.join(died)}" if died else ""))
    print(f"\n合计 {tot_roars} 记 Roar，命中后 8 秒内阵亡 {tot_deaths} 人次，"
          f"命中前血量中位 {sorted(hp_pre_all)[len(hp_pre_all)//2]:.0f}%")

_maxcache = {}
def _maxhp(hp, g, aid, q):
    key = (aid, g)
    if key not in _maxcache:
        r = q(f"""SELECT detail FROM acore_characters.raidtest_events WHERE attempt_id={aid}
                  AND source_guid={g} AND detail LIKE 'resource:hp=%' LIMIT 1;""")
        m = re.match(r"resource:hp=(\d+)/(\d+)", r[0][0]) if r else None
        _maxcache[key] = int(m.group(2)) if m else 1
    return _maxcache[key]

if __name__ == "__main__":
    main(sys.argv[1:])
