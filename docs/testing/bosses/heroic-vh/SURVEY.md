# 英雄紫罗兰监狱（The Violet Hold，map 608）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `src/server/scripts/Northrend/VioletHold/`、mod-playerbots `src/Ai/Dungeon/VH`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp`）和 world DB（`acore_world`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。
> 下文路径简写：`VH/` = `azerothcore-wotlk/src/server/scripts/Northrend/VioletHold/`，`PB/` = `azerothcore-wotlk/modules/mod-playerbots/src/Ai/Dungeon/VH/`，`RT/` = `azerothcore-wotlk/modules/mod-raidtest/src/`。

## 0. 总览

**结论先行：六个牢房 boss 都是 DB spawn、普通 pull 可打，但全都锁在牢房里（`NON_ATTACKABLE` + 不看视野）。只有 instance 私有的 `StartBossEncounter` 能把他们放出来，现有场景键都调不到它。要做一个小的框架改动（两个通用夹具键）才能单独开打。Cyanigosa 是第 18 波由脚本召出来的，没有 DB spawn，工作量大。**

| boss | 普通 entry | 英雄 entry | spawn guid | 牢房内坐标 (x, y, z, o) | 放出后走到 | HARD_RESET | 脚本基类 | 现框架能否单独开战 |
|---|---|---|---|---|---|---|---|---|
| Moragg | 29316 | 31510 | 102384 | (1893.90, 728.13, 47.75, 1.61) | BossStartMove1 (1894.68, 739.39, 47.67) | 否 | BossAI(BOSS_MORAGG=3) | **不能**：放不出来 |
| Erekem（+2 Erekem Guard） | 29315（guard 29395） | 31507（guard 31513） | 102383；guard 102923、102924 | (1871.46, 871.04, 43.42, 5.11)；guard (1892.42, 872.28, 43.42)、(1853.75, 862.45, 43.42) | Erekem→Move2 (1875.17, 860.83, 43.33)；guard→Move21 (1858.85, 855.07)、Move22 (1891.93, 863.39) | 否 | BossAI(4) + ScriptedAI | **不能** |
| Ichoron | 29313 | 31508 | 102352 | (1942.04, 749.52, 30.95, 2.30) | Move3 (1916.14, 778.15, 35.77) | 否 | BossAI(5) | **不能** |
| Lavanthor | 29312 | 31509 | 102351 | (1844.56, 748.71, 38.74, 0.82) | Move4 (1853.62, 758.56, 38.66) | 否 | BossAI(6) | **不能** |
| Xevozz | 29266 | 31511 | 102349 | (1908.42, 845.85, 38.72, 4.85) | Move5 (1906.68, 842.35, 38.64) | 否 | BossAI(7) | **不能** |
| Zuramat the Obliterator | 29314 | 31512 | 102353 | (1934.15, 860.95, 47.30, 3.98) | Move6 (1928.21, 852.86, 47.20) | 否 | BossAI(8) | **不能** |
| Cyanigosa | 31134 | 31506 | **无 DB spawn**（第 18 波由 Sinclari 召出，`TEMPSUMMON_DEAD_DESPAWN`） | 召唤点 (1930.28, 804.41, 52.41)，跳到房间中央 (1892.29, 805.70, 38.44) | — | 否 | BossAI(DATA_CYANIGOSA=2) | **不能**（找不到 boss，也召不出来） |

- 起点坐标：spawn 取自 `creature` 表（spawnMask 3，spawntimesecs 14400）；放出后的目标点是 `VH/violet_hold.h:192-199`（`BossStartMove*`），对应关系在 `VH/instance_violet_hold.cpp:324-337`。
- `flags_extra`：六个普通 entry 和 Cyanigosa 都是 0，英雄 entry 都是 1（INSTANCE_BIND）。**全部不带 HARD_RESET（0x80000000）**。但 evade 的实际效果和 HARD_RESET 差不多，见 §0.3。
- 模板 `unit_flags`：Xevozz / Lavanthor / Ichoron / Zuramat / Cyanigosa 是 514（`NON_ATTACKABLE|IMMUNE_TO_NPC`），Erekem / Moragg 是 33282（多一个 SWIMMING 0x8000），Erekem Guard 是 33536（`IMMUNE_TO_PC|IMMUNE_TO_NPC|SWIMMING`）。英雄 entry 的 `unit_flags` 与普通相同。所有 boss faction 16，rank 1，英雄 HealthModifier 32（Cyanigosa 37.5），DamageModifier 13。
- 副本里只有 39 条 `creature`（全部 spawnMask 3）。**没有静态敌对小怪**：除了 boss 和 guard，只有 Sinclari 30658、4 只 Violet Hold Guard 30659（友方 faction 1718，在门口 x≈1854）、Prison Door Seal 30896、12 只 Defense Dummy Target、若干控制器 / 装饰 NPC（Azure Raider 31118 guid 102908 是 faction 35 的装饰）、小动物。所有敌对小怪都由传送门动态召唤（§0.2）。

### 0.1 instance 脚本（instance_violet_hold.cpp）——对框架最关键的部分

**编号**（`VH/violet_hold.h:126-142`）：`SetBossNumber(MAX_BOSS=9)`（`instance_violet_hold.cpp:77`）。boss 状态槽：`DATA_1ST_BOSS=0`、`DATA_2ND_BOSS=1`、`DATA_CYANIGOSA=2`、`BOSS_MORAGG=3`、`BOSS_EREKEM=4`、`BOSS_ICHORON=5`、`BOSS_LAVANTHOR=6`、`BOSS_XEVOZZ=7`、`BOSS_ZURAMAT=8`。每个 boss 的 BossAI 用自己的槽（3–8），进战置 IN_PROGRESS，死亡置 DONE。

**随机选 boss**（`instance_violet_hold.cpp:405-425`）：
- `EVENT_SUMMON_PORTAL` 每次 `++_waveCount`。第 6 波或第 12 波时，如果两个 persistent data 有任何一个为 0，就 `firstBoss = urand(3, 8)`，`secondBoss` 在 3..8 里重抽直到不同，然后 `StorePersistentData(PERSISTENT_DATA_FIRST_BOSS=0 / SECOND_BOSS=1, …)`（`:415-423`），再在房间中央召一个传送门，传送门召 Azure Saboteur。
- 第 18 波召 Cyanigosa（`:426-435`）。其余波次召普通传送门（`:411-412`）。
- **两个 boss 在第一次到第 6 波时一起定下来，并写进存档**（persistent data 跟 `SaveToDB` 走），之后不再重抽。

**实例数据能不能强制指定某个 boss**：
- `SetData` 只处理 `DATA_PORTAL_LOCATION=34` 和 `DATA_ACHIEV=35`（`:239-250`）。**`FixtureInstanceData` 对选 boss 没有作用**，wave 计数也没有 SetData 入口（`_waveCount` 只有 `GetData(33)` 可读，`:266-267`）。
- 选择结果存放在 persistent data 里。`InstanceScript::StorePersistentData(index, data)` 是 public（`src/server/game/Instances/InstanceScript.h:258`），只是**目前没有任何场景键能调用它**。
- 所以要强制指定 boss，只能用框架调用 `StorePersistentData`；现有配置做不到。

**放出 boss 的方式——instance 的 DoAction，不是 SetData，也不是玩家操作 gameobject**：
1. 第 6/12 波的中央传送门在 3 秒后召 **Azure Saboteur 31079**（`VH/violet_hold.cpp:56-59, 92-95`）。Saboteur 按 persistent data 选路径，走到对应牢房前（`:871-908`），连放 3 次 Shield Disruption 58291，然后 **`_instance->DoAction(ACTION_RELEASE_BOSS=3)`**（`:919-929`）。
2. `DoAction(ACTION_RELEASE_BOSS)`（`instance_violet_hold.cpp:230-235`）：**`_waveCount == 6` 时放 FIRST_BOSS，否则一律放 SECOND_BOSS**，调私有函数 `StartBossEncounter(bossId)`。
3. `StartBossEncounter`（`:284-345`）：`HandleGameObject(对应牢房门, true)` 开门（Erekem 连开两个 guard 门，并给两个 guard 去 `NON_ATTACKABLE`、`SetImmuneToAll(false)`，让他们走到 Move21/22）；boss 走到 `BossStartMove*`，去 `NON_ATTACKABLE`，`SetImmuneToNPC(false)`，`REACT_AGGRESSIVE`。
4. **boss 被放出后不会自己进攻**：7 个 boss 脚本都把 `MoveInLineOfSight` 重写成空函数（例如 `boss_moragg.cpp:72`、`boss_cyanigosa.cpp:131`）。他们走到目标点后原地站着，等玩家先动手。所以放出之后，普通的 `EngageTrigger=pull` 就能开战。
- 牢房门 GO（`gameobject` 表，全部 state 1，即关闭）：Moragg 191606 guid 18129 (1895.07, 733.72, 57.67)；Erekem 191564 guid 16832 (1872.45, 869.00, 47.64)；Erekem Guard 191563 guid 8964 (1892.01, 871.24)、191562 guid 7931 (1854.57, 860.96)；Ichoron 191722 guid 18131 (1938.43, 754.70, 28.78)；Lavanthor 191566 guid 17181 (1847.81, 752.48, 49.30)；Xevozz 191556 guid 5139 (1908.06, 844.89, 41.14)；Zuramat 191565 guid 16846 (1931.87, 859.01, 54.92)。大门 191723 guid 18517 (1822.59, 803.93, 44.36)，state 0（打开）。
- **不能用 `EngageTrigger=gameobject` 去点牢房门**：门只是 `HandleGameObject` 打开的门，没有 gossip 或脚本；就算开了门，boss 也还带着模板里的 `NON_ATTACKABLE`。

**整场事件的入口**：Sinclari 30658（guid 102911，(1830.95, 799.46, 44.42)）走 SmartAI：gossip 菜单 9998 选项 0 → `SMART_ACTION 223` → instance `DoAction(ACTION_START_INSTANCE=1)`（`smart_scripts` entry 30658 id 1；条件：`conditions` 15/9997 要求 instance data 30 == NOT_STARTED）。`DoAction(1)`（`:204-216`）开始后，守卫后撤、召防御系统，4 秒后关大门，再 4 秒后第 1 波（`:357-404`）。之后每一波的触发条件是**上一波的传送门死亡**（`ACTION_PORTAL_DEFEATED` → 3 秒后下一波，`:217-219`；传送门的判定在 `violet_hold.cpp:101-121`）；boss DONE 后 35 秒进下一波（`:157`）。门的血量归零 → `InstanceCleanup` 整场复位（`:220-228`）。

### 0.2 传送门小怪（只在完整链式流程里出现）

- 普通波次每波随机：要么召 Portal Guardian/Keeper（30660/30695/30893）持续引导，再每 20 秒召 3（第 12 波后 4）只 Azure 小怪，直到守门怪死；要么一次召 2（第 12 波后 3）只精英（Captain / Raider / Stalker / Sorceror）（`violet_hold.cpp:56-96`）。
- 小怪按 `violet_hold.h:216-292` 的路径走向大门，到达后对 Prison Door Seal 施 Destroy Door Seal 58040，每跳让门的血量 -1（`violet_hold.cpp:273-278, 963-978`）。
- 隔离的单 boss 场景不会产生传送门，除了下面这一条：**boss DONE 后 35 秒 `EVENT_SUMMON_PORTAL` 仍会执行**（`instance_violet_hold.cpp:157`，`Update` 不检查 `_encounterStatus`），`_waveCount` 0→1，Sinclari 在场就会召一个普通传送门。下一场 attempt 恢复 boss 时 Reset 会触发 `InstanceCleanup`，它会 despawn 传送门和 `_trashMobs`（`:510-517`）。但如果 attempt 间隔超过 35 秒，场上会先出现一波小怪（待实测）。

### 0.3 复位行为（`InstanceCleanup`）——等效于"全体 hard reset"

- 所有 boss 的 `EnterEvadeMode` 都是先 `SetUnitFlag(NON_ATTACKABLE)`，再 `_EnterEvadeMode`（例如 `boss_moragg.cpp:74-78`）。`BossAI::_EnterEvadeMode` 在状态不是 DONE 时 `SetBossState(id, NOT_STARTED)`（`src/server/game/AI/ScriptedAI/ScriptedCreature.cpp:702-710`）。
- VH 的 `SetBossState` 覆盖里，槽 3–8 或 2 置 **FAIL/NOT_STARTED 时直接调 `InstanceCleanup()`**（`instance_violet_hold.cpp:159-163, 178-182`）。前提是状态真的变了，`InstanceScript::SetBossState` 在状态相同时返回 false（`InstanceScript.cpp:415-416`）。
- `InstanceCleanup`（`:480-578`，Cyanigosa 还没 DONE 时）：关掉全部牢房门；**六个 boss 全部 `SetUnitFlag(NON_ATTACKABLE)`、`SetImmuneToNPC(true)`、`DespawnOrUnsummon(0ms, 3s)`**；两个 guard 同样处理并清空 guid；Cyanigosa 直接 despawn；Sinclari、4 个守卫 despawn 后 3 秒重生；传送门和小怪 despawn；`_waveCount` 回到 0/6/12；事件表清空。
- **推论 1**：任何一个 boss 灭团 evade 后，**全部六个 boss 都会在 3 秒内消失再重生**，guid 会变。效果与 HARD_RESET 相同，只是走的不是那个标志。
- **推论 2**：`BossAI::_Reset` 每次都 `SetBossState(_bossId, NOT_STARTED)`（`ScriptedCreature.cpp:660-661`）。**被击杀（DONE）的 boss 由框架 `ResolveOrRestoreSpawn` 重新载入后，Reset 会把 DONE 改成 NOT_STARTED，于是再触发一次 `InstanceCleanup`，把刚恢复的 boss 连同其他人一起再 despawn 3 秒**。`ResetInstance` 的第三趟只读校验（`RT/Orchestrator/AttemptRunner.cpp:1709` 起）很可能因此看到 boss 缺席，判 `scene_invalid`（**待实测**）。可能需要在恢复后等 3 秒再校验，或者把"reset 后等 boss 重新出现"做成通用能力。
- **推论 3**：**VH 场景不能配 `FixtureBossStates`**。把槽 2–8 置 NOT_STARTED/FAIL 会触发整场清理；置 DONE 会让 boss 在 35 秒后开一波传送门。
- 没有 `CheckRequiredBosses` 覆盖，也没有 boss boundary（没有 `LoadBossBoundaries`）。boss 的 evade 由核心的正常脱战规则决定。

### 0.4 进入条件

- `dungeon_access_template`：id 92（普通，min_level 70）、**id 93（英雄，min_level 80，`min_avg_item_level` 180）**。`dungeon_access_requirements` 里没有 92/93 的行，即不需要钥匙、任务或成就。ilvl 200 档装备满足要求。
- `instance_template`：map 608，parent 571，`script = instance_violet_hold`，`allowMount 0`。

### 0.5 mod-playerbots 策略

- context key 与 `getName()` 都是 **`wotlk-vh`**（`azerothcore-wotlk/modules/mod-playerbots/src/Ai/Dungeon/DungeonStrategyContext.h:55`，`PB/VHStrategy.h:16`）。`PlayerbotAI.cpp:1760-1761` 在 `case 608` 自动挂载。RuntimeStrategyName 恒等（`RT/Bot/CombatTrigger.cpp:335-344`）。
- 全部内容（`PB/VHStrategy.cpp:12-48`）：

| boss | trigger → action（优先级） | multiplier |
|---|---|---|
| Erekem | `erekem target`（DPS 且找到 "erekem"）→ `attack erekem`（RAID+1）：DPS 先打 boss，再打 guard（`PB/VHActions.cpp:11-22`） | `ErekemMultiplier`：DPS 的 `DpsAssistAction` 和所有 AoE 动作 → 0（`PB/VHMultipliers.cpp:13-27`） |
| Moragg | **无**（注释写着 TODO Optic Link，`VHStrategy.cpp:19-20`） | 无 |
| Ichoron | `ichoron target`（非治疗）→ `attack ichor globule`（RAID+1）：坦克在 boss 身上没有 Drained 时打 boss；其余人从 `possible targets` 里找 Ichor Globule 29321 打，一次只锁一只，没有球了再回 boss（`PB/VHActions.cpp:24-67`） | `IchoronMultiplier`：Ichoron 在场时，所有人的 DpsAssist / TankAssist / DropTarget → 0 |
| Xevozz | **无**（注释写着 TODO，要求坦克在台阶上来回拉，`VHStrategy.cpp:26-27`） | 无 |
| Lavanthor | 无（注释 tank & spank） | 无 |
| Zuramat | `shroud of darkness`（boss 带 54524/59745）→ `drop target`（HIGH+5）；`void shift`（自己有 Void Shifted 54343 且非治疗）→ `attack void sentry`（RAID+1）：从 `possible targets no los` 找 Void Sentry 29364 打（`PB/VHActions.cpp:69-103`） | `ZuramatMultiplier`：自己带 Void Shifted 时，DpsAssist/TankAssist → 0；boss 带 Shroud 时，所有 `AttackAction` → 0（`PB/VHMultipliers.cpp:43-61`） |
| Cyanigosa | `cyanigosa positioning`（非坦克、非远程 DPS，**也包括治疗**）→ `rear flank`（MOVE+5）（`PB/VHTriggers.cpp:43-51`） | 无 |

---

## 1. Moragg（29316 / 31510）

- **脚本**（`VH/boss_moragg.cpp`）：进战自挂 Ray of Suffering 54442 和 Ray of Pain 54438（`:46-47`）；Corrosive Saliva 54527 打 victim，4–6 秒首发，每 8–10 秒一次（`:56-59`）；**Optic Link 54396**：10–11 秒首发，每 18–21 秒，对 40 码内**最近**的目标施放（`SelectTargetMethod::MinDistance`，`:60-68`）。周期伤害 = 基础值 + **距离 × 25 + 已跳次数 × 100**（`spell_optic_link_aura`，`:85-91`），离得越远、拖得越久伤害越高。
- 机制要求：被 Optic Link 的人靠近 boss 或断视线；治疗要重点奶。由于选的是最近的目标，通常会落在坦克或近战身上。
- 场景：放出点 (1894.68, 739.39, 47.67) 在南侧高台（z 47.7，房间中央 z 38.4），**坦克点候选即放出点前方，待实测**。
- bot 覆盖：无。缺口：Optic Link 没有处理（小–中；落在近战身上时影响不大，落在远程身上时伤害持续增长）。

## 2. Erekem（29315 / 31507）+ 2 × Erekem Guard（29395 / 31513）

- **脚本**（`VH/boss_erekem.cpp`）：进战挂 Earth Shield（每 20 秒补一次）；Chain Heal 0 秒首发，优先给低于 85% 的自己，其次低于 75% 的 guard；**任一 guard 死亡后读条间隔从 8–11 秒缩短到 3–6 秒**（`:92-107`）；Bloodlust 54516 每 35–45 秒；Break Bonds 59463 每 16–22 秒；Earth Shock、Lightning Bolt（35 码随机目标）；**英雄 Stormstrike 51876：两个 guard 都死后每 3 秒一次打 victim**（`:120-128`）。进战时拉两个 guard 一起打（`:72-77`），guard 进战也会拉 boss（`:204-206`）。
- Guard（`:184-243`）：`DoZoneInCombat`，Gushing Wound、Howling Screech、Strike，近战。
- Guard 的 guid 由 `OnCreatureCreate` 按出现顺序记进 `_erekemGuardGuid[0/1]`（`instance_violet_hold.cpp:117-122`），`InstanceCleanup` 会清空（`:551, 558`）。
- 机制要求：打断或驱散 Chain Heal / Earth Shield / Bloodlust，或者先杀 guard；坦克要同时扛三只。
- 场景：boss 放出到 (1875.17, 860.83, 43.33)，两个 guard 走到 (1858.85, 855.07) 和 (1891.93, 863.39)，都在北侧台阶上。**guard 不是 `PrerequisiteSpawns`**（放出前他们不可攻击，放出后与 boss 一起进战），应当作为正常形态的一部分。`KillGateSpawn` 只能填一只，不需要填（击杀判定只看 boss）。
- bot 覆盖：DPS 先打 boss、禁 AoE。缺口：**没有打断和驱散**（`VHStrategy.cpp:15` 注释承认），英雄下 Chain Heal 是否会把战斗拖长待测；先打 boss 的策略在 guard 活着时不会触发 Stormstrike，方向是对的。

## 3. Ichoron（29313 / 31508）

- **脚本**（`VH/boss_ichoron.cpp`）：进战挂 Protective Bubble 54306（`:138`）；Water Bolt Volley 54241 每 10–15 秒。**泡泡被打破时**（`:161-184`）：对全图玩家施 Water Blast 54237，自挂 Drained 59820，变不可选中且隐形，在 5 个固定点（`:28-35`）各召 2 只 **Ichor Globule 29321**（英雄 31515，HealthModifier 0.23），球以 0.3 倍速 `MoveFollow` 向 boss 移动。球碰到 boss（2 码内）→ boss 回 1% 血（`:92-97, 300-309`）；**球被打死 → boss 扣 3% 血**，并在原地放 Splash 59516（`:98-103, 314-320`）。球全部消失或 15 秒后，boss 恢复并重新挂泡泡（25% 血以下不再挂）。25% 血以下 Frenzy 54312（`:150-155`）。
- 场景：放出点 (1916.14, 778.15, 35.77) 在东南侧，靠近 Ichoron 牢房（牢房在更低的 z 30.95）。球的刷点分布在房间四周（(1840.6, 795.4)、(1886.2, 757.7)、(1877.9, 845.9)、(1919.0, 850.6)、(1935.5, 796.2)），离 boss 20–80 码。
- bot 覆盖：较完整。非治疗在 Drained 阶段打球，坦克回 boss。缺口（小）：球被打死时的 Splash 是 AoE，近战挤在一起打球会掉血；`possible targets` 受视线过滤（参见 memory「看不见队友=队友不存在」），台阶另一侧的球可能打不到（待实测）。

## 4. Lavanthor（29312 / 31509）

- **脚本**（`VH/boss_lavanthor.cpp:42-73`）：Firebolt、Flame Breath、Lava Burn 全部打 victim；**英雄 Cauterizing Flames 59466**，3 秒首发，每 10–16 秒一次，AoE。
- 场景：放出点 (1853.62, 758.56, 38.66) 在西南侧，**离门口 4 个友方 Violet Hold Guard（(1854, 798–810, 44)）约 40 码**。boss 被放出时 `SetImmuneToNPC(false)`，与 faction 1718 的守卫互相敌对，可能互殴（待实测）。
- bot 覆盖：无（不需要）。缺口：Flame Breath 是锥形，坦克朝向没有专门处理（小）。

## 5. Xevozz（29266 / 31511）

- **脚本**（`VH/boss_xevozz.cpp`）：Arcane Barrage Volley 54202 每 20 秒；**Summon Ethereal Sphere**：10 秒首发，每 45 秒，普通召 1 个、**英雄召 2 个不同的**（`:75-91`）。球 = Ethereal Sphere 29271 / 英雄 31514，addon 光环 54141 + 54207/59476，unit_flags 131072，`MoveFollow` 跟着 Xevozz 走（`:121`）。每 2 秒检查一次：球离 boss < 3 码 → 对 boss 施 **Arcane Power 54160**（大幅增伤），8 秒后球消失（`:93-112`）。召球 5 秒后打一次 Arcane Buffet（`:72-74`）。
- 机制要求：坦克拉着 boss 远离球（风筝），或者打掉球。
- 场景：放出点 (1906.68, 842.35, 38.64) 就在牢房门口，离 spawn 3.9 码，在北侧。
- bot 覆盖：**无**（TODO）。缺口（中–大，英雄）：两个球会追上来给 boss 叠 Arcane Power，坦克和治疗压力会明显增加。ilvl 200 档能否硬扛过去，**先测基线再决定**。

## 6. Zuramat the Obliterator（29314 / 31512）

- **脚本**（`VH/boss_zuramat.cpp`）：Shroud of Darkness 54524（英雄 59745）5–7 秒首发，每 20 秒一次（`:76-80`）；**Void Shift 54361**：23–25 秒首发，每 18–22 秒，60 码内随机目标，被点名的人被移进暗影相位（Void Shifted 54343）（`:81-88`）；**Summon Void Sentry 54369** 每 12 秒一次（`:89-92`）。召出的 Void Sentry 29364（英雄 31518，faction 16）被设成 phaseMask 16，只有带 Void Shifted 的人能看到；同时在相位 1 召一个球 29365（`NullCreatureAI`，光环 54342，不可攻击）（`:110-118, 140-153`）。Sentry 被打死时成就失败（`:162-167`）。
- 场景：放出点 (1928.21, 852.86, 47.20) 在东北侧高台（z 47.2）。
- bot 覆盖：Shroud 期间停手，Void Shifted 的人打 sentry。缺口（小）：sentry 越积越多时靠被相位的人清，相位持续时间和 sentry 的实际威胁都**待实测**；`possible targets no los` 已绕开视线过滤。

## 7. Cyanigosa（31134 / 31506）

- **来源**：第 18 波 `sinclari->SummonCreature(NPC_CYANIGOSA, CyanigosasSpawnLocation (1930.28, 804.41, 52.41), TEMPSUMMON_DEAD_DESPAWN)`，挂蓝色光环，`MoveJump` 到 MiddleRoomLocation (1892.29, 805.70, 38.44)（`instance_violet_hold.cpp:426-435`）；10 秒后变形（`:438-445`），再 2.5 秒去 `NON_ATTACKABLE`、`SetImmuneToNPC(false)`（`:446-452`）。**这两个事件只在 `EVENT_SUMMON_PORTAL` 的第 18 波分支里排进队列**。
- **技能**（`VH/boss_cyanigosa.cpp:57-109`）：**Arcane Vacuum 58694** 每 30 秒：把命中的人全部拉到 boss 头顶 +10 码（`SpellHitTarget` → `NearTeleportTo`，`:69-75`），**重置仇恨**，自己定身 3 秒；Blizzard 58693（45 码随机目标，地面 AoE）每 15 秒；Tail Sweep 58690（victim，扫尾）每 15–20 秒；Uncontrollable Energy 58688 每 20–25 秒；**英雄 Mana Destruction 59374** 每 20 秒（50 码随机目标）。
- 死亡：`SetBossState(DATA_CYANIGOSA, DONE)` → `_encounterStatus = DONE`，开大门，Sinclari despawn（`instance_violet_hold.cpp:165-177`）。此后 `InstanceCleanup` 不再关牢房门、不再 despawn boss（`:524`）。**击杀后，这个实例基本就作废了**，下一场要换新实例。
- 框架阻塞（大）：
  1. 没有 DB spawn → 只能用 `BossSpawnMode=script`，而 `Scenario.cpp` 规定 script 模式必须配 `EngageTrigger=pull` 和非空 `PrerequisiteSpawns`（`RT/Scenario/Scenario.cpp:814-820`，`BossSpawnMode=script requires EngageTrigger=pull and PrerequisiteSpawns`）。VH 没有静态小怪可以当前置。
  2. 召唤入口是 instance 私有的 `EVENT_SUMMON_PORTAL`，`_waveCount` 没有写入口。可选方案：(a) 从 Sinclari gossip 开始跑完整 18 波加两个随机 boss（链式、耗时长、bot 要守门）；(b) 在核心 fork 加一个 `SetData(DATA_WAVE_COUNT, n)`。它不是修 bug，而是测试钩子，需要用户同意；(c) 框架自己召 Cyanigosa，再手动复刻"变形 + 去 NON_ATTACKABLE"。这等于在框架里重写脚本流程，违背"只编排"的边界，不建议。
  3. 每杀一次都要新实例（DONE 不可逆）。
- bot 覆盖：近战和治疗转到 boss 背后（`rear flank`），避开 Tail Sweep。缺口：Arcane Vacuum 重置仇恨后，坦克要重新拉住（通用仇恨逻辑，待测）；Blizzard 靠 `MasterlessAvoidAoe=1`；**治疗也被要求站到 boss 身后**，可能离开远程的治疗覆盖范围（小）。

---

## 8. mod-raidtest 能力对照

| 需求 | 现有键 | 在 VH 上是否可用 | 缺什么 |
|---|---|---|---|
| boss 寻址 | `BossEntry`（database 模式按 DB spawn） | 六个牢房 boss 可以 | Cyanigosa 没有 DB spawn |
| **把 boss 从牢房放出来** | 无 | **不可用**：`FixtureInstanceData` 的 SetData 不处理 wave 和选 boss；`FixtureBossStates` 反而会触发 `InstanceCleanup`；`FixtureBossNotify` 调的是 boss 的 `SetData(entry, 0)`，BossAI 默认不处理；`EngageTrigger=gameobject` 只能开门 | **新增两个通用夹具键**（见下） |
| 坦克正常拉怪 | `EngageTrigger=pull` | 放出后可用（boss 不看视野，只会等人来打） | — |
| 开战确认 | pull 的坦克仇恨校验 | 可用 | 不能用 `EngageConfirmBossState`（`Scenario.cpp:799-802` 禁止它和 pull 组合），也不需要 |
| 进度夹具 | `FixtureBossStates` | **禁用**（§0.3 推论 3） | — |
| 击杀后恢复 | `ResetInstance` → `ResolveOrRestoreSpawn` | **有风险**：恢复出的 boss 在 Reset 里触发 `InstanceCleanup`，3 秒 despawn（§0.3 推论 2） | 待实测；可能需要"恢复后等 boss 重新出现"再校验 |
| 链式整场（18 波） | `EventStarterEntry` 走 escort + BossState | 不适用（Sinclari 不是 escort，也不是 boss） | 大 |

**建议的最小框架改动**（在 `RT/Orchestrator/AttemptRunner.cpp:784-800` 的 `FixtureInstanceData` 之后，同样写事件流）：
- `FixturePersistentData = <index>:<value>[,…]` → `script->StorePersistentData(index, value)`。
- `FixtureInstanceAction = <action>[,…]` → `script->DoAction(action)`。
- VH 用法：`FixturePersistentData = 1:<3..8>`，`FixtureInstanceAction = 3`。隔离场景里 `_waveCount` 是 0，`DoAction(3)` 走 SECOND_BOSS 分支（`instance_violet_hold.cpp:231-234`），所以写索引 1。保险起见也可以把 0 写成同一个值。
- 这两个调用都是 instance 脚本的公开接口，等价于 Saboteur 走完路径后的那一次 `DoAction(ACTION_RELEASE_BOSS)`，不替 bot 做任何战斗决策。结论口径标「隔离形态（跳过 1–5/7–11 波传送门、Saboteur 与守门）」。
- 夹具每场 attempt 都会执行，而每次 evade 或击杀后 `InstanceCleanup` 都会把 boss 关回牢房并重新挂 `NON_ATTACKABLE`，所以每场都需要重新放一次，这正好符合要求。
- 时序：fixture 执行后，没有前置怪时会在同一个 tick 进 `StartBossPull`（`AttemptRunner.cpp:873-887`）。此时 boss 刚开门还在往外走，`BeginTankPull` 失败时有逐 tick 重试预算（`:2187-2203`）；视线要等门 GO 状态刷新（待实测）。

## 9. campaign 矩阵草案与逐 boss 建议

所有场景共用：`MapId=608`、`DungeonDifficulty=heroic`、`PartySize=5`、`Strategy=wotlk-vh`、`MasterlessAvoidAoe=1`、`EngageTrigger=pull`、h5g 名册。**不配** `FixtureBossStates` / `FixtureInstanceData`。准备点：统一候选房间中央偏门一侧 **(1870, 804, 38.6)**（z 取中央 38.44 附近，**待实测**）；开怪点 = 各 boss 放出点前 8–10 码（**待实测**）。

| encounter | scenario（拟） | 放出参数 | 当前可行性 | 阻塞 | 建议 |
|---|---|---|---|---|---|
| Moragg | `heroic-vh-moragg-h5g` | `1:3` | **需小框架改动** | 放出键 | 做完两个夹具键后首批建；bot 缺 Optic Link 处理，先测基线 |
| Erekem | `heroic-vh-erekem-h5g` | `1:4` | **需小框架改动** | 放出键 | guard 一起放出属于正常形态；关注英雄 Chain Heal 拖长战斗 |
| Ichoron | `heroic-vh-ichoron-h5g` | `1:5` | **需小框架改动** | 放出键 | bot 覆盖最好，建议作为第一只验证放出链路 |
| Lavanthor | `heroic-vh-lavanthor-h5g` | `1:6` | **需小框架改动** | 放出键 | 纯站桩，适合与 Ichoron 一起做链路验证；注意门口友方守卫互殴 |
| Xevozz | `heroic-vh-xevozz-h5g` | `1:7` | **需小框架改动** | 放出键；bot 缺躲球 | 先测基线，如果 Arcane Power 叠满导致灭团，再记为 playerbots 缺口 |
| Zuramat | `heroic-vh-zuramat-h5g` | `1:8` | **需小框架改动** | 放出键 | 已有相位 sentry 逻辑，首轮看 Void Shift 期间目标切换 |
| Cyanigosa | `heroic-vh-cyanigosa-h5g` | — | **大工作量** | 没有 DB spawn、没有 wave 写入口、击杀后实例作废 | 暂缓；若要做，优先评估核心 fork 加 `SetData(DATA_WAVE_COUNT)` 测试钩子（需用户确认），或完整 18 波链式 |

共用风险（首轮必须看日志）：① 击杀后恢复时 `InstanceCleanup` 连锁 despawn 3 秒（§0.3 推论 2），可能导致 `scene_invalid`；② boss 死后 35 秒会开一波传送门；③ 门口 4 个友方守卫可能与放出的 boss 互殴（尤其 Lavanthor）；④ 任何一场 evade 都会让六个 boss 一起 despawn 再重生（guid 改变），观察器按 guid 追踪时需要重新寻址。
