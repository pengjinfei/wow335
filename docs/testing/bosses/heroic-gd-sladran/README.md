# 英雄古达克 · 毒蛇领主斯拉德兰 Slad'ran（29304）

## 接手摘要

- 更新：2026-09-16。状态：**干净基线 0/5 全团灭**，根因已量化，**尚未动手修**。
- 已完成：地形勘测、两个场景（完整档 + 隔离档）、隔离档 5 场基线、承伤与小怪分解。
- 唯一下一步：先量「DPS 的 AoE 乘子被归零」的头寸（见第四节），再决定改不改。
- 阻塞：无。修的话属于 mod-playerbots 的 boss 层（GD），不是共享层。

## 可复现基线

| 仓库 | 分支 | HEAD |
|---|---|---|
| azerothcore-wotlk | `codex/an-formation-despawn-crash` | `fa702e6a5`（本轮未改，工作区 7 个文件 dirty，均为既有状态） |
| mod-playerbots | `codex/shared-heal-los-recovery` | `5ef5adcc`（本轮未改） |
| mod-raidtest | `codex/dtk-scenarios` | `9d36278` + 本轮四个场景 conf（**未提交时的状态见下**） |

**二进制未重编**：worldserver 仍是 2026-09-16 那版（含治疗视线 + main tank 两条共享层修复）。
本轮只改配置与数据库，`scripts/restart_world.sh r49a` 重启，日志 `/tmp/wow335-worldserver-r49a.log`。
`LogInGroupOnly = 1`、`AutoEquipUpgradeLoot = 0`、`BotCheats = ""` 均已核对。
角色 guid 796–800（账号 52–56），`raidtest_accounts` 已补四个新 scenario_key 的映射。

- 场景：`heroic-gd-sladran-disc-n5`，map 604，boss 29304，英雄，5 人，roster normal5-v1。
  准备点 (1775, 621, 124.25)、开怪点 (1775, 666, 129.22)，前置 1 只（127015），
  夹具移除走廊另外八只（127028/127029/127017/127014/127025/127016/127026/127027）。
- 口径 = **隔离 boss 战**，不能记「正常规则机制验收通过」。

## 机制与代码审计

`boss_slad_ran.cpp`（AC 实现，与常见印象不同，**刷怪是持续的、无上限的**）：

| 机制 | 实现 | bot 侧覆盖 |
|---|---|---|
| Poison Nova 55081 / **英雄 59842** | `JustEngagedWith` 起每 16–53 秒一次 AOE | `SladranPoisonNovaTrigger` → `avoid poison nova`（ACTION_RAID+5）；乘子在读条期间把非躲避的移动动作归零 |
| Powerful Bite 48287 | 对当前目标，每 3–10 秒 | 无（坦克吃） |
| Venom Bolt 54970 | 45 码内随机目标，每 10–15 秒 | 无 |
| **血量 ≤90% → 召毒蛇 29680** | `ScheduleHealthCheckEvent(90)` 里挂的是**每 8 秒重复**的 `ScheduleTimedEvent`，每次 2 只，落点 (1717.4,630.0)/(1716.8,635.2)，离 boss 70 码 | 无专门触发器 |
| **血量 ≤75%（英雄）→ 召缠绕者 29713** | 同上，**每 3–5 秒重复**，每次 3 只，落点 (1783.8,646.6)/(1775.0,606.6)/(1765.7,646.5) | 无专门触发器 |
| Grip of Slad'ran 55093（缠绕者施放） | 叠 5 层 → `Snake Wrap 55126`（NPC 29742）把人包住 | `SladranSnakeWrapTrigger` → `attack snake wrap`（ACTION_RAID+4） |

## 尝试记录

**run 576**（完整档 `heroic-gd-sladran-n5`，1 场冒烟）：

| 结果 | 说明 |
|---|---|
| aborted `prerequisite_failed: roster casualty before boss pull` | **走廊九只精英 84.2 秒全清完、boss 全程没被拉进战斗**（地形与前置表都是对的），但法师(799) 在第 17.6 秒被 3 只不同的蛇打了 5 下共 25.4k（血上限 21.0k）阵亡，门禁判作废 |

→ 完整档的阻塞是**清怪期间的仇恨分散**，属于「整本全清」范畴；按当前项目口径（只验证 boss 机制）
先走隔离档，完整档保留待自主清怪成熟后再跑。

**run 577**（隔离档 `heroic-gd-sladran-disc-n5`，5 场）：

| seq | 结果 | 时长 | 死亡 | boss 最低 HP |
|---|---|---|---|---|
| 1 | wipe | 73.9s | 5 | 40% |
| 2 | wipe | 71.1s | 5 | 46% |
| 3 | wipe | 104.0s | 5 | 32% |
| 4 | wipe | 70.4s | 5 | 51% |
| 5 | wipe | 97.3s | 5 | 34% |

**0/5，Wilson 95% CI 0–43%。** 五场都是全员阵亡，首死在 55.8–86.2 秒，随后 10–15 秒内级联团灭。

## 根因（已量化，不是推测）

### 1. boss 召的小怪**一只都没死**

五场合计死亡的小怪只有 5 只 `Unyielding Constrictor`——那正是每场那 1 只前置怪。
`Slad'ran Viper (29680)` 与 `Slad'ran Constrictor (29713)` 的死亡事件 **0 条**。

| seq | 毒蛇 29680（只） | 缠绕者 29713（只） | 小怪合计承伤 |
|---|---|---|---|
| 1 | 11 | 35 | 150.7k |
| 2 | 12 | 30 | 81.5k |
| 3 | 17 | 52 | 77.3k |
| 4 | 10 | 23 | 87.4k |
| 5 | 17 | 49 | 124.7k |

**每场 33–69 只小怪活到团灭。** 小怪合计打出 521.5k / 5 场 = **104.3k/场，占全队承伤的 51%**
（boss 本人 89.7k/场）。缠绕者五场放了 **401 次 Grip of Slad'ran**，触发 **44 次 Snake Wrap**。

### 2. 输出确实撒到小怪身上了，但撒得太散

以 seq 1 为例：打 boss 172.7k、打前置怪 66.1k，剩下的分给了 **40 多个**小怪，
每只只挨 1–9k，**没有一只被打死**。这不是「不打小怪」，是「打了但没有集火」。

### 3. 上游乘子在英雄难度是反效果（待量化，**先别改**）

`GDMultipliers.cpp` 的 `SladranMultiplier`：

```cpp
if (!botAI->IsDps(bot)) { return 1.0f; }
if (action->getThreatType() == Action::ActionThreatType::Aoe) { return 0.0f; }   // ← 全程禁 DPS 的 AOE
if (snakeWrap && dynamic_cast<DpsAssistAction*>(action)) { return 0.0f; }        // ← 有包裹时禁止重新选目标
```

对「每 3–5 秒刷 3 只」的场面，**全程禁 AoE** 正好是反的；而「有包裹时禁止 `dps assist`」
意味着**只要场上还有一个包裹，DPS 就不能切到任何新目标**。上游自己在 `GDStrategy.cpp` 写着
`// TODO: ... Will re-test in heroic.`——**英雄难度上游从没测过**。

⚠ **按 LESSONS 的规矩，改之前必须先量头寸**：
1. `snakeWrap` 存在的秒数占战斗的比例（= `dps assist` 被禁的时长）；
2. DPS 的 AoE 动作被推入但因乘子归零而 `IMPOSSIBLE` 的 tick 数（需 `LogInGroupOnly=0`）；
3. 小怪的实际血量 / 一次 AoE 能否成建制清掉（缠绕者是什么等级、多少血）。
第 2 条要注意 LESSONS 的口径陷阱：**乘子归零也会记成 `IMPOSSIBLE`**，别和施法失败混起来。

## 交接

- 场景已注册、可直接复跑：`raidtest run heroic-gd-sladran-disc-n5 --attempts 5`。
- 连续跑 >5 场会撞 `AccountInstancesPerHour = 5`，每轮前
  `DELETE FROM acore_characters.account_instance_times; DELETE FROM acore_characters.instance WHERE map=604;`
- 完整档 `heroic-gd-sladran-n5` 也已注册，跑它是在测清怪，不是测 boss。
