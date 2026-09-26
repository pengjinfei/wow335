# 英雄映像大厅（Halls of Reflection，map 668）建场景前勘察

> 2026-09-26，只读勘察。资料来源：core 脚本 `Northrend/FrozenHalls/HallsOfReflection/`（下文简写：`h` = `halls_of_reflection.h`，`inst` = `instance_halls_of_reflection.cpp`，`hor` = `halls_of_reflection.cpp`，`falric` / `marwyn` = 两个 boss 文件）、mod-playerbots `Ai/Dungeon/` 与 `Bot/PlayerbotAI.cpp`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp` / `AttemptObserver.cpp`、world / characters DB、客户端 DBC（`data/world/dbc/Spell.dbc`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。

## 0. 总览

| 遭遇 | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 开战方式 | 完成信号 | 现框架能否直接开 |
|---|---|---|---|---|---|---|---|---|
| Falric（波次 1–5） | 38112 | 38599 | 1971983 | (5284.16, 2030.69, 709.32, 5.49) | 否（0 / 英雄 1=INSTANCE_BIND） | 波次事件：第 5 波 `DoAction(1)`，8 秒后 `SetInCombatWithZone` | `BossState(0)=DONE`（BossAI） | **差一点**：夹具可用现有键；缺「开战确认 ≥」与策略门（均为小改） |
| Marwyn（波次 6–10） | 38113 | 38603 | 1971984 | (5335.33, 1982.38, 709.32, 2.34) | 否（0 / 1） | 第 10 波 `DoAction(1)` | `BossState(1)=DONE` | 只能做 Falric+Marwyn 链式；**单独隔离要中等改动** |
| Frostsworn General（小 boss） | 36723 | 37720 | 1972019 | (5413.92, 2116.50, 707.70, 3.95) | 否（0 / 1） | 普通 pull（需 Marwyn DONE 才可见/主动） | `SetData(5, DONE)`；本身正常死亡 | **差一点**：现有键可表达，只卡策略门 |
| 巫妖王逃亡（Lich King escape） | LK 36954；领袖 37554（联盟运行时变 Jaina 36955） | 无（LK 0）；领袖无 | LK 1972025、领袖 1972026 | LK (5552.77, 2262.57, 733.01)；领袖 (5549.51, 2257.59, 733.01) | 否 | 领袖 gossip（`CreatureScript::OnGossipSelect`）→ `SetData(15)` | `BossState(2)=DONE`（LK 走完路径且 4 面冰墙都破） | **不能**：gossip 走的是 AI 钩子，对这个老式脚本无效；另需等 gossip 标志、失败后复位 |

- 副本共 58 条 creature：34 只波次灵魂（5 种 × 6/10）、5 只 Spiritual Reflection、4 个 Ice Wall Target、剧情 NPC 若干、3 只蜘蛛小动物。**逃亡通道上没有 DB 小怪**，逃亡的怪全部是巫妖王召唤的。
- 每只 boss 都**不是 HARD_RESET**（普通 entry `flags_extra=0`），evade 不会 despawn。
- 本地 bot 851–855 全是**联盟**（种族 3/1/1/11），副本里 `GetTeamIdInInstance()` 取联盟：Sylvanas Part1 37223 → Jaina 37221，Sylvanas Part2 37554 → Jaina 36955（`inst:196-203`、`inst:269-300` 的 `UpdateEntry`）。**DB 模板 id 与运行时 entry 不同**，场景键要注意（见 §4.4）。

### 0.1 instance 脚本要点（inst）

- `SetBossNumber(MAX_ENCOUNTER=3)`（`inst:161`），**用 BossState**：`DATA_FALRIC=0`、`DATA_MARWYN=1`、`DATA_LICH_KING=2`。`FixtureBossStates` / `EngageConfirmBossState` / `EventCompletionBossState` 都有效。
- 非 boss 数据（`h:36-52`，均走 `SetData`）：`DATA_INTRO=4`、`DATA_FROSTSWORN_GENERAL=5`、`DATA_BATTERED_HILT=6`、`DATA_LK_INTRO=7`、`DATA_WAVE_NUMBER=8`（**只读**，`GetData(8)` 返回当前波次 0–10）、`ACTION_SHOW_TRASH=11`、`ACTION_SPIRITUAL_REFLECTIONS_COPY/ACTIVATE/HIDE=12/13/14`、`ACTION_START_LK_FIGHT=15`、`ACTION_STOP_LK_FIGHT=16`、`ACTION_DELETE_ICE_WALL=17`。`GetData` 只认 8 和 6（`inst:597-608`），其他 id 一律读 0，所以 `KillOnInstanceData` / `EngageConfirmInstanceData` 只能用 id 8。
- **持久数据槽**（`h:117-124`，`FixturePersistentData` 的 index）：`0 INTRO`、`1 FROSTSWORN_GENERAL`、`2 LK_INTRO`、`3 BATTERED_HILT`。
- 没有 `DoAction` 覆盖 → **`FixtureInstanceAction` 对本副本无效**。
- 没有 boss boundary。波次阶段的出区判据在 instance `Update`：任一非 GM 玩家离 `CenterPos (5309.46, 2006.48)` 2D 距离 **> 70.5 码**，或全员死亡 → `HandleWaveWipe()`（`inst:824-849`，`h:129`）。
- `IsEncounterInProgress()` = 有玩家且波次非 0，或 LK 战斗进行中（`inst:185-188`）：此时核心拒绝**不在图内**的玩家进本（bot 若被传出副本再传回会被拒，待实测）。
- 门（gameobject）：前门 201976（guid 150291，(5264.61, 1959.44)，波次开始关、`HandleWaveWipe` 开）；通往将军走廊的 Impenetrable Door 197341（guid 150294，(5358.96, 2058.75)，Marwyn DONE 才开）；王座前后门 197342/197343（150210/150221，初始开）；Cave In 201596（150303，逃亡终点）。隔离场景直接传送，门不挡路。
- 冰墙 GO 201385 不是 DB spawn，由 LK 施 `SPELL_SUMMON_ICE_WALL 69768` 对 Ice Wall Target 召出；`ACTION_DELETE_ICE_WALL` 只是 `HandleGameObject(GO_ICE_WALL, true)`（开门式），**不删除旧墙**（`inst:528-530`）。

### 0.2 进本门槛

- `dungeon_access_template` id 117（英雄）：`min_level 80`、**`min_avg_item_level 219`**；`dungeon_access_requirements`：任务 **24710（联盟）/ 24712（部落）** Deliverance from the Pit 须已交。
- 851–855 的 `character_queststatus_rewarded` **24710、24712 都有**（PoS 那轮补的）→ 任务门槛满足。
- 平均装等门槛：`env/dist/etc/worldserver.conf` 里 `DungeonAccessRequirements.PortalAvgIlevelCheck = 0`（`PlayerStorage.cpp:7020` 只在开关打开时检查），且 raidtest 用 `TeleportTo` 直接传送 → 不拦 ilvl 200 档。但**英雄映像大厅是按 219 调的**（英雄 Falric HealthModifier 47、Marwyn 67、DamageModifier 13），ilvl 200 档可能明显吃力，首轮基线要单独看。
- 入口：`areatrigger_teleport` 5636 → (5239.01, 1932.64, 707.70)。**AT 5646 (5228.24, 1921.22) 是出口传送（回 571）**，准备点别放在入口传送门附近。
- 剧情 gossip 另有任务门（`hor:154-163`）：**选项 0「开始」需 24710/24712 已完成**（bot 满足）；**选项 1「跳过剧情」需 24500/24802 Wrath of the Lich King**（bot 没有）。

### 0.3 AreaTrigger（map 668）

| AT | 中心 | 形状 | 脚本 | 作用 |
|---|---|---|---|---|
| 5605 | (5539.65, 2247.05, 733.01) | 盒 20.5×94.5×72，o 3.94 | `at_hor_shadow_throne`（`hor:1456-1472`） | 将军已死（持久槽 1）且 LK_INTRO 未做 → `SetData(7, DONE)`：巫妖王对峙剧情 |
| 5632 | (5244.52, 1939.21, 707.70) | 盒 | `at_hor_battered_hilt_start` | 仅带 Quel'Delar 任务光环 70013 时生效，与本测试无关 |
| 5660 | (5276.17, 1971.70, 707.70) | 盒 | `at_hor_battered_hilt_throw` | 同上 |
| 5636 / 5646 | 入口 / 出口 | — | teleport | 进本 / 出本 |
| 5570、5689、5697、5740、5742、5752 | — | — | 无脚本、无 SmartTrigger | 无作用 |

波次事件与 LK 逃亡都**不靠 AT 开战**。

### 0.4 mod-playerbots 策略

- **没有映像大厅策略**：`Ai/Dungeon/` 下无 HoR 目录，`DungeonStrategyContext.h:48-64` 无 `wotlk-hor`；`PlayerbotAI::ApplyInstanceStrategies`（`PlayerbotAI.cpp:1649` 起）的 switch **没有 `case 668`**，`allInstanceStrategies` 列表也没有 `wotlk-hor`。全源码无 Falric/Marwyn/Frostsworn 的任何处理。
- **对框架的直接影响（阻塞，S）**：`AttemptRunner::StartBossPull`（`AttemptRunner.cpp:2206`）要求 `Strategy` 非空且已在所有 bot 的战斗引擎里激活，否则 `raid_invalid: instance combat strategy inactive before pull`；`EnsureCombatInstanceStrategy` 对空名直接返回 false（`RosterLogin.cpp:197-201`）。所以**所有走 StartBossPull 的场景（pull / self / areatrigger / gameobject）在本副本都会被拦**。只有 `EventStarterEntry` 路径不经过这道门（`AttemptRunner.cpp:957-964`、`1364-1379`）。两种解法：
  1. playerbots 加一个 `wotlk-hor` 骨架策略 + `case 668` + 列表项（S；LK 逃亡迟早要这个策略承载行为）；
  2. raidtest 允许显式声明「本图无副本策略」（如 `Strategy = none`）时跳过这道门（S）。
  推荐 1。

---

## 1. 波次事件与 Falric（38112 / 38599）

### 1.1 事件怎么开始

正常流程（全部由脚本驱动，**不是 Frostmourne 祭坛 GO 交互**：祭坛 202236 / 霜之哀伤 202302 只是模型和光效，没有 GO 脚本）：

1. 进本后领袖 Jaina（DB 37223 → 运行时 37221，guid 1971981，(5236.67, 1929.91)）的 AI `Reset()` 在持久槽 0 为 0 时排 pre-intro：10 秒现身、11 秒走到 SpawnPos (5263.22, 1950.96)、**19 秒挂 gossip + questgiver 标志**（`hor:224-237`、`278-281`）。
2. 玩家 gossip 选项 0 → `ACTION_START_INTRO`：联盟台词约 149 秒（`hor:313-412` 累计）+ 共用 LK 剧情约 75 秒（`hor:536-776`）；选项 1（跳过，需 24500）直接进共用 LK 剧情。
3. 共用剧情：巫妖王 37226 现身、Uther 消失，`EVENT_INTRO_LK_5`（`hor:637-666`）把 Falric / Marwyn 从隐身挪到 (5274.9, 2039.2) / (5343.77, 1973.86) 并走到各自 MovePos；`EVENT_INTRO_LK_8` `SetData(11)` 洗牌并显示 34 只灵魂；`EVENT_INTRO_END_SET` `SetData(DATA_INTRO=4, DONE)` → 写持久槽 0 并 `StartNextWave()` = 第 1 波（`inst:404-407`）。

**团灭后的自动重开**（本次隔离的关键）：instance `Update` 每 5 秒检查一次（`inst:824-870`）——持久槽 0 已置、Marwyn 未 DONE、当前无波次也无计时器时，**若全部非 GM 玩家都活着且离 CenterPos ≤ 40 码**（`MAX_DIST_FROM_CENTER_TO_START`，`h:130`），就走恢复序列（`inst:886-933`）：
- step 0：Falric、Marwyn 重新摆位、现身、走向 MovePos；
- 7.5 秒后 step 1：`SetData(ACTION_SHOW_TRASH)` 重新洗牌显示灵魂，`_nextWaveTimer = 7000`；
- 再 7 秒：第 1 波。

也就是说：**只要持久槽 0 = 1，全员站进大厅中心 40 码，约 15–20 秒后事件自己开始**。这是正常规则下「团灭后再来」的原生路径，只是跳过了一次性剧情。

### 1.2 波次结构（inst:651-779）

- `allowedCompositions`（`h:316-326`）：第 1、2 波各 3 只（组合 0/1 随机分配），第 3、4 波各 4 只（组合 2/3），第 6–9 波各 5 只（组合 4–7 随机排列）。**合计 3+3+4+4+5×4 = 34 只**，每只灵魂整场只用一次。第 5 波 = Falric，第 10 波 = Marwyn。（「8 波各 5 只」的说法不准确：前 4 波是 3/3/4/4。）
- 激活：灵魂去 NOT_SELECTABLE、去免疫、`DoAction(1)` → `SetInCombatWithZone()` 并 `AttackStart(SelectTarget(MaxDistance))`——**先打离它最远的人**（通常是远程/治疗）。灵魂站在大厅四周 28–36 码的圆上，同一波来自不同方向。
- 计时：每波开始 `_nextWaveTimer = 150000`；该波（累计）剩余灵魂全死且当前不是第 5/10 波时缩到 5 秒（`inst:635-636`）。**打得慢会叠波**（150 秒硬计时）。第 5 波不设计时，等 Falric 死：`SetBossState(0, DONE)` → 60 秒后第 6 波（`inst:344-351`）。
- 团灭 `HandleWaveWipe()`（`inst:781-817`）：波次归 0、开前门、所有已激活灵魂复位回原位并隐藏、Falric/Marwyn `EnterEvadeMode`，5 秒后隐藏全部。`_falricPhaseComplete` **不清**（见 §2.3）。
- Falric/Marwyn 的 `BossAI` evade → `SetBossState(NOT_STARTED)` → 同样触发 `HandleWaveWipe`（`inst:344-358`）。

灵魂技能（`hor:782-1330`；英雄 entry 38524/38525/38544/38563/38564，HealthModifier 10.5、DamageModifier 13）：
- Ghostly Priest 38175：暗言术痛、**Circle of Destruction**（10 码 AoE）、**Cower in Fear**（20 码内单体恐惧 4 秒）、**Dark Mending**（给友方回血）。
- Phantom Mage 38172：火球、**Flamestrike**（5 码地面）、寒冰箭、冰链；40 秒召 Phantom Hallucination 38567（死时 AoE）。
- Shadowy Mercenary 38177：暗影步、致命毒药、毒刃投掷、肾击。
- Spectral Footman 38173：盾击、Spectral Strike、激怒。
- Tortured Rifleman 38176：射击、诅咒之箭、冰霜陷阱、冰霜射击。

### 1.3 Falric 脚本（boss_falric.cpp）

- `Reset()`：`SetImmuneToAll(true)`（`falric:53-60`），模板 unit_flags 832（IMMUNE_TO_PC | IMMUNE_TO_NPC）；instance 创建时隐身（`inst:218-221`）。**任何 pull 都开不了他**。
- `DoAction(1)`（第 5 波）：喊话，8 秒后 `SetImmuneToPC(false)` + `SetInCombatWithZone()`（`falric:72-85`）。这 8 秒内 evade 会 `Reset()`。
- 技能（`falric:87-137`，DBC）：
  - Quivering Strike 72422：每 5 秒打坦克（60% 武器伤害 + 减益）。
  - Impending Despair 72426：每 12 秒，45 码随机玩家，6 秒周期触发光环（结束时触发效果），可驱散（待核对驱散类型）。
  - **Defiling Horror 72435**：20 秒首发、每 20 秒，全场 **恐惧 4 秒 + 周期伤害**，Falric 同时定身 4 秒、其他技能推迟 5 秒。
  - **Hopelessness** 72395/72396/72397：血量 67%/34%/11% 各一次，100 码敌对光环，**伤害与治疗 −20%/−40%/−60%**（替换上一层）。打到后段输出和治疗都被砍一大截。
- `JustDied`：BossAI → `BossState(0)=DONE`。

### 1.4 附近的怪

大厅里只有波次灵魂（34 只，guid 1971985–1972018，全部在 CenterPos 28–36 码的圆上，z 707.78，模板 NOT_SELECTABLE + 免疫，事件激活前不可攻击）和 2 只蜘蛛小动物（202290 距中心 28.7 码、202296 距中心 55 码）。代表性位置：

| entry | 名称 | guid 范围 | 例 |
|---|---|---|---|
| 38177 | Shadowy Mercenary | 1971985–1971990 | 1971989 (5335.72, 1996.86) |
| 38173 | Spectral Footman | 1971991–1972000 | 1971998 (5313.82, 1978.15) |
| 38176 | Tortured Rifleman | 1972001–1972006 | 1972002 (5337.86, 2003.40) |
| 38175 | Ghostly Priest | 1972007–1972012 | 1972010 (5280.51, 1997.84) |
| 38172 | Phantom Mage | 1972013–1972018 | 1972016 (5279.65, 2004.66) |

完整列表可 `select guid,id,position_x,position_y from creature where map=668 and id between 38172 and 38177`。**不能用 `FixtureDespawnSpawns` 删灵魂**：instance 按 GUID 数组调度（`_trashGUID`），缺了会让波次凑不齐（`StartNextWave` 找不到 entry 就少一只）甚至改变击杀计数。

### 1.5 场景建议（heroic-hor-falric-h5g）

- **夹具**：`FixturePersistentData = 0:1`（持久槽 INTRO=1）。其余交给 §1.1 的原生自动重开。**不要**用 `FixtureInstanceData = 4:x`：`SetData(4)` 每调一次就 `StartNextWave()` 一次，且没先洗牌（组合全 0）时第 1 波一只灵魂都不激活。
- **准备点**：大厅中心 40 码以内、地面 z 707.7 附近，远离四周灵魂圈（28–36 码）。候选 **(5300.0, 1995.0, 707.7)**（离中心约 14.6 码，待实测），坦克稍前、远程在后。5 人必须**全部活着**且都在 40 码内，否则永远不会开。
- **开战**：`EngageTrigger = self`，`EngageConfirmInstanceData = 8:1`（波次 1 出现即确认，约 15–20 秒，在 self 的 120 秒预算内）。`BossEntry = 38112`，默认 database 模式（Falric 是 DB spawn，全程在图里，只是隐身/免疫）。
- **完成**：Falric 正常死亡（BossDeathSeen + 血量 0）。`TimeoutSeconds` 建议 600（4 波最坏 4×150 秒 + Falric）。
- **框架缺口 A（S）——开战确认只认 `==`**：observer 的「遭遇进行中」判据（`AttemptObserver.cpp:915-935`）用 `GetData(id) == value`。第 2 波起 `GetData(8)=2`，判据失效，而 Falric 在第 5 波前一直不在战斗、也没人死 → 约 4–8 秒后 `aborted (stuck)`。需要一个 `>=` 版本（例如新键 `EngageConfirmInstanceDataMin = 8:1`，同时用于开战确认和 observer 的 encounterStateActive）；波次归 0（团灭复位）时自然失效，stuck/wipe 规则照常。`EngageConfirmBossState = 0:1` 不行：Falric 要到第 5 波才 IN_PROGRESS，远超 120 秒预算。
- **框架缺口 B（S）——策略门**：见 §0.4。
- **风险（待实测）**：
  1. 自动重开不受框架控制：只要全员活着站在 40 码内，事件就会自己开始——包括两次 attempt 之间 bot 回到准备点、还在换装/回血的时候。建议**每个 run 1 次 attempt**（沿用 ToC5 冠军 run1323–1328 的做法），或把框架的 attempt 间整备放在 40 码外。
  2. 出区 70.5 码：恐惧（Defiling Horror、Cower in Fear）和 bot 追怪可能把人带出圈 → 整场复位；首轮看复位原因日志。
  3. 灵魂事件激活前是 NOT_SELECTABLE + 免疫，理论上 bot 不会去打；bot 的 `possible targets` 是否会把它们列入（进而空转），待实测。
- **bot 缺口**：
  - 缺口 1（中）：波次小怪每只都先扑最远的人，同时 3–5 只来自不同方向。靠通用坦克/AoE 逻辑；击杀优先级（先 Priest 的 Dark Mending、Mage 的 Flamestrike/幻象）无专门处理。改优先级前先量「输出比 vs 只数比」（memory：改「先打谁」前先量两个比值）。
  - 缺口 2（小–中）：Defiling Horror 全场恐惧——无预防（防护恐惧结界、战栗图腾）逻辑，靠治疗扛。
  - 缺口 3（小）：Impending Despair 驱散、Flamestrike 地面靠 `MasterlessAvoidAoe = 1` 和通用驱散（待实测是否识别）。
  - 缺口 4（无对策，量即可）：Hopelessness 伤害/治疗 −60% 使后段变成总量问题，ilvl 200 档可能是瓶颈（参见 memory「装备才是杠杆」）。

---

## 2. Marwyn（38113 / 38603）

### 2.1 脚本（boss_marwyn.cpp）

- 同 Falric：`Reset()` 全免疫，隐身，第 10 波 `DoAction(1)` 8 秒后进战（`marwyn:54-85`）。
- 技能（`marwyn:87-127`，DBC）：
  - Obliterate 72360：15 秒首发，每 15 秒，坦克近战范围内才放（否则 3 秒后重试），普通 18000 物理，英雄更高。
  - **Well of Corruption 72362**：13 秒首发，每 13 秒，40 码随机玩家脚下 **3 码持久区域（dynobject）**，8 秒。
  - **Corrupted Flesh 72363**：20 秒首发，每 20 秒，AoE 光环 8 秒（DBC aura 133，−25%，具体含义待核对：生命上限或治疗受到）。
  - **Shared Suffering 72368**：5 秒首发，每 15 秒，200 码随机玩家，12 秒周期伤害（每 3 秒 4000）。**被驱散时**剩余伤害按存活人数平分，由 72373 打到目标周围（`spell_hor_shared_suffering_aura`，`marwyn:157-203`）。机制上驱散是对的（分摊）。
- `JustDied` → `BossState(1)=DONE` → 开前门与 Impenetrable Door、Frostsworn General 现身并主动、全员施 71351（任务脚本法术）（`inst:353-377`）。

### 2.2 附近的怪

与 Falric 同一大厅，第 6–9 波共 20 只灵魂。

### 2.3 能不能单独隔离

**现有键做不到干净的 Marwyn 单打**：
- 跳过第 1–5 波靠 instance 私有成员 `_falricPhaseComplete`（`inst:680-702`、`719-720`）。它只在本实例里真的推进到第 6 波时置 true，不持久化，也没有任何 SetData 入口。
- `FixtureBossStates = 0:3`（Falric DONE）无用：在 `_waveNumber == 0` 时 `SetBossState` 什么都不做；自动重开仍从第 1 波开始，第 5 波时 Falric 还活着就会照常出场。
- 如果让 Falric 处于「在图里但已死」（`StartNextWave` 看到 `!IsAlive()` 会跳过第 5 波，`inst:737-743`），需要一个「杀掉指定 spawn」的夹具；`FixtureDespawnSpawns` 走 `DespawnOrUnsummon`，DB 生物会进入尸体/待重生状态，`GetCreature` 是否仍返回它（返回 null 会让第 5 波永远卡住）**待实测**。即便成立，也只是「第 1–4 波 + 第 6–9 波 + Marwyn」，不是隔离。
- 自然路径：同一实例里先杀 Falric，然后在 6–9 波或 Marwyn 团灭，`_falricPhaseComplete` 已为 true，重开时直接从第 6 波开始。可以作为链式场景的第 2 次及以后 attempt（前提是框架 attempt 间不复位 Falric——`ResetInstance` 只复位 `BossEntry` 的 DB spawn，BossEntry=Marwyn 时 Falric 不动；待实测）。

### 2.4 场景建议（heroic-hor-falric-marwyn-h5g，链式）

- 与 §1.5 相同的夹具、准备点、开战方式和框架缺口 A/B；`BossEntry = 38113`，`TimeoutSeconds = 1080`（1–4 波 + Falric + 60 秒 + 6–9 波 + Marwyn，最坏约 15 分钟）。
- Falric 死亡不是本场景的终点：观察器以 Marwyn 为 boss，Falric 死时 Marwyn 血量 100%，`bossDown` 需要 `hpPct == 0`，不会误判。
- 中间 60 秒空档（Falric DONE → 第 6 波）全员脱战、无人死亡：同样依赖缺口 A 的 `>=` 判据（`GetData(8)=5`）才不会被判卡住。
- bot 缺口：
  - 缺口 5（小–中）：Well of Corruption 地面区域，靠 `MasterlessAvoidAoe = 1` 识别 dynobject（待实测）。
  - 缺口 6（小）：Shared Suffering 应被驱散（分摊伤害）；playerbots 通用驱散是否驱它、驱的时机，待实测。
  - 缺口 7（小）：Obliterate 坦克硬吃，靠减伤/治疗。

---

## 3. Frostsworn General（36723 / 37720）

### 3.1 脚本（hor:1339-1454）

- DB spawn 1972019，(5413.92, 2116.50, 707.70)，Impenetrable Door 后的走廊中段。instance 创建时若 Marwyn 未 DONE → 隐身 + REACT_PASSIVE（`inst:237-243`）；Marwyn DONE 时由 `SetBossState` 现身并主动（`inst:362-368`，**只在 `_waveNumber != 0` 的分支里**——夹具直接 `SetBossState(1, DONE)` 时波次为 0，不会让已存在的将军现身）。
- `JustEngagedWith`：`SetData(12)` 给每个活着的玩家一只 Spiritual Reflection（DB guid 1972020–1972024，悬浮在 z 716.4）复制外观；8 秒后 `SetData(13)` 反射体跳下参战（Baleful Strike 69933 普通 2025；死亡时 Spirit Burst 69900 15 码 AoE）。Throw Shield 69222：6 秒首发，每 10 秒，40 码随机玩家，7400 + 效果。
- **离家 30 码就 evade**（`hor:1366-1371`），evade 时隐藏所有反射体。
- `JustDied` → `SetData(5, DONE)`：写持久槽 1，让 LK 36954 与领袖 37554/36955 现身。

### 3.2 附近的怪

走廊里只有 5 只反射体（事件召唤外观，平时隐身）和 1 只蜘蛛 202304 (5386.99, 2080.50)。没有 DB 小怪。

### 3.3 场景建议（heroic-hor-general-h5g，隔离）

- 夹具（现有键即可）：`FixtureBossStates = 1:3`（Marwyn DONE，先于召唤执行，使新召唤的将军在 `OnCreatureCreate` 里不被隐藏）+ `FixtureDespawnSpawns = 1972019`（移除隐身的 DB 将军，免得两个同 entry 叠在一起）+ `FixtureSummonCreature = 36723:5413.92,2116.50,707.70,3.95` + `BossSpawnMode = script`。召出的将军会被 ObjectData 登记为 `NPC_FROSTSWORN_GENERAL`，反射体逻辑用的就是它；家位置 = 召唤点，30 码 evade 圈以召唤点为圆心。
- `EngageTrigger = pull`，准备点在门后走廊西段，候选 **(5385, 2090, 707.7)**（离将军约 38 码，待实测；离门 197341 约 40 码）。`TimeoutSeconds = 300`。
- 阻塞：仅 §0.4 策略门（S）。
- bot 缺口：
  - 缺口 8（小）：反射体（玩家克隆）与将军同时在场，击杀顺序与 Spirit Burst 站位无处理；30 码 evade 圈要求坦克别把将军拖远（参见 memory「躲避动作没有边界判据」）。

---

## 4. 巫妖王逃亡（LK 36954；领袖 37554 → Jaina 36955）

### 4.1 前置剧情与开始方式

1. 将军死 → `SetData(5, DONE)`：持久槽 1，LK 与领袖现身（`inst:411-420`）。
2. 玩家进 AT 5605（王座间）→ `SetData(7, DONE)`：持久槽 2，领袖 `DoAction(ACTION_START_INTRO)`（`inst:469-473`）。领袖对峙巫妖王：约 9 秒后 Jaina 施 Ice Prison 69708 冻住 LK，再 5 秒 `EVENT_SAY_LEAVE`（全员获得 37554/36955 击杀信用，给任务用）并跑到 **LeaderEscapePos (5576.81, 2235.55, 733.01)**，**7 秒后挂 gossip 标志**（`hor:1793-1798`、`1864-1908`）。从 `SetData(7)` 到可 gossip 约 21 秒。
3. 玩家与领袖 gossip → `npc_hor_leader_second::OnGossipSelect`（**`CreatureScript` 级**，`hor:1746-1762`，不看 action）→ `EVENT_START_RUN`：`SetData(15)` → `BossState(2)=IN_PROGRESS`、领袖 `setActive` 并跑向第 1 停靠点；LK 去冰牢、`SetInCombatWithZone`、1.5 秒后沿 `PathWaypoints[0..2]` 追（`hor:1909-1922`、`1666-1675`）。

### 4.2 逃亡机制（npc_hor_lich_king，hor:1501-1739）

- LK 是 **NullCreatureAI**，血量掉到 70% 以下立刻回 75%（`hor:1607-1608`），**打不死、也不该打**；每秒 `SetInCombatWithZone()` 把全员拉进战斗（`hor:1632-1634`）。
- 路径：19 个路点（`h:356-377`，z 从 733 升到 785），领袖停靠点 `WP_STOP = {0, 5, 8, 10, 14, 18}`；4 个 Ice Wall Target（DB 1972027–1972030，(5550.62, 2079.75)、(5504.2, 1974.7)、(5445.09, 1881.48)、(5321.39, 1758.07)）。
- LK 走到第 2 路点 → 喊话、对第 1 墙目标施冰墙，4 秒后上 **Remorseless Winter 69780**（自身光环：周期触发 + 附近减速 75%），改走剩余全程路径 3..17，1 秒后召第 1 波（`hor:1546-1562`、`1676-1689`）。
- 每面墙的召唤（`hor:1690-1722`）：墙 1 = 食尸鬼（69818，周期召唤光环）+ 1 Risen Witch Doctor 36941；墙 2 = 1 Lumbering Abomination 37069 + 食尸鬼 + 2 巫医；墙 3 = 2 憎恶 + 食尸鬼 + 2 巫医；墙 4 = 3 憎恶 + 4 巫医 + 两批食尸鬼。食尸鬼每批只数待实测（69818 是 3 秒、0.5 秒周期的触发光环，英雄可能换法术）。召唤物主动找 350 码内最近玩家（+1000 仇恨），home 设在下一停靠点（`hor:1571-1584`）。英雄：憎恶 37549（HP×15，Vomit Spray 10 码锥形 + Cleave）、巫医 37551（HP×7.5，Curse of Doom、暗影箭、30 码暗影箭雨）、食尸鬼 37550（Leap）。
- 本墙召唤物全死 → `WallCompleted()`：开墙、1 秒后召下一面墙、7.5 秒（第 3 墙后 11 秒）后召下一波，并通知领袖跑向下一停靠点（`hor:1531-1544`、`1802-1806`、`1816-1828`）。第 4 墙破后 LK 去掉 Remorseless Winter。
- **失败条件**：
  - LK 与领袖 2D 距离 ≤ 12.5 码（且领袖 x < 5575、LK 带 Remorseless Winter）→ Harvest Soul 70070 定住领袖，3 秒后 `Unit::Kill` 领袖 + **Fury of Frostmourne 70063（全场 1,000,000）**（`hor:1619-1631`、`1657-1665`）。领袖 `DamageTaken` 把致死伤害截到 1 血（`hor:1810-1814`），所以只会以这种方式死。
  - LK 带 Remorseless Winter 期间，每 2 秒对「在他身后」的玩家（`(px − lkx) + (py − lky) > 20`，路径是 x、y 递减方向）施 Zap，**10000 伤害**（`hor:1639-1646`、`1599-1603`）。掉队 / 被击退到 LK 后面的 bot 会被连续秒。
- **完成**：LK 走完路径时若 `currentWall == 4` → `SetBossState(2, DONE)`（`hor:1563-1567`）。之后 instance 播结尾：炮艇、Cave In、**英雄模式 `PermBindAllPlayers()`**、全员 `KilledMonsterCredit(38211)`（`inst:961-1103`）。
- **复位**：只有**图里没有玩家**时，LK 才 `summons.DespawnAll()` 并 `SetData(16)`（`hor:1649-1653`）。`SetData(16)` 本身（`inst:480-530`）：复活/送回领袖到 LeaderEscapePos 并恢复 gossip、LK 回家并重挂冰牢、`BossState(2)=FAIL`、开冰墙——但**不清召唤物、不删已召出的冰墙 GO**。bot 死在图里时，这套复位永远不会自动发生。

### 4.3 附近的怪

逃亡路线上**没有 DB 小怪**；王座间只有 LK 1972025、领袖 1972026、Cave In Dummy 1972031（终点）。

### 4.4 框架能力对照与缺口

| 需求 | 现有键 | 是否可用 | 缺什么 |
|---|---|---|---|
| 跳过前三战与对峙剧情 | `FixtureInstanceData = 5:3,7:3` | 可用：`SetData(5)` 写持久槽 1 并让 LK/领袖现身，`SetData(7)` 写持久槽 2 并播对峙（约 21 秒后可 gossip） | — |
| gossip 开始事件 | `EventStarterEntry` | **不可用**：`StartScriptedEventGossip` 调的是 `starter->AI()->sGossipSelect(tank, 0, 0)`（`AttemptRunner.cpp:2524`），领袖 AI 是 NullCreatureAI，**真正的逻辑在 `CreatureScript::OnGossipSelect`**，调用石沉大海（HoS Brann 能用，是因为他写在 AI 的 `sGossipSelect` 里，`brann_bronzebeard.cpp:183`） | **缺口 C（S）**：先走 `sScriptMgr->OnGossipSelect(player, creature, GOSSIP_SENDER_MAIN, action)`（与客户端选项包的核心路径一致），返回 false 再调 AI；action 可配（Part1 领袖需要 `GOSSIP_ACTION_INFO_DEF+1 = 1001`） |
| 等 gossip 标志 | 无 | `StartScriptedEventGossip` 看到没有 gossip 标志就立刻 `Abort("starter gossip unavailable")`；夹具刚写完时领袖还在对峙 | **缺口 D（S）**：在 N 秒内轮询 `UNIT_NPC_FLAG_GOSSIP`（`AttemptStartDelaySeconds` 在传送前等待，帮不上） |
| DB 模板 id ≠ 运行时 entry | `BossSpawnMode = script` | 可用：script 模式按运行时 entry 在 200 码网格里找（`AttemptRunner.cpp:1594-1611`），`BossEntry = EventStarterEntry = 36955`；database 模式的 `ResetInstance` 按 DB id 37554 建复位目标，与 36955 对不上（待实测会不会判 `scene_invalid`） | — |
| 完成判据 | `EventCompletionBossState = 2` | 可用 | — |
| 事件阶段 | `EventPhases = 2:1` | 可用（`BossState(2)=IN_PROGRESS` 即已起跑；单阶段不会再次 gossip） | — |
| 护送者死亡 = 团灭 | `EventFailureEscortEntry = 36955` | 可用（领袖只会被 Harvest Soul 杀死） | — |
| 跟随 | `EventFollowStarter = true` | 可用：脱战时跟 Jaina | — |
| 失败后复位 | `FixtureInstanceData = 16:1` | 部分：能送回领袖/LK、置 FAIL，但残留召唤物和冰墙 GO 不会清 | 每个 run 1 次 attempt（新实例），或 **缺口 E（M）**：复位时清 LK 召唤物与冰墙 GO |
| 击杀后再打 | — | 不可：DONE 后 LK 隐身、英雄 PermBind | 每个 run 1 次 attempt |

- 场景草案（缺口 C、D 修好后）：`MapId = 668`、`BossEntry = 36955`、`BossSpawnMode = script`、`EventStarterEntry = 36955`、`EventPhases = 2:1`、`EventCompletionBossState = 2`、`EventFailureEscortEntry = 36955`、`EventFollowStarter = true`、`EventTrackEntries = 37069,36941,36940`（憎恶优先打骷髅标记）、`FixtureInstanceData = 5:3,7:3`、`MasterlessAvoidAoe = 1`、`TimeoutSeconds = 600`；准备点 = 开怪点，候选 **(5582.0, 2230.0, 733.0)**（LeaderEscapePos 东南侧 7 码，在 LK「身后」判据的前方，待实测）。`Strategy` 在事件路径上不校验，可先不填（填了也不会被这条路径检查）。
- 结论口径：隔离（跳过前三战与对峙剧情），逃亡本身完整。

### 4.5 bot 缺口

- **缺口 9（大，最可能的失败点）——别打巫妖王**：LK 敌对（faction 2102）、可攻击、每秒拉全员进战斗、血量 2000 倍且回血，bot 的通用目标选择很可能锁定他（尤其坦克），站在他身边吃 Remorseless Winter 减速并被他追上领袖。需要 HoR 策略：LK 乘数置 0 / 禁止作为目标，优先清召唤物。
- **缺口 10（大）——跑在 LK 前面**：杀完一波要立即跟领袖前进；掉队进入 LK 身后 20 码判据会被 Zap 连秒；击退（憎恶 Cleave、Vomit Spray）也会把人推到后面。`EventFollowStarter` 只在脱战时跟随，战斗中不管位置。
- 缺口 11（中）：每面墙是 DPS 竞速（LK 匀速逼近），第 4 墙 3 憎恶 + 4 巫医 + 两批食尸鬼，AoE 与击杀顺序（巫医的暗影箭雨、诅咒）决定成败；ilvl 200 档可能不够。
- 缺口 12（小）：地形高差（z 733 → 785）上的寻路，待导航实测（memory：los 证不了导航网格）。

---

## 5. mod-raidtest 能力对照（汇总）

| 需求 | 现有键 | 在 HoR 是否可用 | 缺什么 |
|---|---|---|---|
| 副本策略门 | `Strategy`（StartBossPull 强制） | **全部 pull/self 场景被拦**（无 `wotlk-hor`、无 `case 668`） | 缺口 B（S）：playerbots 加骨架策略，或 raidtest 允许声明无策略 |
| 跳过波次剧情 | `FixturePersistentData = 0:1` | 可用，触发原生「团灭后重开」 | — |
| 波次期间保持「遭遇进行中」 | `EngageConfirmInstanceData`（只 `==`） | 仅第 1 波有效 | 缺口 A（S）：`>=` 版本 |
| Marwyn 单打 | 无 | 不可 | M：需要能置 `_falricPhaseComplete` 的入口（core 脚本无）或接受链式 |
| 将军隔离 | `FixtureBossStates` + `FixtureDespawnSpawns` + `FixtureSummonCreature` + script 模式 | 可用 | 仅缺口 B |
| 老式 CreatureScript gossip | `EventStarterEntry` | **不可用** | 缺口 C（S） |
| 等 gossip 标志 | 无 | — | 缺口 D（S） |
| LK 逃亡完成 | `EventCompletionBossState = 2` | 可用 | — |
| LK 失败复位 | `FixtureInstanceData = 16:1` | 部分 | 缺口 E（M），或每 run 1 attempt |
| instance DoAction | `FixtureInstanceAction` | 无效（HoR 不覆盖 DoAction） | 不需要 |

## 6. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| Falric（含 1–4 波） | `heroic-hor-falric-h5g` | 隔离（跳过开场剧情，波次完整） | 待建 | 框架：缺口 A、B（均 S） | 修 A/B → 实测准备点（40 码内、全员存活）→ 首轮基线，统计每波用时、叠波次数、出区复位次数、Hopelessness 后输出 |
| Frostsworn General | `heroic-hor-general-h5g` | 隔离（夹具置 Marwyn DONE 并召出） | 待建 | 缺口 B（S） | 修 B → 实测准备点 → 基线 |
| Falric + Marwyn（含 1–9 波） | `heroic-hor-falric-marwyn-h5g` | 链式（跳过开场剧情） | 待建 | 同 Falric；Marwyn 单打需 M | Falric 稳定后再跑 |
| 巫妖王逃亡 | `heroic-hor-escape-h5g` | 隔离（跳过前三战与对峙剧情），逃亡完整 | 待建 | 框架：缺口 C、D（S），E（M，或每 run 1 attempt）；bot：缺口 9、10（L） | 修 C/D → 跑一场看 bot 是否打 LK、能否跟上 → 再决定 HoR 策略范围 |

## 7. 优先级建议

1. **现在就能建、只差小改的**（先做，同一批小改覆盖三个场景）：
   - 缺口 B（策略门，S）：推荐在 playerbots 加 `wotlk-hor` 骨架（`DungeonStrategyContext` 注册 + `PlayerbotAI.cpp` `case 668` + `allInstanceStrategies` 列表），后续 LK 行为直接挂在上面。
   - 缺口 A（`EngageConfirmInstanceData` 的 `>=` 版本，S）。
   - 修完即可跑 **Frostsworn General**（只需 B，纯现有键，最快出结果）和 **Falric**（A+B）。
2. **小框架改动后可建**：**巫妖王逃亡**——缺口 C（gossip 走 `sScriptMgr->OnGossipSelect`）+ D（轮询 gossip 标志），均为编排层，不代写 bot 行为；每个 run 只跑 1 次 attempt 规避缺口 E。第一轮的目的只是看清 bot 在逃亡里的真实表现。
3. **大的**：
   - 逃亡的 bot 行为（缺口 9 不打 LK、缺口 10 跑在 LK 前、缺口 11 墙间竞速）——需要新写 HoR 策略，属 playerbots 大改，按「大改先跳过记下待确认」处理。
   - Marwyn 单独隔离（M）——没有干净入口，建议直接用链式场景，不为它改框架。
   - 完整形态（真人式 gossip 选项 0 + 约 3.7 分钟剧情 + 波次 + 将军 + 逃亡的全链）：缺口 C 修好后可以用 `EventStarterEntry = 37221`（action 1001）从开场剧情开始，但一次 attempt 近 20 分钟、失败后复位不受控，排最后。
