# 英雄达克萨隆要塞 / 召唤者诺沃斯（Novos the Summoner）

场景：`heroic-dtk-novos-n5`（map 600，boss entry 26631）

## 接手摘要

- 更新日期：2026-09-16 凌晨。**状态：基线即通关，bot 策略一行未改；改的是框架的一道开怪门禁。**
- 结果：冒烟 run 549 一场 147.6 秒击杀；基线 run 550 五场 → **4 击杀 / 0 团灭 / 1 场框架作废**，
  零死亡，140–148 秒。**五次有效尝试全部击杀。**
- 唯一下一步：King Dred(27483) / 先知塔隆金(26632) 建场景跑基线。
- 遗留（框架，未修）：run550/seq4 开怪被拒（见下「框架缺陷」），5 场丢 1 场。

## 框架缺陷一：开怪后 boss 变不可选中 → 整场被误判作废（**已修**）

诺沃斯 `JustEngagedWith` 里立刻 `SetUnitFlag(NON_ATTACKABLE|NOT_SELECTABLE)` 进 P1（奥术力场护体）。
mod-raidtest 的 `CombatTrigger::BeginAssistForAll` 要求**每个跟随者都能对 boss 下 assist**，
而此刻 `IsValidAttackTarget(boss)` 必然为 false，于是 `pull failed (not all followers entered combat)`
——run 548 首场即此，一场都跑不起来。

修法（mod-raidtest，`src/Bot/CombatTrigger.cpp`，+20 行）：boss 带 `NON_ATTACKABLE|NOT_SELECTABLE` 时，
放行跟随者（解除 hold）并记一条 INFO，**不代它们选目标**——之后打小怪还是打别的由 bot 自己的引擎决定。
boss 是否真进战斗已经由 `AwaitTankAggro` 确认过，`BossAI::_JustEngagedWith` 的 `DoZoneInCombat`
也已经把全队拉进战斗。这条对任何「开怪即进入不可攻击阶段」的 boss 都成立（阿努巴拉克潜地同理）。

验证：同一场景重跑，run 549 一场 147.6 秒击杀、run 550 五场 4 击杀。

## 框架缺陷二：新实例里 boss 还不可选中就发开怪（**未修**）

run 550 / seq 4：`pull_rejected ... distance=16.7 los=true valid=false alive=true in_world=true evade=false`，
即开怪那一刻 boss 仍带不可攻击标志。五场里只出现一次，前三场与第五场同样流程都正常。
`AttemptRunner` 的 `clean boss spawn` 校验只确认 spawn 在、活着，**没有确认它可被攻击**。

候选修法：开怪前若 boss 不可选中，等几个 tick 再判（预算内），超时才 abort；别直接 abort。
未做——需要再编译一次，留给下一轮和别的框架改动一起。

## 可复现基线

| 仓库 | 分支 | HEAD |
|---|---|---|
| azerothcore-wotlk | codex/an-formation-despawn-crash | `fa702e6a5`（7 个文件未提交，沿用上一轮） |
| mod-playerbots | codex/uk-ingvar-los-recovery | `1e285dff`（干净，**本 boss 未改动**） |
| mod-raidtest | codex/an-runtime-strategy-names | `d030865` + 本轮未提交改动（CombatTrigger 放行 + `casting=` 探针） |

- 二进制：2026-09-16 增量编译（`CombatTrigger.cpp` 1 个 TU + 链接），worldserver 以 `restart_world.sh r36a` 重启。
- 装备档 normal5-v1，roster 796–800，`GearProfile = none`，无 cheat。

## 场景设计

- 准备点 **(-378.85,-760.35,28.59)** = 上游 `NOVOS_PARTY_POSITION`（DTKActions.h:17），距 boss 22.7 码、los=true。
  诺沃斯 `MoveInLineOfSight` 被重写成空 + `UNIT_FLAG_DISABLE_MOVE`，**开怪前不会因靠近而拉怪**，
  所以这里不需要仇恨半径余量。
- 开怪点 **(-379,-748,27.71)**，boss 正南 10.3 码，los=true。
- 无前置怪：50 码内只有甲虫/老鼠这类中立小动物。`TimeoutSeconds = 480`（P1 有 ≥70 秒硬结构）。

## 机制实测（run 549+550 六场）

| 机制 | 实测 | 结论 |
|---|---|---|
| 奥术力场 47346（P1 护体） | 5 次（每场一次） | P1 正常进入 |
| 水晶操控者 26627（16/32/48/64 秒左右交替） | 每场四只，全部被清 → P2 | **bot 自主处理**，没有专门的框架指派 |
| 楼梯小怪流（27598/27600/27597） | 持续；小怪对队伍造成 **40k–76k/场**，与 boss 的 80k–133k 同量级 | 小怪在这个 boss 上**有真实头寸**（与 Trollgore 相反） |
| P2：寒冰箭 59855(64)、暴风雪 59854(17)/59856(28)、英勇召唤随从 59910(10)/59933(40) | 全部触发 | P2 正常 |
| 上游 DTK 三条 Novos 行为（avoid arcane field / novos positioning / novos target priority） | **未量**——它们都以 `find target "novos the summoner"` 取 boss，而 P1 boss 不可选中，很可能整条链不亮 | **未覆盖**；零死亡通关所以没有排查动机，想量要开 `LogInGroupOnly=0` |

## 尝试记录

| run / attempt | 结果 | 时长 | 死亡 |
|---|---|---|---|
| 548 / 1 | aborted（框架门禁，见缺陷一） | — | 0 |
| 549 / 1（冒烟，修后） | kill | 147.6s | 0 |
| 550 / 1,2,3,5 | **kill ×4** | 140–148s | 0 |
| 550 / 4 | aborted（框架，见缺陷二） | — | 0 |

## 判定

**正常规则通关（隔离 boss 战口径）**：不清路怪（本来没有）、不改难度装备、无 cheat，
bot 自主清掉四只水晶操控者进 P2 并击杀，五次有效尝试 5/5 零死亡。
唯一的改动在 mod-raidtest 的开怪门禁（编排层），没有碰 bot 行为。
