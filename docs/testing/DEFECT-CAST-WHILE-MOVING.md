# 共享层缺陷：bot 移动时放弃一切读条法术（不会停下来施法）

> 状态：**已定位、已量化、未修复**。
> 发现于 2026-09-12 英雄艾卓-尼鲁布 / 阿努巴拉克第三轮（run449–run456）。
> 这是本项目目前已知影响面最大的单个底层缺陷，**建议单开一轮上下文专门修**。

## 一句话

`PlayerbotAI::CastSpell` 在 bot 处于移动状态时，把**任何有读条时间的法术直接取消并返回
失败**，而本该解决这件事的 `bot->StopMoving()` 被注释掉了。bot 从不为了施法停下来，
于是在任何有强制位移的战斗里，它退化成只会放瞬发法术。

## 代码位置

`azerothcore-wotlk/modules/mod-playerbots/src/Bot/PlayerbotAI.cpp:3946`
（分支 `codex/an-trash-cc-shackle`，函数 `bool PlayerbotAI::CastSpell(uint32 spellId, float x, float y, float z, ...)`）

```cpp
    spell->prepare(&targets);

    if (bot->isMoving() && spell->GetCastTime())
    {
        // bot->StopMoving();                                  // <-- 被注释掉
        SetNextCheckDelay(sPlayerbotAIConfig.reactDelay);
        spell->cancel();
        delete spell;
        return false;                                          // <-- 直接放弃
    }
```

注意它是在 `spell->prepare()` **之后**才判断的，所以每次都白走一遍施法准备再取消。

调用链：
`CastSpellAction::Execute`（`src/Ai/Base/Actions/GenericSpellActions.cpp:181`）
`return botAI->CastSpell(spell, GetTarget());` → 上面那段 → 返回 false
→ 引擎把该动作记为 `FAILED`，`SetNextCheckDelay(reactDelay)` 后下个 tick 重来；
如果 bot 还在动，再次 `FAILED`。没有任何机制让它停下来。

## 证据

诊断配置：`AiPlayerbot.LogInGroupOnly = 0`，逐 tick 轨迹落在
`azerothcore-wotlk/Playerbots.log`（注意：**不在** `env/dist/logs/`，服务器 cwd 是
`azerothcore-wotlk/`）。

### 1. 成功率随读条时间单调崩塌

run456（`heroic-an-anubarak-n5`，单场 258.0 秒击杀）里戒律牧师 `Raidtebnfivc` 的动作结果：

| 动作 | 读条 | OK | FAILED | IMPOSSIBLE | PREREQ | 合计 |
|---|---|---|---|---|---|---|
| power word: shield on party | 瞬发 | **25** | 102 | 82 | 127 | 379 |
| renew on party | 瞬发 | **14** | 40 | 65 | 54 | 207 |
| prayer of mending on party | 瞬发 | **13** | 22 | 85 | 35 | 200 |
| penance on party | 2.0s 引导 | **8** | 43 | 35 | 51 | 143 |
| flash heal on party | 1.5s | **3** | 25 | 57 | 28 | 113 |
| **greater heal on party** | **2.5s** | **0** | 33 | 44 | 33 | 110 |
| shoot（魔杖） | — | 23 | 0 | 75 | 23 | 220 |

汇总：**瞬发治疗 52 次成功 / 0 次因此失败；有读条的治疗 11 次成功 / 101 次 FAILED
（失败率 92%）；2.5 秒的强效治疗 110 次尝试、0 次成功。**

统计口径（可复现）：

```bash
cd azerothcore-wotlk && python3 - <<'EOF'
import re, collections
pat=re.compile(r"<botname> A:(.+?) - (OK|FAILED|IMPOSSIBLE|USELESS|PREREQ|\S+)")
c=collections.defaultdict(collections.Counter)
for line in open('Playerbots.log',errors='ignore'):
    m=pat.search(line)
    if m: c[m.group(1).strip()][m.group(2)]+=1
for name,ct in sorted(c.items(), key=lambda kv:-sum(kv[1].values()))[:16]:
    print(name, dict(ct))
EOF
```

### 2. GCD 利用率

258 秒 ÷ 1.5 秒 GCD ≈ 172 个 GCD，实际只有 **63 次治疗落地（37%）**，
同时甩了 23 次魔杖。跨 5 场统计（run455，约 1220 秒）同样形状：
治疗施法 374 次（每 3.3 秒一次），魔杖 **250 次**。

**牧师有一半以上的 GCD 在空转，不是蓝不够，也不是被打断。**
（蓝量：`hymn of hope` / `shadowfiend` / `mana potion` 全程 `IMPOSSIBLE`，即从未进入低蓝档。）

### 3. 后果：坦克被爆发打死，队伍随之崩

run455 五场团灭的死亡顺序（`raidtest_events` 的 `event_type='death'`，
`source_guid` = 死者、`target_guid` = 击杀者）：

- 4/5 场是**坦克先倒**，治疗死在坦克之后 → 治疗阵亡是结果不是起因
- 27 次死亡里约 20 次的击杀者是小怪（守卫 29216 / 毒疗者 29217，`DamageModifier = 7.5`）
- 历史 6 次超时，坦克 6/6 阵亡，其中 5 次凶手是小怪

只有瞬发 HoT + 护盾顶不住 2–4 只 7.5 倍伤近战精英加上 17k 的践踏。

### 4. 顺带发现（不致命）

每次直接治疗前都会推一个 `remove shadowform` 前置动作，run456 单场 **197 次全部 USELESS**
（戒律牧师根本没有暗影形态）。治疗链路上的冗余，可一并清理。

## 排除项（已核实，不是原因）

- **不是不会法术**：`character_spell` 里 guid 797 同时拥有 47540 / 53005 / 53006 / 53007
  （苦修四个等级）、48071 快速治疗、48063 强效治疗、48072 治疗祷言、48120 联合治疗。
- **不是策略表写错**：`src/Ai/Class/Priest/Strategy/HealPriestStrategy.cpp:49-72`
  的 `party member critical health` / `low health` 顺序是
  盾 → 治疗祷言 → **苦修 → 快速治疗**，优先级正确。
- **不是蓝量**：见上。
- **不是视线**：本轮场景坐标已修到门内侧，治疗对坦克有视线（上一轮的 LoS 缺陷见
  `bosses/heroic-an-anubarak/README.md`）。
- **不是打断**：boss 与小怪都没有沉默/打断技能。

## 修复方向（未实施，供接手判断）

**不要简单地把 `bot->StopMoving()` 取消注释。** 无条件停下会让 bot 站在穿刺地刺里读条，
也会破坏躲践踏这类保命走位——本副本恰好两者都有。

需要区分两类移动：

| 移动来源 | 是否该为施法让路 |
|---|---|
| 阵型/跟随/走位微调（`combat formation move` 等） | **该让**。run456 单场 365 次评估、**0 次 OK**，纯粹在挡施法 |
| 机制闪避（躲穿刺 `dodge impale`、躲践踏 `dodge pound`） | **不该让**，这些是保命动作 |

可能的形状（按侵入性从小到大）：

1. **让治疗动作自己负责停下来**：在 `CastHealingSpellAction` 一侧，判定当前移动是否来自
   低优先级来源，若是则 `StopMoving()` 后再施法。不碰共享的 `CastSpell`。
2. **给 `CastSpell` 加一个"允许为施法停步"的开关**，由调用方（动作）传入，机制闪避动作不传。
3. **引入移动优先级**：`MovementAction` 已有 `MovementPriority` 概念
   （见 `src/Ai/Base/Actions/MovementActions.cpp`），可据此判定是否可被施法打断。

接手时请先确认 `MovementPriority` 的现有语义，再决定走哪条。

## 回归验收口径

改完至少要验这三条，都不需要新工具：

1. **同一场景同一装档，重跑 `heroic-an-anubarak-n5` 5 场**，对比
   `greater heal on party` / `flash heal on party` / `penance on party` 的 OK 次数
   （当前基线：0 / 3 / 8，单场 258 秒）。
2. **确认机制闪避没被破坏**：`dodge impale` 命中次数与承伤应维持在 run449 水平
   （8 次 / 46,759，对比无闪避时的 79 次 / 439,741）。
3. **回归已通过的旧 boss**，尤其治疗压力大的那几个（见 `BOSS-LEDGER.md`）。
   这是共享层改动，影响面是全部内容，不能只看本副本。

## 现场状态（交接时）

- 三个仓库分支：core `codex/an-formation-despawn-crash`、
  mod-playerbots `codex/an-trash-cc-shackle`、mod-raidtest `codex/an-runtime-strategy-names`
- `AiPlayerbot.LogInGroupOnly` 已改回 `1`（诊断开关不能留在打开状态）
- worldserver 跑的是含践踏侧移的二进制；本轮试过又**回退**的改动见
  `bosses/heroic-an-anubarak/README.md` 的「本轮试过并回退」一节
