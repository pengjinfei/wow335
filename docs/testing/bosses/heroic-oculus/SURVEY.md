# 英雄魔环（The Oculus，map 578）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `src/server/scripts/Northrend/Nexus/Oculus/`、mod-playerbots `src/Ai/Dungeon/OC/`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp`）、world DB（`acore_world`）和客户端 DBC（`data/world/dbc/Spell.dbc`、`SpellRadius.dbc`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**；三个浮空平台（Varos 中心台、Urom 三个外环台和内环台）**能否步行、导航网格是否存在也都待实测**。
> 下文源码路径缩写：`OC/` = `azerothcore-wotlk/src/server/scripts/Northrend/Nexus/Oculus/`，`PB/` = `azerothcore-wotlk/modules/mod-playerbots/src/Ai/Dungeon/OC/`，`RT/` = `azerothcore-wotlk/modules/mod-raidtest/src/`。

## 0. 总览

| boss | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 设计上的战斗形态 | 门禁 | 建议 |
|---|---|---|---|---|---|---|---|---|
| Drakos the Interrogator | 27654 | 31558 | 100172 | (947.79, 1045.80, 360.05, 0.31) | 否（0 / 1） | **地面** | 无 | **现有键可建**（`pull`） |
| Varos Cloudstrider | 27447 | 31559 | 100235 | (1285.60, 1070.36, 439.52, 3.58) | 否（0 / 1） | **龙背**（设计）；boss 本身不会飞 | 10 只 Centrifuge Construct 死亡（`CentrifugeCount≥10`）才去掉 `NON_ATTACKABLE` 和 50053 护盾 | 地面形态：**现有键可拼**（`FixtureInstanceData` 10 次 `5:3`），但平台可达性待实测、结论须降级；龙背形态：**大工程** |
| Mage-Lord Urom | 27655 | 31560 | 100220 | (1177.47, 937.72, 527.41, 2.22)（外环 1 号台） | 否（0 / 1） | **地面**（龙只用来在平台间飞） | Varos DONE 才可攻击；本体战前要走 3 个外环台（每台召 4 只幻象怪，然后传走） | 隔离：**现有键可拼但有风险**（召第二只 Urom 到内环台），更稳的是**小框架改动**（把 DB Urom 传送到内环台）；链式：大 |
| Ley-Guardian Eregos | 27656 | 31561 | 1971378 | (1077.04, 1086.21, 655.50, 4.19)，**飞行 + 随机游荡 50 码** | 否（0 / 1） | **只能龙背** | Urom DONE 才可攻击 | **大工程**（bot 骑龙/飞行在无 master 下完全不工作） |

- HARD_RESET 判定读普通 entry（`GetEntry()`）：四个普通 entry `flags_extra` 都是 0，英雄 entry 都是 1（INSTANCE_BIND），**都没有 0x80000000**。
- 四只 boss 的普通 entry `unit_flags=32768`；Varos/Urom/Eregos 的「不可攻击」全部是脚本在 `Reset()` 里按 instance 数据动态加的（见各节）。
- 副本共 125 条 `creature` 记录，全部 spawnMask 3。
- **进入要求**：`dungeon_access_template` id 73（普通，min_level 75）/ id 74（英雄，min_level 80、`min_avg_item_level=180`）；`dungeon_access_requirements` 对 73/74 **没有任何行**（无钥匙/任务/成就要求）。ilvl 200 档满足。入口 AT 5246 → (1055.93, 986.85, 361.07, 5.745)。`instance_template.allowMount=1`。

### 0.1 instance 脚本（OC/instance_oculus.cpp）——对框架最关键的几点

- **没有 `SetBossNumber`，也不用 `SetBossState`**（`Initialize()` 只清数组，`OC/instance_oculus.cpp:55-64`）。进度放在 `m_auiEncounter[4]`，全部走 `SetData/GetData`（`:136-225`）。枚举（`OC/oculus.h:32-46`）：
  - `DATA_DRAKOS=0`、`DATA_VAROS=1`、`DATA_UROM=2`、`DATA_EREGOS=3`（值为 EncounterState：0 NOT_STARTED / 1 IN_PROGRESS / 3 DONE）；
  - `DATA_CC_COUNT=5`、`DATA_AMBER_VOID=6`、`DATA_EMERALD_VOID=7`、`DATA_RUBY_VOID=8`（成就用）。
  - 因此 `GetBossState()` 永远 TO_BE_DECIDED（`InstanceScript.h:252`），`IsEncounterInProgress()` 永远 false（`InstanceScript.cpp:147-153`，遍历空 `bosses`）。**`FixtureBossStates` / `EngageConfirmBossState` / `EventCompletionBossState` 全部无效**，一律用 `FixtureInstanceData` / `EngageConfirmInstanceData`。
- **各 `SetData` 的副作用**：
  - `SetData(0, DONE)`：显示离心构造体计数世界状态；英雄开启 Make It Count 计时成就（`:140-150`）。**开龙笼门和三位给龙 NPC 走位不在这里**，在 Drakos 的 `JustDied`（`OC/boss_drakos.cpp:97-113`）和给龙 NPC 自己的 `UpdateAI`（`OC/oculus.cpp:105-160`，读 `GetData(DATA_DRAKOS)==DONE`）。
  - `SetData(1, DONE)`：隐藏计数，并**直接去掉 Urom 的 `UNIT_FLAG_NON_ATTACKABLE`**（`:151-160`）。
  - `SetData(2, DONE)`：**直接去掉 Eregos 的 `NON_ATTACKABLE`**（`:161-166`）。
  - `SetData(3, DONE)`：刷出 Cache of Eregos（`:167-181`）。
  - **`SetData(5, x)` 不看 x 的值，每调一次计数 +1**（上限 10）；到 10 时去掉 Varos 的 `NON_ATTACKABLE`、打断施法、移除 50053（`:182-195`）。计数也由 `OnUnitDeath` 在 Centrifuge Construct 27641 死亡时 +1（`:130-134`）——**`DespawnOrUnsummon` 不会触发，`FixtureDespawnSpawns` 删构造体不算数**。
  - 只有 `data == DONE(3)` 时才 `SaveToDB()`（`:207-208`）。所以 CC 计数夹具要写成 `5:3`，才会被存档。
- 存档格式：`m_auiEncounter[0..3]` + `CentrifugeCount`（`:248-264`）。
- **没有 boss boundary、没有门**（只有 3 个 Dragon Cage Door 193995，guid 3586/3953/4314，关着三位给龙 NPC）。隔离场景直接传送，不受影响。
- **没有 AreaTrigger 脚本**（`areatrigger_scripts` 对 578 无行）。

### 0.2 mod-playerbots 策略（PB/）

- context key 与 `getName()` 都是 **`wotlk-occ`**（`DungeonStrategyContext.h:59,83`，`PB/OCStrategy.h:16`）。`PlayerbotAI.cpp:1733-1735` 在 `case 578` 自动挂载。**注意是 `occ` 不是 `oc`**，场景 `Strategy = wotlk-occ`。
- 全部内容（`PB/OCStrategy.cpp:10-47`）：

| 对象 | trigger → action（优先级） | 说明 |
|---|---|---|
| Drakos | `unstable sphere` → `avoid unstable sphere`（MOVE+5） | 非坦克；只躲**已停下**的 Unstable Sphere，12+1 码，每次最多退 3 码（`PB/OCActions.cpp:12-40`，`PB/OCTriggers.cpp:13-30`） |
| 龙 | `drake mount` → `mount drake`（RAID+5） | **只在 `master` 骑龙且自己没骑时触发**（`PB/OCTriggers.cpp:32-38`）；动作按 2/2/1（琥珀/翡翠/红玉）分配，`AddItem` 精华并 `UseItemAuto`（`PB/OCActions.cpp:43-116`） |
| 龙 | `drake dismount` → `dismount drake` | master 下龙则跟着下（`PB/OCTriggers.cpp:40-46`） |
| 龙 | `group flying` → `occ fly drake`（NORMAL+1） | **要求 master 在龙上**；Eregos 在场且无 Planar Shift 时飞到 55 码内并面向他，否则跟随 master 的龙呈 3/4 圆编队（`PB/OCActions.cpp:128-167`） |
| 龙 | `drake combat` → `occ drake attack`（NORMAL+5） | 不要求 master；按龙种放技能：琥珀叠 Shock Charge/Shock Lance、对激怒的目标放 Stop Time、Temporal Rift；翡翠 Leeching Poison / Touch the Nightmare / Dream Funnel 治队友龙；红玉 Searing Wrath / Evasive Maneuvers / Martyr（`PB/OCActions.cpp:169-326`） |
| Varos | 无（`varos cloudstrider` trigger 注释掉，作者写「无法识别被标记的核心」，`PB/OCStrategy.cpp:27-30`） | — |
| Urom | `arcane explosion` → `avoid arcane explosion`（MOVE+5）；`time bomb` → `time bomb spread`（MOVE+4） | 爆炸读条时去 3 个硬编码安全点之一（`PB/OCActions.h:16-21`：(1138.88,1052.22,508.36)、(1084.62,1079.71,508.36)、(1087.42,1020.13,508.36)）；中 Time Bomb 离队友 12 码 |
| Eregos | 无 trigger | — |

- Multiplier（`PB/OCMultipliers.cpp`）：`MountingDrakeMultiplier`（master 在龙上而自己没上时除上龙外全部置 0）、`OccFlyingMultiplier`（**在载具上时除 `OccFlyDrakeAction` 外所有 MovementAction 置 0**）、`UromMultiplier`（按 bot 自己的位置判断阶段，离三个外环台任一 <60 码时不打 Urom；爆炸读条时只留躲爆炸；近战不躲 AoE；中 Time Bomb 时只留散开）、`EregosMultiplier`（Planar Shift 期间停龙攻击）。
- **关键结论：raidtest 队伍全是无 master 的 bot**（`RT/Bot/RosterLogin.cpp:153-172` 的 masterless 补丁）。`drake mount` / `drake dismount` / `group flying` 三个 trigger 在 `GetMaster()==nullptr` 时恒 false，所以**现状下 bot 永远不会上龙，即使被塞上龙也不会飞**（`OccFlyingMultiplier` 还会把其它移动全部压成 0，龙原地不动）。只有 `drake combat` 在无 master 时仍可工作。
- mod-playerbots 的通用层没有载具支持；上载具的代码都是各副本自己写的（`TOC/TOCActions.cpp:218` `ToCMountAction::EnterVehicle`、`ICC/Action/ICCActions_GSB.cpp:154`、`Uld/UldActions.h:43` 等），`PlayerbotAI::CanCastVehicleSpell/CastVehicleSpell`（`Bot/PlayerbotAI.h:536-538`）是通用的载具施法入口。

### 0.3 龙（载具）脚本要点（OC/oculus.cpp）

- 三条龙：Emerald 27692 / Amber 27755 / Ruby 27756，VehicleId 70，`npc_oculus_drake`（VehicleAI）。由精华物品召唤：Emerald Essence 37815（法术 49345）、Amber 37859（49461）、Ruby 37860（49462），物品 `Map=578`、`maxcount=1`、冷却 15 秒、持续 7200 秒。
- 给龙 NPC Verdisa 27657 / Belgaristrasz 27658 / Eternos 27659（guid 100222/100224/100225）：**只有 `GetData(DATA_DRAKOS)==DONE` 才出正常 gossip**（`OC/oculus.cpp:166-171`），`StoreEssence/RemoveEssence` 发/收精华（`:219-235`）。
- 龙召出后 **5 秒内没人上就飞走消失**（`:458-472`）；乘客下龙也消失（`:378-398`）。
- 龙 `UpdateAI` 首帧：`!IsEncounterInProgress() || GetData(EREGOS)==IN_PROGRESS` 才留下，否则立刻飞走（`:420-455`）。因为本 instance 没有 boss 向量，`IsEncounterInProgress()` 恒 false，**任何时候都能召龙**。`GetData(DATA_UROM)==DONE` 时补上第 6 个技能（Dream Funnel 50344 / Temporal Rift 49592 / Martyr 50253，`:427-440`）。
- `IsSummonedBy` 里「Eregos 战斗中召龙就让 Eregos 消失」的防刷判断用的是 `GetBossState(DATA_EREGOS)`（`:347-349`），**恒为 TO_BE_DECIDED，永不触发**。
- **高风险点（源码推断，待实测）**：`SpellHitTarget`（`:400-411`）——龙的技能（`m_spells[0..7]`）命中一个**活着、`!CanFly()`、敌对**、且非区域目标法术的目标时，**直接杀死骑手**。`Creature::CanFly()` = 移动模板允许飞行 或 当前正在飞（`Creature.h:87`）。Varos 27447、Centrifuge Construct 27641 在 `creature_template_movement` **都没有行**（默认不能飞），而龙的单体技能 Shock Lance 49840、Leeching Poison 50328、Touch the Nightmare 50341、Searing Wrath 50232、Temporal Rift 49592 在 DBC 里都是 `TARGET_UNIT_TARGET_ENEMY(6)` 单体（Stop Time 49838、Martyr 50253 是区域/自身）。按字面读，**在本核心上骑龙打 Varos 或构造体会把骑手秒杀**。Eregos 31561/27656、Greater Ley-Whelp 28276、Azure Ring Guardian 27638 的 `Flight=1`，不受影响。这点决定 Varos 的龙背形态是否可行，建场景前要先用 GM 真人验证一次。

---

## 1. Drakos the Interrogator（27654 / 31558）

### 1.1 脚本（OC/boss_drakos.cpp）

- ScriptedAI。`MoveInLineOfSight` 为空（`:120`）——**不会因接近而自动进战**，只能主动拉。
- `Reset()`：`SetData(DATA_DRAKOS, NOT_STARTED)`（`:75-81`）。没有任何门禁。
- `JustEngagedWith`：`SetData(0, IN_PROGRESS)`、`SetInCombatWithZone()`；Magic Pull 10–15 秒首发、Thundering Stomp 3–6 秒、召球 2 秒（`:83-95`）。
- 技能：
  - **召 Unstable Sphere 28166**：每 2 秒在自己 5 码内召 2 个（`:157-166`）；Magic Pull 后 1.5 秒再召 4 个（`:167-174`）。球 18 秒后消失，`REACT_PASSIVE`，在以 **(961.29, 1049.0, 360.0) 为圆心、40 码半径**内随机游走，10 秒后停下，此后每 2 秒放 Unstable Sphere Pulse 50757（`:197-250`）。场上稳定会有 ~18 个球。
  - **Magic Pull 51336**：每 15–25 秒，DBC 半径 99，把全场拉到身边（`:139-148`）。
  - **Thundering Stomp 50774**：每 10–20 秒，DBC 半径 60，伤害 + 击退（效果 98）（`:149-156`）。
- `JustDied`：`SetData(0, DONE)` 并打开三个龙笼门（`:97-113`）。不是 HARD_RESET。

### 1.2 附近的怪

Drakos 所在的底层大厅（z≈360）**90 码内除了三位友方给龙 NPC（15–22 码）没有任何敌对怪**。最近的敌对：Azure Spellbinder 100420 (1050.0, 1108.0, 361.2) 119.7 码、Azure Inquisitor 100413/100412 约 125–129 码，Azure Ring Guardian 101848（随机游荡，z392.9）126 码。Crystal Spider 32261 是小动物（type 8，faction 190）。入口 (1055.93, 986.85) 离 Drakos 约 123 码。

### 1.3 场景建议

- **框架**：无阻塞，现有键即可。`MapId=578`、`BossEntry=27654`、`Strategy=wotlk-occ`、`EngageTrigger=pull`、`EngageConfirmInstanceData=0:1`（可选，`boss_in_combat` 回退也够）。
- 准备点候选 **(985.0, 1045.0, 360.0)**（Drakos 东约 37 码，在球的活动圆内侧边缘，待实测）。更保守可放在球圆外 **(1005.0, 1045.0, 360.5)**（离球圆心 44 码，待实测）。Magic Pull 99 码，站位远近不影响开战后的聚拢。
- 注意：击退 60 码范围 + 99 码拉人会让 bot 频繁换位，首轮日志要看有没有被踩出大厅（大厅边界和掉落待实测）。
- bot 缺口：
  - 缺口 1（小）：躲球只躲停下的球，且近战/坦克不躲（作者注释：躲了更乱）。ilvl 200 下大概率直接扛过。
  - 缺口 2（小）：Stomp 击退后的回位靠通用追击。
- **结论：现有键可建，建议第一个做**，先测基线。

---

## 2. Varos Cloudstrider（27447 / 31559）

### 2.1 脚本（OC/boss_varos.cpp）

- **门禁**：`Reset()` 里 `GetData(DATA_CC_COUNT) < 10` 时加 `UNIT_FLAG_NON_ATTACKABLE` 并自挂 **Centrifuge Shield 50053**（DBC：效果 6+3，免疫类），否则移除（`:92-115`）。计数到 10 时 instance 也会主动移除（`OC/instance_oculus.cpp:188-194`）。
- **Centrifuge Construct 27641 / 30905**：10 只（guid 101917/101918/101919/101922/101924/101933/101937/101967/101974/102064），分三组在外环（z432.96 或 z439.52），离 Varos 150–290 码，**不在 Varos 的平台上**。脚本 `npc_centrifuge_construct`：进战放 Empowering Blows 50044，被龙打时把龙的骑手拉进战斗（`OC/oculus.cpp:479-517`）。
- `JustEngagedWith`：`SetData(1, IN_PROGRESS)`、`SetInCombatWithZone()`；Amplify Magic 5–10 秒首发，召 Azure Ring Captain 5 秒首发，Energize Cores 立即开始（`:117-129`）。
- 技能：
  - **Energize Cores**：61407（瞄准）→ 4.5 秒后 root 自己、朝固定角度放 **50785**（DBC：`TARGET_UNIT_CONE_ENEMY_54`，半径 100，伤害）→ 角度 +90° → 2 秒后下一轮（`:218-240`）。即每 6.5 秒扫一个象限的锥形，**起始角 6.20，顺序固定**。8 个 Centrifuge Core 28183（NullCreatureAI，不可选中）在平台上 43 码一圈（guid 100227–100234，z439.2），只做视觉。
  - **Call Azure Ring Captain**：每 16 秒轮换 51002/51006/51007/51008，并在 100 码内随机玩家脚下召 **Arcane Beam 28239**（13 秒，跟随该玩家，周期伤害 51019），由 Azure Ring Captain 28236（无 DB spawn，法术召出，`Flight=1`）打光束视觉（`:175-217`）。
  - **Amplify Magic 51054**：每 17.5–22.5 秒，50 码内随机目标（`:168-174`）。
  - 近战：`DoMeleeAttackIfReady()`。
- `JustDied`：`SetData(1, DONE)`，在尸体处召 Image of Belgaristrasz 28012（剧情）（`:131-140`）。`EnterEvadeMode` 只是解 root（`:142-147`）。不是 HARD_RESET。

### 2.2 平台与附近的怪

- Varos 平台：Varos 在 (1285.6, 1070.4, 439.5)，8 个 Core 在 43 码圈 z439.2——推测平台半径 ≥ 43 码且 z≈439，**是否有导航网格、能否站人待实测**。设计上玩家骑龙绕平台飞，不落地。
- 平台 80 码内只有 Azure Ring Guardian 27638（`Flight=1`，随机游荡）：100932 (1268.6, 1040.8, 487.7) 34 码（高 48 码）、101882 64 码、101892 65 码（下方 60 码）、101893 68 码、101498 74 码、101874 80 码。它们高度差大，是否会被 `SetInCombatWithZone` 或巡游卷进来待实测。

### 2.3 场景建议

- **门禁夹具（现有键能表达）**：`FixtureInstanceData = 5:3,5:3,5:3,5:3,5:3,5:3,5:3,5:3,5:3,5:3`（10 次，每次 +1；`RT/Scenario/Scenario.cpp:523-537` 不去重，`RT/Orchestrator/AttemptRunner.cpp:809-811` 逐条 `SetData`）。可加 `0:3` 让 Drakos 记为 DONE（不影响 Varos 本身，只是和真实进度一致）。**构造体用 `FixtureDespawnSpawns` 删除不计数**，别用。
- **形态 A：地面（非设计形态）**。bot 直接传送到 Varos 平台，`EngageTrigger=pull`、`BossEntry=27447`、`EngageConfirmInstanceData=1:1`。准备点候选 **(1255.0, 1070.0, 439.5)**（Varos 西 30 码、在 Core 圈内，待实测）。风险：
  - 平台能否步行、边缘掉落（参见 memory「bot 掉出平台」），首轮必须先 los + 地面高度两遍法。
  - Energize Cores 是 100 码锥形、按固定象限旋转；bot **没有**任何躲锥逻辑（trigger 被注释），近战和坦克会被周期扫中。Arcane Beam 跟人 13 秒，靠通用 avoid aoe 能否识别（它是跟随型 NPC + 周期光环，不是 dynobject）待实测。
  - 结论口径：**「隔离 + 地面非设计形态」**，只能说明 bot 能在地面打过 Varos 的技能组，不能算按设计通关。
- **形态 B：龙背（设计形态）——大工程**：
  1. 先确认 §0.3 的「龙技能打不会飞的目标会秒骑手」是否属实；若属实，Varos 龙背战在本核心上本身就打不了，要先在核心 fork 修（memory「服务端缺陷在核心 fork 修」）。
  2. 无 master 的上龙、飞行编队、绕 Varos 飞/躲锥全都要在 playerbots 里重写（见 §4）。
- **建议**：先做形态 A 的平台可达性实测（只读 los/高度），可达就建 `heroic-oc-varos-h5g`（地面、隔离），结论标降级；形态 B 挂起，记为大改待确认。

---

## 3. Mage-Lord Urom（27655 / 31560）

### 3.1 脚本（OC/boss_urom.cpp）

- **门禁**：`Reset()`：`GetData(DATA_VAROS) != DONE` 时加 `NON_ATTACKABLE`；自挂 Evocation 51602（`:122-142`）。Varos DONE 时 instance 也会主动移除（`OC/instance_oculus.cpp:151-160`）。
- **四个位置**（`:78-88`，与 `spell_target_position` 一致）：
  | 阶段 | 坐标 | 说明 |
  |---|---|---|
  | 0 | (1177.47, 937.72, 527.41) | DB spawn，外环 1 号台 |
  | 1 | (968.66, 1042.53, 527.32) | 外环 2 号台（Summon Menagerie 50476 的传送目标） |
  | 2 | (1164.02, 1170.85, 527.32) | 外环 3 号台（50495 的目标） |
  | 3 | (1118.31, 1080.38, 508.36) | **内环，本体战**（50496 的目标） |
  `GetPhaseByCurrentPosition()` 按离哪个点 <20 码判定，都不近时返回 0（`:113-120`）。
- **开战流程**（`:144-189`）：
  - 阶段 0/1/2：`lock=true`，读条 Summon Menagerie（DBC：效果 5 TELEPORT_UNITS，目标 `spell_target_position`）。`SpellHit` 时在**当前台**召 4 只幻象怪（300 秒，`SetInCombatWithZone` 后自选目标）、把 home 设到下一台、对可见玩家销毁自己、脱战、重新 Evocation，5 秒后解锁（`:241-280`，`:309-323`）。阶段 0 召 Air×2 + Water + Fire，阶段 1 召 Ogre×2 + Naga + Murloc，阶段 2 召 Cloudscraper×2 + Mammoth + Wolf（`:71-76`）。
  - 阶段 3：`SetData(2, IN_PROGRESS)`、`SetInCombatWithZone()`、**home 重设回阶段 0 台**（`:158`），Frostbomb 7–11 秒、传中心 30–35 秒、Time Bomb 20–25 秒。
- `AttackStart` 只在离 (1103, 1049, 510) <55 码时生效（`:191-198`）——外环台上他从不追人。
- 技能（阶段 3）：
  - **Frostbomb 51103**：打 victim，每 7–11 秒；DBC 半径 15 的地面区域（`:339-343`）。
  - **Time Bomb 51121 / 英雄 59376**：100 码内随机目标，每 20–25 秒（`:344-348`），到时爆炸（按 bot 策略的假设是 10 码波及）。
  - **传中心 + Empowered Arcane Explosion 51110 / 英雄 59377**：每 25–30 秒，`SPELL_TELEPORT 51112` 到 (1103.69, 1048.76, 512.28) 浮空、root、不可攻击，读条爆炸（DBC 半径 99，英雄 11000 基础伤害），英雄 7 秒后传回原位（`:281-299`，`:349-367`）。99 码意味着**跑不出范围，只能靠视线遮挡**——bot 的 3 个安全点就是按这个假设写的。
- `EnterEvadeMode`：`lock` 期间不 evade；否则解飞行/root 后走基类 evade（`:371-382`）。**因为阶段 3 把 home 设回了阶段 0 台，团灭后 Urom 会回外环 1 号台，下一次还得从头走 3 个台**。
- `JustDied`：`SetData(2, DONE)`；如果死在中心浮空处，尸体传回原位（`:219-234`）。不是 HARD_RESET。

### 3.2 附近的怪

- 三个外环台和内环台 60 码内**都没有 DB 敌对怪**，只有小动物 Crystal Spider。Azure Ring Guardian（`Flight=1`、随机游荡）最近 101835 (1186.0, 1058.6, 556.7) 离内环中心 84 码，高 48 码。
- 幻象怪全是 Urom 召出的（300 秒 TempSummon），每个外环台一组 4 只。

### 3.3 场景建议

- **进度夹具**：`FixtureInstanceData = 0:3,1:3`（Drakos、Varos DONE；`1:3` 会直接去掉 Urom 的 `NON_ATTACKABLE`，之后每次 `Reset()` 也会读到 Varos DONE）。
- **隔离本体战**（跳过 3 个外环台）有两条路：
  - **路 1（现有键可拼，风险中）**：仿净化斯坦索姆 Mal'Ganis（`env/dist/etc/modules/mod-raidtest-scenario-heroic-cos-malganis-h5g.conf`）：`BossSpawnMode=script`、`FixtureDespawnSpawns=100220`、`FixtureSummonCreature = 27655:1118.31,1080.38,508.36,4.25`、`EngageTrigger=pull`、`EngageConfirmInstanceData=2:1`。召出的 Urom 在内环点 <20 码，判定为阶段 3，直接进本体战。夹具顺序是先 `FixtureInstanceData` 后 `FixtureSummonCreature`（`RT/Orchestrator/AttemptRunner.cpp:800-866`），所以召出时的 `Reset()` 已能看到 Varos DONE。风险：① 召出的 Urom 团灭后 home 是外环 1 号台，会尝试飞回去，下次 attempt 场上可能残留一只非阶段 3 的 Urom，script 模式可能绑错（`FindBossNear`，待实测）；② instance 的 `uiUromGUID` 会被新召出的覆盖（`OC/instance_oculus.cpp:76-78`），对击杀判定无害；③ TempSummon 与 DB spawn 的区别（死亡不留存档以外的副作用）。
  - **路 2（小框架改动，推荐）**：新增一个夹具键，比如 `FixtureTeleportBoss = x,y,z,o`：在 attempt 开始时对绑定的 DB boss 做 `NearTeleportTo` + `SetHomePosition`。Urom 在内环点就会被判为阶段 3，团灭 evade 回到外环 1 号台后，下一次 attempt 再传一次即可。比路 1 少掉「多只同 entry」的问题。
- 准备点候选：内环三个 bot 安全点之一 **(1138.88, 1052.22, 508.36)**（离内环 boss 点 35 码，待实测）。内环是否为连续地面、有没有导航网格待实测。
- **链式（走 3 个外环台）——大**：bot 需要在外环台之间飞（原设计骑龙），或框架每阶段把全队传送到下一台（新的「分阶段传送」能力）；每台还要清 4 只幻象怪。暂不做。
- bot 缺口：
  - 缺口 1（中）：爆炸安全点是硬编码的 3 个点，是否真的挡视线待 `raidtest los` 从 (1103.69, 1048.76, 512.28) 实测；`UromMultiplier` 在读条期间压掉其它移动，bot 若到不了安全点会原地吃满 99 码爆炸（英雄 11000 基础）。
  - 缺口 2（小）：Time Bomb 散开 12 码，Frostbomb 近战不躲。
  - 缺口 3（小）：`UromMultiplier::GetPhaseByCurrentPosition` 以 bot 自己离外环台 <60 码为「非本体阶段」，内环点离外环 3 号台约 102 码、离 2 号台约 155 码，不会误判；但如果准备点放偏到外环附近会导致 bot 不打 Urom。
- **结论：路 1 现有键可试，但更稳的是路 2 的小框架改动**；两者都是隔离形态。

---

## 4. Ley-Guardian Eregos（27656 / 31561）

### 4.1 脚本（OC/boss_eregos.cpp）

- **位置**：DB spawn 1971378 (1077.04, 1086.21, 655.50)，`MovementType=1` 随机游荡 50 码，`creature_template_movement` Ground/Swim/**Flight=1**，`creature_template_addon.bytes1=50331648`（悬停/飞行动画）。最近的落脚点是 Cache of Eregos 所在的高台 (1015.06, 1051.09, 605.62)，比他低 50 码。**地面近战完全够不着，远程 40 码大概率也够不着（待实测）**。
- **门禁**：`Reset()`：`GetData(DATA_UROM) != DONE` 时加 `NON_ATTACKABLE`（`:86-98`）。Urom DONE 时 instance 主动移除（`OC/instance_oculus.cpp:161-166`）。
- `JustEngagedWith`：`SetData(3, IN_PROGRESS)`，按 750 码内有没有各色龙记三个「Void」成就数据，`SetInCombatWithZone()`；Arcane Barrage 立即、Arcane Volley 5 秒、Enraged Assault 35 秒、召幼龙 40 秒（`:100-132`）。
- 技能：
  - **Arcane Barrage 50804**：打 victim，每 2.5 秒（`:190-194`）。
  - **Arcane Volley 51153**：全场，每 8 秒（`:195-198`）。
  - **Enraged Assault 51170**：每 35 秒自身激怒（`:199-203`）——琥珀龙的 Stop Time 用来对付它。
  - **召 Greater Ley-Whelp 28276**：每 40 秒 5 只，在自己 ±25 码立方体内随机点（**含 z**），`DoZoneInCombat(300)`（`:204-216`，`:163-169`）。
  - **Planar Shift 51162（仅英雄）**：血量 ≤60% 和 ≤20% 各一次，自身免疫 + 召 3 个 Planar Anomaly 30879（飞行，追随机玩家，15 秒后 Planar Blast）（`:144-154`，`:217-238`）。
  - 有 Planar Shift 或 Stop Time 光环时整个 `UpdateAI` 跳过（`:176-177`）。
- `JustDied`：`SetData(3, DONE)`，召 Spotlight GO（`:134-142`）。不是 HARD_RESET。

### 4.2 场景建议

- **只有龙背形态**。需要的东西：
  1. **进度夹具**（现有键）：`FixtureInstanceData = 0:3,1:3,2:3`（`2:3` 去掉 Eregos 的 `NON_ATTACKABLE`，也让龙拿到第 6 个技能）。
  2. **上龙**：给每个 bot 一个精华并使用（或直接召龙 + 上载具）。这在 raidtest 里属于「编排」，可以做成夹具（中）；但 memory「mod-raidtest 框架边界」要求不代写 bot 行为，**更合理的是在 playerbots 里让 `drake mount` 在无 master 时按组内角色自行上龙**。
  3. **飞行**：`OccFlyDrakeAction` 和 `group flying` 都要求 master 在龙上（`PB/OCActions.cpp:128-134`），而 `OccFlyingMultiplier` 会把其它移动全部压成 0。无 master 时龙原地不动，55 码射程内够不着游荡的 Eregos 就完全不打。需要改成以坦克/组长的龙为锚点，或者无 master 时直接以 Eregos 为目标飞近。
  4. **开怪/确认**：`EngageTrigger=pull` 要求坦克能「拉」一只在空中游荡的 boss——骑龙状态下坦克的仇恨动作是龙技能，现有拉怪流程是否适用待确认；`EngageConfirmInstanceData=3:1` 可用。
  5. 结果观察：bot 伤亡实际是龙的伤亡（龙死骑手掉落），观察器口径要跟着改。
- **结论：大工程**，属于「大改的 boss 先跳过记下待确认」（memory「不停推进 boss/副本」）。

---

## 5. mod-raidtest 能力对照

| 需求 | 现有键 | 在 Oculus 上是否可用 | 缺什么 |
|---|---|---|---|
| 坦克正常拉怪 | `EngageTrigger=pull` | Drakos、Varos（地面）、Urom（内环）可用 | Eregos 在龙背上，不适用 |
| 进度门禁夹具 | `FixtureInstanceData=<id>:<value>`（`SetData`） | 可用：Varos `5:3`×10；Urom `1:3`；Eregos `2:3` | — |
| boss 状态键 | `FixtureBossStates`、`EngageConfirmBossState`、`EventCompletionBossState` | **无效**（本副本没有 BossState） | 用 `*InstanceData` 版本 |
| 开战确认 | `EngageConfirmInstanceData` | `0:1` / `1:1` / `2:1`（仅阶段 3 写）/ `3:1` | — |
| 移除构造体计数 | `FixtureDespawnSpawns` | **不计数**（`OnUnitDeath` 不触发） | 用 `5:3`×10 |
| boss 直接放到本体阶段 | `FixtureSummonCreature` + `BossSpawnMode=script` | Urom 可拼（路 1），有残留/绑错风险 | 推荐新增 `FixtureTeleportBoss`（小） |
| 分阶段整队传送（Urom 链式） | 无 | — | 大，暂不做 |
| bot 上载具 / 骑龙飞行 | 无 | Varos（设计形态）、Eregos 需要 | 大：playerbots 无 master 骑龙 + 飞行；raidtest 可能要发精华 |
| AreaTrigger / GO / 剧情 NPC | `areatrigger` / `gameobject` / `EventStarterEntry` | 不需要 | — |

## 6. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| Drakos the Interrogator | `heroic-oc-drakos-h5g` | 完整（附近无怪） | 待建 | 无 | 实测准备点 → 首轮基线；看击退/拉人后的位置和球伤害 |
| Varos Cloudstrider | `heroic-oc-varos-h5g` | 隔离 + **地面非设计形态**（`5:3`×10） | 待建 | 平台可达性待实测；bot 无躲锥逻辑 | los/高度实测平台 → 可达则首轮基线；龙背形态先验证 §0.3 秒骑手问题，挂起 |
| Mage-Lord Urom | `heroic-oc-urom-h5g` | 隔离（跳过外环 3 台，`0:3,1:3`） | 待建 | 路 1 可试；推荐小框架改动 `FixtureTeleportBoss` | 实测内环地面与爆炸安全点 los → 先试路 1 → 不稳再做路 2 |
| Ley-Guardian Eregos | `heroic-oc-eregos-h5g` | 隔离（`0:3,1:3,2:3`）+ 龙背 | 挂起 | **大**：bot 无 master 骑龙/飞行；上龙编排；龙背拉怪与观察口径 | 记为大改待确认，跳过 |

共用事实：instance 不用 BossState（所有 `*BossState` 键失效，用 `*InstanceData`）；Varos 的门禁是 CC 计数（每次 `SetData(5, ·)` +1，只在值为 3 时存档，删构造体不算数）；Urom/Eregos 的门禁分别是上一只 DONE，instance 会主动去掉 `NON_ATTACKABLE`；四只都不是 HARD_RESET、都没有 boundary；策略 `wotlk-occ` 由 map 578 自动挂载，但骑龙相关 trigger 都依赖 master，在全 bot 队伍里失效；Drakos 是唯一不需要任何改动就能建的 boss。
