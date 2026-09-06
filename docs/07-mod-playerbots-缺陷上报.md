# mod-playerbots 缺陷整改/上报文档（2026-09-04）

> 项目: `mod-playerbots`（AzerothCore 3.3.5a WotLK Playerbot fork）
> 提交基线: `2f7d9f77` (master)
> 上报方: mod-raidtest 自动化团测框架（框架仅观察记录，不代写 bot 行为逻辑）
> 状态: 供评审/向上游提交 PR 或 issue

## 摘要

mod-raidtest 在 Naxxramas（地图 533）真实战斗的事件流与位置采样归因中，发现 mod-playerbots 三处**独立**缺陷，均导致机器人无法按真实团队副本策略正常战斗。缺陷①为 NAXX Patchwerk BOSS 站位动作整段被注释（未启用）；缺陷②为通用"近战接近目标"判定对大型 BOSS 失真的核心逻辑问题；缺陷③为 Gluth 僵尸处理在 10/25 人模式下均失效（僵尸无人拦截，boss 无限吃僵尸回血）。三者共同造成:近战/坦克不贴近 BOSS、坦克零仇恨、团灭。

---

## 缺陷 ①：Patchwerk 站位动作整段被注释（未启用）

### 现象

10 人团队传送到 Patchwerk 房间任一安全点后，所有 bot 停留在原地不推进;坦克不走向主坦位、远程不拉开距离。BOSS 仇恨打击（Hateful Strike）随即非目标地命中 DPS/治疗，秒杀团灭。

### 证据链（file:line）

| 位置 | 内容 |
|---|---|
| `src/Ai/Raid/Naxx/Action/NaxxActions_Patchwerk.cpp:11-40` | `PatchwerkRangedPositionAction::Execute()` 实现**整段被 `//` 注释**，内含关键逻辑: 判定远程距 boss 12-15 码、`MoveTo` 到正确距离 |
| `src/Ai/Raid/Naxx/NaxxActionContext.h:51` | 动作注册被注释: `//creators["patchwerk ranged position"] = ...` |
| `src/Ai/Raid/Naxx/NaxxActionContext.h:88` | 工厂方法被注释: `//static Action* patchwerk_ranged_position(...)` |
| `src/Ai/Raid/Naxx/NaxxStrategy.cpp:67-76` | 三个触发器被注释: `//"patchwerk tank" (tank face)`, `//"patchwerk ranged" (ranged position)`, `//"patchwerk non-tank" (rear flank)` |
| `src/Ai/Raid/Naxx/Action/NaxxActions.h:325-328` | 动作类声明被注释: `//class PatchwerkRangedPositionAction` |

### 对照（其他 BOSS 站位是激活的）

同目录下其他 NAXX BOSS 站位动作均正常注册与使用:
- `NaxxStrategy.cpp:42` `"kel'thuzad" → kel'thuzad position`
- `NaxxStrategy.cpp:49` `"anub'rekhan" → anub'rekhan position`
- `NaxxStrategy.cpp:89` `"thaddius phase transition" → thaddius move to platform`
- `NaxxStrategy.cpp:102` `"sapphiron ground" → sapphiron ground position`

### Git 历史

`git blame` 确认: 该注释自 2026-03-06 (`18bd6558`) 引入 Naxxramas 策略时就处于注释状态——**作者已写好但从未启用**。

### 建议修法

取消三处主要注释（实现、注册、触发器），保留 `ActionContext.h` 与 `Actions.h` 中的类声明:
```
NaxxActions_Patchwerk.cpp: 恢复 PatchwerkRangedPositionAction::Execute
NaxxActionContext.h:88:     恢复 patchwerk_ranged_position 工厂
NaxxStrategy.cpp:71-73:    恢复 "patchwerk ranged" → patchwerk ranged position
```
也可附加恢复"patchwerk tank"(tank face) 触发器以强化坦克面向。若该动作因历史原因被刻意禁用（如移动死锁），请给出替代方案而非留悬念。

---

## 缺陷 ②：近战接近目标的距离判定对大型 BOSS 失真

### 现象

位置采样显示: 巨型 BOSS（Patchwerk，站距 5 码）与其 10 人团队相距约 5 码时，所有 bot **一毫米不再移动**——`enemy out of melee` 触发器不激活、`reach melee` 动作不执行，近战（尤其坦克）永远不会贴脸。坦克全程只施放无目标 buff、零近战攻击，导致仇恨清零。

### 链路

```
OutOfRangeTrigger::IsActive()      (RangeTriggers.cpp:155-164)
ReachTargetAction::isUseful()      (ReachTargetActions.cpp:31)
    └─ 都调用 → Unit::IsWithinCombatRange(target, distance)
```

核心判定（`src/server/game/Entities/Unit/Unit.cpp:766-779`）:
```cpp
float sizefactor = GetCombatReach() + obj->GetCombatReach();  // 双方体型半径合计
float maxdist   = distance + sizefactor;
return distsq < maxdist * maxdist;
```

### 根因

`IsWithinCombatRange` 将 **BOSS 的体型半径**（`GetCombatReach`）并入"可打击距离"，用于触发玩家的移动。对大型 BOSS（Patchwerk CombatReach 数十码）:
```
distance=0.75 + bot reach(1.5) + boss reach(≈8-10)  → 判定阈值 ≈ 10+ 码
实际站距 5 码 < 10 码  → 判定"已在近战内" → reach melee 不触发 → 不移动
```

该函数语义是"是否在合击中（体型边缘接触即可）"，用于玩家跟怪合理；但被 mod-playerbots 复用为"近战该不该更靠近"的移动判据，对大型 BOSS 造成误判——真实战斗里 bot 需要站到**实际攻击距离**（远程拉满、近战贴平），而非体型边缘。

### 证据（运行时位置采样）

```
boss(entry16028) 位置: 逐步从3256逼近到 3281
所有bot位置:      恒 3286（一毫米不动）
间隔 ≈ 5 码 ≈ 触发阈值内 → 永远判定"已够近"
```

### 建议修法（二选一，倾向 2）

1. **移动判定用实际距离**: `ReachTargetAction::isUseful`/`OutOfRangeTrigger` 对"近战接近目标"改用纯距离判定（`GetDistance` 比较，不含体型合计），或新写 `IsWithinMeleeAttackRange` 语义。
2. **判定阈值按目标** 在大型 BOSS 上收紧: 对 `GetObjectSize() > N` 的 BOSS 目标使 `maxdist` 收敛到"bot reach + 目标 attack reach"，而非两者体型合计。**注意**: 有两个策略同时依赖此判定（RangedCombatStrategy 的移动作业、MeleeCombatStrategy 的 `enemy out of melee`），修法应一并验证。

### 风险提示

改动将影响:
- `EnemyOutOfMeleeTrigger`（近战走近）
- `EnemyOutOfSpellRangeTrigger`（远程射程逼近）
- `ReachSpellAction` / `ReachMeleeAction` cent大使用同一判定
建议改动后用 Kael'Thas、Anub'Rekhan 等不同体型 BOSS 回归验证远近战都能正确走位。

---

## 复现步骤（mod-raidtest 实测环境）

前置: 已编译 mod-raidtest 场景 `naxx-patchwerk`，10 个 80 级 bot（装备 ilvl 264-284 史诗、职业 1坦2治疗7DPS），`playerbots.conf` 关键项: `RandomBotAutologin=1`, `MinRandomBots=0`, `MaxRandomBots=0`。

```
1. .raidtest run naxx-patchwerk --attempts 3
2. 观察 attempt 判定: 3/3 aborted, notes='boss lost combat state (stuck/reset)'
3. 查询 raidtest_events 位置采样:
   SELECT e.rel_ms, e.detail FROM raidtest_events e
   WHERE e.attempt_id=? AND e.detail LIKE 'pos:%' AND e.actor_entry=0;  -- 复数 bot
   → 所有 bot 位置恒定约 5 码外
4. 查询坦克动作: 仅 0~15 次无目标 buff, 无 boss 目标技能
```

## 影响范围

- 通道: 所有 NAXX Patchwerk（架设只 read `naxx-patchwerk` 场景）；缺陷② 影响所有大型/巨型 BOSS 的近战 AI 效率。
- 观察到的最小表现: bot 场均 DPS 施法 ~10 次、BOSS 血量仅降 3-5% 即团灭，攻坚 WotLK 团本（尤其 ICC 大型 BOSS）受阻。

## 关联

- 本项目 context: `docs/06-mod-raidtest-B2-激活输出循环-设计.md`
- 完整数据: `.superpowers/sdd/progress.md` 中 "B2 深挖" 段

---

## 缺陷 ③：Gluth 僵尸处理在 10/25 人模式下均失效（僵尸无人拦截，boss 无限吃僵尸回血）

### 现象

`mod-raidtest` 的 `naxx-gluth` 场景（10 人，10 bot：1 坦 2 治疗 7 DPS）实测：boss 血量钉死在 97-99%，团队输出 113k-206k 全被 boss 回血对冲，战斗 60-73s 全灭（或拖到 timeout）。**根因不是输出不够，是僵尸完全无人处理**：Gluth 每 10s 召唤 Zombie Chow，僵尸径直走向 boss，被 `MoveInLineOfSight` 6.5 码内 `SetGazeOn` 吃下，**每次回 5% 血**。60s 战斗 boss 吃 6-7 只 = 回 30-35% 血。

**25 人模式同样失效**（run44，3 坦克[主坦+2血DK] 6 治疗 16 DPS）：修正框架实例难度后，boss 确以 25 人难度运行（施放 `54427` 25 人 Enrage、白字 15-24k），三坦克被正确识别（`Bots role: tank: 3`），但玩家对僵尸总伤害仍 ≈0，boss 吃 10 只僵尸，73.4s 全灭。

### 证据链（file:line + 实测数据）

**策略代码（已实现但 10 人触发不了）：**
`modules/mod-playerbots/src/Ai/Raid/Naxx/Action/NaxxActions_Gluth.cpp`:

| 位置 | 内容 |
|---|---|
| `NaxxActions_Gluth.cpp:12-87` | `GluthChooseTargetAction::Execute` —— 僵尸处理三路分工 |
| `:36-37` | 主坦 / **index 0 副坦** → 打 boss（`IsAssistTankOfIndex(bot,0)`） |
| `:38-48` | **index 1 副坦** → 拦截血量>10% 的近身僵尸（`IsAssistTankOfIndex(bot,1)`） |
| `:49-63` | 猎人 → 点名 `GetVictim()==boss` 且在 `spellDistance` 内的僵尸 |
| `:64-78` | 其他 DPS → 只杀 **血量 ≤ `decimatedZombiePct=10`** 的僵尸（依赖 Decimate 先削血） |

**三个分支在 10 人标准阵容全部落空：**

1. **副坦拦僵尸**：`IsAssistTankOfIndex(bot,1)` 需要"第 2 个非主坦坦克"（主坦被 `GetMainTankGuid` 排除后 index 从 0 起）。10 人带 1 个副坦（血 DK）时副坦是 **index 0** → 走打 boss 分支。实测 run41：血 DK 对僵尸 **0 伤害**、全程站主坦位。
2. **猎人点名**：`spellDistance=28.5`（PlayerbotAIConfig.cpp:110），僵尸出生中门 `zombiePos[0]=(3267.9,-3172.1)`，猎人在 `rangedPos=(3301.45,-3139.29)`，距离 **~47 码 > 28.5** → 猎人分支永不触发。
3. **DPS 杀僵尸**：`decimatedZombiePct=10` 假设僵尸先被 **Decimate** 削到 ≤10%。但 10 人模式 Decimate 在 **110s**（`boss_gluth.cpp:111` `RAID_MODE(110s,90s)`），而团队 **60-73s 就全灭**（run38/41）→ Decimate 根本没到，僵尸全程满血，DPS 分支永不激活。

**实测数据（raidtest_events）：**

| 指标 | run38（1坦） | run41（+血DK副坦） |
|---|---|---|
| 玩家对僵尸总伤害 | 0 | 1643（≈0） |
| boss 吃僵尸次数 | 6 | 7 |
| 团队对 boss 输出 | 113k | 206k |
| boss 最低血 | 98% | 97% |
| 全灭时间 | 61s | ~66s |

### 25 人验证：index1 副坦同样拦不住僵尸（run44，3 坦克 6 治疗 16 DPS）

**背景**：为验证"僵尸处理是否只适配 25 人"，先修复了 mod-raidtest 的实例难度 bug（组难度未设置导致 25 人场景实际创建 10 人实例，见进度台账 B2 段），使 boss 确以 25 人难度运行。25 人下 3 坦克阵容让 `IsAssistTankOfIndex(bot,1)`（第 2 个非主坦坦克）**首次真实存在**，但拦僵尸分支依旧未触发。

**实测（run44，attempt 1788426346）：**

| 指标 | run44（25人 3坦） |
|---|---|
| 25 人难度确认 | boss 施放 `54427`（25 人 Enrage）而非 28371；白字 15-24k |
| 角色识别 | `Bots role: tank: 3`（血 DK 的 `BloodDKStrategy` 带 `STRATEGY_TYPE_TANK` 已激活） |
| 主坦 | 战士 601（boss 攻击 3 次 62k，6s 后移动追 boss） |
| 血 DK 副坦(602/603) | **全程钉在 engage point(3278,-3162) 不动**，各打 boss 34-38k，对僵尸 **0 伤害** |
| 玩家对僵尸总伤害 | ≈0 |
| boss 吃僵尸 | 10 只 |
| 全灭 | 73.4s（Decimate 90s 未到） |

**index1 分支为何仍落空（三层原因叠加）：**

`GluthChooseTargetAction`（`NaxxActions_Gluth.cpp:38-48`）拦僵尸分支条件：
```cpp
else if (botAI->IsAssistTankOfIndex(bot, 1))   // 第 2 个非主坦坦克
{
    for (Unit* t : target_zombies)
        if (t->GetHealthPct() > 10 && t->GetVictim() != bot &&
            t->GetDistance2d(bot) <= 10.0f)     // 僵尸必须走到副坦 10 码内
            target = t;
}
```

1. **僵尸路径不进副坦 10 码**：僵尸出生中门(3267.9,-3172.1) → 直线冲向 boss(3283.09,-3156.96)，`MoveInLineOfSight` 6.5 码内即被 boss 吃掉。副坦钉在 engage point(3278.29,-3162.06)，僵尸走直线不经过其 10 码范围 → `GetDistance2d <= 10` 永不满足。
2. **index1 分支无 fallback**：`NaxxActions_Gluth.cpp:79` `if (!target || current==target) return false`——副坦走 index1 分支但找不到可拦截僵尸时 target 保持 null → **不切目标**，继续打 boss（实测 602/603 各打 boss 45-54 次）。
3. **副坦拦截走位依赖 Decimate**：`GluthPositionAction` 的 index1 分支（`NaxxActions_Gluth.cpp:119-139`）在 `BeforeDecimate()` 前才让副坦去 `beforeDecimatePos` 拦截；而 25 人 Decimate 是 **90s**（`RAID_MODE(110s,90s)`），run44 仅 73.4s 全灭 → **Decimate 未到，副坦未就位**。

**结论**：25 人 index1 副坦存在、tank 识别正确，但拦僵尸分支因"僵尸路径 10 码 + 无 fallback + 依赖 Decimate"三层限制仍未触发。**僵尸处理完全绑定 Decimate 时间轴**——10 人 Decimate 110s、25 人 90s，团队都活不到，故两种难度下僵尸均无人处理（缺陷③ 为 10/25 人共性问题，非"只适配 25 人"）。

### 根因

`GluthChooseTargetAction` 的僵尸处理**假设**：① 有 2 个副坦克（index 1 才能拦僵尸）；② 猎人在 28.5 码内点名僵尸；③ Decimate 会把僵尸削到 ≤10% 供 DPS 补刀；④ 副坦在 Decimate 前走到 `beforeDecimatePos` 拦截。四个假设对 **10 人标准阵容全部不成立**（1 副坦=index 0、猎人 47 码外、Decimate 110s 太晚、副坦不提前走位）；对 **25 人 3 坦克阵容**（index1 存在）也因"僵尸直线路径不进副坦 10 码 + index1 分支无 fallback + Decimate 90s 仍未到"而失效。**僵尸处理完全绑定 Decimate 时间轴，团队活不到 Decimate 就没有任何僵尸处理路径**。

### 建议修法（mod-playerbots）

任选其一（倾向 2）：

1. **副坦 index 语义修正**：让 index 0 的副坦也执行僵尸拦截（`NaxxActions_Gluth.cpp:38` 从 `IsAssistTankOfIndex(bot,1)` 改为 `IsAssistTankOfIndex(bot,0)`，或按 raid 人数分流）。
2. **DPS 主动处理满血僵尸**：`NaxxActions_Gluth.cpp:64-78` 增加"僵尸存在且血量>10% 时优先转火"的分支（不必等 Decimate），使 10/25 人标准阵容 DPS 都能拦截僵尸——这是最直接破"绑死 Decimate"的方案。
3. **副坦拦截范围/时机修正**：放宽 index1 分支的 `GetDistance2d <= 10` 阈值，或让副坦在 Decimate 前就主动走向僵尸路径（`zombiePos` 中门一侧），拦截直线冲 boss 的僵尸。
4. **猎人射程放宽**：`spellDistance` 或猎人点名分支改用更远的距离阈值（需评估对 25 人平衡的影响）。

### 风险提示

改动影响 Gluth 全难度（10/25 人）的僵尸处理与仇恨分配；建议改后用 10/25 人各跑一次，验证 DPS 是否优先转火僵尸、boss 回血是否被遏制、坦克是否还能维持主坦仇恨。修改 `decimatedZombiePct`/`GetDistance2d` 等阈值时注意不要破坏 Decimate 后的正常转火节奏。

---

## 缺陷 ④：Loatheb 坦克不建立仇恨 + 站位点逼近 50 码脱战边界

### 现象

`naxx-loatheb` 场景（10 人）实测：团队输出正常（run54 全队 2.69M，术士/贼/法/圣骑/萨/猎各自 267k-585k），boss 血量能掉到 59%（run52 74%），但**boss 前 120s 从不普攻坦克**——它一直在打 DPS（猎人 45k、术士 44k 等），坦克只吃到 Necrotic Aura 的 153 低伤。**坦克从开局就没进 boss 仇恨表**（boss 首刀 1489ms 打猎人），导致 DPS 逐个被切死、团队 144s 全灭。

**run55 追加（2026-09-06）**：换血DK+防骑坦克阵容**并未解决建仇**（主坦对 boss 仍 0 输出，见证据③），且出现**新的 DPS 侧引擎停摆**：run55 开局前 60s 全团对 boss 输出 ≈0（仅防骑 4 次 3818），boss 血量 100% 钉死 60s，最终只掉到 86%（比 run54 的 59% 明显退步）——归因见"根因 4"。

### 证据链（file:line + 实测数据）

**① 坦克不建仇（mod-playerbots 策略）：**

`LoathebChooseTargetAction`（`NaxxActions_Loatheb.cpp:30-57`）的选目标逻辑**不区分角色**——任何 bot（含坦克）只要孢子 `GetDistance2d <= 1.0f` 就打孢子，否则打 boss。坦克 run54 前 30s 施法全是 buff（55594 智力×5、5302 盾击×14 打 0 目标）+ 打孢子（355 嘲讽打在 895 上、12721/12868 打 919），**全程不对 boss 出手**（run54 坦克对 boss 仅 2 次 575 伤害）。

**② 站位点逼近脱战边界（mod-playerbots 站位 + 框架 engage）：**

| 位置 | 值 | 距 Loatheb 出生点(2909,-3997.41) |
|---|---|---|
| `NaxxBossHelper.h:347` `mainTankPos` | (2877.57,-3967.00) | **43.7 码** |
| `boss_loatheb.cpp:152-160` `IsInRoom()` | 距出生点 >50 码 → `EnterEvadeMode()` | 脱战阈值 50 码 |

`mainTankPos` 距出生点 43.7 码，**几乎贴着 50 码脱战线**——boss 被打时拉向站位点，位置波动即超 50 码触发 `EnterEvadeMode` 回满血。run52 实测：boss 50s 打到 74% 后被拉远脱战回满 100%。

**③ 实测对比（框架侧 engage 修复前后 + run55 坦克换血DK/防骑验证）：**

| run | 阵容/坦克 | 坦克对 boss | engage 点 | boss 最低血 | 脱战 |
|---|---|---|---|---|---|
| run52 | 战士主坦 | 575×2 | rangePos(2896,-3980) 距出生点 26 码 | 74% | 是（50s 拉远回满） |
| run54 | 血DK主坦 | **575×2** | 出生点旁(2909,-3991) | **59%** | 否（144s 全灭后归位） |
| run55 | 血DK主坦+防骑 | **1488×5** | 出生点旁(2909,-3991) | 86% | 否（148s 全灭后归位） |

框架侧把 engage 点改到出生点旁后，boss 不再中途拉远脱战（run54 稳定掉到 59%）——**但坦克仇恨问题独立存在**，是 Loatheb 打不过的真正瓶颈。run54/55 换血DK主坦（甚至加防骑）后**坦克对 boss 伤害仍是个位数×575/1488**：两场主坦全程打孢子/站桩 buff，boss 仇恨表依旧靠 DPS 建立。**结论：建仇缺陷与坦克职业无关**，血DK 的 `BloodDKStrategy` 自带输出循环≠会拉 boss，缺陷④ 的"坦克引擎不激活"是通用坦克问题而非战士特例（此前"工程绕过换血DK"方案被证伪）。

### 根因

1. **mod-playerbots 坦克策略未对 boss 建立初始仇恨**：Loatheb 没有显式"坦克开局拉 boss"的动作，坦克依赖通用 Attack 循环，但 `LoathebChooseTargetAction` 让坦克优先被孢子抢目标，且坦克引擎未把 boss 设为 current target → boss 仇恨表为空。
2. **坦克引擎激活不稳定（B2-8 深挖补充）**：战士主坦的 combat 引擎是否激活**在 run 间不稳定**——run52 输出 81k（正常攻击循环）、run54 仅 575（全程只 buff 55594 命令怒吼/57723 等、不打 boss）。同为干净登录的 run，差异仅由 mod-playerbots 引擎初始化随机性造成（同族于 run50 DPS 停摆）。run55 追加证实**该缺陷与坦克职业无关**：换血DK主坦+防骑后，主坦对 boss 仍是 5 次 1488（run54 血DK 2 次 575），全程打孢子/站桩——血DK 的 `BloodDKStrategy` 自带输出循环只保证"副坦当 DPS 用"时输出正常，不等于会主动拉 boss 建仇。
3. **站位点设计逼近脱战边界**：`mainTankPos(2877,-3967)` 距出生点 43.7 码（<50 脱战阈值），框架 engage 点又偏离出生点，双重叠加导致 boss 拉远脱战（run52）。框架侧已通过 engage 调整缓解，但站位缺陷仍在。
4. **run55 独有：DPS 战斗引擎"施法决策抖动"**（2026-09-06 深挖）——run55 开局前 60s 全团对 boss 输出 ≈0（mage/术/猎/贼/萨/暗牧 共施法 200+ 次、damage 结算 0 次，仅防骑 4 次 3818），boss 血量 100% 钉死。**决定性证据是施法间隔**：前 60s 全团 spell 事件**恒定 1.092s**（mage 20 连发全部 1088-1098ms，= GCD 急速压缩）——即 bot **每个 GCD 发起一次读条、读条从未完成就被打断**，下个 GCD 立即重试；60s 后 spell 间隔变为参差的真实读条节奏（21ms~3.6s），伤害才开始结算（65s 起与 spell 1:1）。已排除：boss 免疫/护盾（`boss_loatheb.cpp` 无免疫技能）、站位（位置采样全对：mage 在 rangePos、血DK/防骑在 mainTankPos）、距离/LoS（cast 已通过检查，20 码在射程内）、目标失效（run55 仅一个 Loatheb guid=106）。65s 转折与防骑死亡同帧（64856ms vs 首命中 65446ms），疑为仇恨重排/决策重置使引擎稳定。**根因在 mod-playerbots 战斗引擎的施法决策**：bot 每 tick 重评估当前动作，判定读条无用即打断——run 间随机性决定该 run 是否进入"持续自打断"状态（同族于 run50 DPS 停摆、缺陷④ 坦克引擎不激活）。

### 建议修法（mod-playerbots）

1. **Loatheb 坦克仇恨专项**：`LoathebChooseTargetAction` 增加"坦克优先 boss"分支——坦克不因孢子抢目标而放弃 boss，开局对 boss `Attack` + 嘲讽（真实打法：坦克踩孢子吃暴击但保持仇恨）。
2. **战斗引擎激活确定性（坦克+DPS 两侧，run55 追加）**：战士主坦 combat 引擎偶发不激活（run54 全程 buff 不打 boss），血DK 主坦同样不建仇（run55 1488）；run55 更出现 DPS 侧"施法决策抖动"（前 60s 读条每 GCD 被打断、0 结算）。三者同根因——mod-playerbots 引擎初始化/决策的 run 间随机性。建议排查 `PlayerbotAI::ChangeEngine` 与 `currentEngine` 初始化竞态，以及施法决策对读条动作的每 tick 重评估（判定无用即打断）——masterless bot 拉怪后应确定性切入稳定的输出/仇恨循环。
3. **站位点校正**：`mainTankPos(2877,-3967)` 若为通用 Naxx 站位模板，建议按 Loatheb 实际出生点(2909,-3997) 复核，保持距出生点 <40 码留足脱战余量。

**工程绕过（mod-raidtest 侧，run55 后已证伪旧方案）**：原"把 roster 主坦从战士改为血DK"的绕过**被 run54/55 证伪**——血DK 主坦同样 0 建仇（575/1488），且 run55 连 DPS 引擎都抖动。当前无纯 roster 侧绕过；若继续验证 Loatheb，需先解决 mod-playerbots 引擎稳定性（建议修法 2），或接受多次 run 抽样取"引擎恰好稳定"的一次。

### 风险提示

改动影响 Loatheb 10/25 人（25 人 `mainTankPos25` 同理需复核）；修坦克仇恨后需重测确认 boss 全程普攻坦克、DPS 不再被切死。框架侧 engage 调整（run54 已验证）已缓解脱战，可作为权宜。