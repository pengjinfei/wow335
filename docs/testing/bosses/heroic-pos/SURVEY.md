# 英雄萨隆矿坑（Pit of Saron，map 658）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `Northrend/FrozenHalls/PitOfSaron/`、mod-playerbots `Ai/Dungeon/PoS`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp`）、world DB 和客户端 DBC（`data/world/dbc/Spell.dbc`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。

## 0. 总览

| boss | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 脚本基类 | 开战方式 | 现框架能否正常开战 |
|---|---|---|---|---|---|---|---|---|
| Forgemaster Garfrost | 36494 | 37613 | 201992 | (712.14, -215.70, 527.07, 5.87)，**waypoint 巡逻** path 2019920 | 否（0 / 1） | ScriptedAI | 普通 pull；**带 6 只 Wrathbone Siegesmith 编队一起进战** | **能**：`EngageTrigger=pull` |
| Ick（载具 522）+ Krick（乘客） | Ick 36476 / Krick 36477 | 37627 / 37629 | Ick 202042（Krick 是 `vehicle_template_accessory`，无 DB spawn） | (852.85, 123.53, 510.03, 3.26) | 否（0 / 1） | ScriptedAI（Ick）+ NullCreatureAI（Krick） | 普通 pull；**`CanAIAttack` 要求 `InstanceProgress >= 1`（开场剧情播完）** | **能**（需 `FixtureInstanceData=4:1` 或确认开场剧情已自然播完，待实测） |
| Scourgelord Tyrannus + Rimefang | Tyrannus 36658 / Rimefang 36661 | 36938 / 无 | Rimefang 202135 (1017.30, 168.97, 642.93, 5.27)；**Tyrannus 是 Rimefang 的载具乘客，无 DB spawn** | — | 普通 entry 带 0x80000000，但 `EnterEvadeMode` 被覆盖且不调基类，**标志不生效**；evade 时自己 `DespawnOrUnsummon`，并让 Rimefang `DespawnOnEvade()`（20 秒后连同乘客重生） | ScriptedAI | **AreaTrigger 5633** → 召 Gorkun 事件 → 约 38 秒后 Tyrannus 跳下、`DoZoneInCombat` | **不能**：AT 已支持，但 boss 是载具乘客，database 模式找不到；script 模式只允许配 pull |

- 三个英雄 entry 的 `flags_extra` 都只有 1。HARD_RESET 判定读普通 entry（`GetEntry()`），只有 Tyrannus 普通 entry 带标志，但他的 `EnterEvadeMode` 不走 `CreatureAI::EnterEvadeMode`，所以实际行为由脚本决定（见 §3.1）。
- 副本共 229 条 `creature` 记录（228 条 spawnMask 3，1 条只在英雄）。28 只 Invisible Stalker 36848（`npc_pos_icicle_trigger`）沿隧道分布，下文列怪时排除。

### 0.1 instance 脚本（instance_pit_of_saron.cpp）——对框架最关键的一点

- **没有 `SetBossNumber`，也不用 `SetBossState`**。进度放在 `m_auiEncounter[3]` 和 `InstanceProgress`，全部走 `SetData/GetData`：
  - `DATA_GARFROST=0`、`DATA_ICK=1`、`DATA_TYRANNUS=2`（值为 EncounterState：0 NOT_STARTED / 1 IN_PROGRESS / 3 DONE）；
  - `DATA_INSTANCE_PROGRESS=4`：0 NONE → 1 FINISHED_INTRO → 2 FINISHED_KRICK_SCENE → 3 AFTER_WARN_1 → 4 AFTER_WARN_2 → 5 AFTER_TUNNEL_WARN → 6 TYRANNUS_INTRO。**`SetData(4, x)` 只在 x 大于当前值时生效（单调）**，每次改动都 `SaveToDB()`。
  - 因此 `GetBossState()` 永远 TO_BE_DECIDED，`EngageConfirmBossState` / `FixtureBossStates` / `EventCompletionBossState` **全部无效**；要用 `EngageConfirmInstanceData` / `FixtureInstanceData`（已支持）。
- **Tyrannus 从不置 IN_PROGRESS**（只有 Reset 置 NOT_STARTED、JustDied 置 DONE），所以他的开战确认不能用 `EngageConfirmInstanceData=2:1`。
- `SetData(DATA_GARFROST, DONE)`：在 FBSSpawnPos (695.7, -118.8, 513.9) 召 Gorkun Ironskull 37592（剧情：带奴隶走到 Garfrost 尸体旁）。**每调一次召一只**。
- `SetData(DATA_GARFROST/ICK, DONE)` 两个都 DONE 时打开 **Ice Wall 201885（guid 305，(932.3, -80.7, 591.7)）**，它挡在通往隧道的路上。
- `SetData(DATA_TYRANNUS, DONE)`：召 Sylvanas/Jaina Part2（结尾剧情）。
- 没有 boss boundary；各 boss 自己在 UpdateAI 里做「victim 出区就回满血 evade」检查（见各节）。
- 门：只有 Ice Wall 和出口的 HoR Portcullis 201848（(1106.1, 251.7)）。隔离场景直接传送，门不挡路。
- **AreaTrigger（map 658）**，全部是客户端驱动；有脚本的只有这 5 个：

  | AT | 中心 | 形状 | 脚本 | 作用 |
  |---|---|---|---|---|
  | 5578 | (859.3, 44.4, 515.0) | 球 r34.5 | SmartTrigger → Tyrannus 事件 NPC（guid 201851）`SetData(1,1)` | 隧道前第 1 波（需 Garfrost+Ick DONE 且 progress==2 且事件 NPC 已到等待点 1） |
  | 5579 | (960.1, 75.3, 566.2) | 球 r38.1 | `SetData(1,2)` | 第 2 波（需 progress==3 且第 1 波击杀计数归零） |
  | 5580 | (969.9, -117.4, 597.9) | 球 r20.5 | `SetData(1,3)` | 进隧道：progress→5，冰锥开始掉（需第 2 波计数归零） |
  | 5589 | (752.5, -52.6, 508.7) | 球 r20 | SmartTrigger → 奴隶 guid 202279/202285 `SetData(1234,1)` | 奴隶剧情 |
  | **5633** | **(1006.9, 179.0, 628.2)** | **球 r51.5** | **`at_tyrannus_event_starter`** | **Tyrannus 遭遇开关**（见 §3.1） |

### 0.2 mod-playerbots 策略

- context key 与 `getName()` 都是 **`wotlk-pos`**（`DungeonStrategyContext.h:63`，`PoSStrategy.h:16`）。`PlayerbotAI.cpp:1781` 在 `case 658` 自动挂载。RuntimeStrategyName 恒等。
- 全部内容：

| boss | trigger → action（优先级） | multiplier |
|---|---|---|
| Garfrost | **无**（`GarfrostMultiplier` 定义了但函数体恒返回 1 且**没注册**） | 无 |
| Ick & Krick | `ick and krick` → `ick and krick`（RAID+5，Ick 在场即激活）：① 中 Pursuit（或 Ick 正在对别人施 Pursuit 且自己非坦克）且离 Ick <20 码 → 以 `ICKANDKRICK_TANK_POSITION` (816.85, 102.33, 509.16) 为圆心、20 码半径绕圈；② Poison Nova 施法中且 <20 码 → `MoveAway` 11 码；③ 场上有 Exploding Orb（带 69017 光环）且离最近的 <7 码 → 16 个方向打分找 7 码外、离 boss 30 码内、远离队友的点；④ 坦克在以上都不发生时每次 3 码地把 Ick 拖到坦克点 | `IckAndKrickMultiplier`：Poison Nova 施法且 <20 码、中 Pursuit 的非坦克 <15 码、非治疗在 Explosive Barrage 施法期间 → 除本 action 外全部置 0 |
| Tyrannus | `tyrannus` → `tyrannus`（RAID+5）：远程在 boss 血量 <99% 后与 10 码内队友散开（每次 3 码） | 无 |

- `PoSTriggers.h` 定义了 `SPELL_MARK_OF_RIMEFANG`、`RIMEFANG_SPELL_HOARFROST(_HC/_HC2)` 但**没有使用**。
- 所有 trigger 按名字 `find target`。注意 Tyrannus 事件 NPC 36794/36795 也叫「Scourgelord Tyrannus」，但 progress≥5 时它在 (781, 265, 552)，离竞技场约 240 码，不会误触发。

---

## 1. Forgemaster Garfrost（36494 / 37613）

### 1.1 脚本（boss_forgemaster_garfrost.cpp）

- **开战前**：`Reset()` 去 Permafrost、恢复武器、REACT_AGGRESSIVE、`SetData(DATA_GARFROST, NOT_STARTED)`。unit_flags 32832，faction 2102，**普通 pull**。没有进度门禁。
- **他在巡逻**：MovementType 2，path 2019920 共 26 点，在锻造平台 z526.7–528.9 上来回（x 645–720、y -194 – -228），在 (719.5, -227.9) 停 3 秒。开怪点要跟着他走，或让坦克直接追。
- **编队**：leader 201992，成员 6 只 **Wrathbone Siegesmith 36907 / 英雄 37639**（faction 21 敌对，无 AI 脚本，英雄 rank 1、HealthModifier 2、DamageModifier 1），`groupAI=5` = MEMBER_ASSIST_LEADER | EVADE_TOGETHER，`dist=0`（不跟随）：

  | guid | 坐标 | 离 spawn |
  |---|---|---|
  | 202072 | (717.8, -212.1, 527.3) | 6.7 |
  | 202027 | (690.0, -231.9, 526.8) | 27.4 |
  | 202238 | (686.9, -234.6, 526.8) | 31.5 |
  | 201855 | (723.5, -170.9, 527.5) | 46.2 |
  | 201927 | (657.6, -174.5, 526.8) | 68.3 |
  | 202159 | (646.6, -191.2, 526.8) | 70.0 |

  `CreatureGroup::MemberEngagingTarget`：leader 进战且带 MEMBER_ASSIST_LEADER 时，所有活着、没有 victim 的成员都 `EngageWithTarget(target)`。**拉 Garfrost = 同时拉 6 只小怪**（血量低，但近战伤害会压坦克/治疗）。
- `JustEngagedWith`：自挂 **Permafrost 70326**（周期触发 70336），`DoZoneInCombat`，`SetData(DATA_GARFROST, IN_PROGRESS)`，Throw Saronite 5–7.5 秒首发。
- 技能：
  - **Throw Saronite 68788**：每 12.5–20 秒，140 码内随机玩家（先密语提示），落点召一块 **Saronite Rock GO 196485**，落地砸中的人受伤并被击晕（68789）。
  - **Permafrost 70336**（每跳一层，DBC：伤害 + aura 87 受伤增加 + 周期 dummy）：`spell_garfrost_permafrost` 过滤——**近战范围内的目标一律命中；近战范围外的目标，只要有任何一块 Saronite Rock 在 boss 与目标之间（`IsInBetween` 宽 4 码）就不命中**。场上还没有石头时全员命中。机制要求：远程/治疗躲到石头后面让层数掉掉。层数 ≥10 时成就失败（Doesn't Go to Eleven）。
  - **66% 血**：REACT_PASSIVE、清目标、Thundering Stomp 68771，1.25 秒后跳到北熔炉 **(722.56, -234.16, 527.18)**，root 后施 Forge Blade（换剑），恢复追击，Chilling Wave 68778 10 秒后首发、每 35 秒（对 victim）。
  - **33% 血**：再 Stomp，跳到南熔炉 **(639.26, -210.12, 529.02)**，换锤，Deep Freeze 70381 10 秒后首发、每 35 秒（随机目标，DBC：伤害 + 晕 + 减速）。
- **出区 evade**：每 tick 检查 victim 坐标，**x<600 或 x>770 或 y<-270 或 y>-137 或 z<514 或 z>550** 就回满血 `EnterEvadeMode`，并让编队里所有在战斗中的成员一起 evade。
- `JustDied`：DONE（召 Gorkun 37592 剧情）。不是 HARD_RESET。

### 1.2 附近的怪

Garfrost 所在平台（z527）上**除了他自己的 6 只 Siegesmith 没有别的怪**。最近的外部生物都在下层（z513，低 14 码）、约 96–105 码：Wrathbone Laborer 201947 (645.8,-119.1)、201952 (746.5,-124.2)，Horde Slave 202269，Iceborn Proto-Drake 201991（path 2019910，(679.2,-100.6)）。平台上还有两台 Forgemaster's Anvil GO（(638,-209.5)、(726.3,-237.7)，就是两次跳跃的落点旁）。

### 1.3 场景建议

- **框架**：无阻塞。`EngageTrigger=pull`、`BossEntry=36494`、`Strategy=wotlk-pos`。坦克仇恨校验应能通过（Garfrost 正常追坦克）；但 6 只 Siegesmith 同时进战，`PrerequisiteSpawns` 不适用（它们与 boss 同时开战），要么接受「带小怪」作为正常副本形态，要么隔离档 `FixtureDespawnSpawns=202072,202027,202238,201855,201927,202159`（结论降级）。建议**先正常形态**。
- 准备点候选 **(695.0, -149.9, 527.9)**：平台北口（Gorkun 剧情的落点，推测是坡道顶），离 Garfrost spawn 68 码、离 201855 约 33 码，在出区盒内（y>-137 才出界）。开怪点：让坦克直接拉（boss 在巡逻），或在 **(700, -205, 526.8)** 附近等他经过。全部**待实测**（坡道 z、los、巡逻相位）。
- 出区盒很紧（y -137 就是北界），准备点不能再往北放，flee/击退也可能把坦克推出盒导致 evade，首轮日志要看 evade 原因。
- bot 缺口：
  - **缺口 1（中–大，英雄）**：没有任何 Saronite Rock 躲 LOS 逻辑。远程/治疗会一直叠 Permafrost（受伤增加 + 冻伤），打得越久越危险。要做需要：找场上 GO 196485 → 选一块使 boss–自己连线被挡的站位 → 周期性回去施法。属 bot 行为，归 playerbots。
  - 缺口 2（小）：Throw Saronite 落点无躲避（先有密语提示，落点是 GO 不是 dynobject，avoid aoe 大概率识别不了）。
  - 缺口 3（小）：Deep Freeze / Chilling Wave 靠治疗扛。
  - ilvl200 档下可能直接扛过（战斗不长），**建议先测基线再决定是否做 LOS**。

---

## 2. Ick（36476 / 37627）+ Krick（36477 / 37629）

### 2.1 脚本（boss_krickandick.cpp）

- **结构**：Ick 是 VehicleId 522 的载具，`vehicle_template_accessory` 把 Krick 装在 seat 0（summontype 6）。**可攻击的是 Ick**；Krick unit_flags 33554496（不可选中 + 免疫玩家），NullCreatureAI，只替 Ick 施法。击杀判定 = Ick 死亡。
- **进度门禁**：`CanAIAttack()` 恒等于 `GetData(DATA_INSTANCE_PROGRESS) >= INSTANCE_PROGRESS_FINISHED_INTRO(1)`。进度为 0 时 Ick 对任何目标都「不能攻击」→ 拉了也会立刻 evade。
  - 进度 1 由**开场剧情**写入：`npc_pos_leader`（Sylvanas 36990 / Jaina 36993，guid 1972267，在入口 (424.46, 212.16, 528.8)）的 `SetData(DATA_START_INTRO)`，调用方有两个：`instance::OnPlayerEnter`（任何玩家进副本时）和入口两只 Deathwhisper Necrolyte（guid 201888、202281，(497, 199/248)）的 `JustEngagedWith`。剧情约 54 秒，事件 16 写 progress=1。
  - **风险（待实测）**：raidtest 直接 `TeleportTo` 到场景点；如果首个 bot 进图时入口网格（~424, 212）没加载，`OnPlayerEnter` 里 `GetCreature(leader)` 拿不到，剧情不会开始，进度永远是 0（除非有人去打入口的 Necrolyte）。**所以 Ick 场景应配 `FixtureInstanceData = 4:1`**，或者先读 `GetData(4)` 确认。
- `JustEngagedWith`：Krick 喊话，`DoZoneInCombat`，`SetData(DATA_ICK, IN_PROGRESS)`。
- 技能（Ick 的 events，由 Ick/Krick 施放）：
  - Toxic Waste 69024（Krick，40 码随机，地面毒池）：3–5 秒首发，每 7–10 秒。
  - Mighty Kick 69021（Ick，打 victim，击退）：10–20 秒首发，每 20–25 秒。
  - Shadow Bolt 69028（Krick，35 码随机）：10 秒首发，每 14 秒。
  - **特殊技能**：25 秒首发，之后每 25–30 秒，三选一：
    - **Pursuit 68987**：Ick 对 70 码内随机玩家施放（DBC：目标身上挂光环 + 仇恨效果），命中后 Ick `AttackStart` 该玩家、REACT_PASSIVE 12 秒（追着他打）。被追的人要跑。
    - **Poison Nova 68989 / 英雄 70434**：Ick 自身读条 AoE（半径索引 18），离开范围。
    - **Explosive Barrage**：Krick 69012 + Ick 69263，其它事件推迟 20 秒；周期对 100 码内每个玩家脚下召 Exploding Orb（69015），球自增长 16 跳后爆炸 69019。要躲开球。
- **出区 evade**：victim 离 `KrickCenterPos` (836.65, 115.08, 510.0) **超过 80 码或 z 偏离 ±20** 就回满血 evade。
- 死亡：Ick 将死时 Krick 下车、`DoAction(1)` 播结尾剧情（Sylvanas/Jaina 过来、Tyrannus 出场、Krick 被杀），progress → 2。Ick `JustDied` → DONE。不是 HARD_RESET；evade 时载具 `Reset(true)` 重装 Krick。

### 2.2 附近的怪（KrickCenterPos 65 码内）

| guid | entry | 名称 | 坐标 | 离 Ick | 巡逻 / formation |
|---|---|---|---|---|---|
| 202156 | 36879 | Plagueborn Horror | (860.6, 116.5, 510.0) | **10.4** | 静止；SmartAI：Pustulant Flesh、Toxic Waste、**死亡时 Blight Bomb 69582** |
| 202236 | 36879 | Plagueborn Horror | (826.3, 117.0, 509.5) | 27.3 | 随机游走 15 码（离坦克点 12 码） |
| 201903 | 36879 | Plagueborn Horror | (790.2, 132.3, 509.7) | 63.2 | 游走 15 |
| 201981 | 36879 | Plagueborn Horror | (805.9, 73.9, 510.0) | 68.3 | 游走 15 |
| 201833 | 36879 | Plagueborn Horror | (777.2, 88.1, 512.5) | 76 | 游走 15 |

Plagueborn Horror 36879 / 英雄 37635：faction 16，rank 1，英雄 HealthModifier 20（精英怪），**无编队**。其余 100 码以上是奴隶（友方）和小动物。

### 2.3 场景建议

- **框架**：`EngageTrigger=pull`、`BossEntry=36476`、`Strategy=wotlk-pos`，加 **`FixtureInstanceData = 4:1`**（开场剧情完成；只写 progress，属于隔离形态但等价于进副本后无交互自动播完的剧情，结论可正常记）。现有键即可表达，无需框架新增。
  - Ick 没有 IN_PROGRESS 之外的特殊确认需求，普通 pull 的坦克仇恨校验应能通过。Pursuit 期间 Ick 追别人，是正常机制，观察器不要把它判成坦克丢仇恨。
- 前置 / 夹具：**202156 必须处理**（离 boss 10 码，一拉就进战）；202236（游走到坦克点附近）也应处理。建议 `PrerequisiteSpawns = 202236,202156`（正常形态，由 bot 先清）或 `FixtureDespawnSpawns = 202156,202236,201903,201981,201833`（隔离档）。注意 Horror 死亡放 Blight Bomb，前置清怪时会有伤亡压力。
- 准备点候选 **(800, 85, 510)**：离 Ick 约 60 码、离 KrickCenterPos 46 码（在 80 码 evade 圈内），离 201981/201833 约 15–25 码（需先处理）。开怪点：策略坦克点 **(816.85, 102.33, 509.16)**（离 Ick 41.7 码，坦克上前拉后自己会退回来）。全部**待实测**。
- bot 覆盖与缺口：
  - 覆盖：Pursuit 绕圈、Poison Nova 退开、Explosive Barrage 躲球、坦克定点。三个特殊技能都有处理，是 PoS 策略里最完整的一只。
  - 缺口 1（小–中）：Poison Nova 只 `MoveAway` 11 码，而技能半径索引 18（DBC 半径索引，**待实测**实际码数）；如果半径 >11 码，退开不够。
  - 缺口 2（小）：Pursuit 绕圈以固定坐标为圆心，可能跑出 80 码圈或跑进未清的 Horror（参见 memory「躲避动作没有边界判据」）。
  - 缺口 3（小）：Toxic Waste 靠 `MasterlessAvoidAoe=1` 的通用躲地面（待实测）。

---

## 3. Scourgelord Tyrannus（36658 / 36938）+ Rimefang（36661）

### 3.1 脚本（boss_scourgelord_tyrannus.cpp + pit_of_saron.cpp）

- **结构**：Rimefang 36661（VehicleId 535，NullCreatureAI，unit_flags 66 = 不可攻击，DB spawn 202135，在竞技场上空 z642.9 盘旋）。Tyrannus 是它的 `vehicle_template_accessory`（seat 0，summontype 6），**不是 DB spawn**（`m_spawnId=0`，不在 `GetCreatureBySpawnIdStore()` 里）。Tyrannus 构造时 REACT_PASSIVE，`Reset()` 设 NON_ATTACKABLE，unit_flags 832（含 IMMUNE_TO_PC）。
- **开战链（精确）**：
  1. 玩家进入 **AT 5633**（球，中心 (1006.9, 179.0, 628.2)，半径 51.5）→ `at_tyrannus_event_starter::OnTrigger`，条件全部满足才执行：`progress >= 5`、`GetData(GARFROST)==DONE`、`GetData(ICK)==DONE`、`GetData(TYRANNUS)!=DONE`、`GetGuidData(MARTIN_OR_GORKUN)` 为空。
  2. 在 TSSpawnPos (1069.49, 88.99, 631.5) 召 **Gorkun Ironskull 37581**（`npc_pos_martin_or_gorkun_second`，联盟变 Martin Victus 37580），走到 TSMidPos (1051.5, 126.6)；progress → 6。
     - **Gorkun 的构造函数里立即**让 Tyrannus 喊话、`SetImmuneToPC(false)`、REACT_AGGRESSIVE，并对 100 码内最近玩家 `AttackStart` + `DoZoneInCombat`。也就是说：**踩 AT 的瞬间 Tyrannus 就进战斗了**，但他仍骑在 Rimefang 上、仍带 NON_ATTACKABLE，bot 打不到他；出区 evade 检查从这一刻起生效。
  3. Gorkun：每 150 ms 召一只被解放的奴隶（16 只 Freed Slave，友方），15 秒后喊话，再 8 秒后 Tyrannus 喊话、全体面向 5.26，**再 15 秒后 `Tyrannus->DoAction(1)`**；同时开始每 3 秒补召 Fallen Warrior 36841（最多 3 只，在 (1060.95, 102.79) 刷出，与奴隶互相进战）。
  4. `DoAction(1)`：Rimefang 去光环、沿 path 3000218 飞行；Tyrannus 跳到 **(1023.46, 159.12, 628.2)**，去 NON_ATTACKABLE、`SetImmuneToPC(false)`、`DoZoneInCombat()`（并在 Gorkun 事件 1 里对 100 码内最近玩家 `AttackStart`）。**从踩 AT 到 Tyrannus 可攻击约 38 秒。**
- 技能（DoAction(1) 起算）：
  - Forceful Smash 69155：14–16 秒首发（victim 在近战范围才放，否则 3 秒后重试），1 秒后 **Unholy Power 69167**（自增益：伤害提升等），之后 40–48 秒再循环。坦克吃重击。
  - **Overlord's Brand 69172**：4–6 秒首发，每 11–12 秒，95 码内随机目标挂 8 秒光环。DBC：带印记者**造成的伤害会复制一份（69189）打到 Tyrannus 的当前目标**，**施放的治疗会复制一份（69190）治疗 Tyrannus**。机制要求：被印记的 DPS 停手、被印记的治疗停奶（或只奶自己），否则坦克和 boss 血量都会失控。
  - **Icy Blast 69232**（Rimefang 施放）：5 秒首发，每 5 秒，190 码内随机玩家；落点生成持续区域 69238（PERSISTENT_AREA_AURA：减速 + 周期伤害），会越积越多。
  - **Mark of Rimefang / Hoarfrost**：25 秒首发，每 25 秒，190 码内随机玩家；Rimefang 对其施 Hoarfrost 69246（触发导弹，落点 69245 伤害 + **击晕**）。同时 Icy Blast 推迟 10 秒。被点名的人要跑出落点。
- **出区 evade**：victim 离 TSDistCheckPos (1009.29, 163.15, 628.16) **超过 100 码或 z 偏离 ±20**，回满血 evade。
- **`EnterEvadeMode` 覆盖（不调基类）**：让 Gorkun `DoAction(1)`（清掉所有奴隶召唤物）并 despawn、清空 `MARTIN_OR_GORKUN` guid；让 Rimefang `DespawnOnEvade()`（默认 20 秒重生，重生后重新装上 Tyrannus 乘客）；自己 `DespawnOrUnsummon()`。**所以 HARD_RESET 标志没有意义，但效果等价：每次 evade 后 boss guid 都会变**。
- `CanAIAttack`：不打 Gorkun/Martin 和所有 Freed Slave。
- `JustDied`：DONE（召 Sylvanas/Jaina Part2，Rimefang 被隐藏，Sindragosa 结尾剧情）。**击杀后同一实例里 Tyrannus 不会再出现**（`OnCreatureCreate` 在 DONE 时把 Tyrannus/Rimefang 设为不可见）。

### 3.2 附近的怪

- TSCenterPos (990.48, 165.37) **90 码内只有 Rimefang**（和 1 只老鼠）。
- 但 Gorkun 事件的刷点 TSSpawnPos (1069.49, 88.99) 紧挨着隧道出口的静态编队：

  | leader | 成员 | 坐标 | 离 TSSpawnPos | 离 TSCenterPos |
  |---|---|---|---|---|
  | **202248**（Fallen Warrior） | 202163、202246（Wrathbone Skeleton）、202165（Fallen Warrior） | (1058–1070, 93–100, 630–631) | **4–11 码** | ≈95–100 码 |
  | 202212（Wrathbone Skeleton） | 202132（Skeleton）、202200、202105（Wrathbone Sorcerer） | (1067–1079, 34–49, 630–631) | ≈40–55 码 | ≈135 码 |

  友方奴隶在 202248 编队旁边刷出，很可能互相进战，把这组怪带进竞技场或引来 bot。

### 3.3 隧道 gauntlet 与事件怪（链式场景才相关）

- **第 1 波**（AT 5578，progress 2→3）：召 2 只 Ymirjar Deathbringer 36892（沿样条路径飞下，3.5 秒后可攻击）+ 8 只 Wrathbringer 36840 / Flamebearer 36893（Emerge 后 3.5 秒转主动）；每只死亡时 SmartAI `SetData(2,1)` 给事件 NPC，**计数 10**。
- **第 2 波**（AT 5579，progress 3→4）：Fallen Warrior 36841 ×4 + Wrathbone Coldwraith 36842 ×2 从 (927, -72, 592) 冲向 (926, -46.6, 591)；**英雄再加 6 只**冲到 (937.8, 21.2, 574.6)，**计数 12**。
- **隧道**（AT 5580，progress 4→5）：28 只 Invisible Stalker 36848（x 954–1082、y -138–84、z 595–634）每 16–24 秒各自施 Tunnel Icicle 69424，召 Collapsing Icicle 36847（2.5 秒施 69428/69426：先地面阴影、后坠落伤害）。隧道里还有 7 组静态怪：201982、202015（+202085、202257）、202068（+201871）、202045（+202265）、201939（+201876、202158、201926）、202212 组、202248 组，外加单只 201889、201998（Disturbed Glacial Revenant 36874）。
- 每一步都要 bot 走进对应 AT（客户端包）且前一波计数归零。现在框架只支持**一个** `EngageAreaTrigger`，没有「沿途按顺序发多个 AT」的能力；bot 也没有躲冰锥逻辑。**链式 gauntlet 暂不可行，只做隔离档。**

### 3.4 场景建议

- **进度夹具**（现有键可以表达）：`FixtureInstanceData = 0:3,1:3,4:5`（Garfrost DONE、Ick DONE、progress=5）。副作用：每次 attempt 都会在 Garfrost 处召一只 Gorkun 37592（剧情 NPC，远离竞技场），并打开 Ice Wall；progress=5 会让隧道冰锥开始掉（隔离档不走隧道，无影响）。结论需标「隔离形态（跳过 gauntlet）」。
- **开战**：`EngageTrigger = areatrigger`、`EngageAreaTrigger = 5633`，坦克站在盒内（候选 **(1000, 170, 628.2)**，离 AT 中心 11 码）。开战确认：`EngageConfirmInstanceData` 不能用 2:1（从不置 IN_PROGRESS）；4:6 与 `boss_in_combat` 都会在 AT 触发瞬间成立（Gorkun 构造时就让 Tyrannus 进战），**早于 boss 可攻击约 38 秒**。确认本身没问题，但观察器必须容忍开头约 38 秒「boss 在战斗中却 NON_ATTACKABLE、骑在载具上、没有伤害」的阶段，不能判成卡住或坦克丢仇恨（与 UP Skadi 同类需求）。**待实测**：Tyrannus 作为乘客处于战斗但够不到 victim 时，是否会因不可达而提前 evade。
- **阻塞（框架，中）——boss 是载具乘客**：
  1. `FindBossNear()` 在 database 模式只扫 `GetCreatureBySpawnIdStore()`，找不到 Tyrannus；script 模式能用 200 码网格查找，但 `Scenario.cpp` 规定 `BossSpawnMode=script` 必须配 `EngageTrigger=pull` 和非空 `PrerequisiteSpawns`。需要放开：允许 `BossSpawnMode=script` + `EngageTrigger=areatrigger`（不要求前置），或新增「按载具 spawn（Rimefang 202135）解析乘客」的键。
  2. `ResetInstance()` 只恢复 boss entry / 前置 / kill gate 的 DB spawn；Tyrannus evade 后要靠 **Rimefang 202135** 重生（20 秒）才会回来。需要把 Rimefang 纳入恢复范围（例如新增 `ResetExtraSpawns=202135`，或在 script 模式下等 `ScriptBossAppearTimeoutSeconds`）。
  3. 击杀后同实例不可重打（DONE 时隐藏 Tyrannus/Rimefang，且 `SetData(2, 0)` 不会把已隐藏的单位变回可见）：每次击杀后需要新实例（roster 重建），或框架里显式恢复。
  - 这些都是编排/寻址问题，不代替 bot 做战斗决策。
- 前置 / 夹具：**`FixtureDespawnSpawns = 202248,202163,202246,202165`**（奴隶刷点旁的编队，强烈建议）；202212 组（202212、202132、202200、202105）视首轮情况再加。友方 NPC（Gorkun、16 只奴隶、补刷的 Fallen Warrior）会一直在场，观察器要容忍「场上有友方 NPC 与敌方小怪互殴」，DPS 目标选择可能被补刷的 Fallen Warrior 分走（参见 memory「副本节点作用域劫持」）。
- 准备点 = 开怪点（AT 在开怪点触发，38 秒剧情期间队伍原地待命；Tyrannus 虽已进战，但技能事件由 DoAction(1) 才排，剧情期间 Rimefang 不放 Icy Blast/Hoarfrost）。站位需在 TSDistCheckPos 100 码内、z 628 ±20。**待实测**。
- bot 缺口：
  - **缺口 1（大）**：Overlord's Brand 无处理。被印记的 DPS 继续输出 = 坦克多吃一份伤害；被印记的治疗继续奶 = 给 boss 回血。英雄下可能决定成败。
  - **缺口 2（中）**：Mark of Rimefang / Hoarfrost 无处理（常量定义了没用），被点名者不跑会被击晕 + 高伤害，且可能站在人群里。
  - 缺口 3（中）：Icy Blast 持续区域越积越多，靠 `MasterlessAvoidAoe=1` 识别 dynobject（待实测）；现有的远程 10 码散开会和躲地面互相拉扯。
  - 缺口 4（小）：Unholy Power 期间坦克减伤/风筝无专门处理。

---

## 4. mod-raidtest 能力对照

| 需求 | 现有键 | 在 PoS 上是否可用 | 缺什么 |
|---|---|---|---|
| 坦克正常拉怪 | `EngageTrigger=pull` | Garfrost、Ick 可用 | — |
| 进度门禁夹具 | `FixtureInstanceData=<id>:<value>`（`SetData`） | 可用：Ick `4:1`，Tyrannus `0:3,1:3,4:5` | — |
| boss 状态键 | `EngageConfirmBossState`、`FixtureBossStates`、`EventCompletionBossState` | **无效**（本副本不用 BossState） | 用 `*InstanceData` 版本 |
| AreaTrigger 开战 | `EngageTrigger=areatrigger` + `EngageAreaTrigger=5633` | 包能发、条件可由夹具满足 | 见下一行 |
| 载具乘客 boss 寻址/恢复 | `BossSpawnMode=script`（仅限 pull + 前置） | **不可用**（Tyrannus） | 允许 script 模式配 areatrigger；恢复 Rimefang 202135；击杀后换实例 |
| 开战确认 | `EngageConfirmInstanceData`、`boss_in_combat` 回退 | Tyrannus 只能用 `boss_in_combat`（120 秒预算够） | — |
| 多 AT 顺序推进（gauntlet） | 无 | — | 链式 Tyrannus 需要，暂不做 |
| 剧情 NPC | `EventStarterEntry` | 不需要（开场剧情自动播放；且该键要求 starter 就是 boss、走 escort 与 BossState） | — |
| 移除夹具 / 前置 / 准备点 | `FixtureDespawnSpawns`、`PrerequisiteSpawns`、`Preparation*` | 可用 | — |

## 5. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| Forgemaster Garfrost | `heroic-pos-garfrost-h5g` | 完整（带 6 只 Siegesmith） | 待建 | 无（bot：石头 LOS 缺失，影响待量） | 实测准备点与巡逻相位 → 首轮基线，统计 Permafrost 层数与远程死亡 |
| Ick & Krick | `heroic-pos-ick-h5g` | 隔离（progress 夹具 + Horror 前置/移除） | 待建 | 无 | 先确认 `GetData(4)`，配 `FixtureInstanceData=4:1` → 实测坦克点 → 首轮基线 |
| Scourgelord Tyrannus | `heroic-pos-tyrannus-h5g` | 隔离（跳过 gauntlet：`0:3,1:3,4:5` + AT 5633） | 待建 | 框架：载具乘客 boss 的寻址与恢复（中）；bot：Overlord's Brand（大）、Hoarfrost（中） | 框架放开 script+areatrigger 并恢复 Rimefang → 首轮基线 |

共用事实：instance 不用 BossState（所有 `*BossState` 键失效，用 `*InstanceData`）；Ick 需要 progress≥1，Tyrannus 需要 Garfrost/Ick DONE + progress≥5 + AT 5633；三只都用自定义「victim 出区回满血 evade」而非 boundary；Garfrost 是巡逻 + 6 只编队小怪；Krick、Tyrannus 都是载具乘客；策略 `wotlk-pos` 由 map 658 自动挂载，Garfrost 无策略，Ick 覆盖较全，Tyrannus 只有远程散开。
