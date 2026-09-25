# 英雄净化斯坦索姆（The Culling of Stratholme，map 595）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `src/server/scripts/Kalimdor/CavernsOfTime/CullingOfStratholme/`、mod-playerbots `src/Ai/Dungeon/CoS`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp` / `AttemptObserver.cpp`）和 world DB（`acore_world`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文坐标都来自脚本常量或 DB，**作为站位点都没有做过 los 和地面高度实测（待实测）**。
> 版本基线：core `4048589b3`、mod-playerbots `eb2aadb5`、mod-raidtest `ccb8d3e`。
> 下文路径缩写：`h` = `culling_of_stratholme.h`，`inst` = `instance_culling_of_stratholme.cpp`，`cos` = `culling_of_stratholme.cpp`。

## 0. 总览

| boss | 普通 entry | 英雄 entry | DB spawn | 出生点 (x, y, z, o) | HARD_RESET | 谁召唤 | 可攻击时机 | 现有键能否隔离开战 |
|---|---|---|---|---|---|---|---|---|
| Meathook | 26529 | 31211 | **无** | (2351.45, 1197.81, 130.45, 3.83) `h:171` | 否（0 / 1） | Arthas `SendNextWave`，第 4 波清完后召唤 `cos:1342-1343` | 召唤后站着不动，正常 pull | **不能**：没有能直接跳到他的状态，前面有 4 波 |
| Salramm the Fleshcrafter | 26530 | 31212 | **无** | 同上 `h:172` | 否（0 / 1） | Arthas `SendNextWave`，第 9 波（Meathook 后再 4 波）`cos:1344-1345` | 同上 | **不能**：同上 |
| Chrono-Lord Epoch | 26532 | 31215 | **无** | 召唤 (2463.13, 1115.39, 152.47)，走到 (2451.81, 1112.90, 149.22) `h:176-177` | 否（0 / 1） | Arthas 市政厅剧情 `EVENT_ACTION_PHASE3+15` `cos:1101-1113` | 约 21 秒剧情后 `SetInCombatWithZone` `cos:1124-1134` | **不能**：要 Arthas 的 gossip + 市政厅约 15 只怪 |
| Mal'Ganis | 26533 | 31217 | **无** | (2298.25, 1500.56, 128.37, 4.95) `h:179` | 否（0 / 1） | Arthas `ACTION_START_MALGANIS` `cos:488-501` | Arthas 走到 wp55 后 7 秒 `cos:671-676`、`cos:1149-1160` | **不能**：要 gossip；**他不会死**（见 §4），现有击杀判定判不出来 |
| Infinite Corruptor（仅英雄） | 32273 | 32313 | **无** | (2329.07, 1276.98, 132.68, 4.0) `h:178` | 否（0 / 1） | 副本脚本 `instance->SummonCreature`：`SetData(DATA_START_WAVES)` 时召唤 `inst:131-140` | 召唤后原地引导，正常 pull | **勉强能**（script 模式 + 借一只 DB 僵尸当前置 + `FixtureInstanceData=4:1`，见 §5） |

- 5 个 boss 在 `creature` 表里**都没有 spawn**（map 595 共 353 条 creature，spawnMask 全是 3）。Arthas 26499 有 DB spawn：guid **1970935** (1920.87, 1287.12, 142.94)。
- `flags_extra`：普通 entry 全部 0，英雄 entry 全部 1（INSTANCE_BIND）。HARD_RESET 判定读普通 entry（`CreatureAI.cpp:271-275`），**全部不带**。
- 5 个 boss 都是临时召唤物，evade 后回到召唤点（home = 召唤位置）。Meathook、Salramm、Epoch、Mal'Ganis 在 Arthas 的 `summons` 列表里：**Arthas 调用 `Reset()` 时 `summons.DespawnAll()` 会把它们一起清掉**（`cos:515-519`）；**Arthas 死亡时也清**（`cos:411-417`）。
- 访问：`dungeon_access_template` id 78（普通，min_level 75）、id **79（英雄，min_level 80，min_avg_item_level 180）**；`dungeon_access_requirements` 对两者**都没有行**（不要钥匙、任务或成就）。入口 AT 5150 → (1431.1, 556.92, 36.69)。ilvl 200 档满足。
- 进入副本时非人类/矮人/侏儒角色会被施加人类幻象 35482/35483（`inst:73-74`），只是外观。

### 0.1 instance 脚本（inst）——对框架最关键的几点

- **不调 `SetBossNumber`，也不用 `SetBossState`**；`IsEncounterInProgress()` 恒返回 false（`inst:53-56`）。存档只有 `_encounterState` 和 `_guardianTimer` 两个数（`inst:357-366`）。所以 `FixtureBossStates` / `EngageConfirmBossState` / `EventCompletionBossState` 在本副本**全部无效**，只能用 `*InstanceData`。
- Data id（`h:26-39`）：`0 DATA_ARTHAS_EVENT`、`1 DATA_GUARDIANTIME_EVENT`（只读）、`2 DATA_SHOW_CRATES`、`3 DATA_CRATE_COUNT`、`4 DATA_START_WAVES`、`5 DATA_SHOW_INFINITE_TIMER`、`6 DATA_ARTHAS_REPOSITION`、`7 DATA_INTRO_EVENT_FINISHED`（只读）。
- **进度 `SetData(0, x)`**（`inst:157-170`）：直接赋值，**不单调**，也不校验；只有 x=2（START_INTRO，开始开场剧情）和 x=6（KILLED_SALRAMM，让 Arthas 继续前进）会顺带触发 Arthas 的 DoAction，其他值只改数字、立即 `SaveToDB()`。取值见 `h:116-130`：

  | 值 | 含义 | Arthas 重排后的位置（`inst:318-355`） | ReorderInstance 的动作（`cos:1260-1320`） |
  |---|---|---|---|
  | 3 FINISHED_INTRO | 开场剧情结束 | LeaderIntroPos2 (2050.66, 1287.33, 142.67) | 下一点 wp9，挂 gossip |
  | 4 FINISHED_CITY_INTRO | 城门剧情结束 | LeaderIntroPos2special (2092.15, 1276.65, 140.52) | 下一点 wp12；**10 秒后刷第 1 波** |
  | 5 KILLED_MEATHOOK | Meathook 已死 | 同上 | `waveGroupId=4` → 立刻刷第 6 波（表内第 5 组） |
  | 6 KILLED_SALRAMM | Salramm 已死 | 同上 | `DoAction(ACTION_KILLED_SALRAMM)`：10 秒后走向市政厅 |
  | 7 REACHED_TOWN_HALL | 到达市政厅门口 | LeaderIntroPos3 (2365.63, 1194.84, 131.97) | 下一点 wp21，挂 gossip |
  | 8 KILLED_EPOCH | Epoch 已死 | LeaderIntroPos4 (2423.12, 1119.43, 148.07) | 下一点 wp32，挂 gossip，开书架门 188686 |
  | 9 LAST_CITY | 密道出口 | LeaderIntroPos5 (2540.48, 1129.06, 130.86) | 下一点 wp46，挂 gossip |
  | 10 BEFORE_MALGANIS | Mal'Ganis 前 | LeaderIntroPos6 (2327.39, 1412.47, 127.69) | 下一点 wp55，挂 gossip |
  | 11 FINISHED | 通关 | Arthas 设为不可见（`inst:83-84`） | — |

- **ReorderInstance 只在 Arthas `Reset()` 里调用**（`cos:527-533`），`SetData(0, x)` 本身不会让 Arthas 重排。**`SetData(6, 2)` 会在下一次 instance Update 调用 `arthas->AI()->Reset()`**（`inst:171-176`、`inst:224-239`）。所以 **`FixtureInstanceData = 0:<x>,6:2`（按这个顺序）就能把事件跳到任意阶段**。这和 Chromie「跳过开场」gossip 用的是同一条路径（`SetData(0, 3)` 后直接 `arthas->AI()->Reset()`，`cos:1544-1553`），不是框架自造的状态。
  - 注意：Reset 发生在**下一个** instance Update，不是在 SetData 调用时同步完成。框架在夹具后同一 tick 读 Arthas 状态会读到旧值（待实测）。
  - 注意：Arthas 已在护送中时，`ReorderInstance` 里的 `Start(true)` 会报「already escorting」直接返回（`ScriptedEscortAI.cpp:436-440`），在战斗中则报「while in combat」（`:430-434`）。之后的 `SetNextWaypoint` 仍作用在旧航点表上，因为航点表相同，预计不影响（**待实测**）。
- **`SetData(4, 1)`（DATA_START_WAVES）**（`inst:131-140`）：更新波数 worldstate；英雄下把 `_guardianTimer` 设为 26 分钟，且在 `!_infiniteGUID` 时**在 (2329.07, 1276.98, 132.68) 召唤 Infinite Corruptor**。它**不会刷小怪波次**，波次由 Arthas 的 `SummonNextWave` 刷（`cos:940-944`）。
- `_infiniteGUID` 只在 `OnCreatureCreate` 里赋值（`inst:88-90`），**从不清零**：Corruptor 死后或超时消失后，同一实例里再 `SetData(4,1)` / `SetData(5,1)` 都**不会再召唤**。
- 计时器（`inst:253-279`）：每分钟 SaveToDB，归零时对 Corruptor `DoAction(ACTION_RUN_OUT_OF_TIME)` → 他喊话后 0.5 秒消失（`boss_infinite.cpp:114-125`）。每次 `SetData(4,1)` 都把计时器重置为 26 分钟。
- 门：书架门 GO 188686 guid 67455 (2473.27, 1121.36, 149.96)，进度 ≥8 时打开；出口门 191788 guid 67462 (2241.28, 1475.46, 131.86)，进度 11 时打开（`inst:94-109`、`cos:636-641`、`cos:1167-1176`）。隔离场景直接传送，门不挡路。
- AreaTrigger：map 595 有 11 个 AT；有脚本的 5250/5251/5252/5291 都只是 SmartTrigger 让路边 NPC 说话（`SetData 0 1` 给某个 NPC guid），**跟 boss 无关**。**没有任何 boss 用 AT 开战。**

### 0.2 Arthas 的事件链（npc_arthas，cos:300-1380）

- 护送航点在 `script_waypoint` entry 26499，共 57 点（0–56）。关键点：wp8 城门（进度→3）、wp11 第二个市民、wp12 起在城中等波、wp20 市政厅门口（进度→7）、wp22 市政厅第一场、wp26/29/31 楼上三场时空裂隙、wp36 书架、wp45 密道出口（进度→9）、wp54 Mal'Ganis 前（进度→10）、wp55 面对 Mal'Ganis、wp56 战后。
- gossip 入口（`cos:305-380`）：`OnGossipHello` 按进度给菜单项；`OnGossipSelect` **只检查 `HasNpcFlag(UNIT_NPC_FLAG_GOSSIP)`，不校验进度和距离**，根据 action 调用 DoAction：

  | action | 效果 | 用于 |
  |---|---|---|
  | `GOSSIP_ACTION_INFO_DEF+1`（1001） | `ACTION_START_CITY`：城门剧情（Mal'Ganis 亮相）→ 进度 4 → 刷波 | Meathook / Salramm 链 |
  | `+2`（1002）→ `+3`（1003） | +2 只是翻到下一页菜单；+3 = `ACTION_START_TOWN_HALL` | Epoch |
  | `+4`（1004） | `ACTION_START_SECRET_PASSAGE` | 走密道 |
  | `+5`（1005） | `ACTION_START_LAST_CITY` | 最后一段街道 |
  | `+6`（1006） | `ACTION_START_MALGANIS`：召唤 Mal'Ganis（免疫 + 不可攻击），Arthas 前进 | Mal'Ganis |

- 这些是 `CreatureScript::OnGossipSelect(player, creature, sender, action)`，**不是 `CreatureAI::sGossipSelect`**。框架现有的 `StartScriptedEventGossip` 调的是 `starter->AI()->sGossipSelect(tank, 0, 0)`（`AttemptRunner.cpp:2399-2415`），对 Arthas **无效**；要走 `sScriptMgr->OnGossipSelect(tank, arthas, GOSSIP_SENDER_MAIN, 1000+N)`。
- 波次（`cos:207-258`、`cos:1235-1249`、`cos:1322-1351`）：8 组 × 4 只，由 Arthas 召唤，**原地站着不动**（小怪都是 SmartAI，只有战斗施法，没有移动逻辑），刷新时给所有玩家发 POI 引路。只有 Arthas 自己的召唤物死亡才计数（`SummonedCreatureDies`，并且要求进度在 (3, 7) 区间，`cos:426-430`）；每组 4 只死完进下一组。第 4 组后召唤 Meathook，第 9 组后召唤 Salramm。各组刷在 (2164, 1255)、(2254, 1163)、(2348, 1202)、(2139, 1356) 等**相距 100 码以上**的街区，需要队伍沿街自行找过去。
- 市政厅（`cos:955-1148`、`cos:1353-1380`）：wp22 三个「躁动的市民」变成 Infinite 小怪并解除免疫（`cos:1015-1039`），然后楼上 wp26 一个时空裂隙（4 只），wp29、wp31 各两个裂隙（每个 2 只），每场都 `SetInCombatWithZone` 并对 Arthas 加仇恨。Arthas `AttackStart` 参战。清完后召唤 Epoch。
- Arthas 自己的战斗能力：光环 52442、驱邪术 52445（7–14 秒一次打随机目标）、血量 <40% 圣光术 52444（`cos:1193-1212`、`cos:1251-1258`）。

---

## 1. Meathook（26529 / 31211）

### 1.1 脚本（boss_meathook.cpp）

- ScriptedAI，**不读 instance**（`:54-114`）。构造时喊话（SAY_SPAWN）。
- 技能（`:64-70`、`:95-110`）：
  - Disease Expulsion 52666：开战 4 秒后开始，每 6 秒自施（AoE 疾病）；
  - Constricting Chains 52696：开战 15 秒后开始，每 14 秒一次，目标是 **50 码内仇恨最低**的玩家（`SelectTargetMethod::MinThreat`），引导型控制；
  - Frenzy 58841：开战 20 秒后开始，每 20 秒一次。
- 没有 boundary、没有 evade 检查，走默认仇恨规则。

### 1.2 召唤与复位

- 只在 Arthas `SendNextWave` 中 `waveGroupId==4` 时召唤（`cos:1341-1343`），召唤点 (2351.45, 1197.81, 130.45)。前面必须先让第 0–3 组共 16 只死完。
- 召唤点周围 20 码内的 DB 单位：4 只 Agitated Stratholme Citizen 31126、3 只 Resident 31127、若干 Citizen 28167/28169（faction 190）、2 个 Civilian Transformation Trigger 28815。这些是城门剧情里会被 Mal'Ganis 感染的市民（`cos:888-912`）。**是否敌对、会不会被 bot 当成目标，待实测。**
- 团灭后：Meathook evade，回到召唤点，**不会消失**，同一实例可以再打。击杀后进度→5，Arthas 立即刷下一组（`cos:1327-1331`）。

### 1.3 mod-playerbots

- `CoSStrategy.cpp:12-13` 只有注释「可以固定位置坦克让治疗卡视线躲控制」，**没有任何节点**。

---

## 2. Salramm the Fleshcrafter（26530 / 31212）

### 2.1 脚本（boss_salramm.cpp）

- ScriptedAI，**不读 instance**（`:65-159`）。技能：
  - Shadow Bolt 57725：打当前目标，7 秒后开始、每 10 秒；
  - Steal Flesh 52708：对当前目标引导，11 秒后开始、每 12 秒；光环结束时给自己加 52712、给目标加 52711（`:162-186`，属性偷取）；
  - Summon Ghouls 52451：16 秒后开始、每 10 秒，召唤 Ghoul Minion 27733；
  - Explode Ghoul 52480：22 秒后开始、每 15 秒，**对第一只活着的食尸鬼施放**（`:107-116`），被引爆的食尸鬼对周围造成 AoE；
  - 英雄：Curse of Twisted Faith 58845，打当前目标，25 秒后开始、每 30 秒（`:89-90`、`:151-154`）。
- 死亡时清掉所有食尸鬼（`:93-97`）。

### 2.2 召唤与复位

- `waveGroupId==9` 时召唤（`cos:1344-1345`），召唤点与 Meathook 相同。前提是 Meathook 已死，并且第 5–8 组共 16 只清完。
- 击杀后进度→6 → Arthas 10 秒后前往市政厅（`cos:1332-1336`、`cos:450-456`）。

### 2.3 mod-playerbots（有缺陷）

- `explode ghoul` → `explode ghoul spread`（ACTION_MOVE+5，`CoSStrategy.cpp:16-17`）。
- **trigger 永远不会触发**：`ExplodeGhoulTrigger::IsActive` 比对的是 `NPC_RISEN_GHOUL`（`CoSTriggers.cpp:22`），这个常量来自 core 的 `PetDefines.h:121`，值 **26125（死亡骑士宠物食尸鬼）**；而 action 用的是本模块定义的 `NPC_GHOUL_MINION = 27733`（`CoSTriggers.h:18`、`CoSActions.cpp:21`）。两者 entry 不一致，trigger 找不到对象，action 永远不会执行。
- 即使 entry 修正了，trigger/action 都扫描 `nearest corpses`（尸体），而 Explode Ghoul 是对**活着**的食尸鬼施放、爆炸发生在它死之前，按尸体躲是事后才动。
- 没有针对 Steal Flesh、诅咒（可驱散性待查）的处理。

---

## 3. Chrono-Lord Epoch（26532 / 31215）

### 3.1 脚本（boss_epoch.cpp）

- ScriptedAI，**不读 instance**（`:61-153`）。技能：
  - Wounding Strike 52771：打当前目标，3 秒后开始、每 6 秒；
  - Curse of Exertion 52772：50 码内随机目标，每 9 秒；
  - Time Warp 52766 + Time Step 52737：25 秒后开始、每 25 秒；Time Step 命中后对新目标连跳，最多 3 次（`:87-102`）；
  - 英雄：Time Stop 58848 自施，20 秒后开始、每 20 秒（`:83-84`、`:124-127`）。

### 3.2 召唤与开战

- 由 Arthas 在市政厅楼上三场裂隙清完后召唤（`cos:1101-1113`）：先加免疫 + NON_ATTACKABLE，走到 (2451.81, 1112.90, 149.22)；3 秒 + 14 秒 + 7 秒剧情后（`cos:1114-1123`）解除免疫、转为主动、**对 Arthas 加仇恨并 `SetInCombatWithZone()`**（`cos:1124-1134`）。开战是**区域强制进战**，不是 pull。
- Arthas 同时参战；Epoch 死后进度→8（`cos:1135-1147`）。
- 召唤点附近 60 码内只有 3 只 Spider 14881（faction 190，环境小动物）和 Magistrate Barthilas 30994（faction 35，友好）。

### 3.3 复位

- 团灭后 Epoch 会继续和 Arthas 打。Arthas 死亡 → `JustDied` 清掉召唤物（包括 Epoch）→ `SetData(6,2)` → 复活并 Reset → 按进度 7 回到 wp21 等 gossip（`cos:411-417`、`inst:224-239`）。**这是脚本自带的完整复位**，但时长取决于 Epoch 多久打死 Arthas（Arthas 有圣光术自疗，可能拖很久，待实测）。框架也可以主动 `FixtureInstanceData=6:2` 强制 Reset（清掉召唤物）。

### 3.4 mod-playerbots

- `epoch ranged` → `epoch stack`（ACTION_MOVE+5，`CoSStrategy.cpp:21-22`）：非近战在找到 Epoch 时每次最多移动 10 码，贴到 5 码内（`CoSActions.cpp:33-58`、`CoSTriggers.cpp:33-36`）；猎人除外。
- `EpochMultiplier`（`CoSMultipliers.cpp:15-25`）：Epoch 在场时，非猎人的 `FleeAction` 置 0。
- 设计意图应该是减少 Time Step 连跳的距离。注释承认「不确定是否有效」（`CoSStrategy.cpp:20`）。Time Stop、诅咒没有处理。

---

## 4. Mal'Ganis（26533 / 31217）

### 4.1 脚本（boss_mal_ganis.cpp）

- ScriptedAI（`:62-168`）。Reset 时对击退免疫（`:74-75`）。技能：
  - Carrion Swarm 52720：打当前目标（锥形），6 秒后开始、每 7 秒；
  - Mind Blast 52722：50 码内随机目标，11 秒后开始、每 6 秒；
  - Sleep 52721：随机目标，20 秒后开始、每 17 秒（魔法控制，是否可驱散待查 DBC）；
  - Vampiric Touch 52723：15 秒后开始、每 30 秒自施（造成伤害时回血）。
- **他不会死**：`DamageTaken` 在致命伤害时把伤害置 0，设置 `finished`，停止回血，加免疫 + NON_ATTACKABLE + REACT_PASSIVE，通知 Arthas `ACTION_KILLED_MALGANIS`，施放 58630 给击杀credit，刷宝箱（英雄 193597，位置 (2288.35, 1498.73, 128.41)），然后 `EnterEvadeMode()`（`:105-131`）。之后 Reset 喊话并在 20 秒后消失（`:77-81`）。
  - Arthas 收到通知后 evade，22 秒 + 5 秒后把进度设为 **11 FINISHED** 并开出口门（`cos:502-512`、`cos:1161-1176`）。
  - **框架影响**：`AttemptObserver` 的 Kill 需要「boss 血量 0 且 CombatEventBus 看到 boss 死亡事件」（`AttemptObserver.cpp:767-806`）。Mal'Ganis 血量不会归零，也没有死亡事件，所以**打赢也只会被记成 timeout/wipe**。需要新的完成判据（见 §6）。

### 4.2 召唤与开战

- 路径：进度 10 → Arthas 在 LeaderIntroPos6 (2327.39, 1412.47) 挂 gossip → action 1006 → 清掉 Arthas 其他召唤物，召唤 Mal'Ganis（免疫 + 不可攻击），Arthas 跑向 wp55 (2303.02, 1480.07, 128.14)（`cos:488-501`）→ 到达后喊话，7 秒后解除免疫、`SetInCombatWithZone()`、对 Arthas 加仇恨，Arthas 攻击（`cos:671-676`、`cos:1149-1160`）。**同样是区域强制进战。**
- **用现有夹具即可把事件跳到这里**：`FixtureInstanceData = 0:10,6:2`。中间的市政厅、密道、最后一段街道全部跳过。
- 附近 60 码只有友好的 Chromie 30997（guid 1971038）和环境小动物，**无需清怪**。
- 复位：Mal'Ganis 在 Arthas 的 summons 里。团灭后 Arthas 死亡或框架 `6:2` 强制 Reset 都会让他消失，Arthas 回到 LeaderIntroPos6 重新挂 gossip。**击杀后**进度是 11，Arthas 被 `SetVisible(false)`（`cos:1178-1181`），Reset 不会把可见性改回来，并且宝箱和出口门会留在场上。所以击杀后同一实例**不建议**再打；每个 run 登录时框架会解绑旧实例（`RosterLogin.cpp:334-360`），**一个 run 计一次击杀最稳**（待实测多 attempt 表现）。

### 4.3 mod-playerbots

- `CoSStrategy.cpp:24` 只有注释，**没有节点**。Sleep 驱散、Carrion Swarm 躲正面都靠通用逻辑。

---

## 5. Infinite Corruptor（32273 / 32313，仅英雄）

### 5.1 脚本（boss_infinite.cpp）

- ScriptedAI（`:54-161`）。Reset 时在 (2337.6, 1270.0, 132.95) 召唤 Time Rift 28409、在 (2319.3, 1267.7, 132.8) 召唤 Guardian of Time 32281（`:72-73`），2 秒后对自己施 60422 Corruption of Time 引导（`:129-137`）；**如果 `GetData(1)`（计时器）为 0，0.5 秒后自己消失**（`:68-70`）。
- 技能：Void Strike 60590 打当前目标，8 秒后开始、每 8 秒；Corrupting Blight 60588 打 50 码内随机目标，12 秒后开始、每 12 秒（`:79-85`、`:146-157`）。死亡时清掉召唤物、`SetData(5, 0)`（计时器清零），并移除所有玩家身上的 60588（`:87-112`）。

### 5.2 召唤与复位

- `SetData(4, 1)` 在英雄模式下立刻召唤（`inst:131-140`），位置 (2329.07, 1276.98, 132.68)。**不需要 Arthas 或任何进度**。进度 0 时 Arthas 停在城外 (1920.87, 1287.12)，距这里 400 码以上，不会被卷进来。
- `unit_flags=64`（不是 NON_ATTACKABLE），faction 1720，召唤后可以直接 pull。
- 团灭后：evade 回到召唤点，Reset 重召裂隙和守护者（如果计时器还在走）。**击杀后同一实例不能再召唤**（`_infiniteGUID` 不清零，见 §0.1）。
- 周围 DB 单位：**Risen Zombie 27737**（faction 2075 敌对，MovementType 1 随机游走），guid 1970881（3.6 码）、1970885（12.2 码）、1970882（19.7 码）、1970890（21.4 码）、1970893（35.3 码）、1970892（54.5 码）、1970886（55.1 码），另有 Rat 和 Roach（环境小动物）。

### 5.3 mod-playerbots

- `CoSStrategy.cpp:26` 只有注释，**没有节点**。Corrupting Blight 在 3.3.5 是疾病还是诅咒待查 DBC；驱散靠通用逻辑。

---

## 6. mod-raidtest 能力对照

框架调用顺序（`AttemptRunner.cpp:627-885`）：先 `FindBossNear` 找 boss，找到后排队写 attempt 行，**然后**依次执行 `FixtureDespawnSpawns` → `FixtureBossStates` → `FixtureInstanceData` → KillGate → 前置怪 / scripted event / `StartBossPull`。

| 需求 | 现有键 / 机制 | 在 CoS 上是否可用 | 缺什么 |
|---|---|---|---|
| 找 boss（database 模式） | 扫 `GetCreatureBySpawnIdStore()`（`:1528-1541`） | **全部不可用**：5 个 boss 都没有 DB spawn；`ResetInstance` 找不到 boss spawn 直接失败（`:1754-1760`） | — |
| 找 boss（script 模式） | 以 bot 为中心 200 码网格按 entry 查找（`:1509-1524`）；前置怪清完后等待 boss 出现 | 可用，但 `Scenario.cpp:814-821` 规定 **必须 `EngageTrigger=pull` + 非空 `PrerequisiteSpawns`** | 放开「script 模式不带前置」：夹具召唤出 boss 后直接等待它出现（小改） |
| 跳进度 | `FixtureInstanceData=0:<x>,6:2`（SetData 调用，`:784-806`） | **可用**，与 Chromie 跳过开场同一路径 | Arthas Reset 延后一个 instance Update 才执行（待实测时序） |
| 召唤 Corruptor | `FixtureInstanceData=4:1` | **可用**（仅英雄） | — |
| 触发 Arthas gossip | `EventStarterEntry` + `StartScriptedEventGossip`（`:2399-2415`） | **不可用**：调的是 `AI()->sGossipSelect(tank,0,0)`，Arthas 走的是 `CreatureScript::OnGossipSelect(action)`；且 `EventStarterEntry` 要求 `EventCompletionBossState`（`Scenario.cpp:768-778`），本副本不用 BossState；starter 被当成 ctx.boss | 新增例如 `FixtureGossipCreature=<entry>:<action>`，通过 `sScriptMgr->OnGossipSelect` 执行（小改） |
| 区域强制进战 | `EngageTrigger=pull` + `ScriptBossAcceptAutoEngage` | Epoch / Mal'Ganis 解除免疫时会 `SetInCombatWithZone`，框架需要接受「boss 自己进战」 | 与 gossip 键一起设计：gossip 后等 boss 可攻击或进战，确认方式用 `boss_in_combat`（小改） |
| 完成判据 | Kill = 血量 0 + 死亡事件（`AttemptObserver.cpp:767-806`） | Meathook / Salramm / Epoch / Corruptor 可用；**Mal'Ganis 不可用** | 新增 `EventCompletionInstanceData=0:11`，或者识别「Mal'Ganis `finished`」（血量被锁定且带 NON_ATTACKABLE）（小改） |
| 直接召唤 boss | 无 | Meathook / Salramm 没有任何 SetData 能直接召唤 | 若走隔离档：新增 `FixtureSummonCreature=<entry>:x,y,z,o`（小改，但属于「框架摆怪」，口径降级为隔离，且没有 Arthas 协助）；若走完整档：需要「按顺序追打召唤小怪波次」的编排能力（大改） |
| 清前置 | `PrerequisiteSpawns` | 只接受 DB spawn；波次和市政厅小怪都是临时召唤物，**不能作为前置** | — |
| 移除干扰单位 | `FixtureDespawnSpawns` | 可用（Corruptor 旁的僵尸） | — |
| 护送跟随 | `EventFollowStarter` | 依赖 EventStarterEntry 那一套，目前不可用 | Epoch 完整档需要跟随 Arthas 走市政厅（中等） |

---

## 7. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| Infinite Corruptor | `heroic-cos-corruptor-h5g` | 隔离（夹具召唤；跳过 26 分钟限时） | 待建 | 无硬阻塞（借用僵尸前置） | 见 §8 |
| Mal'Ganis | `heroic-cos-malganis-h5g` | 隔离（`0:10,6:2` 跳过前面剧情，**有 Arthas 协助**，与正常流程一致） | 待建 | gossip 键 + 完成判据（都是小改） | 框架加两个键 → 实测 Reset 时序 → 首轮基线 |
| Chrono-Lord Epoch | `heroic-cos-epoch-h5g` | 完整档：`0:7,6:2` + gossip 1003 + 市政厅约 15 只怪；或隔离档：直接召唤 | 待建 | 完整档：gossip + 跟随护送（中）；隔离档：召唤键（小） | 先做隔离档量 boss 本身，再决定是否做市政厅 gauntlet |
| Meathook | `heroic-cos-meathook-h5g` | 隔离（直接召唤）；完整档需清 4 组 | 待建 | 召唤键（小）；完整档需要追打波次（大） | 同上 |
| Salramm | `heroic-cos-salramm-h5g` | 隔离（直接召唤）；完整档需 Meathook + 4 组 | 待建 | 同上；bot 侧 Explode Ghoul 躲避 trigger 失效（entry 错） | 修 trigger 后再测 |

共用事实：instance 不用 BossState；5 个 boss 都没有 DB spawn；都不带 HARD_RESET；Arthas 的 Reset 会清掉除 Corruptor 外所有 boss；`0:<x>,6:2` 是脚本认可的跳进度方式；策略 `wotlk-cos` 由 map 595 自动挂载（`PlayerbotAI.cpp:1739-1741`），RuntimeStrategyName 恒等（`CombatTrigger.cpp:335-344`），只覆盖 Salramm（失效）和 Epoch。

---

## 8. 逐 boss 建议

- **Infinite Corruptor —— 现在就能用现有键建（隔离档）**，但方法比较别扭：
  `BossSpawnMode=script`、`EngageTrigger=pull`、`FixtureInstanceData=4:1`、`FixtureDespawnSpawns=1970881,1970885,1970882,1970890,1970893`（boss 身边的僵尸），`PrerequisiteSpawns=1970886`（或 1970892，约 55 码外的一只僵尸，只是为了满足 script 模式「必须有前置」的校验），`ScriptBossAppearTimeoutSeconds` 取小值。待实测：①僵尸游走，55 码外的前置在清怪时会不会把 Corruptor 带进战斗（会的话 Recovery 会作废，`AttemptRunner.cpp:1100-1110`）；②FindBossNear 的 200 码网格以 bot 为中心，准备点必须在 Corruptor 200 码内；③每个 run 只能打死一次。建议框架放开「script 模式不要求前置」后再去掉这只借来的僵尸。
- **Mal'Ganis —— 需要小的框架改动**：①gossip 键（`sScriptMgr->OnGossipSelect(tank, Arthas, 0, 1006)`）；②script 模式不要求前置，gossip 后等 boss 出现；③完成判据 `EventCompletionInstanceData=0:11`（或识别 finished 状态）。夹具 `FixtureInstanceData=0:10,6:2`。改完后保真度高：Arthas 协助、boss 行为与正常流程一致，只跳过前面的路程。
- **Chrono-Lord Epoch —— 隔离档需要小改，完整档需要中等改动**：隔离档加 `FixtureSummonCreature=26532:2451.81,1112.90,149.22,3.36`，但会失去 Arthas 协助，也没有剧情免疫阶段，结论要降级。完整档用 `0:7,6:2` + gossip 1003 + 跟随 Arthas 走完市政厅三场裂隙；gossip 键与 Mal'Ganis 共用，但还缺「跟随护送 NPC 并打他的召唤物」的编排。
- **Meathook —— 需要小的框架改动（仅隔离档）**：`FixtureSummonCreature=26529:2351.45,1197.81,130.45,3.83` + script 模式不要求前置。boss 脚本不依赖 instance，隔离保真度尚可。完整档（清 4 组分散的召唤小怪）需要大改，暂不做。召唤点周围的市民（faction 190）是否会干扰，待实测，必要时用 `FixtureDespawnSpawns` 移除。
- **Salramm —— 同 Meathook（仅隔离档，小改）**；另外 bot 侧 `ExplodeGhoulTrigger` 的 entry 错误（26125 vs 27733）是明确的 bot 缺陷，按「底层缺陷如实记录」，在 playerbots 开发分支修复后再测。
