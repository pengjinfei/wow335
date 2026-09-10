# 英雄魔枢（The Nexus，map 576）夹具勘测与进度门禁

更新：2026-09-10。本文件是魔枢四个 boss 共用的**夹具层**记录：坐标怎么定的、哪些方案被实测
推翻、以及凯利丝塔萨的进度门禁。各 boss 的战斗结论在各自的 README。

## 为什么选魔枢

- 四个 boss 全在地面，无载具、无护送、无 gameobject 前置（**凯利丝塔萨除外**，见下）。
- mod-playerbots 上游已有 `wotlk-nex` 策略（`src/Ai/Dungeon/Nex/`），覆盖四个 boss 的机制：
  `telestra firebomb` / `telestra split phase` / `chaotic rift` / `ormorok spikes` /
  `ormorok stack` / `intense cold` / `keristrasza positioning`。策略名映射见下。
- mmap 四个 boss 房间的 tile 都存在：`5763031/5763032/5763033/5763131/5763132`。

## 装备与难度基线（不变）

`normal5-v1`（ilvl 上限 187，普通五人本毕业档）、boss 英雄难度、`BotCheats = ""`、
`AutoEquipUpgradeLoot = 0`。英雄难度下 boss 等级 82、房间小怪等级 80。

## 框架改动（mod-raidtest，本轮唯一一处代码改动）

`CombatTrigger::RuntimeStrategyName` 原来只映射 `"wotlk-uk" -> "utgarde keep"`。map 576 的
Context 注册键是 `"wotlk-nex"`，而 `Engine::addStrategy` 以 `WotlkDungeonNexStrategy::getName()`
即 `"nexus"` 存放，因此 `RosterLogin::EnsureCombatInstanceStrategy` 会认为策略未生效，
`StartBossPull` 一律 `raid_invalid: instance combat strategy inactive before pull`。
改为一张映射表并加入 `"wotlk-nex" -> "nexus"`。运行时已验证：日志
`AttemptRunner: strategy='wotlk-nex' active=true on leader ...`。

## roster：四个场景共用同一套 5 个角色

mod-raidtest 原本按 `scenario_key` 给每个场景各建一套角色，而角色名被截到 12 字符后
同一 roster 的基名相同、只靠单字母后缀区分，`kNameAttempts = 5` 只够 6 个场景。
`normal5-v1` 的 `Raidteanfive` + `a..e` 已被 keleseth-n5 / skarvald-dalronn-n5 / ingvar-n5 /
nexus-telestra-n5 / nexus-anomalus-n5 占满，第 6 个场景直接
`roster ensure failed (create failed)`。

**没有改代码放宽后缀空间**，而是按「一套装备档位只要一套角色」把 `raidtest_accounts` 里
四个魔枢场景（以及各探针场景）的映射统一指向 `heroic-nexus-telestra-n5` 那套：
角色 guid **796–800**（`Raidteanfivc` 圣骑坦克 / `Raidtebnfivc` 戒律牧 / `Raidtecnfivc` 盗贼 /
`Raidtednfivc` 法师 / `Raidteenfivc` 萨满，账号 52–56）。同一时刻只有一个 run 在跑，
且每场 attempt 都会按 roster 蓝图重新配装，共用是安全的；附带好处是四个 boss 的样本
来自完全相同的五个角色。
guid **801–805**（`*nfivd`）是共用之前给 anomalus 建的一套，现已无映射引用，留着未删
（删角色要走框架的完整删除链，不宜手工 SQL）。10 人本/更难的副本再另建账号。

## 坐标勘测：导航探针的两种用法

零位移探针（`Preparation` = 候选点，`NavigationWaypoints` = 同一点，`NavigationOnly = 1`）
**只能证明「点在可走多边形上」，证不了连通性**。probe-g 的 `(239.2,-249.0,-8.40)` 零位移通过，
实际是一小块孤岛：路径 `type=4 actual_end=247.20,-248.27,-8.25 find_path=0x40000040
component=disconnected`，bot 站上去谁也拉不动，`prerequisite_failed: clearing timeout`。
要验证连通性必须用**位移探针**：起点 = 候选点，终点 = 另一个已知可走点（如 boss 生成点）。

| 探针 | 候选点 | 用途 | 结果 |
|---|---|---|---|
| probe-a | 487.0, 89.1, -16.04 | 泰蕾斯特拉拉怪点（boss 正西 7.7 码） | 在网格上 |
| probe-b | 275.0, -215.0, -9.00 | 奥莫洛克拉怪点（boss 东北 14.5 码） | 在网格上 |
| probe-c | 519.0, 100.0, -16.04 | 泰蕾斯特拉清怪点（距 boss 26.9 码） | 在网格上，但 26.9 码仍会拉到 boss |
| probe-d/h | 519.0, 106/110, -16.04 | 泰蕾斯特拉清怪点（距 boss 29/32 码） | 在网格上；**32 码可用** |
| probe-e | 245.0, -243.6, -8.40 | 奥莫洛克清怪点（距 boss 27.0 码） | 在网格上，27 码仍会拉到 boss |
| probe-f | 247.3, -241.6, -8.40 | 同上（24.0 码） | 在网格上 |
| probe-g | 239.2, -249.0, -8.40 | 同上（35.0 码） | 在网格上但**孤岛，不连通** |
| （位移探针） | 起点候选点 → 终点 boss 生成点 | 验证连通性 | 用于奥莫洛克与泰蕾斯特拉的拉怪点 |

探针场景是一次性勘测工件，用完已删除（结论保留在本表）。复现配方：

```
[Scenario]
MapId = 576
BossEntry = <该 boss>
PartySize = 5
DungeonDifficulty = heroic
Strategy = wotlk-nex
RosterFile = "mod-raidtest-roster-normal5-v1.conf"
GearProfile = none
EngageX/Y/Z    = <boss 生成点>
TimeoutSeconds = 120
EngageTrigger  = pull
PreparationX/Y/Z = <候选点>
# 零位移（只验证点在网格上）：终点 = 候选点自身
# 位移（验证连通性）：终点 = boss 生成点或另一已知可走点
NavigationWaypoints     = <终点 x,y,z,o>
NavigationOnly          = 1
NavigationTimeoutSeconds = 20
```

通过 = `navigation_complete: N waypoint(s) reached`；
失败 = `navigation_failed: ... type=… actual_end=… component=disconnected`，
其中 `actual_end` 就是能到达的最远点，可直接当投影点用。
新场景要重启 worldserver 才注册，且 `raidtest_accounts` 里要给探针 scenario_key
插一行指向已有角色，否则会触发建角（见上一节的名字空间限制）。

## 实测到的三条硬数值

1. **英雄 boss 仇恨半径 = 22 码。** `Creature::GetAggroRange`：`detection_range`(20) 减
   等级差（玩家 80 − boss 82 = −2），`Rate.Creature.Aggro = 1`，且 `CanStartAttack` 末尾
   要求 `IsWithinLOSInMap`。房间小怪等级 80，同式得 20 码。
2. **远程 bot 站桩距离约「离目标 26 码」。** run338 采样：目标 `126465` 在 (517.0,90.3)，
   法师站在 (541.9,80.9)，26.6 码。**选清怪点必须把这 26 码算进去**——它决定会不会多拉一组。
3. **「清小怪时 boss 参战」有两个互不相同的成因，别混为一谈。**
   - **成因 A：bot 走进了 boss 的 22 码半径**（泰蕾斯特拉）。清怪点距 boss 26.9 码时
     run348 5/5 场触发 `preclear_boss_invalid: alive=true combat=true`；把清怪点推到
     **32 码**后不再触发，并拿到 4 场零死亡击杀。26 码的远程站桩距离是这里的关键余量。
   - **成因 B：守卫本身离 boss 太近，挨打即触发协助**（奥莫洛克）。run355 把清怪点放到
     距 boss **41.5 码**的花园侧仍然触发：守卫在 (254.45,-238.90)（距 boss 17.1 码）
     挨到第一下伤害（rel_ms 3086）后 **90 毫秒**（rel_ms 3145）boss 就进入战斗，
     且 boss 全程停在生成点。**这条与队伍站位无关，挪清怪点解决不了。**
     运行配置 `CreatureFamilyAssistanceRadius = 10`，17.1 码仍触发；
     推测是 `Creature::CallAssistance` 按包围半径计距、而奥莫洛克模型较大
     （`creature_template_model.DisplayScale = 1.15`），**该推测未验证**。
     排除项：`Creature::CallForHelp` 只被个别脚本调用，魔枢的小怪与 boss 都没有
     对应 `smart_scripts`；boss 与守卫之间无 `creature_formations` 仇恨联动。

## 被实测推翻的两个夹具方案（别重走）

1. **「守卫组留活、只打 boss」不可行。**
   - 泰蕾斯特拉（run341，拉怪点在 boss 正西 7.7 码、距守卫 29.8 码）：5/5 场守卫全部参战，
     7.9/9.0/12.8 秒陆续加入。原因是守卫距 boss 仅 22.1 码，近战站 boss 背面加上
     `telestra firebomb -> firebomb spread` 散开动作，必然进入守卫的 20 码半径。
   - 奥莫洛克（run343，拉怪点距 boss 14.5 码、距守卫 31.9 码）：5/5 场守卫全部参战，
     Crystalline Keeper 288,315 + Tender 160,307，比 boss 本人的 150,258 还多。
   - boss 与守卫之间**没有** `creature_formations` 或 `linked_respawn` 仇恨联动（已查表），
     所以不是联动，是距离 + 战斗中的移动。
2. **奥莫洛克的守卫组是巡逻怪，不是站桩怪。** DB 生成点在 x∈[247.9,253.4]，但运行时实测
   `preclear_target` 采样到同一只 `28231` 在 **(303.55,-240.54,-14.09)** 和
   **(285.51,-233.67,-8.41)**——沿平台到花园的斜坡游走 50 余码。所以「固定清怪点 + 固定
   前置 GUID」这套夹具对它天然不稳：巡逻走到 boss 边上时开怪就会连 boss 一起拉。
   四只是一个 `creature_formation`（leader 126445，成员 126444/126605/126606，groupAI=514
   = IDLE_IN_FORMATION | LEADER_ASSISTS_MEMBER）。

## 凯利丝塔萨：真机制进度门禁，无法隔离测试

`heroic-nexus-keristrasza-n5`（run337）以 `pull failed (boss not engaged)`、boss 100% 血结束。
不是坐标问题：

- `boss_keristrasza.cpp:100-120`：她带 `UNIT_FLAG_NON_ATTACKABLE` 与 `SPELL_FROZEN_PRISON`
  (47854)，`RemovePrison(true)` 的条件是 `CanRemovePrison()`，即
  `DATA_TELESTRA_ORB`(5) / `DATA_ANOMALUS_ORB`(6) / `DATA_ORMOROK_ORB`(7) 三个状态全为 `DONE`。
- `instance_nexus.cpp:140-158`：这三个状态只由 `SetData(GO_TELESTRA_SPHERE/…)` 置位，
  也就是**点击三个球体 gameobject**（188526 / 188527 / 188528）；而球体又要在对应 boss
  `DONE` 之后才 `RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE)`（同文件 106-125 行）。

因此「打通魔枢四个 boss」在框架层需要**同一个副本实例内的多 boss 链式场景 + 三次
gameobject 使用**，现有 `Scenario`（一个 `BossEntry` + 可选一个 `KillGateSpawn`）做不到，
且 attempt 之间会清实例绑定。这是需要用户决定的框架工作，不是本轮能顺手带过的配置问题。

## 复现所需

- 场景模板：`azerothcore-wotlk/modules/mod-raidtest/conf/mod-raidtest-scenario-heroic-nexus-*.conf.dist`
  （运行配置在 `env/dist/etc/modules/` 下的同名 `.conf`；**场景启动时扫描注册，改完必须重启
  worldserver**）。
- 每轮前：`DELETE FROM acore_characters.account_instance_times;`
  `DELETE FROM acore_characters.instance WHERE map = 576;`
- 判读：等 `raidtest_runs.finished_at` 非空；跑动中的 attempt 行是 `aborted/0/NULL` 占位。
- 二进制含 mod-raidtest 的 `dfc7372`（夹具死亡误判修复）与 `14282f3`（三组只读采样），
  加上本轮未提交的 `CombatTrigger` 策略名映射，不是纯净上游。
