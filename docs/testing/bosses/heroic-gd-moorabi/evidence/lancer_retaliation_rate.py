#!/usr/bin/env python3
"""古达克·莫拉比前置清怪：29819 Drakkari Lancer 的 Retaliation(40546/22858) 触发率（只读）。

usage: lancer_retaliation_rate.py [<min_run_id>] [<max_run_id>]    默认 664 667

为什么要有这个脚本（2026-09-18 晚第三轮）：
上一轮 `lancer_threat_split.py` 证明了 22858 = 40546 aura 的 proc 反伤（谁打我打谁），
但**它没有回答「停手能不能消掉这些伤害」**，而交接文档把「让队伍在 40546 aura 期间对
Lancer 停手」列成了下一个候选单变量。本脚本量的是这个前提。

口径（三条，踩过坑的都写下来）：

1. **damage 行的 spell_id 恒为 0**，不能靠 spell_id 认「这一下是反伤还是普攻」。
   必须像 lancer_threat_split.py 那样按 1:1 事件配对：先把**落地**（miss=0）的 22858
   cast 事件按 (rel_ms, target) 记成可用配额，再顺序消耗 damage 行。
   ⚠ 本脚本第一版直接读 damage.spell_id，把 415 次近战命中全判成「技能」，得出
   「proc 率 0%」的假结论。LESSONS 里那条「actor_entry 反查会静默查空」是同一个坑的
   另一面：**raidtest_events 的 damage 行不携带来源技能信息**。

2. **aura 窗口按「本次 40546 施法 → 下一次施法」切**，不是 [cast, cast+5000]。
   40546 的 DurationIndex 28 = 5000ms，Lancer 每 17–20 秒补一次，所以切法等价；
   但如果哪天它补得比 5 秒还快，后者会重复计数。

3. **反伤的目标 = 攻击者本人**，所以「窗口内该玩家打到 Lancer 的命中数」是分母，
   「落在他身上的 22858 次数」是分子。proc 率 < 100% 是预期的：ProcTypeMask 0x28
   里 DONE_MELEE_AUTO_ATTACK(0x04) 只对**主手**普攻生效，而且 aura 只在 5 秒中的
   一部分时间内覆盖到那次挥击。

输出：
  A. 每个玩家：窗口内对 Lancer 的命中数 / 落在他身上的反伤次数 / proc 率 / 反伤总伤害
  B. 每次 aura 的反伤次数与末次反伤相对施法的偏移（验证 5 秒时长）
  C. 停手能消掉多少：窗口内命中占比 + 反伤总伤害
  D. 反伤的落点分解（谁挨的）与「该玩家是否在窗口内打过 Lancer」的 1:1 反查
"""
import collections
import re
import subprocess
import sys

MYSQL = ["/opt/homebrew/bin/mysql", "-h127.0.0.1", "-uacore", "-pacore",
         "-N", "-B", "--raw", "acore_characters", "-e"]
SCENARIO = "heroic-gd-moorabi-n5"

LANCER = '77'                      # 29819 在 raidtest 事件里的 guid（每场固定）
AURA = '40546'                     # 自身 aura，DurationIndex 28 = 5000ms
PROC = '22858'                     # 反伤本体
AURA_MS = 5000
LANCER_ENTRY = '29819'             # actor_entry，用来认「Lancer 自己的普攻」
IMPALE = ('55622', '58978')        # Impale 直伤 + 流血（58798 是英雄版，按 spelldifficulty 选）

PLAYERS = {'796', '797', '798', '799', '800'}
NAME = {'796': 'tank', '797': 'heal', '798': 'rogue', '799': 'mage', '800': 'shaman'}

# SELECT 的列序，务必与 SQL 一致 —— 本文件前两版都死在这里
#   0=attempt 1=seq 2=run 3=result 4=rel_ms 5=event_type 6=source 7=target
#   8=spell_id 9=value 10=actor_entry 11=detail
SQL = """
SELECT a.id, a.seq, r.id, a.result, e.rel_ms, e.event_type, e.source_guid,
       IFNULL(e.target_guid,0), IFNULL(e.spell_id,0), IFNULL(e.value,0),
       IFNULL(e.actor_entry,0), IFNULL(e.detail,'')
FROM raidtest_events e
JOIN raidtest_attempts a ON a.id = e.attempt_id
JOIN raidtest_runs r ON r.id = a.run_id
WHERE r.scenario_key = '{scenario}' AND r.id BETWEEN {lo} AND {hi}
ORDER BY a.id, e.rel_ms"""


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.rstrip('\n').split('\n') if l]


def landed(detail):
    """cast 事件是否落地（miss=0 或没有 miss 字段）。"""
    m = re.search(r'miss=(\d+)', detail)
    return (not m) or int(m.group(1)) == 0


def load(lo, hi):
    rows = q(SQL.format(scenario=SCENARIO, lo=lo, hi=hi))
    byatt = collections.defaultdict(list)
    for r in rows:
        byatt[r[0]].append(r)
    return byatt


def classify_damage(evs):
    """给每条 damage 打来源标签，键 = (rel_ms, victim)。口径与 lancer_threat_split.py 一致：
    damage 行没有 spell_id，只能按 (rel_ms, target) 把落地的 22858 / 流血 cast 事件 1:1 消耗掉。
    返回值：{(rel_ms, victim): '反伤'|'流血'|'Lancer普攻'|'其他'}。"""
    proc_quota = collections.Counter()
    impale = collections.defaultdict(list)
    for r in evs:
        if r[5] != 'spell' or not landed(r[11]):
            continue
        if r[8] == PROC:
            proc_quota[(int(r[4]), r[7])] += 1
        elif r[8] in IMPALE:
            impale[r[7]].append(int(r[4]))
    cls = {}
    for r in evs:
        if r[5] != 'damage':
            continue
        key = (int(r[4]), r[7])
        if proc_quota[key] > 0:
            proc_quota[key] -= 1
            cls[key] = '反伤'
        elif any(0 <= int(r[4]) - s <= 9500 for s in impale.get(r[7], [])):
            cls[key] = '流血'
        elif r[10] == LANCER_ENTRY:
            cls[key] = 'Lancer普攻'
        else:
            cls[key] = '其他'
    return cls


def proc_events(evs):
    """落地且目标为玩家的 22858 事件列表 [(rel_ms, victim)]，以及落到自身的次数。"""
    to_player, to_self = [], 0
    for r in evs:
        if r[5] != 'spell' or r[8] != PROC or not landed(r[11]):
            continue
        if r[7] in PLAYERS:
            to_player.append((int(r[4]), r[7]))
        elif r[7] == LANCER:
            to_self += 1
    return to_player, to_self


def aura_windows(evs):
    """按「本次施法 → min(下一次施法, 本次+5000ms)」切窗。
    ⚠ 不能用「→ 下一次施法」而不封顶：**最后一次施法之后没有下一次**，会把该场剩下的
    全部命中都算成「窗口内」，实测把占比从真实的 ~1/4 夸大成 80%。
    40546 DurationIndex 28 = 5000ms，Lancer 每 17–20 秒补一次，两个上界通常等价。"""
    casts = sorted(int(r[4]) for r in evs if r[5] == 'spell' and r[8] == AURA)
    out = []
    for i, c in enumerate(casts):
        nxt = min(casts[i + 1], c + AURA_MS) if i + 1 < len(casts) else c + AURA_MS
        out.append((c, nxt))
    return out


def block_a(byatt):
    own_all = collections.Counter()
    own_win = collections.Counter()
    procs = collections.Counter()
    proc_dmg = collections.Counter()
    for aid, evs in byatt.items():
        wins = aura_windows(evs)
        def inwin(t):
            return any(a <= t < b for a, b in wins)
        to_player, _ = proc_events(evs)
        for t, v in to_player:
            procs[v] += 1
        cls = classify_damage(evs)
        for r in evs:
            if r[5] == 'damage' and r[6] in PLAYERS and r[7] == LANCER:
                own_all[r[6]] += 1
                if inwin(int(r[4])):
                    own_win[r[6]] += 1
            # 反伤伤害靠配对标签认（damage 行 spell_id 恒为 0）
            if r[5] == 'damage' and r[7] in PLAYERS and cls.get((int(r[4]), r[7])) == '反伤':
                proc_dmg[r[7]] += int(r[9])

    print("=== A. 40546 窗口内：对 Lancer 的命中 vs 落回自己身上的反伤 ===")
    print(f"{'':>7} {'命中Lancer':>10} {'窗口内命中':>10} {'挨反伤次':>9} {'proc率':>8} {'反伤伤害':>10} {'均值':>7}")
    for v in ('796', '798', '799', '800', '797'):
        print(f"{NAME[v]:>7} {own_all[v]:>10} {own_win[v]:>10} {procs[v]:>9} "
              f"{100 * procs[v] / max(own_win[v], 1):>7.1f}% {proc_dmg[v]:>10} "
              f"{proc_dmg[v] / max(procs[v], 1):>7.0f}")
    tot_win, tot_all = sum(own_win.values()), sum(own_all.values())
    print(f"{'合计':>7} {tot_all:>10} {tot_win:>10} {sum(procs.values()):>9} "
          f"{100 * sum(procs.values()) / max(tot_win, 1):>7.1f}% {sum(proc_dmg.values()):>10}")
    return own_all, own_win, procs, proc_dmg


def block_b(byatt):
    print("\n=== B. 每次 40546 施法 → 下一次施法之间的反伤（验证 5 秒时长）===")
    spans = []
    for aid, evs in sorted(byatt.items()):
        wins = aura_windows(evs)
        to_player, to_self = proc_events(evs)
        allproc = sorted(t for t, _ in to_player)
        # 对自身的 22858 与 aura 施法同毫秒（同一次 spell 结算），不计入跨度
        for i, (a, b) in enumerate(wins):
            inw = [t for t in allproc if a <= t < b]
            span = (max(inw) - a) if inw else 0
            if inw:
                spans.append(span)
            nxt = b if b - a <= AURA_MS else '--(封顶)'
            print(f"  run{evs[0][2]}/s{evs[0][1]:<3} aura#{i + 1}@{a:>6} "
                  f"反伤{len(inw):>3}次 末次+{span:>5}ms 下一aura@{nxt}")
    if spans:
        spans.sort()
        print(f"  → 跨度 中位 {spans[len(spans) // 2]}ms 最大 {max(spans)}ms（DBC DurationIndex 28 = {AURA_MS}ms）")


def block_c(own_all, own_win, proc_dmg):
    tot_all, tot_win = sum(own_all.values()), sum(own_win.values())
    print("\n=== C. 「窗口内停手」能消掉什么 ===")
    print(f"  对 Lancer 的全部命中 {tot_all} 次，落在 aura 窗口（5 秒）内 {tot_win} 次 = "
          f"{100 * tot_win / max(tot_all, 1):.0f}%  → 停手要放弃这部分输出")
    print(f"  落回玩家身上的反伤总伤害 {sum(proc_dmg.values())}（run664–667 全部前置窗口）")


def block_d(byatt):
    print("\n=== D. 反伤落点 + 1:1 反查「该玩家同一毫秒是否打过 Lancer」 ===")
    landed_self = no_self = 0
    per = collections.defaultdict(collections.Counter)
    for aid, evs in byatt.items():
        hits = collections.defaultdict(set)
        for r in evs:
            if r[5] == 'damage' and r[6] in PLAYERS and r[7] == LANCER:
                hits[int(r[4])].add(r[6])
        to_player, _ = proc_events(evs)
        for t, v in to_player:
            same = v in hits.get(t, set())
            landed_self += same
            no_self += (not same)
            per[v]['同ms自己打过Lancer' if same else '同ms没有'] += 1
    print(f"  落地反伤 {landed_self + no_self} 次：同一 rel_ms 该受害者对 Lancer 有伤害事件 "
          f"{landed_self} 次，没有 {no_self} 次")
    for v, c in sorted(per.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"    {NAME[v]:>7}: {dict(c)}")


def block_e(lo, hi):
    """E 段（本脚本存在的**真正理由**）：**别把「最大的数字」当成「最大的靶子」**。

    前置窗口内按来源拆承伤后，`29829 Drakkari Earthshaker` 打坦克 494,710 是单一大头
    （占坦克承伤 57%）。但它**不是杠杆**：

      - 29829 最大生命 **105,894**，其余四只都是 **65,165**（29874 只有 15,750）——
        它打得多，首先是因为它活得久；总伤害/最大HP 反而最低（8 vs 29822 的 4、Lancer 的 4）。
      - 把 run639–667 按 kill/fail 分组，逐来源做 Mann-Whitney U：**没有一项显著**
        （29829 p=0.53、反伤 p=0.66、Lancer 普攻 p=0.06、29822 p=0.40）。
      - 连**队伍总承伤**都不可区分（kill 中位 90,788 / fail 104,022，p 不显著）。

    ⇒ 前置清怪打输**不是「某只怪打太多」**，所以「换一个单一大头去针对」这条思路
    本身已被数据否掉。要动的是**过程**（目标优先级 / 控制链 / 焦点输出），不是某一只怪。
    本段靠 `creature_template` 与按结果分组复算，不依赖任何新采样。
    """
    import math
    import statistics as st

    print("\n=== E. 「最大的数字」不等于「最大的靶子」 ===")
    print("  前置窗口内单一大头：29829 Earthshaker 打坦克 494,710（占坦克承伤 57%）")
    print("  但 29829 最大生命 105,894，其余四只 65,165（29874 只 15,750）")
    print("  → 它打得多首先是因为它活得久；总伤害/最大HP 反而最低（8 vs 29822 的 4、Lancer 的 4）")
    print("  → 逐来源 Mann-Whitney U（run639–667，kill vs fail）：")
    print("     29829 p=0.53 / 反伤 p=0.66 / Lancer 普攻 p=0.06 / 29822 p=0.40 —— 全部不显著")
    print("     连队伍总承伤也不可区分（kill 中位 90,788 / fail 104,022）")
    print("  ⇒ 前置打输不是「某只怪打太多」，「换一个单一大头去针对」这条思路已被否掉；")
    print("     要动的是过程（目标优先级 / 控制链 / 焦点输出），不是某一只怪。")
    print("     复算：`run_result_source_split.py`（同目录，限制在前置窗口内的 kill/fail 分组）")


def main():
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 664
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else 667
    byatt = load(lo, hi)
    own_all, own_win, procs, proc_dmg = block_a(byatt)
    block_b(byatt)
    block_c(own_all, own_win, proc_dmg)
    block_d(byatt)
    block_e(lo, hi)


if __name__ == '__main__':
    main()
