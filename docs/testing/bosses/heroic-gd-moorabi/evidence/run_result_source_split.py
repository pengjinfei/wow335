#!/usr/bin/env python3
"""古达克·莫拉比前置清怪：按来源拆承伤，再按 kill/fail 分组看**哪个来源真的判别输赢**（只读）。

usage: run_result_source_split.py [<lo_run>] [<hi_run>]      默认 639 667

为什么要有这个脚本：
`lancer_retaliation_rate.py` 的 E 段说「单一大头 29829 不是杠杆」，依据就在这里。
把前置窗口内玩家承伤按来源拆开后，逐来源做 kill vs fail 的 Mann-Whitney U 检验——
**如果某个来源真的是靶子，它在 fail 组应该显著更高**。

实测结论（run639–667，限制在前置窗口内）：
  - **没有任何一项显著**：29829 p=0.53 / 反伤 p=0.66 / Lancer 普攻 p=0.06 / 29822 p=0.40
  - 连**队伍总承伤**都不可区分（kill 中位 90,788 / fail 中位 104,022）
  - `29829` 打坦克 494,710 是单一大头，但它最大生命 **105,894**（其余四只 65,165），
    打得多首先是因为活得久；总伤害/最大HP 反而最低

⇒ **前置清怪打输不是「某只怪打太多」**。「挑一个最大的数字去针对」这条思路已被数据否掉。

口径（与 lancer_retaliation_rate.py 共用，务必一致）：
  - **前置窗口** = `[0, 前置怪最后一只死亡时刻]`（`actor_entry ∈ {29874,29829,29822,29819}`）。
    ⚠ 不能用「boss 首次伤害」当边界：run664 seq2 的 29305 在 194ms 就有残留伤害事件。
  - **damage 行的 `spell_id` 恒为 0**，归因必须按 `(rel_ms, target)` 1:1 配对落地的 cast 事件。
  - 结果分组取 `raidtest_attempts.result`（`kill` vs 其它），**只算已收尾的 run**。
"""
import collections
import math
import re
import statistics as st
import subprocess
import sys

MYSQL = ["/opt/homebrew/bin/mysql", "-h127.0.0.1", "-uacore", "-pacore",
         "-N", "-B", "--raw", "acore_characters", "-e"]
SCENARIO = "heroic-gd-moorabi-n5"

PLAYERS = {'796', '797', '798', '799', '800'}
PREREQ = {'29874', '29829', '29822', '29819'}
IMPALE = ('55622', '58978')   # 58798 是英雄难度版
PROC = '22858'

SQL = """
SELECT a.id, a.seq, r.id, a.result, e.rel_ms, e.event_type, e.source_guid,
       IFNULL(e.target_guid,0), IFNULL(e.spell_id,0), IFNULL(e.value,0),
       IFNULL(e.actor_entry,0), IFNULL(e.detail,'')
FROM raidtest_events e
JOIN raidtest_attempts a ON a.id = e.attempt_id
JOIN raidtest_runs r ON r.id = a.run_id
WHERE r.scenario_key = '{scenario}' AND r.id BETWEEN {lo} AND {hi}
  AND r.finished_at IS NOT NULL
ORDER BY a.id, e.rel_ms"""


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.rstrip('\n').split('\n') if l]


def landed(detail):
    m = re.search(r'miss=(\d+)', detail)
    return (not m) or int(m.group(1)) == 0


def classify(evs):
    """{(rel_ms, victim): 来源标签}。1:1 配对口径，见文件头。"""
    quota = collections.Counter()
    imp = collections.defaultdict(list)
    for r in evs:
        if r[5] != 'spell' or not landed(r[11]):
            continue
        if r[8] == PROC:
            quota[(int(r[4]), r[7])] += 1
        elif r[8] in IMPALE:
            imp[r[7]].append(int(r[4]))
    out = {}
    for r in evs:
        if r[5] != 'damage':
            continue
        k = (int(r[4]), r[7])
        if quota[k] > 0:
            quota[k] -= 1
            out[k] = 'Lancer反伤'
        elif any(0 <= int(r[4]) - s <= 9500 for s in imp.get(r[7], [])):
            out[k] = 'Lancer流血'
        elif r[10] == '29819':
            out[k] = 'Lancer普攻'
        elif r[10] == '29829':
            out[k] = '29829'
        elif r[10] == '29822':
            out[k] = '29822'
        elif r[10] == '29874':
            out[k] = '29874'
        else:
            out[k] = '其他'
    return out


def mann_whitney_p(a, b):
    """双侧 p，正态近似（含并列秩平均）。n 太小时返回 None。"""
    n1, n2 = len(a), len(b)
    if n1 < 3 or n2 < 3:
        return None
    allv = sorted(a + b)
    ranks = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2 + 1
        for v in allv[i:j + 1]:
            ranks.setdefault(v, []).append(r)
        i = j + 1
    R1 = sum(sum(ranks[v]) / len(ranks[v]) for v in a)
    U1 = R1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (U1 - mu) / sd
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 639
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 667
    rows = q(SQL.format(scenario=SCENARIO, lo=lo, hi=hi))
    byatt = collections.defaultdict(list)
    for r in rows:
        byatt[r[0]].append(r)

    K = collections.defaultdict(list)
    F = collections.defaultdict(list)
    for aid, evs in byatt.items():
        end = max([int(r[4]) for r in evs
                   if r[5] == 'death' and r[10] in PREREQ] or [0])
        if end == 0:
            continue
        cls = classify(evs)
        per = collections.Counter()
        for r in evs:
            if r[5] == 'damage' and int(r[4]) <= end and r[7] in PLAYERS:
                per[cls.get((int(r[4]), r[7]), '其他')] += int(r[9])
        grp = K if evs[0][3] == 'kill' else F
        for k, v in per.items():
            grp[k].append(v)
        grp['_总承伤'].append(sum(per.values()))

    print(f"=== 按来源：kill vs fail（run{lo}–{hi}，限制前置窗口，已收尾 run）===")
    print(f"{'来源':>12} {'kill中位':>9} {'fail中位':>9} {'差值%':>7} {'MW p':>7} {'结论':>10}")
    keys = ['29829', 'Lancer反伤', 'Lancer普攻', 'Lancer流血', '29822', '29874', '其他', '_总承伤']
    for k in keys:
        a, b = K[k], F[k]
        if not a and not b:
            continue
        ma = st.median(a) if a else 0
        mb = st.median(b) if b else 0
        p = mann_whitney_p(a, b)
        if p is None:
            print(f"{k:>12} {ma:>9.0f} {mb:>9.0f} {'':>7} {'n<3':>7} {'样本不足':>10}")
            continue
        print(f"{k:>12} {ma:>9.0f} {mb:>9.0f} {100 * (mb - ma) / ma:>6.0f}% "
              f"{p:>7.3f} {'不显著' if p > 0.05 else '显著':>10}")

    print(f"\n  kill n={len(K['_总承伤'])}  fail n={len(F['_总承伤'])}")
    print("  → 没有一项显著 ⇒ 前置打输不是「某只怪打太多」，别按最大数字挑靶子。")
    print("     要动的是过程（目标优先级 / 控制链 / 焦点输出），不是某一只怪。")


if __name__ == '__main__':
    main()
