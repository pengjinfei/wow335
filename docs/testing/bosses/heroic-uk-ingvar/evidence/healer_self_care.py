#!/usr/bin/env python3
"""因格瓦尔：治疗自己残血时到底有没有被治疗（含自治）的逐场口径。

背景（2026-09-15 run531/532 十场）：治疗在 50% 血以下停留 **94 秒**，其中只有 **12 秒**
收到过任何治疗（含 HoT 跳动）；七次阵亡里死前 12 秒收到 0–4 次。不是没蓝（死时法力 11k/16.7k），
是 `PartyMemberToHeal::Calculate` 的排序：probeValue = 血量% + 到自己的距离/10，
自己的距离项恒为 0，坦克隔 25 码也只加 2.5，于是坦克长期以微弱优势压过自己，治疗永远是"第二低"。

口径：
- 只算治疗存活期（死后采样剔除）。
- **残血秒** = 治疗自己血量 <50% 的采样秒。
- **获治疗秒** = 这些秒里出现任意一条以治疗为 target 的 `heal:` 事件（含 HoT 跳动，偏保守）。
- **坦克更低秒** = 同刻坦克的 probeValue 近似值（血量% + 2.5）仍低于治疗自己，即"被坦克抢走"。

用法：healer_self_care.py <run_id> [...]
"""
import subprocess, sys, re
from collections import defaultdict

MYSQL = "/opt/homebrew/opt/mysql@8.4/bin/mysql"

def q(s):
    return [l.split("\t") for l in subprocess.run([MYSQL,"-uroot","-N","--batch","-e",s],
            capture_output=True,text=True,check=True).stdout.splitlines() if l]

def main(runs):
    ids = ",".join(runs)
    cls = dict(q("SELECT guid,class FROM acore_characters.characters WHERE guid BETWEEN 791 AND 795;"))
    tank = next(g for g, c in cls.items() if c == "2")
    healer = next(g for g, c in cls.items() if c == "5")
    tot = defaultdict(int)
    print(f"{'run/seq':>9} {'res':>5} {'治疗<50%秒':>10} {'其中获治疗':>11} {'坦克更低秒':>11} {'治疗死亡':>8}")
    for aid, run, seq, res in q(f"""SELECT id,run_id,seq,result FROM acore_characters.raidtest_attempts
                                    WHERE run_id IN ({ids}) AND result<>'aborted' ORDER BY run_id,seq;"""):
        hp = defaultdict(dict)
        for g, r, d in q(f"""SELECT source_guid,rel_ms,detail FROM acore_characters.raidtest_events
                             WHERE attempt_id={aid} AND detail LIKE 'resource:hp=%';"""):
            m = re.match(r"resource:hp=(\d+)/(\d+)", d)
            if m and int(m.group(2)):
                hp[g][int(r)//1000] = 100.0*int(m.group(1))/int(m.group(2))
        dead = q(f"""SELECT MIN(rel_ms) FROM acore_characters.raidtest_events
                     WHERE attempt_id={aid} AND event_type='death' AND source_guid={healer};""")
        dt = int(dead[0][0])//1000 if dead and dead[0][0] not in ('NULL', None) else 10**9
        healed = {int(r)//1000 for (r,) in q(f"""SELECT rel_ms FROM acore_characters.raidtest_events
                                                 WHERE attempt_id={aid} AND detail LIKE 'heal:%'
                                                 AND target_guid={healer};""")}
        low = got = tanklower = 0
        for s, p in sorted(hp.get(healer, {}).items()):
            if s >= dt or p >= 50:
                continue
            low += 1
            if s in healed:
                got += 1
            tp = hp.get(tank, {}).get(s)
            if tp is not None and tp + 2.5 < p:
                tanklower += 1
        tot['low'] += low; tot['got'] += got; tot['tl'] += tanklower
        print(f"{run+'/'+seq:>9} {res:>5} {low:>10} {got:>11} {tanklower:>11} "
              f"{(str(dt)+'s') if dt < 10**9 else '-':>8}")
    pct = 100.0*tot['got']/tot['low'] if tot['low'] else 0
    print(f"\n合计：治疗 <50% 共 {tot['low']} 秒，其中 {tot['got']} 秒收到治疗 = **{pct:.0f}%**；"
          f"{tot['tl']} 秒被坦克的取值分压过")

if __name__ == "__main__":
    main(sys.argv[1:])
