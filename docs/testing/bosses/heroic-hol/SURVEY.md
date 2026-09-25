# 英雄闪电大厅（Halls of Lightning，map 602）建场景前勘察

> 2026-09-25，只读勘察：源码（core 脚本、mod-playerbots `Ai/Dungeon/HoL`、mod-raidtest `Scenario.cpp`）+ world DB。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los/地面高度实测**，
> 建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。

## 0. 总览

| boss | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 脚本基类 | 最大风险 |
|---|---|---|---|---|---|---|---|
| General Bjarngrim | 28586 | 31533 | 126981 | (1262.0, -26.9, 33.5, 4.727) | 否（28586=0，31533=1） | `npc_escortAI`（非 BossAI） | 约 570 码环形巡逻；4 个停靠台各有 4–5 只 10 码内的怪 |
| Volkhan | 28587 | 31536 | 126982 | (1332.38, -102.078, 56.801, 2.077) | 否（0 / 1） | BossAI | 周期冲向铁砧；距 (1331.9,-106,56) >95 码就 evade |
| Ionar | 28546 | 31537 | 126873 | (1081.99, -261.809, 61.291, 0.017) | 否（0 / 1） | BossAI | playerbots 的 `DISPERSE_POSITION` 在东侧怪堆里（离 Cyclone 7.5 码） |
| Loken | 28923 | 31538 | 126985 | (1186.47, 33.83, 60.81, 3.159) | 否（0 / 1） | BossAI | 最干净：45 码内无怪，最近的巡逻怪在 88 码外 |

- 英雄 entry 的 `flags_extra=1`（`CREATURE_FLAG_EXTRA_INSTANCE_BIND`），四个 boss 的普通和英雄 entry 都**没有** `0x80000000`。所以 AN/AK 那种 evade 后被 despawn 的坑在这里不会出现。
- 四个 spawn 的 `spawnMask` 都是 3，`creature_template_addon.visibilityDistanceType`：Bjarngrim=4，其余=3。
- 副本里一共有 187 条 `creature` 记录。

### instance 脚本（instance_halls_of_lightning.cpp）

- `SetBossNumber(4)`，encounter id：`DATA_BJARNGRIM=0`、`DATA_IONAR=1`、`DATA_LOKEN=2`、`DATA_VOLKHAN=3`。
- **没有覆盖 `CheckRequiredBosses`**，基类默认返回 true，所以 Loken 等 boss **不要求**其他 boss 先死。**没有 boss boundary**（没有 `LoadBossBoundaries`）。
- 门（`DOOR_TYPE_PASSAGE`，对应 boss 状态为 DONE 时打开）：
  - `GO_VOLKHAN_DOOR` 191325 guid 65574 (1277.44, -164.66, 53.52)：Volkhan 死后打开，通往 Hall of Watchers 和 Ionar。
  - `GO_IONAR_DOOR` 191326 guid 65575 (1074.30, -232.21, 62.55)：Ionar 死后打开，通往 Loken 那条走廊。
  - 隔离场景直接传送进房间，门不挡路。但如果要链式打整本，门的状态决定了 bot 能否自己走过去。
- `GO_LOKEN_THRONE` 192654 guid 65583 (1124.02, 34.00, 60.53)：只做 ObjectData 登记，脚本里没有用到。
- AreaTrigger `at_hol_hall_of_watchers`（5082 (1225.8,-164.4,60)、5083 (1187.1,-164.2,60)、5084 (1175,-193.8,60)）只触发一次。玩家踩到时，会在 50 码内随机唤醒 2–4 只视线内带 Freeze Anim 的 Titanium Siegebreaker(28961)/Thunderer(28965)，把它们的 home 设成玩家位置，5 秒后攻击。这些怪在 Volkhan 门到 Ionar 之间，只影响链式路线，隔离场景不受影响。

### mod-playerbots 策略

- context key 与 `getName()` 都是 **`wotlk-hol`**（`DungeonStrategyContext.h:58`，`HoLStrategy.h:16`）。`PlayerbotAI::ApplyInstanceStrategies` 在 `case 602` 自动挂上。raidtest 的 `CombatTrigger::RuntimeStrategyName` 现在是恒等映射（上游已统一改名），不需要补硬编码表。
- 触发器、动作、multiplier 全表见各 boss 小节。汇总如下：

| boss | trigger → action（优先级） | multiplier |
|---|---|---|
| Bjarngrim | `stormforged lieutenant` → `bjarngrim target`（RAID+5，仅 DPS，先打副官 29240）；`whirlwind` → `avoid whirlwind`（RAID+4，离 boss 10 码） | `BjarngrimMultiplier`：旋风斩施法中禁掉其它移动；副官在场时，非坦克的 `DpsAssistAction` 和 AoE 置 0 |
| Volkhan | `volkhan` → `volkhan target`（RAID+5，非坦非奶一律打 Volkhan） | `VolkhanMultiplier`：非坦非奶的 `DpsAssistAction` 和 AoE 置 0（不打熔岩傀儡，减少碎裂） |
| Ionar | `ionar disperse` → `disperse position`（MOVE+5，去 (1161.152,-261.584,53.223)）；`ionar tank aggro` → `ionar tank position`（MOVE+4，(1078.860,-261.928,61.226)）；`static overload` → `static overload spread`（MOVE+3，离带减益者 10 码）；`ball lightning` → `ball lightning spread`（MOVE+2，远程离队友 7 码） | `IonarMultiplier`：boss 不可见时只放行 disperse/static 两种移动；Disperse 施法中禁冲锋 |
| Loken | `lightning nova` → `avoid lightning nova`（MOVE+5，离 boss 22 码）；`loken ranged` → `loken stack`（MOVE+4，远程贴近到 2 码，猎人 6.5 码） | `LokenMultiplier`：全程禁 `FleeAction`；闪电新星施法中只放行 avoid 移动、禁冲锋 |

注意：每个 trigger 和 action 都用 `find target` 按**名字**找 boss，而且没有按 boss 做作用域隔离。隔离场景没问题；链式场景要留意相邻 boss 节点劫持（见 memory「副本节点作用域劫持」）。

---

## 1. General Bjarngrim（28586 / 31533）

### 1.1 脚本（boss_bjarngrim.cpp）

- **巡逻**：基类是 `npc_escortAI`。构造函数里 `AddWaypoint` 写了 7 个点，然后 `Start(isActiveAttacker=true, …, instantRespawn=false, canLoopPath=true)`，**无限循环**、走路速度：

  | WP | 坐标 | 停留 | 备注 |
  |---|---|---|---|
  | 1 | (1262.0, -26.9, 33.5) | 10 秒 | = spawn，南台；到达后 2.5 秒施 Charge Up |
  | 2 | (1262.18, 99.3, 33.5) | 10 秒 | 北台（往返 126 码） |
  | 3 | (1262.0, -26.9, 33.5) | 0 | 回南台，移除临时电荷 |
  | 4 | (1332.0, -26.6, 40.18) | 10 秒 | 中台（70 码） |
  | 5 | (1395.092, 36.6425, 50.038) | 10 秒 | 东高台（89 码） |
  | 6 | (1332.0, -26.6, 40.18) | 0 | |
  | 7 | (1262.0, -26.9, 33.5) | 0 | 循环 |

  一圈约 570 码加 40 秒停留，走路速度下粗估约 4–4.5 分钟。DB 里 `creature.MovementType=2`、`creature_addon.path_id=1269810`（14 点，路线相同，带 `waypoint_scripts` 12698101/12698102 施 52092/52098）。但 `npc_escortAI::Start` 发现当前是 `WAYPOINT_MOTION_TYPE` 时会 `MovementExpired()+MoveIdle()`，所以**实际以脚本的 7 点 escort 为准**，DB 路径只是冗余。`creature_formations` 里他是一个只有自己的 formation（leader=member=126981，groupAI 0），没有成员。
- **Reset()**：`summons.DespawnAll()` 后，在身边随机 4–12 码召 **2 只 Stormforged Lieutenant（29240/英雄 30973）**，`MoveFollow(me, 3, 2.5 / 3.78)`，所以副官跟着他巡逻。这两只是召唤物（spawnId=0）。还会清光环、上战斗姿态、`SetBossState(NOT_STARTED)`。
- **JustEngagedWith**：`SetInCombatWithZone()`，RollStance，每 20 秒换一次姿态（姿态在三种之间随机 ±1）。
  - 技能按事件组调度。注意代码里的分组和注释对不上：Pummel/Mortal Strike/Slam 挂在 BATTLE 组，Intercept/Cleave/Whirlwind 挂在 BERSERKER 组，Reflection/Knock Away/Ironform 挂在 DEFENSIVE 组。进入某个姿态时，**另外两组延后 20 秒**，但不取消。
  - 首次时间：Pummel 5s、Reflection 8s、Ironform 12s、Knock Away(AoE 击退) 16s、Intercept(40 码随机目标) 23s、Mortal Strike 24s、Cleave 25s、Whirlwind 26s（重复 25s）、Slam 30s。
- **没有 EnterEvadeMode 覆盖**，用的是 `npc_escortAI::EnterEvadeMode`：护送状态下 `ReturnToLastPoint()`，跑回 home（= 进战斗位置），然后接着巡逻。`UpdateEscortAI` 在进战斗后 `!UpdateVictim()` 时直接调 `Reset()`，副官会重召。
- 副官 AI：Arc Weld 2 秒后开始、每 20 秒一次；Renew Steel 10–11 秒后开始、每 10–14 秒一次，**治疗 Bjarngrim**。
- 成就数据 `DATA_BJARNGRIM_ACHIEVEMENT`：开怪时是否带临时电荷，与验证无关。

### 1.2 附近的怪

spawn 点 45 码内（游戏里 Hardened Steel / Stormforged 的 unit_flags=32832=UNK_6|SWIMMING，都是可攻击的普通敌对，faction 16，rank 1）：

| guid | entry | 名称 | 坐标 | 距 spawn | 巡逻 / formation |
|---|---|---|---|---|---|
| 126898 | 28579 | Hardened Steel Berserker | (1258.4, -35.7, 33.6) | 9.5 | 静止，无 formation |
| 126885 | 28578 | Hardened Steel Reaver | (1252.4, -26.7, 33.6) | 9.6 | 静止 |
| 126914 | 28580 | Hardened Steel Skycaller | (1269.1, -33.7, 33.6) | 9.8 | 静止（远程，贴近 5 码会 Disengage） |
| 126941 | 28582 | Stormforged Mender | (1262.9, -39.2, 33.5) | 12.4 | path 1269410：绕南台小圈 (1252.8–1267.1, -39.5 – -28.9) |
| 126917 | 28581 | Stormforged Tactician | (1269.8, 3.9, 33.5) | 31.8 | path 1269170：走道上 y 0.5 ↔ 32.4 往返 |
| 126923 | 28581 | Stormforged Tactician | (1293.6, -34.5, 36.1) | 32.6 | 静止（通往中台的坡上） |

巡逻停靠点 40 码内：

| 停靠点 | 怪（guid entry 距离） |
|---|---|
| 北台 (1262.18, 99.3) | 126905 Skycaller 10.2、126906 Skycaller 10.2、126895 Berserker 10.5、126918 Tactician 12.7（path 1269180）、126940 Mender 31.1（path 1269400：x≈1269，y 39.2↔68.8）、126922 Tactician 32.4 |
| 中台 (1332, -26.6, 40.18) | 126899 Skycaller 9.9、126878 Reaver 10.2、126886 Berserker 10.4、126939 Mender 12.1（path 1269390）、126923 Tactician 39.5 |
| 东高台 (1395.09, 36.64, 50.04) | 126888 Berserker 9.9、126900 Skycaller 10.1、126880 Reaver 10.5、126915 Tactician 11.5（path 1269150）、126925 Tactician 11.8（path 1269250）、126924 Tactician 33.2（path 1269240）、126933 Mender 35.7（path 1269330） |

这些怪都没有 `creature_formations` 记录，SmartAI 里也没有 call-for-help 或 link 事件。但它们离他的停靠点只有约 10 码，他在哪里被开，那里的一组就会被拉进来。

### 1.3 场景建议（风险最高）

- **核心问题**：boss 的位置取决于巡逻进度，`FindBossNear` 会找全图离开怪点最近的那只 28586，所以找得到。难点在：
  1. 队伍在固定准备点等待时，他可能正沿 x≈1262 的走道南北往返，**直接走进准备点**，提前开战。
  2. 有前置清怪时，raidtest reset 会把 boss `NearTeleportTo` 回 spawn 并调 `AI()->Reset()`，但 escort 的 waypoint 进度不会归零，他会接着朝下一个 WP 走。这一点需要先跑一次只观察位置的探针，确认行为。
- **隔离档建议**：用 `FixtureDespawnSpawns` 移除南台一组 126898,126885,126914,126941，外加走道巡逻 126917 和坡上的 126923。开怪点放在南台北侧走道 **(1262, -3, 33.5)**，距 spawn 23.9 码（z 待实测）。准备点 **(1266, 15, 33.5)**，距 spawn 42.1 码，离 126940 巡逻端点 24.4 码。可以把 **126940（Mender，走道 y39–69 巡逻）** 留作唯一前置，满足「前置清怪 → 恢复 → 传送」的流程，做法与斯拉德兰相同。
  - 但这个准备点**就在他 WP1↔WP2 的必经路线上**。能否成立，取决于 reset 后他是否停在 WP1，还是立刻往北走，必须先实测。备选做法：把开怪、准备都放到中台或东高台（同样要移除当地的一组），或者在他某次 10 秒停留时拉。
- 副官必须先打（策略就是这么写的）：两只副官会持续给 boss 回血，并附加 Arc Weld。
- 完整档口径需要把 4 个停靠台的约 18 只怪都算进来，工作量大，建议先做隔离档。

---

## 2. Volkhan（28587 / 31536）

### 2.1 脚本（boss_volkhan.cpp）

- `JustEngagedWith`：`SetInCombatWithZone`。事件：
  - `EVENT_MOVE_TO_ANVIL` 9–14 秒首发，之后每 30–36 秒一次。他跑速设为 4.0、REACT_PASSIVE，沿 `GetNextPos` 分段 `MovePoint`：
    - y < -180 → (1308 或 1355, -178, 52.5)
    - y < -145 → (1308 或 1355, -137, 52.5)
    - y < -130 → (1320 或 1343, -123, 56.7)
    - 否则直接到铁砧 (1327, -96, 56.7)
    - 到铁砧后施 Temper(52238) 并 root；命中后召 **2 只 Molten Golem（28695/英雄 30969）**，解除 root，重新追击。
  - `EVENT_HEAT` 18–38 秒首发。只在场上有活的 Molten Golem 时施 Heat(52387，给傀儡叠层)，每 9–24 秒一次，Temper 之后重排。
  - `EVENT_CHECK_HEALTH` 每秒检查一次，血量 <25% 时施一次 Shattering Stomp(52237)，让所有 Brittle Golem 碎裂（Shatter 52429 AoE）。碎裂超过 4 只，成就失败。
  - **`EVENT_POSITION` 每 4 秒检查一次：距 (1331.9, -106, 56) 超过 95 码就 `EnterEvadeMode()`**（软栓绳）。
- Molten Golem：3 秒 Immolation Strike（每 5 秒）。5 秒时**只执行一次**随机换目标（清仇恨，给目标 +30000）。受到致命伤害时不死：英雄难度先放 Blast Wave(23113)，再变成 **Brittle Golem 28681**（不可攻击、不可选中、眩晕、伤害置 0），等 Stomp 把它震碎。
- `JustDied` 会 despawn 100 码内所有 Slag(28585)。
- 没有 EnterEvadeMode 或 SummonedCreatureEvade 覆盖（BossAI 默认）。

### 2.2 附近的怪

spawn 点 45 码内：

| guid | entry | 名称 | 坐标 | 距离 | 备注 |
|---|---|---|---|---|---|
| 126875 | 28823 | Volkhan's Anvil | (1322.2, -89.3, 61.3) | 17.0 | 触发器 NPC（faction 35，NOT_SELECTABLE，flags_extra 130） |
| 126831 | 32258 | Gold Beetle | (1349.7, -101.1, 23.3) | 37.7 | 小动物 |
| 126974 | 28585 | Slag | (1332.2, -124.3, 23.2) | 40.2 | **下层 z23**（低 33 码，不同楼层），随机游走 8 码 |
| 126968 | 28585 | Slag | (1325.6, -128.4, 23.2) | 43.2 | 同上 |

45–65 码（同在 z≈52–56，是 GetNextPos 用到的房间南半环，多半就是他的房间）：

| guid | entry | 名称 | 坐标 | 距 boss | 巡逻 / formation |
|---|---|---|---|---|---|
| 126950 | 28583 | Blistering Steamrager | (1360.0, -139.7, 52.1) | 46.9 | 随机游走 5 码 |
| 126948 | 28583 | Blistering Steamrager | (1305.5, -140.8, 52.1) | 47.4 | 随机游走 5 码 |
| 126947 | 28583 | Blistering Steamrager | (1298.1, -135.2, 54.8) | 47.7 | 随机游走 5 码 |
| 126949 | 28583 | Blistering Steamrager | (1368.4, -136.4, 56.0) | 49.8 | 随机游走 5 码 |
| 126960 | 28584 | Unbound Firestorm | (1370.4, -144.5, 52.9) | 57.1 | 随机游走 5 码 |
| 126959 | 28584 | Unbound Firestorm | (1295.1, -145.5, 52.1) | 57.4 | 随机游走 5 码 |
| 126954 | 28583 | Blistering Steamrager | (1311.2, -159.0, 52.3) | 60.9 | **formation leader**，path 1269540 绕南环 (1311–1355, -187 – -142) |
| 126955 | 28583 | Blistering Steamrager | (1354.3, -162.4, 52.0) | 64.3 | 126954 的成员（groupAI 514） |

另外还有 5–6 只 Slag 在下层（z23.2），不同楼层，不计入。北侧 y -40 – -100 之间 DB 没有任何怪，最近的是 Bjarngrim 中台那一组（126939/126878/126886，68–71 码，z40）。

### 2.3 场景建议

- 开怪点 **(1320, -123, 56.7)**：这是脚本 `GetNextPos` 自己用的台阶点，可以确认可行走。距 boss 24.3 码，距 126948 23.4 码，距南环巡逻 126954 最近约 37 码。
- 准备点候选 **(1308, -137, 52.5)**：同样是脚本点，距 boss 42.8 码，但**离 126948 只有 4.6 码**。只有把西侧一组设为前置并清掉才能用。
- 前置建议：`PrerequisiteSpawns` 放西侧 126947、126948、126959（离开怪点和准备点在 30 码内）。东侧 126949、126950、126960 与南环巡逻对 126954、126955 可以作前置，也可以移除（隔离档）。它们离开怪点 37–47 码，但 Volkhan 冲铁砧时会经过台阶点，巡逻对还会绕环。
- 北侧（从 Bjarngrim 中台过来的方向）如果有通道，可以作为更干净的准备点。但 DB 里没有怪或路径点能证明那一段的地面，需要实测。
- 栓绳 95 码：开怪点和准备点都在圈内，不构成问题。

---

## 3. Ionar（28546 / 31537）

### 3.1 脚本（boss_ionar.cpp）

- `JustEngagedWith`（BossAI，`DoZoneInCombat`）：Ball Lightning 7–11 秒后开始（随机非坦克，每 8–18 秒一次）；Static Overload 6–12 秒后开始（随机目标，每 9–14 秒一次；**英雄模式到期不击退**，只在普通难度击退）。
- **50% 血量只触发一次** Disperse(52770)：召 5 只 Spark of Ionar（28926/英雄 31867，20 秒后消失，不可攻击，伤害归零，每 3 秒随机换一名玩家跟随，自带 Random Lightning）。Ionar 自己**隐身并眩晕**，20 秒后召回火花（2.5 倍速回到分裂点），再过 5 秒火花消失，Ionar 现身、解除眩晕，重新排技能。之后不会再次分裂（`ScheduleHealthCheckEvent(50)` 只注册一次）。
- 没有 EnterEvadeMode 覆盖。

### 3.2 附近的怪

spawn 点 45 码内：

| guid | entry | 名称 | 坐标 | 距离 | 巡逻 |
|---|---|---|---|---|---|
| 126876 | 28826 | Stormfury Revenant | (1110.8, -266.0, 57.0) | 29.4 | 静止 |
| 126877 | 28826 | Stormfury Revenant | (1110.8, -256.8, 57.0) | 29.5 | 静止 |
| 126822 | 32258 | Gold Beetle | (1089.6, -292.5, 61.3) | 31.6 | 小动物 |
| 126874 | 28547 | Storming Vortex | (1119.2, -264.9, 56.9) | 37.6 | path 1268740：x≈1118，y -248.2 ↔ -275 往返 |

45–80 码：126894/126893 Stormforged Construct (1081.4/1065.9, -209, 61.3) 52–55 码，在 Ionar 门 (1074,-232) 之后；东南 Cyclone(28825) ×4 加 Revenant 76298 在 (1117–1138, -317 – -325, 57) 65–80 码。没有 formation。

**策略的 `DISPERSE_POSITION` (1161.152, -261.584, 53.223)（距 Ionar 79 码）45 码内**：

| guid | entry | 名称 | 距该点 | 巡逻 |
|---|---|---|---|---|
| 76282 | 28825 | Cyclone | 7.5 | 随机游走 5 码 |
| 76280 | 28825 | Cyclone | 8.9 | 随机游走 5 码 |
| 76278 | 28547 | Storming Vortex | 14.4 | 随机游走 5 码 |
| 76296 | 28826 | Stormfury Revenant | 16.9 | path 762960：x≈1176，y -298 ↔ -246.6 |
| 76279 | 28825 | Cyclone | 19.4 | 随机游走 5 码 |
| 76281 | 28825 | Cyclone | 24.6 | 随机游走 5 码 |
| 76283 | 28825 | Cyclone | 26.0 | 随机游走 5 码 |
| 126874 | 28547 | Storming Vortex | 42.3 | 见上 |
| 52912 | 28965 | Titanium Thunderer | 43.2 | 冰冻（Hall of Watchers 西缘） |

→ 分裂阶段全队会跑 79 码进这堆怪里。**隔离档必须把这一堆一起移除，或者清掉**，否则分裂阶段必然连怪。要不要改这个坐标属于 playerbots 自身的问题，只能如实记录，不能用 raidtest 代写。

### 3.3 场景建议

- 开怪点 **(1108, -261.5, ≈57.0)**：夹在两只 Revenant 之间的台阶下沿（z 取 Revenant 的 57.0，待实测），距 Ionar 约 26 码。
- 准备点 **(1140, -261.5, z 待测，52.3–57 之间)**：距 Ionar 58.5 码，离 Vortex 巡逻线约 22 码，离 Cyclone 76282 27 码。
- 前置 / 移除：126876、126877（离开怪点 8 码，**必须**是前置）；126874（巡逻穿过准备点和开怪点之间，前置）；DISPERSE 一堆 76278–76283、76296（移除或前置）。坦克站位 `IONAR_TANK_POSITION` (1078.86, -261.93, 61.23) 就在 spawn 上。
- 链式档：从 Volkhan 门过来要穿过 Hall of Watchers（31 只冰冻 Titanium 加 3 个一次性唤醒触发器）和 Cyclone 厅（17 只 Cyclone、5 只 Revenant、2 只 Vortex），不属于本轮范围。

---

## 4. Loken（28923 / 31538）

### 4.1 脚本（boss_loken.cpp）

- `MoveInLineOfSight`：玩家进入 40 码内时喊 intro（只喊一次），纯文本。
- `ScheduleTasks`（BossAI 开怪时调用）：
  - 3 秒后施 **Pulsing Shockwave**（59414 光环加 52961）：spell script 把伤害按**与 Loken 的二维距离倍乘**（距离超过 1 码开始线性放大），所以全队必须贴身。
  - **Lightning Nova** 15 秒首发、每 15 秒一次。期间 `MoveIdle`，在 56502 光环移除后恢复追击。需要跑出范围（策略用 22 码）。
  - **英雄**：Arc Lightning(52921) 10 秒首发、每 12 秒一次，100 码随机目标；同时启动成就计时 Timely Death。
  - 75/50/25% 只喊话，没有新阶段。
- 没有 EnterEvadeMode 覆盖，**不要求其他 boss 先死**（instance 没有 CheckRequiredBosses）。entry 的 unit_flags=0（普通 28923），开局就可攻击。

### 4.2 附近的怪

spawn 点 **45 码内只有 Loken 自己**。100 码内：

| guid | entry | 名称 | 坐标 | 距离 | 巡逻 |
|---|---|---|---|---|---|
| 126828 | 32258 | Gold Beetle | (1189.8, 82.7, 60.8) | 49.0 | 小动物 |
| 126820 / 126832 | 32258 | Gold Beetle | (1156.8, 97.9) / (1156.6, -30.1)，z60.8 | 70.6 | 小动物（说明 z60.8 的地面覆盖 x1156–1190、y -30–98） |
| 126919 | 28581 | Stormforged Tactician | (1254.7, 55.4, 33.5) | 76.5 | path 1269190，Bjarngrim 那层（z33.5，不同楼层） |
| 126984 | 28920 | Stormforged Giant | (1099.0, 19.6, 53.6) | 88.9 | path 1269840：x 1067–1099，y 8–20 |
| 126983 | 28920 | Stormforged Giant | (1098.1, 54.1, 53.7) | 91.0 | path 1269830：x 1067–1100，y 51–60 |

没有 formation。

### 4.3 场景建议（最干净）

- 开怪点 **(1160, 34, 60.8)**：Loken 正西 26.5 码（在 40 码 intro 圈内；z 参考小动物和王座高度，待实测）。
- 准备点 **(1140, 34, 60.7)**：距 Loken 46.5 码，距两只 Giant 的巡逻端点约 44 码（并低约 7 码），距王座 16 码。
- 不需要前置和移除。两只 Giant 可以不动。如果实测发现准备点能被 Giant 巡逻看到，就把准备点东移到 (1145,34) 附近，或者把 Giant 设为前置。
- 策略覆盖齐全（新星躲避、远程贴近、禁逃跑），适合作为本副本的第一条基线。

---

## 5. 场景 conf 格式参考

示例：`env/dist/etc/modules/mod-raidtest-scenario-heroic-gd-sladran-disc-h5g.conf`（隔离档，含前置和夹具）与 `…-heroic-an-hadronox-full-h5g.conf`（summon 触发）。`[Scenario]` 段用到的键：

| 键 | 含义 |
|---|---|
| `MapId` / `BossEntry` | 地图、boss **普通** entry（HoL：602 / 28586、28587、28546、28923） |
| `PartySize` / `DungeonDifficulty` | 5 / `heroic` |
| `Strategy` | 副本策略 key：`wotlk-hol` |
| `RosterFile` / `GearProfile` | 当前 ilvl 200 档：`mod-raidtest-roster-heroic5gear-n5talents-v1.conf` / `none` |
| `EngageX/Y/Z/O` | 开怪点：队伍最后传送到这里，从这里拉 boss |
| `PreparationX/Y/Z/O` | 准备点：有前置时队伍先在这里清前置 |
| `PrerequisiteSpawns` | 必须先打掉的 spawn guid（会走「清怪 → 恢复 → 传送开怪点」流程；需要 dungeon 模式和准备点） |
| `PrerequisiteTimeoutSeconds` | 前置清怪超时 |
| `FixtureDespawnSpawns` | 夹具直接移除的 spawn（口径变成「隔离」，台账要分开记） |
| `EngageTrigger` | `pull`（默认，坦克拉）或 `summon`（配 `SummonTriggerEntry`、`SummonTriggerRadius`、`EngageConfirmBossState=<bossId>:<state>`，不能和前置同用） |
| `TimeoutSeconds` | 单次 attempt 超时 |
| `MasterlessAvoidAoe` | 1 = 无真人 master 也加 avoid aoe（AN 的经验） |

`Scenario.cpp` 另外还支持：`BossSpawnMode(database/script)` 和 `ScriptBoss*`、`Event*`（剧情事件）、`FixtureBossStates`、`FixtureBossNotify`、`PrerequisiteGameObjects`、`KillGateSpawn`、`PrerequisiteMinBossDistance(+BossEntry)`、`PrerequisiteRepullDelaySeconds`、`PrerequisiteCc*`、`AttemptStartDelaySeconds`、`Navigation*`、`Tank/NonTankPreparation*`（分职责准备点）、`PrerequisiteO`、`RaidDifficulty`。

## 6. campaign 矩阵草案（按 CAMPAIGN-TEMPLATE.md）

| encounter | scenario（拟） | 范围 | 当前状态 | 证据与记录 | 下一步 |
|---|---|---|---|---|---|
| Loken | `heroic-hol-loken-h5g` | 完整（房内无怪） | 待建 | 本文 §4 | 实测开怪点/准备点 los 与地面 → 首轮基线 |
| Volkhan | `heroic-hol-volkhan-h5g` | 完整（前置清西侧 3 只）或隔离 | 待建 | 本文 §2 | 实测 (1320,-123)/(1308,-137)，决定前置名单 |
| Ionar | `heroic-hol-ionar-disc-h5g` | 隔离（移除 DISPERSE 怪堆） | 待建 | 本文 §3 | 实测开怪点 z；Revenant ×2 作前置 |
| General Bjarngrim | `heroic-hol-bjarngrim-disc-h5g` | 隔离（移除南台一组） | 待建 | 本文 §1 | 先做巡逻位置探针，确认 reset 后的巡逻行为 |

共用事实：没有 HARD_RESET；没有 required-boss 检查；没有 boss boundary；两扇门都是 PASSAGE（隔离档不受影响）；策略 `wotlk-hol` 由 map 602 自动挂载。
