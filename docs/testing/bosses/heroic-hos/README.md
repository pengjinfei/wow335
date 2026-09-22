# 英雄岩石大厅（HoS，map 599）/ campaign

## Encounter 矩阵

| encounter | 当前范围与结论 | 状态 | 记录 | 下一步 |
|---|---|---|---|---|
| Krystallus | 20-spawn 证据边界 5/5 kill、总 2 deaths；不等于完整副本。 | 当前配置击杀 | 本文历史记录 | 仅在另行定义完整房间范围时继续。 |
| Maiden of Grief | 隔离 boss 5/5 kill、1 death；不等于完整房间。 | 当前配置击杀 | [README](../heroic-hos-maiden/README.md) | 仅在另行定义完整房间范围时继续。 |
| Tribunal of Ages | r32 lifecycle 1/5 DONE；r34 diagnostics 不计分且未验收。 | **调查中（当前）** | [README](../heroic-hos-tribunal/README.md) | 仅以新的单一、可观测假说重启；不得重跑同类诊断。 |
| Sjonnir the Ironshaper | 无有效 scenario 或战斗样本；同实例 Tribunal 前置后的 playerbot 自主路线不存在，raidtest 不可代移。 | **跳过（框架阻断）** | [README](../heroic-hos-sjonnir/README.md) | 不得用 fixture、状态写入或强制移动绕过。 |

> 用户指示：Tribunal 基线未通过时先转入下一 boss。Sjonnir 已因可复核的 normal-rule 续链框架缺口跳过，且没有下一 boss 可选；因此回归仍未完成的 Tribunal。两项路由决定均不改变 Tribunal 的 1/5 样本口径。

## Krystallus 历史接手摘要

- 更新：2026-09-21；Krystallus 的现有结论不变：首个隔离冒烟因房内外单位参战而口径无效；其后 20-spawn 证据边界另有有效样本，见下文。Tribunal of Ages 在 r32 同配置为 1/5 Brann lifecycle DONE（run745 491.468 秒零死完成；run746/run748/run750/run751 522.820/463.049/499.753/473.432 秒全灭），详见[独立 Tribunal 记录](../heroic-hos-tribunal/README.md)。
- 固定基线拟定为英雄难度、normal5-v1、5 人、`AiPlayerbot.BotCheats = ""`；运行配置已只读核对
  `AutoEquipUpgradeLoot = 0`、`BotCheats = ""`、`LogInGroupOnly = 1`。
- 本轮只完成源码/数据库/静态地形审计；没有修改 core、mod-playerbots、mod-raidtest、装备、难度、cheat 或 boss 数值，亦未编译。
- worldserver 在 `raidtest status` 时为 IDLE；最新已结束 run 是 696（古达克巨像），没有 HoS run。

## 仓库与运行基线（只读）

| 仓库 | 分支 / HEAD | 接手时状态 |
|---|---|---|
| 管理库 | `main` / `d713740` | 已有古达克文档修改与新增艾克/证据文件；未动 |
| core | `main` / `c747f55ca` | 仅已有日志、raidtest 输出 untracked；未动 |
| mod-playerbots | `codex/gd-takeover` / `f0e08d97` | 11 个既有 GD 未提交文件；未动 |
| mod-raidtest | `codex/gd-takeover` / `aa01349` | 既有莫拉比与艾克框架改动、艾克 conf；未动 |

运行进程为 worldserver + `scripts/fifo_relay.py`。为加载**只新增的场景配置**（未编译），已用
`restart_world.sh hos-krystallus-r1` 重启；日志确认二进制仍为 core `c747f55ca` 并 ready，且
`scenario list` 已登记 `heroic-hos-krystallus-disc-n5`。未把源码 HEAD 当作二进制证明。

## 机制与代码审计

### core / DB

- DB 中唯一的常驻 Krystallus spawn 是 `creature.guid=126790`，普通 entry **27977**，坐标
  `(1008.56, 759.914, 208.706, o=2.566)`，`spawnMask=3`；它不是运行时召唤 boss，现有 reset/按 spawn
  解析合约可承载。
- `creature_template(27977).difficulty_entry_1=31381`；英雄替换 entry 为 **31381**。27977 的
  `ScriptName=boss_krystallus`，31381 的 `flags_extra=1` 且无独立 ScriptName。此处记录的是 DB 映射，
  不是对英雄运行态的推测。
- `boss_krystallus.cpp`：开怪后 Boulder Toss 8 秒、Stomp 5 秒、Ground Slam 15 秒；英雄额外 Ground Spike
  10 秒。Ground Slam 对当前 victim 触发后 boss 被动且 `AttackStop()`，延迟其它事件 10 秒，8 秒后 Shatter；
  1.5 秒后移除 stoned aura。Shatter spell script 会去掉 stoned 并触发伤害；其 effect 按与施法者的二维距离
  线性衰减（距离超过 1 码开始）。这里还没有真实英雄施法/伤害事件，时序仅为静态审计。
- instance 脚本只用 `SetData(BOSS_KRYSTALLUS, NOT_STARTED/IN_PROGRESS/DONE)` 记 encounter；未发现
  Krystallus 前置死亡、召唤、不可攻击或门禁链。不能据此把房内敌对单位擅自从完整房间口径删掉。

### mod-playerbots

- `PlayerbotAI`、`DungeonStrategyContext` 已注册 `wotlk-hos` / `WotlkDungeonHoSStrategy`，其策略名为
  `halls of stone`；mod-raidtest 的 `RuntimeStrategyName` 映射亦已有 `wotlk-hos -> halls of stone`。
  尚未以 HoS attempt 证明运行时策略已激活。
- HoS 策略对 Krystallus 注册 `ground slam -> shatter spread`（`ACTION_RAID+5`）和
  `KrystallusMultiplier`。触发器在 bot 自己拥有 50827 或 50833 时亮；动作每 tick 相对最近队友背离 5 码，
  直至最近队友距离达到 40 码。该 aura 窗口内 multiplier 禁掉除 `ShatterSpreadAction` 外的移动动作。
- 这是已有策略的静态覆盖，不是机制验收：尚未确认触发器实际 PUSH/OK、实际散开路径是否 on-mesh、Shatter
  是否按预期因距离降低承伤，也未提出新策略。

## 房间与前置审计

- boss 附近没有与 126790 同 formation 的条目；Krystallus 本身 `MovementType=0`。
- 常驻敌对单位不能被当背景忽略。最近的非 boss DB 单位包括 6 个 `Crystalline Shardling`（27973），
  距 boss **23.3–40.3** 码，及 Dark Rune Worker 126698（41.9 码）、Dark Rune Shaper 126720（42.3 码）、
  Dark Rune Controller 126732（50.2 码）。27973 faction=16、无不可攻击 flag；126732 是路径 1267320 的巡逻
  （`MovementType=2`，路径在 `(943.67..969.47, 770.36..795.37, 194.98..199.28)`）。
- 27966 在战斗中会召唤 Shardling（SmartAI spell 51507）；因此“当前 DB 表中的 shardling 数量”不能替代
  完整房间范围定义。现有资料还不能可靠划定哪些敌对 spawn 属于 Krystallus 房、哪些是进入该房前的路线包。

## 静态地形勘测（`raidtest los`）

所有网格点严格两遍：先以 `z=210` 只读取每一点的 `vmap_floor_from`，再仅用该点自己的真实地面 z
重测到 boss 地面 z=208.63；未把第一遍的高空 `los` 用作结论。以下第二遍全部 `los=true`：

| 候选 | 实测地面 z | 至 boss 2D 距离 | 对 boss LOS | 用途判定 |
|---|---:|---:|---|---|
| (980, 760) | 203.79 | 28.6 | true | 候选，尚未验导航 |
| (985, 750) | 207.56 | 25.6 | true | **隔离基线的首选待验点** |
| (985, 770) | 202.43 | 25.6 | true | 候选，尚未验导航 |
| (990, 745) | 209.78 | 23.8 | true | 候选，尚未验导航 |
| (990, 775) | 202.78 | 23.9 | true | 候选，尚未验导航 |
| (995, 740) | 211.99 | 24.1 | true | 候选，尚未验导航 |
| (995, 780) | 203.81 | 24.2 | true | 候选，尚未验导航 |
| (1000, 785) | 205.05 | 26.5 | true | 候选，尚未验导航 |

首选点处在英雄 boss 约 22 码仇恨半径之外、又在坦克 30 码远程开怪范围内；但静态 LOS 不是
on-mesh 或到 boss 的连通性证明，且不证明远程约 26 码站桩后的全队位置安全。

## 场景设计（先定口径，未落 conf）

### A. `heroic-hos-krystallus-disc-n5`：隔离 boss 基线（拟议）

- 范围：仅验证 Krystallus 本体机制；**不**把它表述为完整房间或副本通关。
- 不使用 fixture 删除、状态直写、召唤、仇恨干预或任何数值/装备/难度/cheat 改动。
- 预备/开怪候选统一为 `(985,750,207.56)`；因无前置时框架在 Preparation 点开怪，不能把它误写成
  “准备点远、实际开怪点另在 boss 脚边”。落 conf 前必须以位移探针验该点 on-mesh 且连通，并复核五人实际开怪
  后的 LOS/站位与最近敌对 spawn。

### B. `heroic-hos-krystallus-room-n5`：正常规则完整房间（尚未定义）

- 只有先把 boss 房边界、所有应清的常驻 spawn、巡逻路径和 combat-assist 关系逐项实测后才可写
  `PrerequisiteSpawns`。不可从“离 boss 最近”或“DB spawn 数”猜一个列表，也不可先删怪再把结果称完整房间。
- 若某个常驻单位因原生机制必然随 boss 参战，它必须保留在该口径；若是跨房巡逻干扰，必须用路径/距离/参战证据
  说明其不属于房间，才可不列入范围。当前无足够证据作此划分。

## 首个场景冒烟：run697 / attempt 1（**口径无效，不计入基线**）

- 新建并注册 `heroic-hos-krystallus-disc-n5`（tracked template + gitignored runtime copy）；无 fixture、
  Heroic / normal5-v1 / `BotCheats=""`。运行前清了 `account_instance_times` 与 map 599 instance。
- run697/seq1 于 181.812 秒以 `wipe` 结束，5 死、boss 最低 32%。这**不是**“隔离 boss 0/1”或策略失败：
  从 67.068 秒起 27966 Dark Rune Controller 参战（对队伍 64,229 伤害），27973 Shardling 从 67.283 秒
  参战（32,745），另有 27974 Eroded Shardling（1,634）。`actor_entry=0` 的 75,972 是玩家 source 的伤害记录，
  不能当成第三方怪；其与 boss 技能的精确归因尚未完成。故场景实际已经是 boss 加多个外来敌对单位。
- 候选点/开怪链本身已通过最低验证：reset 找到 126790、boss 27977；6.911 秒采样中 tank 与 boss 均在
  上层（tank `(1000.39,762.26,206.93)`、boss `(1000.86,756.67,207.76)`），boss `combat=true`、
  `unreachable=false`。这只能证明该坐标可开怪，**不能**证明全队导航或隔离范围有效。
- 机制确实出现但不作效果判断：boss spell event 有 Ground Slam 50827×8、heroic Ground Spike 59750×11；
  玩家侧可见 50833×30。既有 HoS strategy 在 tank 的运行时策略串中出现 `halls of stone`，但本次未单独量
  `shatter spread` 的 PUSH/OK，且污染场不用于评价其成败。
- Controller 的首个拉入链已闭合：62.556 秒 boss 对全队施 50827，64.557 秒四人获得 50833；
  priest(817) 的每秒位置从 60.975 秒 `(973.11,759.70,203.21)` 连续西移至 66.984 秒
  `(957.45,759.35,201.79)`。Controller 的 DB spawn/path 起点为 `(959.43,770.36,198.82)`，
  67.068 秒首次对该 priest 造成 6,274 伤害；距约 11.0 码。即既有 Ground Slam 散开把成员推进了
  该巡逻怪的仇恨范围，**不是 boss 自己 assist 或场景随机参战**。
- 27973 于 Controller 后 215ms 首次伤害、27974 于其后 6.8 秒首次伤害；二者与 Controller 的
  summon/assist 关系尚未完全区分。它们不能从完整房间口径中删除，也不能在未证明其非遭遇战内容前
  用 fixture 做“干净隔离”。

## Controller 前置验证：run698 / attempt 1（范围限定，**不是完整房间通关**）

- 新场景 `heroic-hos-krystallus-controller-n5` 仅把已由 run697 证实会被机制散开拉入的 Controller
  126732 列为正常规则 `PrerequisiteSpawns`；无 fixture。为注册此**配置**重启 `hos-krystallus-r2`，未编译；
  复用同一 normal5-v1 roster 816–820。
- run698/seq1：Controller 于 18.044 秒死亡，恢复完成 40.703 秒，boss 开怪 40.704 秒；
  **140.435 秒 kill、零玩家死亡**。事件中 boss death 是唯一第二条 death，不能误读为玩家死亡。
- 修正事件边界：Controller 的 6,558 伤害全部在其 18.044 秒死亡**前**（5.127–12.140 秒），
  Eroded Shardling 228 也在 17.726–21.737 秒；两者不是 boss 段残留。boss 段是 27973 source 79/78
  在 114.359–135.924 秒的 970 伤害。Controller 曾在 17.717 秒施 51507 Summon Shardling 至
  `(971.69,769.91,200.36)`；该召唤与 source 79/78 的精确 GUID 对应尚未有观察字段证明。
  因此此场只证明“Controller 前置链 + Krystallus”可完成，
  **不能称隔离基线、完整房间或通关**，也不能与 run697 混算。
- boss 机制覆盖：50827×4、heroic 59750×6；尚未以 tick/PUSH/OK 口径验 `shatter spread`，不从本场推策略效果。

## 来源观测与第二次 controller-chain 诊断：run699 / attempt 1

- 获得编译授权后，仅在 `CombatEventBus` 的 creature 来源事件 detail 中加入只读
  `origin:spawn_id` 与 `summoner`；不触碰策略、仇恨、移动、数值或场景规则。`worldserver` 已以
  四线程重建并重启；全仓 codestyle 脚本因既有 core 文件报错而非零退出，改动文件无其列出的诊断，
  另以 `git diff --check` 复核。
- run699/seq1 直接闭合 source 79/78：它们分别是**常驻** `27973` spawn `126777`
  `(960.285,789.112,195.944)` 与 `126776` `(951.382,789.054,195.397)`，summoner 均为空；
  不是 51507 临时召唤。Controller `46` 同样确认是 spawn `126732`。它们无 creature_formation 关系。
- 此诊断 run 为 148.548 秒 kill，但有两名玩家死亡（41.749 秒、110.644 秒），不得加入任何无死亡/
  效能样本。关键产出只是房间边界证据：126776/126777 仍在 boss 阶段（83.349–129.617 秒）参战，
  必须纳入下一个最小正常规则前置表，不能再称 controller-only 链。

## 最小证据房间首场：run700 / attempt 1（无效，边界继续扩大）

- r4 重启确认 `heroic-hos-krystallus-min-room-n5` 已加载；此前置仅为 126732、126776、126777，无 fixture。
  run700/seq1 于 278.024 秒 wipe，5 名玩家死亡、boss 最低 31%；**不得**记为策略失败或完整房间结果。
- 来源观测排除猜测：boss 期实际还拉入常驻 Controller `126728`（27966，6,590 伤害）与下层常驻
  shardling `126757`–`126761`、`126779`、`126782`–`126788`。后者坐标群在
  x=937–981、y=806–845、z=185–191；tank 于 177.551 秒死亡在 `(976.63,831.45,186.82)`，
  直接证明队伍已被机制移动/战斗路径带入下层怪群，而非 boss assist。`27974` source 152 是 Controller
  126728 的临时召唤物（spawn_id=0，summoner=43），不列为 DB 前置。
- 因此 126732/126776/126777 只能称“最小已知上层前置”，不能称最小房间。下一个正常规则候选前置表应
  纳入本场所有常驻来源；仍须以清怪执行次序验证，不能把它们删成 fixture。

## 证据房间首场：run701 / attempt 1（有效但仅 n=1）

- r5 重启加载 `heroic-hos-krystallus-evidenced-room-n5` 后，run701/seq1 在 261.437 秒 **kill**；
  1 名玩家死亡（144.063 秒，boss 段），所以这是“正常规则、证据边界房间 1/1 kill、1 death”，
  **不是零死亡、稳定率或全副本通关**结论。
- 前置阶段 0–99.583 秒结束，恢复于 116.886 秒完成、boss 于 116.887 秒开始；所有非 boss 对玩家伤害
  都在 99.582 秒前。故本 boss 段没有外来常驻怪污染，首次可作为该证据边界场景的有效 boss 样本。
- 观察层还发现未显式列入的常驻 `126780`、`126781` 在前置战中被正常 assist 并死亡；下一版候选表应补入
  二者，使配置的声明与实战实际清怪集一致。临时 27974 仍仅为两个 Controller 的 summon。

## 补全前置后的首场：run702 / attempt 1（中止，准备点失效）

- r6 加载了补入 126780/126781 的 20-spawn 配置。run702/seq1 在 8.415 秒以
  `prerequisite_invalid: boss missing or engaged before clearing completed` 中止；无死亡、boss 100%，
  不是 wipe 或 boss 样本。
- 证据指向场景准备点而非前置表：开场仍在 `(985,750,207.56)`，其到 boss 17.34 码、已在
  22 码 aggro 半径内；清 126728 时 bot 移至 `(994.09,746.54,209.81)`，距 boss 11.49 码，
  8.409 秒 boss 对 mage(819) 建立威胁。preclear guard 正确中止，未把污染战计样。
- 因此该点只能用于**无前置时的直接开 boss**，不再可用于 20-spawn 的清怪准备。重新选点前须先取
  真实地面 z、验证 on-mesh/到 126728 的连通性，再以真实 z 测到 boss/前置的 LOS；不得凭估计坐标改配置。

## 重新勘测准备点后的第二有效样本：run703 / attempt 1

- 候选 `(940,800,192.87)` 先以 vmap 取真实 floor（192.87），再以该真实 z 验：到 boss 79.4 码、LOS=true；
  到 126728 16.8 码、LOS=true，到 126732 35.4 码、LOS=true。r7 加载此点后，前置于 46.107 秒完成，
  恢复于 57.780 秒、boss 于 57.787 秒开始，实测也证明该点 on-mesh 且清怪链不触发 boss guard。
- run703/seq1：**215.188 秒 kill、1 名玩家死亡**（83.532 秒，boss 段）。所有非 boss 伤害止于
  46.107 秒，boss 段无外来常驻怪。与 run701 共同构成当前证据边界配置的 **2/2 kill、每场 1 death**；
  样本量仍不能宣称稳定、零死亡或全副本通关。
- run702 的 8.415 秒 aborted 保持单列的准备点失效证据，不能并入该 2 场分母。

## Ground Slam → Shatter 因果审计（有效 boss 段的 run701/run703）

- 两个有效样本的首轮均是同一因果链：Ground Slam `50827` → 约 2.0 秒后全员 `50833` →
  约 5.0 秒后全员 `50812` → 约 2.0 秒后 boss `61546`（Shatter）；mage(819) 都恰在 Shatter 时死亡。
  run701：135.051 → 137.054 → 142.058 → **144.063** 秒；run703：74.527 → 76.528 → 81.528 →
  **83.532** 秒。故两场的 1 death 不是外怪或 Ground Spike，且 Shatter 直接因果已闭合。
- run703 Shatter 前最后位置采样（81.546 秒）中 819 在 `(969.87,747.20)`；其最近 teammate 817 仅
  **15.9 yd**，820 为 20.0 yd，远低于策略 `ShatterSpreadAction` 的 40 yd 目标。全队最小配对距离亦仅
  15.9 yd。`50833`/`50812` 覆盖只能说明触发/aura 到达，**不能**当作成功散开。
- 因此当前 2/2 kill 的每场 1 death 都伴随首轮可复现的 `shatter spread` 执行失败。尚未改策略：先保留
  此基线和因果证据，后续若修动作，必须新分支/新构建、重做前置与非 HoS 回归，不能将结果混入当前基线。

## 实验性单变量：一次补足 40 yd（run704，失败，已在源码回退）

- 经授权只改 `ShatterSpreadAction` 的一步距离：5 yd → `40 - 当前距最近队友`，r8 编译运行；场景、前置、
  装备、难度和 cheat 均未变。run704/seq1 前置 90.429 秒完成、107.490 秒开 boss，boss 段无外怪，
  但 **282.503 秒 kill、4 death**，不得与基线合并。
- 首轮仍在 Shatter 133.339 秒死亡：817 与 819 在 131.385 秒仅约 **9.2 yd**；同 tick 有玩家互伤
  818→817 6,366、819→817 12,636 等，闭合为 Shatter 伤害。原因是按“各自最近队友”独立取反方向时，
  817/819 从堆叠点朝近似同向移动，单次补足距离反而不能形成全局分离。
- 因此“把 5 改大”被证伪；已将 `HoSActions.cpp` **源码回退为原 5 yd**，当前运行中的 r8 二进制仍是
  实验变体，下一次任何运行前必须重建并重启回退版。后续若再修，需设计全队稳定的 slot/中心参考，
  不能再次用最近邻独立 MoveAway。

## 回退基线确认：run705 / attempt 1

- 已四线程重建并以 r9 重启原 5 yd 版本；run705/seq1 前置于 71.176 秒完成、99.546 秒开 boss，
  **191.300 秒 kill、零玩家死亡**。所有非 boss 伤害止于 71.176 秒，boss 段继续无外来常驻怪。
- 这是回退后首条有效样本，证明 r8 的 4 death 不会留在运行二进制中。当前原策略的有效证据为
  **3/3 kill、总 2 death**（run701/run703/run705）；仍远不足以宣称稳定。

## 补足至 5 个有效样本：run706/707

- run706/seq1：前置 56.873 秒完成、68.496 秒开 boss，**169.125 秒 kill、零死亡**，所有非 boss
  伤害止于 53.213 秒。该 run 的 seq2 于 0.915 秒被 guard 中止：bot 820 在离 boss 72.73 码且目标仍为
  126728 时对 boss 造成 3,051 伤害；这是连续 attempts 的异常启动污染，不是 boss 样本，未计分母。
- 清掉 instance/CD 后单独 run707/seq1：前置 66.472 秒完成、74.466 秒开 boss，**194.759 秒 kill、零死亡**；
  非 boss 伤害止于 66.472 秒。它证明单场冷启动可复现，不以 run706/seq2 的 aborted 伪补样。
- 至此原 5 yd 版本、20-spawn 证据边界配置有 **5/5 kill、总 2 death（2/5）**：run701、703 各 1 death，
  run705、706/seq1、707 均零死亡。可称“当前配置的击杀稳定（n=5）”，**不可称零死亡稳定或全副本通关**；
  首轮 Shatter 的既有死亡因果仍是下一策略工作项。

## 下一步

1. 保持 20-spawn 证据前置与 `(940,800,192.87)` 准备点继续采样，逐场审计前置完成后
   是否还有非 boss source；达到预先声明样本量前不下稳定率结论。
2. 单独从有效 boss 段提取 Ground Slam→50833→Shatter 的目标、位置、死亡因果，量 `shatter spread`，不将
   清怪阶段事件混入机制分母。
3. 若出现新的常驻 source，先按 spawnId/summoner 闭合并重新定义证据边界；不得用 fixture 删除或猜列。
4. 只有完整前置表和清怪点闭合后，才评估该证据边界是否可升级为完整房间；现有 `-disc-`/空前置配置不得产生
   可计样本。

## 交接

- 本轮新增 HoS 场景模板、运行配置、只读来源观测与文档；获得授权后已编译 worldserver，未提交。
- 静态 LOS 的持久证据为 worldserver 日志 `/tmp/wow335-worldserver-eck-close-r1.log`（本轮命令与两遍输出）；本文件保留所有可复核坐标、真实地面 z 与结论，日志不是唯一证据。
