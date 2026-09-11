# 英雄魔枢 / 凯利丝塔萨（Keristrasza, 26723）/ `heroic-nexus-keristrasza-n5`

## 接手摘要

- 更新日期 2026-09-11。状态：**核心缺陷已修并推送，但她仍未打过**——阻塞从
  「机制上不可能」变成「队伍连不过前面三个 boss」。
- 已完成：定位到阻断是**核心侧缺陷**（使用球体没有任何处理代码）→ 在 core 分支
  `codex/nexus-containment-sphere` 补上 `go_nexus_containment_sphere` + SQL 绑定 →
  框架加 `PrerequisiteGameObjects`（清怪后使用 gameobject）→ 场景改为链式 →
  实测球体确实变为可选中并被成功使用。
- 唯一下一步：链式跑不完。卡在**第一场**（泰蕾斯特拉 + 她那 4 只守卫，run377 105 秒 2 死），
  以及**boss 之间没有恢复窗口**（run378 只杀一个 boss 就
  `prerequisite_failed: natural recovery timeout`，即台账里「bot 不喝水」那个老缺陷）。
- 阻塞：不再是机制不可能，而是这套装备档位下能不能连过三个 boss。

## 可复现基线

- 装备档位 `normal5-v1`、boss 英雄难度（等级 82、`HealthModifier = 38`）、`BotCheats = ""`。
- core **`codex/nexus-containment-sphere` @ `0ef8ef265`**（已推 fork `mine`；未建 PR）。
- mod-raidtest `dev` @ **`d535365`**；mod-playerbots `codex/nexus-anomalus-rift-focus` @ `34886ce1`。
- 场景（链式）：map 576 / boss 26723 / 英雄 / 5 人 / `TimeoutSeconds = 420` /
  `PrerequisiteTimeoutSeconds = 1500` /
  `PrerequisiteSpawns = 126480,126599,126663`（泰蕾斯特拉 → 阿诺姆鲁斯 → 奥莫洛克）/
  `PrerequisiteGameObjects = 65547,65548,65549`（三个封印球体）/
  拉怪点 (309.0,-5.5,-15.48)（boss 实测生成点 (301.45,-5.46,-15.48) 正东 7.6 码）/
  准备点 (519.0,110.0,-16.04)（泰蕾斯特拉的清怪点，位移探针验证过）。
- 角色 guid 796–800（本副本四个 boss 共用同一套）。

## 原始阻断的代码级证据（修复前）

run337：`aborted`，`notes = pull failed (boss not engaged)`，boss HP 100%，0 死亡。
拉怪动作发出了，boss 没有进战斗。原因不在坐标：

1. `boss_keristrasza.cpp:100-120`：她在 `Reset()` 里按 `CanRemovePrison()` 决定是否上
   `UNIT_FLAG_NON_ATTACKABLE` + 冰冻牢笼(47854)，默认就是**不可攻击**；解除条件是
   `DATA_TELESTRA_ORB`(5) / `DATA_ANOMALUS_ORB`(6) / `DATA_ORMOROK_ORB`(7) 全为 `DONE`。
2. `instance_nexus.cpp:140-158`：这三个状态**只由** `SetData(GO_TELESTRA_SPHERE /
   GO_ANOMALUS_SPHERE / GO_ORMOROK_SPHERE)` 置位，即使用三个球体
   （gameobject 188526 / 188527 / 188528）。
3. `instance_nexus.cpp:106-125`：球体本身带 `GO_FLAG_NOT_SELECTABLE`，只有在对应 boss
   `GetBossState(...) == DONE` 之后才可选中。

**而「使用球体」这一步在本 build 上根本没有实现**（五处独立核实）：
`instance_nexus::SetData` 全代码库没有任何调用者；核心 `GameObject::Use` 的 GOOBER 分支
不通知副本脚本；三个球体的 `gameobject_template.ScriptName` 为空；它们的 goober
`eventId = 0`（走不到 `event_scripts` / `EventInform`）；`event_scripts` 里对应行数为 0；
脚本树里没有任何 containment sphere 的 GO 脚本。
**结论：杀光三个 boss 也放不出她——球体只会变成「可点」，点了没有代码响应。**
这是核心/DB 侧的缺口，不是框架限制。

## 已完成的修复

### 核心侧（`azerothcore-wotlk` @ `codex/nexus-containment-sphere` `0ef8ef265`）

新增 `go_nexus_containment_sphere`：`OnGossipHello` 里 `instance->SetData(GetEntry(), 0)`，
再通知附近的凯利丝塔萨重算 `CanRemovePrison()`（副本脚本没存她的 GUID，三个球体距她
28–29 码，就近查找）。`GameObject::Use` 开头已拒绝带 `GO_FLAG_NOT_SELECTABLE` 的球体，
即对应 boss 未死时点不动，**进度门禁没有被绕过**。
`pending_db_world` 的 `rev_1789098661479490000.sql` 把三个球体的 `ScriptName` 绑上
（`apps/codestyle/codestyle-sql.py` 通过）。

### 框架侧（mod-raidtest `d535365`）

- 新场景键 `PrerequisiteGameObjects`：前置怪全清后按 `gameobject.guid` 使用指定对象，
  每个结果写 `prerequisite_gameobject_use` / `_missing` 事件。这是编排层的一次交互，
  不是战斗行为。
- 顺带修掉一个夹具缺陷（run376 根因）：配装前只清了副本、没清 bot 的残留战斗状态，
  而完整 AI reset 只在 `attemptSeq > 1` 跑（attempt 1 跑它会打乱初始站位，见 run87/88），
  于是上一轮遗留战斗状态的 bot 在新 run 首场被核心拒绝穿护甲/戒指/饰品
  （`EQUIP_ERR_NOT_IN_COMBAT = 60`）、而旧装备已被卸下 → **角色被扒光**、整场
  `fixture_invalid`，且之后每场重复失败（牧师只剩衬衣与三件武器，武器在战斗中允许更换）。
  修复后 run377 夹具通过。

### 实测到哪一步

- **球体链路通了**：run378 里奥莫洛克死后，
  `prerequisite_gameobject_use:spawn=65549 entry=188528 selectable=true`，框架成功使用。
- **端到端放她出来尚未验证**：需要三个球体全部被使用，而队伍还连不过三个 boss。
- `acore_characters.instance.completedEncounters` 本轮读到 8，与预期
  （`DATA_ORMOROK_EVENT` bit 2 + `DATA_ORMOROK_ORB` bit 7）对不上，**未追查**，
  不作为任何结论的证据。

## 链式场景的两个拦路点（都不是机制问题）

`PrerequisiteSpawns` 本来就是「先杀掉这些生成点再拉 boss」，三个 boss 就是三个 creature
spawn，**不需要新的多遭遇战状态机**。但：

1. **第一场就打不过**：run377 在泰蕾斯特拉处 105 秒 2 死。场景没把她那 4 只守卫列为前置，
   但守卫照样参战（距她 22.1 码，见 [清怪战术记录](../heroic-nexus/TRASH-TACTICS.md)），
   于是变成 run341 测过的「boss + 4 精英」0/5 形态。要连过就得把两组守卫也编进前置，
   而奥莫洛克那组还需要择时开怪——但 `PrerequisiteMinBossDistance` 比较的是「前置目标到
   **场景 boss**」的距离，链式场景里场景 boss 是凯利丝塔萨、离得很远，**门禁等于失效**。
   这是链式场景下的已知限制。
2. **boss 之间没有恢复窗口**：run378 只杀了一个 boss 就撞
   `prerequisite_failed: natural recovery timeout`（框架给 120 秒自然恢复）。
   真人会在 boss 之间喝水，而 bot 的喝水缺陷早有记录。链式要成立，这条几乎必须先修。

## 机制与代码审计

| 机制 | trigger → action | 正常规则 | 运行证据 | 结论 |
|---|---|---|---|---|
| 刺骨寒冷（Intense Cold 48094/48095） | `intense cold` → `intense cold jump`（`NexStrategy.cpp:44`） | 是 | 无（仍未能开怪） | **未覆盖** |
| 龙侧位站位 | `keristrasza positioning` → `rear flank`（`ACTION_MOVE + 4`） | 是 | 无 | **未覆盖** |
| 水晶枷锁 / 水晶火吐息 / 尾扫 | 无专门 trigger | — | 无 | **未覆盖** |

## 尝试记录

| run / attempt | 形态 | 结果 | 备注 |
|---|---|---|---|
| 337 / 1 | 隔离（修复前） | aborted | `pull failed (boss not engaged)`，boss 100%、0 死 |
| 376 / 1 | 链式（首次） | aborted | `fixture_invalid`——牧师残留战斗被拒穿护甲（已修） |
| 377 / 1 | 链式 | aborted | 105.4 秒 2 死，卡在泰蕾斯特拉 + 4 守卫 |
| 378 / 1 | 探针（只清奥莫洛克 + 用他的球体） | aborted | 球体 `selectable=true` 且被使用；随后 `natural recovery timeout` |

## 交接

- 复现：`raidtest run heroic-nexus-keristrasza-n5 --attempts 1`（需运行 `0ef8ef265` 的核心
  二进制，且 `gameobject_template.ScriptName` 已绑定——SQL 已应用到本机 `acore_world`）。
- 证据：本地 MySQL `raidtest_events`（run 337 修复前，376/377/378 链式与探针）。
- 新会话下一条安全操作：**先修「bot 不喝水」**（台账 2026-09-10 条目已有根因），
  否则链式永远卡在第二个 boss 之前；之后再决定要不要把两组守卫编进前置。
