# 英雄魔枢 / 奥莫洛克（Ormorok the Tree-Shaper, 26794）/ `heroic-nexus-ormorok-n5`

## 接手摘要

- 更新日期 2026-09-10。状态：**完整链路正常规则击杀**（4 只巡逻精英守卫 + boss）——
  8 场 **6 击杀 / 0 团灭 / 2 场清怪阶段减员未进 boss**，六场击杀全部零死亡、103–124 秒。
- 已完成：0/5 基线 →「守卫组分不开」的三条反证 → 定位到真正的难点是**开怪时机** →
  mod-raidtest 新增 `PrerequisiteMinBossDistance` + 把自主选怪的恢复推迟到开怪那一刻 →
  用位移导航探针勘测出唯一可用的等待点 → 8 场样本。
- 唯一下一步：压清怪阶段的减员（2/8 场因此没进到 boss，与泰蕾斯特拉同类问题，
  是 ilvl 187 打 4 只等级 80 精英的真实难度）。
- 阻塞：无。**bot 策略一行未改**——这个 boss 是纯夹具/编排问题。

## 结论对照（固定装备/难度/cheat）

| | 修复前 run343 | 修复后 run367 + run368 |
|---|---|---|
| 形态 | boss + 4 精英一次开怪（分不开） | **完整链路：先清 4 只守卫，再打 boss** |
| 结果 | 0 击杀 / 5 团灭 | **6 击杀 / 8 尝试，0 团灭**，2 场清怪减员未进 boss |
| boss 最低血量 | 90%（最好一场） | 0% |
| 死亡 | 每场 5 死 | 六场击杀 **0 死** |
| 时长 | 17.7–38.1 秒全灭 | 击杀 **103–124 秒**（含清怪） |

装备档位 `normal5-v1`（ilvl 上限 187）、boss 英雄（等级 82、`HealthModifier = 32`）、
`BotCheats = ""`、`AutoEquipUpgradeLoot = 0` 全程未变。

## 可复现基线

- mod-playerbots `codex/nexus-anomalus-rift-focus` @ `34886ce1`（**本 boss 未改一行策略**）。
- mod-raidtest `dev` @ 本轮提交（`PrerequisiteMinBossDistance` + 延迟恢复自主选怪）。
- core `Playerbot` @ `516b14df1`。
- 场景：map 576 / boss 26794 / 英雄 / 5 人 / `TimeoutSeconds = 420` /
  `PrerequisiteTimeoutSeconds = 300` / `PrerequisiteMinBossDistance = 24.0`。
  - 前置怪：`126445`/`126444`(Crystalline Tender 28231) + `126606`/`126605`(Crystalline Keeper 26782)，
    等级 80 精英，构成 `creature_formation`（leader 126445，groupAI = 514 =
    `IDLE_IN_FORMATION | LEADER_ASSISTS_MEMBER`），**沿平台到花园的斜坡巡逻**。
  - 清怪点 **(287.0, -260.0, -12.0)**，拉怪点 **(275.0, -215.0, -9.00)**，均经导航探针实测。
- 角色 guid 796–800（本副本四个 boss 共用同一套）。

## 根因：难点是开怪时机，不是坐标也不是 bot 策略

守卫组冷启动时在生成点附近，**距 boss 仅 17.1 码**。三条实测反证「绕开守卫」这条路：

1. run336：拉怪点距守卫 8 码 → 同时开 boss + 4 精英，25.7 秒全灭、boss 仅掉到 92%。
2. run343：拉怪点改到距守卫 31.9 码、只打 boss，**5/5 场守卫仍全部参战**
   （Crystalline Keeper 288,315 + Tender 160,307 > boss 本人 150,258）。
3. run355：清怪点放到花园侧、距 boss 41.5 码，守卫在 (254.45,-238.90) 挨到第一下伤害
   （rel_ms 3086）后 **rel_ms 3145** 就记录到 boss 参战，boss 全程停在生成点。
   即触发距离是「小怪到 boss」而不是「队伍到 boss」，挪队伍位置无解。
   运行配置 `CreatureFamilyAssistanceRadius = 10`；17.1 码仍触发，**具体核心路径未定位**
   （`Creature::CallForHelp` 只被个别脚本调用，魔枢的小怪与 boss 都没有对应 `smart_scripts`；
   boss 与守卫之间无 `creature_formations` 仇恨联动）。按实测阈值处理。

真人的做法是**等巡逻走远再开怪**。所以这里要解决的是「什么时候下达开怪指令」。

## 框架改动（mod-raidtest，两处，只影响开怪时机）

1. **新增场景键 `PrerequisiteMinBossDistance`**（0 = 关闭）：前置目标与 boss 的距离小于该值时
   不下达开怪指令，只等待，上限仍由 `PrerequisiteTimeoutSeconds` 兜住。
   本场景取 **24.0**（已实测 17.1 码会触发；按包围半径估算有效半径约 17–18 码，留余量）。
2. **把「恢复 bot 自主选怪」推迟到真正开怪那一刻**。原来 `RestoreHeldFollowerStrategies()`
   在 `prerequisites_start` 就调用，于是 bot 在门禁等待期间自己就把附近的东西打起来了，
   门禁形同虚设（run360 实测：队伍 1.2 秒开始输出、7.9 秒 boss 参战）。

两处都只决定**什么时候开怪**：不改 bot 的战斗决策与目标选择、不动仇恨、不改 boss 属性、
不传送穿墙、不缩小遭遇战范围（4 只守卫仍然必须被清掉才进 boss 段）。

## 清怪点勘测：四个候选、三种不同的失败方式

等待期间**队伍必须保持脱战**，否则 bot 的战斗引擎会自己去点巡逻守卫，
门禁被 `next->IsInCombat()` 跳过。因此清怪点要同时离 boss、离巡逻路线、离其它小怪都够远。

| 候选点 | 距 boss | 距柔叶怪 | 距巡逻路线 | 结果 |
|---|---|---|---|---|
| (303.55,-240.54,-14.09) | 41.5 | **13.7 / 14.4** | 远 | run361：1 击杀 / 1 abort。柔叶怪拖进战斗 |
| (298.30,-238.03,-12.29) | 35.6 | **19.2 / 19.7** | 远 | run362 **0/5**：同上，1.7–7.7 秒即 boss 参战 |
| (289.72,-234.36,-9.30) | 26.3 | 26.8 / 28.0 | **0（在路线上）** | run363 **0/3**：4.92 秒 Crystalline Keeper 主动打来（其时距 boss 约 9 码），5.2 秒 boss 协助 |
| **(287.0,-260.0,-12.0)** | **41.2** | **≥25.3** | **24.1** | **run367 3/3、run368 3/5** |

`Crystalline Frayer`(26793) 是绕不开的干扰源：它们**在奥莫洛克死前打不死**
（`instance_nexus.cpp:249` 的 `_allowDeath`，血空进种子壳复活），且 `MoveRandom(10.0f)` 游走，
花园里有 44 只。所有 x ≥ 309 的区域都在它们范围内。

坐标勘测方法：**位移导航探针**（起点 = 已实测可站点，终点 = 候选点，`NavigationOnly = 1`）。
零位移探针只能证明「点在网格上」，证不了连通性——本轮 (280,-256,-10) 就是零位移会通过、
实际 `component=disconnected`（`end_nearby=280.00,-256.00,-8.03 end_distance=1.97`）。
配方见 [夹具勘测](../heroic-nexus/FIXTURE-SURVEY.md)。

## 机制与代码审计

| 机制 | trigger → action | 正常规则 | 运行证据 | 结论 |
|---|---|---|---|---|
| 水晶尖刺 | `ormorok spikes` → `dodge spikes`（`ACTION_MOVE + 5`） | 是（坦克贴内） | run343 出现 `Crystal Spike`(27099) 伤害 | **已触发**，命中率未量化 |
| 非坦克集合 | `ormorok stack` → `dodge spikes` | 是 | 六场击杀零死亡（间接证据） | 未单独采样 |
| 法术反射 | 无（`NexStrategy.cpp:37` TODO） | — | — | **未覆盖**（上游未实现） |
| 狂乱 | 无 | — | — | 未覆盖 |

## 尝试记录

| run / attempt | 形态 | 结果 | 时长 | 死亡 | boss HP |
|---|---|---|---|---|---|
| 336 / 1 | 拉怪点距守卫 8 码 | wipe | 25.7s | 5 | 92% |
| 343 / 1–5 | 只打 boss，距守卫 31.9 码 | wipe ×5 | 17.7–38.1s | 5 每场 | 90–96% |
| 349 / 1–5 | 清怪点 27 码，无门禁 | aborted ×5 | 0.75–1.05s | 0 | 100% |
| 352 / 1–2 | 清怪点 (239.2,-249.0) 孤立网格 | aborted ×2 | 180s | 0 | 100% |
| 355 / 1–2 | 清怪点花园 41.5 码，无门禁 | aborted ×2 | 3.1/3.9s | 0 | 100% |
| 359 / 1–2 | 门禁 28，清怪点平台侧 27 码 | aborted ×2 | 14.6s | 0 | 100% |
| 360–363 | 门禁 + 延迟恢复选怪，三个清怪点 | 见上表 | | | |
| **367 / 1** | 门禁 24 + (287,-260,-12) | **kill** | 103.1s | **0** | 0% |
| **367 / 2** | 同上 | **kill** | 123.6s | **0** | 0% |
| **367 / 3** | 同上 | **kill** | 113.7s | **0** | 0% |
| **368 / 1** | 同上 | **kill** | 114.3s | **0** | 0% |
| 368 / 2 | 同上 | aborted | 22.6s | 1 | 100% |
| 368 / 3 | 同上 | aborted | 36.3s | 1 | 100% |
| **368 / 4** | 同上 | **kill** | 113.9s | **0** | 0% |
| **368 / 5** | 同上 | **kill** | 117.3s | **0** | 0% |

## 仍未验证的限制

- **清怪阶段减员会作废整场 attempt**（368/2、368/3，各 1 死）。4 只等级 80 精英对
  ilvl 187 五人是实打实的压力，与泰蕾斯特拉同类；判稳定率时要把「到达 boss 的比例」
  与「boss 段成功率」分开算（当前 boss 段是 6/6）。
- boss 侧协助的核心路径未定位，`PrerequisiteMinBossDistance = 24` 是按实测阈值取的经验值。
- 巡逻周期没有量化；门禁等待时间在样本里都很短（首次 hold 后 30–40 秒内完成清怪），
  但没有测过最坏情况。

## 交接

- 复现：`raidtest run heroic-nexus-ormorok-n5 --attempts 5`。
- 证据：本地 MySQL `raidtest_events`（run 336/343 修复前，349–363 夹具迭代，367/368 修复后）。
- 新会话下一条安全操作：与泰蕾斯特拉一起处理「清怪阶段减员」这个共同瓶颈。


## 2026-09-24 ilvl 200 装备档复跑（独立 cohort）

- 场景 `heroic-nexus-ormorok-h5g`：由原 normal5 场景复制，**仅** `RosterFile` 换为 `mod-raidtest-roster-heroic5gear-n5talents-v1.conf`（天赋/雕文/补给同 normal5-v1，装备 17 件全 ilvl 200 已回读核对）。binary：playerbots `7e77a827`、raidtest `35ca8f5`（SHA `d3fbfef4…`）。
- 结果：**5/5 kill、1 死**（run849–853，77–92 秒）。对照 normal5 完整链路 6/8。不与 normal5 任何 cohort 合算。
