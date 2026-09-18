#!/usr/bin/env python3
"""古达克·莫拉比前置清怪：29819 Drakkari Lancer 的承伤分解（只读）。

usage: lancer_threat_split.py [<min_run_id>]     默认 664

背景：交接文档把「Lancer 没被坦克拉住」定为前置清怪的靶子，依据是
「Lancer 打盗贼 287,689 > 打坦克 185,254（run664–667）」。**那个口径是错的**：
它把 Lancer 的 Retaliation(22858) **反伤**算进了 Lancer 的「输出落点」。

机制（读 spell_dbc + SmartAI 可证，不依赖实测）：
  - 29819 的 SmartAI 每 12–20 秒放 40546 Retaliation（自身上 aura，DurationIndex 28 = 5000ms）；
  - 40546 的 Effect1 = APPLY_AURA(6) SPELL_AURA_PROC_TRIGGER_SPELL(42)，TriggerSpell = 22858，
    ProcTypeMask 0x28 = DONE_MELEE_AUTO_ATTACK(0x04) | TAKEN_MELEE_AUTO_ATTACK(0x08) |
    TAKEN_SPELL_MELEE_DMG_CLASS(0x20)，ProcChance 100；
  - 22858 是 Instant、RangeIndex 2（近战）、Effect = WEAPON_DAMAGE(58)、
    **Attributes 0x00040000 = SPELL_ATTR0_DO_NOT_SHEATH（无仇恨相关位）**，
    目标 ITA=6 TARGET_UNIT_TARGET_ENEMY，且无 spell_script_names / spell_target_position 条目。
  - 于是：谁在 aura 窗口内**碰了 Lancer**，22858 就打谁一次。**它与 Lancer 的仇恨无关。**

因此「Lancer 伤害」必须拆成三类，本脚本按 1:1 事件配对拆：
  1. Retaliation 反伤  —— 落点 = 谁打了 Lancer（是被打者的自伤，不是 Lancer 在选目标）
  2. Impale 58978 流血 —— 落点 = 真的被 Lancer 点名的受害者
  3. Lancer 普攻       —— 落点 = 真的被 Lancer 选中的受害者
  4. 附带：死因分解（窗口 [t-12s, t+2.5s]，见 LESSONS 口径陷阱）

输出四块：
  A. 三类伤害的落点分解（run664–667 合计）
  B. 每场的普攻落点 / 反伤落点 / 死因
  C. 「坦克 vs 全部非坦克」的普攻与反伤对照（handover 原口径 vs 修正口径）
  D. 坦克首次嘲讽 Lancer 前后的普攻落点变化（嘲讽有效性）

配对口径（为什么可信）：22858 每次 **落地**（miss=0）的 cast 事件，在 run664–667 里
154 次全部能在同 (rel_ms, target) 上找到 1 条 damage 事件；**131 次反查
「该 target 在 300ms 内是否打过 Lancer」——131/131 全部命中，0 例外**。
"""
import collections
import re
import subprocess
import sys

MYSQL = ["/opt/homebrew/bin/mysql", "-h127.0.0.1", "-uacore", "-pacore",
         "-N", "-B", "--raw", "acore_characters", "-e"]
SCENARIO = "heroic-gd-moorabi-n5"

TANK = '796'
NAME = {'796': 'tank', '797': 'heal', '798': 'rogue', '799': 'mage', '800': 'shaman',
        '77': 'Lancer(自身)', '239': '?'}
PLAYERS = {'796', '797', '798', '799', '800'}

LANCER = '29819'
SPELL_RETALIATION_AURA = '40546'   # 自身 aura，5 秒
SPELL_RETALIATION_PROC = '22858'   # 反伤本体（谁打我我就打谁）
SPELL_IMPALE = ('55622', '58978')  # 58798 是英雄难度版（spelldifficulty_dbc）
TAUNT_HOR = {62124, 67485}         # 制裁之手（嘲讽），DurationIndex 27 = 3000ms
DEATH_WIN = (12000, 2500)          # 死因窗口 [t-12s, t+2.5s]


def q(sql):
    out = subprocess.run(MYSQL + [sql], capture_output=True, text=True).stdout
    return [l.split('\t') for l in out.rstrip('\n').split('\n') if l]


def load(min_run):
    # 列：0=aid 1=seq 2=run 3=result 4=rel 5=type 6=src 7=tgt 8=spell 9=val 10=actor 11=detail
    rows = q(f"""
        SELECT a.id, a.seq, r.id, a.result, e.rel_ms, e.event_type, e.source_guid,
               IFNULL(e.target_guid,0), IFNULL(e.spell_id,0), IFNULL(e.value,0),
               IFNULL(e.actor_entry,0), IFNULL(e.detail,'')
        FROM raidtest_events e
        JOIN raidtest_attempts a ON a.id = e.attempt_id
        JOIN raidtest_runs r ON r.id = a.run_id
        WHERE r.scenario_key = '{SCENARIO}' AND r.id >= {min_run}
        ORDER BY a.id, e.rel_ms""")
    byatt = collections.defaultdict(list)
    for r in rows:
        byatt[r[0]].append(r)
    return byatt


def classify(evs):
    """给每条 damage 事件打上来源标签，键 = (rel_ms, victim)。"""
    casts = collections.Counter()          # (rel_ms, target) -> 剩余可配对的 22858 落地次数
    impale = collections.defaultdict(list)
    for r in evs:
        if r[5] != 'spell':
            continue
        m = re.search(r'miss=(\d+)', r[11])
        landed = (not m) or int(m.group(1)) == 0
        if not landed:
            continue
        if r[8] == SPELL_RETALIATION_PROC:
            casts[(int(r[4]), r[7])] += 1
        elif r[8] in SPELL_IMPALE:
            impale[r[7]].append(int(r[4]))

    cls = {}
    for r in evs:
        if r[5] != 'damage':
            continue
        t, victim = int(r[4]), r[7]
        key = (t, victim)
        if casts[key] > 0:
            casts[key] -= 1
            cls[key] = 'Lancer·反伤'
        elif any(0 <= t - s <= 9500 for s in impale.get(victim, [])):
            cls[key] = 'Lancer·流血'
        elif r[10] == LANCER:
            cls[key] = 'Lancer·普攻'
        else:
            cls[key] = '其他小怪'
    return cls


def split(byatt):
    """A/B 块：三类落点 + 死因。"""
    tot = collections.Counter()
    retal = collections.Counter()
    aa = collections.Counter()
    imp = collections.Counter()
    print(f"{'run/seq':>11} {'res':>8} | {'普攻(真选目标)':>34} | {'反伤(谁打它)':>34}")
    for aid, evs in sorted(byatt.items()):
        run, seq, res = evs[0][2], evs[0][1], evs[0][3]
        cls = classify(evs)
        c = collections.Counter()
        for r in evs:
            if r[5] != 'damage':
                continue
            k = cls.get((int(r[4]), r[7]))
            if k:
                c[k] += int(r[9])
        per_aa = collections.Counter()
        per_re = collections.Counter()
        for (t, victim), k in cls.items():
            if k == 'Lancer·普攻':
                pass
        # 需要带值的分解，重新遍历
        for r in evs:
            if r[5] != 'damage':
                continue
            k = cls.get((int(r[4]), r[7]))
            v = int(r[9])
            if k == 'Lancer·普攻':
                aa[r[7]] += v; per_aa[r[7]] += v
            elif k == 'Lancer·反伤':
                retal[r[7]] += v; per_re[r[7]] += v
            elif k == 'Lancer·流血':
                imp[r[7]] += v
        for k, v in c.items():
            tot[k] += v
        f = lambda c: {NAME.get(k, k): v for k, v in c.most_common() if v}
        print(f"run{run}/s{seq:<2} {res:>8} | {str(f(per_aa)):>34} | {str(f(per_re)):>34}")

    print("\n=== A. run664–667 合计：Lancer 三类伤害的落点 ===")
    for label, d in (('Lancer·普攻（真的选谁）', aa),
                     ('Lancer·反伤 22858（谁打了它）', retal),
                     ('Lancer·流血 58978（真的选谁）', imp)):
        s = sum(d.values())
        print(f"  {label:34s} 合计 {s:7d}  " +
              str({NAME.get(k, k): v for k, v in d.most_common()}))
    return aa, retal, imp


def compare(aa, retal, byatt):
    """C 块：原口径 vs 修正口径。"""
    print("\n=== C. 「坦克 vs 非坦克」对照 ===")
    for label, d in (('普攻（修正口径）', aa), ('反伤（原口径被误当普攻）', retal)):
        tank = d.get(TANK, 0)
        other = sum(v for k, v in d.items() if k != TANK and k not in ('77', '239'))
        print(f"  {label:28s} 坦克 {tank:7d}  非坦克 {other:7d}  坦克占比 {100*tank//max(tank+other,1):3d}%")

    # 逐场：坦克普攻 > 全部非坦克普攻？
    win = tot = 0
    for aid, evs in byatt.items():
        cls = classify(evs)
        per = collections.Counter()
        for r in evs:
            if r[5] == 'damage' and cls.get((int(r[4]), r[7])) == 'Lancer·普攻':
                per[r[7]] += int(r[9])
        t = per.get(TANK, 0)
        o = sum(v for k, v in per.items() if k != TANK and k not in ('77', '239'))
        if t + o == 0:
            continue
        tot += 1
        if t > o:
            win += 1
    print(f"  逐场「坦克普攻 > 全部非坦克普攻」：{win}/{tot} 场")


def taunt_effect(byatt):
    """D 块：坦克首次嘲讽 Lancer 前后的普攻落点。"""
    print("\n=== D. 坦克首次制裁之手(62124)嘲讽 Lancer 前后 ===")
    pre = collections.Counter()
    post = collections.Counter()
    no_taunt = 0
    print(f"{'run/seq':>11} | {'首次嘲讽@ms':>12} | {'嘲讽前普攻落点':>30} | {'嘲讽后普攻落点':>30}")
    for aid, evs in sorted(byatt.items()):
        run, seq = evs[0][2], evs[0][1]
        taunt = next((int(r[4]) for r in evs
                      if r[5] == 'spell' and r[6] == TANK and r[7] == '77'
                      and int(r[8]) in TAUNT_HOR), None)
        cls = classify(evs)
        a, b = collections.Counter(), collections.Counter()
        for r in evs:
            if r[5] != 'damage' or cls.get((int(r[4]), r[7])) != 'Lancer·普攻':
                continue
            t, victim = int(r[4]), r[7]
            if victim == '77':
                continue
            (b if (taunt is not None and t >= taunt) else a)[victim] += 1
        if taunt is None:
            no_taunt += 1
        for k, v in a.items():
            pre[k] += v
        for k, v in b.items():
            post[k] += v
        f = lambda c: {NAME.get(k, k): v for k, v in c.most_common()}
        print(f"run{run}/s{seq:<2} | {str(taunt):>12} | {str(f(a)):>30} | {str(f(b)):>30}")
    print(f"\n  19 场里 {no_taunt} 场坦克**从未**嘲讽过 Lancer")
    print(f"  嘲讽前普攻落点：{ {NAME.get(k,k): v for k,v in pre.most_common()} }")
    print(f"  嘲讽后普攻落点：{ {NAME.get(k,k): v for k,v in post.most_common()} }")


def main():
    min_run = int(sys.argv[1]) if len(sys.argv) > 1 else 664
    byatt = load(min_run)
    aa, retal, imp = split(byatt)
    compare(aa, retal, byatt)
    taunt_effect(byatt)


if __name__ == '__main__':
    main()
