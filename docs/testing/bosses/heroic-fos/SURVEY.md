# 英雄灵魂洪炉（The Forge of Souls，map 632）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `Northrend/FrozenHalls/ForgeOfSouls/`、mod-playerbots `Ai/Dungeon/FoS`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp`）、world DB 和客户端 DBC（`data/world/dbc/Spell.dbc`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。

## 0. 总览

| boss | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 脚本基类 | 开战方式 | 现框架能否正常开战 |
|---|---|---|---|---|---|---|---|---|
| Bronjahm | 36497 | 36498 | 201707 | (5297.31, 2506.46, 686.15, 3.25) | 否（0 / 1） | BossAI（DATA_BRONJAHM=0） | 普通 pull | **能**：`EngageTrigger=pull` |
| Devourer of Souls | 36502 | 37677 | 201736 | (5661.75, 2507.39, 708.91, 4.08) | **是**（普通 entry 36502 带 0x80000000；判定用 `GetEntry()`=普通 entry，英雄同样生效） | BossAI（DATA_DEVOURER=1） | 普通 pull | **能**：pull；HARD_RESET 由 `ResolveOrRestoreSpawn()` 兜底 |

- 两个英雄 entry 的 `flags_extra` 都只有 1（INSTANCE_BIND）。HARD_RESET 的判定在 `CreatureAI::EnterEvadeMode` 末尾，读的是 `sObjectMgr->GetCreatureTemplate(me->GetEntry())`，`GetEntry()` 永远是普通 entry（`Creature::InitEntry` 里 `SetEntry(Entry)`），所以**英雄模式下 Devourer 同样会在 evade 后 `DespawnOnEvade()`**（默认 20 秒重生）。
- 模板 `unit_flags`：Bronjahm 32832，Devourer 64，开局即可攻击，没有剧情门禁。faction 16（敌对）。
- 副本共 117 条 `creature` 记录（spawnMask 全为 3）。其中 36967「Spiteful Apparition (Ambient)」是 unit_flags 33554688（不可选中）的氛围怪，下文列怪时排除。

### 0.1 instance 脚本（instance_forge_of_souls.cpp）

- **用 boss 状态**：`SetBossNumber(MAX_ENCOUNTER=2)`，`DATA_BRONJAHM=0`、`DATA_DEVOURER=1`。BossAI 在 `JustEngagedWith` / `JustDied` / `JustReachedHome` 里自动置 IN_PROGRESS / DONE / NOT_STARTED。所以 `EngageConfirmBossState`、`FixtureBossStates` 在本副本**有效**（与 UP/PoS 不同）。
- **没有覆盖 `CheckRequiredBosses`**：Devourer 不要求 Bronjahm 先死。隔离场景不需要任何进度夹具。
- **boss boundary**（`LoadBossBoundaries`，boss 自己出界就 `EnterEvadeMode(EVADE_REASON_BOUNDARY)`）：
  - Bronjahm：圆 (5297.3, 2506.45) 半径 100.96；
  - Devourer：平行四边形，三个角 (5663.56, 2570.53)、(5724.39, 2520.45)、(5570.36, 2461.42)。
- 覆盖 `SetBossState`：两个都 DONE 时 `HandleOutro()`（召 Sylvanas/Jaina Part2 与一群勇士，纯剧情）。
- **开场剧情纯装饰**：Sylvanas 37596（部落）/ Jaina 37597（联盟）guid 1972092 在入口 (4899.98, 2208.16, 638.82)，gossip 选项触发 `DoAction(1)` 播 6～8 句台词，**不改任何实例数据、不解锁任何东西**。bot 不点也不影响开战。
- 门：副本内没有门 GO（只有入口/出口传送门和 Crucible Brazier 201600，任务用）。
- AreaTrigger：5642（入口出口传送）、5688（出口传送）、5672 (5661.35, 2507.09, 708.83) 球半径 10.4（就在 Devourer 脚下，**没有 areatrigger_scripts / SmartTrigger**，不影响遭遇）。

### 0.2 mod-playerbots 策略

- context key 与 `getName()` 都是 **`wotlk-fos`**（`DungeonStrategyContext.h:64`，`FoSStrategy.h:16`）。`PlayerbotAI.cpp:1775` 在 `case 632` 自动挂载。RuntimeStrategyName 恒等，不用补表。
- 全部内容：

| boss | trigger → action（优先级） | multiplier |
|---|---|---|
| Bronjahm | `move from bronjahm` → `move from bronjahm`（MOVE+5：boss 正在施 Corrupt Soul 68839 且自己中了时，离 boss 10 码内就 `FleePosition` 15 码）；`switch to soul fragment` → `attack corrupted soul fragment`（RAID+2：50 码内有活的 Corrupted Soul Fragment 36535 时**只给它挂骷髅标记**，action 返回 false，不直接攻击）；`bronjahm position` → `bronjahm group position`（RAID+1：坦克无碎片时走到 `BRONJAHM_TANK_POSITION` (5297.92, 2506.70, 686.07)，碎片在坦克与 boss 之间时绕到 boss 背面 5 码；非坦克在 Soulstorm 光环/施法期间向 boss 靠近到远程 6.5 码、近战 2 码） | `BronjahmMultiplier`（已注册）：boss 在场时**所有 bot 的 `TankAssistAction` 置 0**；中 Corrupt Soul 时除 `MoveFromBronjahmAction` 外的移动全部置 0。`AttackFragmentMultiplier` 定义了但**没注册** |
| Devourer | `devourer of souls` → `devourer of souls`（RAID+1：boss 身上有「mirrored soul」光环时，非坦克非治疗转身背对 boss，靠「不面向就不能出手」停手） | 无 |

- Mirrored Soul 69051 的 DBC：效果 0 = SCRIPT_EFFECT(77) 对目标，效果 1 = dummy 光环对目标，**效果 2 = dummy 光环对施法者自己**。所以 `GetAura("mirrored soul", boss)` 能在 boss 身上找到光环，检测逻辑成立。但转身只能停住需要面向的施法与近战，**宠物、已上的 DoT、不需面向的法术不受影响**。
- `SPELL_WAILING_SOULS` 在 `FoSTriggers.h` 里定义了但**没有任何 trigger/action 使用**。
- 所有 trigger 都用 `find target` 按名字找 boss，没有作用域隔离（两个 boss 距离 365 码，互不干扰）。

---

## 1. Bronjahm（36497 / 36498）

### 1.1 脚本（boss_bronjahm.cpp）

- **开战前**：`Reset()` 去 DISABLE_MOVE，自己挂 Soulstorm Channel OOC 69008（纯视觉）。没有不可选中/免疫标志，**普通 pull 即可**。
- `JustEngagedWith`：BossAI（IN_PROGRESS + 进 zone 战斗），去掉 OOC 光环。
  - Shadow Bolt 70043：2 秒首发，之后每 2 秒一次，**只在 victim 不在近战范围时**施放（坦克贴脸就不放）。
  - Magic's Bane 68793：5–10 秒首发，每 10–15 秒，打当前目标周围（半径索引 28）；spell script 对**蓝条目标**额外加伤 = 最大法力的一半，英雄上限 15000。
  - Corrupt Soul 68839：14–20 秒首发，每 20–25 秒，100 码内随机玩家，挂 4 秒（durIdx 35）dummy 光环；到期在该玩家处召 **Corrupted Soul Fragment 36535 / 英雄 36617**（NullCreatureAI，REACT_PASSIVE，每秒 `MovePoint` 朝 Bronjahm 走，**走到 2 码内就施 Consume Soul 68861 给 boss 回血并消失**）。机制要求：中者离开 boss，碎片出现后 DPS 在它走到 boss 前打掉。
- **P2（35% 血）**：`DamageTaken` 里一次性触发——设 DISABLE_MOVE、原地 idle、施 Teleport 68988（回中心），取消 Corrupt Soul，所有事件推迟 6 秒，Fear 8–14 秒首发。
  - Soulstorm 68872：命中 Teleport 后立即施放，自身光环 + 周期伤害。`spell_bronjahm_soulstorm_targeting` 过滤：`AllWorldObjectsInExactRange(caster, 10, false)` → **把 10 码以内的目标剔除**，也就是**站在 boss 10 码内安全，10 码外挨打**。
  - Fear 68950：每 8–12 秒，10 码内随机 1 人（`SPELLVALUE_MAX_TARGETS=1`）。
  - DISABLE_MOVE 期间 boss 不动，只在攻击就绪时转向 victim。
- `EnterEvadeMode`：去 DISABLE_MOVE 后走 BossAI（NOT_STARTED、回家）。**不是 HARD_RESET**。
- 成就：Soul Power（击杀时 4 个以上碎片存活）——与测试无关。

### 1.2 附近的怪（spawn 45 码内：**没有**）

Bronjahm 站在 z686 的平台上。45 码内没有任何 DB 生物；最近的都在**低 10 码**的下层（z675–678）：

| guid | entry | 名称 | 坐标 | 距离 | dz | 巡逻 / formation |
|---|---|---|---|---|---|---|
| 201762 | 36516 | Soulguard Animator | (5266.6, 2540.9, 675.3) | 46.1 | -10.8 | 201698 编队成员 |
| 201790 | 36516 | Soulguard Animator | (5317.0, 2549.8, 675.3) | 47.6 | -10.8 | **leader**：201790 + 201732（Soul Horror, 60.6）+ 201748（Animator, 76.2），静止 |
| 201706 | 36478 | Soulguard Watchman | (5253.1, 2529.3, 676.5) | 49.8 | -9.6 | **leader**，path 2017060：x 5248–5259、y 2484–2539、z675–678 往返（最近点 (5254.2, 2483.8) 离 boss 48 码），成员 201764（53.6） |
| 201791 | 36551 | Spiteful Apparition | (5261.7, 2463.1, 678.0) | 56.1 | -8.2 | 随机游走 20 码（unit_flags 131072，进战斗前隐形；SmartAI 进战后放 Spite） |
| 201698 | 36516 | Soulguard Animator | (5244.3, 2565.0, 675.3) | 78.9 | -10.8 | **leader**：201698 + 201762 + 201695（Soul Horror, 61.2） |
| 201700 | 36478 | Soulguard Watchman | (5343.5, 2451.4, 686.4) | 71.8 | +0.2 | **leader**，path 2017000：从 (5343.5,2451.4) 向东到 (5454.5,2471.8)，z686→706，成员 201757（70.1）。**与 boss 同层**，是去 Devourer 走廊的起点 |
| 201740 | 2110 | Black Rat | (5339.9, 2467.9) | 57.5 | 0.2 | 小动物 |

70–110 码：Soulguard Bonecaster/Reaper/Adept 组 201734（201734、201776、201758、201686，(5222–5241, 2415–2433, 671.8)，约 97–110 码、低 14 码）。

→ 同层只有 **201700 + 201757**（巡逻离 boss 72 码往东走，一般不会进战场，但离 boundary 100 码的圆以内）。下层三组离 boss 46–79 码、低 10 码；Soulstorm/Fear/flee 可能把 bot 推下平台（参见 memory「bot 掉出平台」）。

### 1.3 场景建议

- **框架**：无阻塞。`EngageTrigger=pull`、`BossEntry=36497`、`Strategy=wotlk-fos`。可选 `EngageConfirmBossState` 不需要。
- 开怪点：boss 本体 / `BRONJAHM_TANK_POSITION` (5297.9, 2506.7, 686.07) 附近。准备点候选 **(5325, 2478, 686.4)**（平台东南，离 boss 约 40 码，离 201700 巡逻起点 30 码）——**待实测**，入口方向与平台边缘都需要 los/地面高度确认；如果平台上找不到 40 码外的点，就退到 25–30 码。
- 前置 / 夹具候选：
  - `FixtureDespawnSpawns = 201700,201757`（同层巡逻，隔离档）；
  - 下层三组（201790/201732/201748、201706/201764、201698/201762/201695）与 201791：先按「不处理」跑基线，若日志里出现下层怪进战斗或 bot 掉层，再加入 `FixtureDespawnSpawns` 或 `PrerequisiteSpawns`。
- bot 覆盖与缺口：
  - 覆盖：Corrupt Soul 离开、碎片骷髅标记、P2 Soulstorm 靠近 boss。
  - **缺口 1（中）**：碎片只挂骷髅，不直接切目标；DPS 是否按 RTI 打骷髅取决于默认 `rti` 行为（**待实测**：看碎片是否在走到 boss 前被打掉，统计 Consume Soul 68861 命中次数）。
  - **缺口 2（小–中）**：`BronjahmMultiplier` 对所有 bot（含坦克）屏蔽 `TankAssistAction`，坦克被碎片/Fear 打断后能否重新选中 boss 待观察。
  - 缺口 3（小）：Fear 无处理（10 码内随机 1 人，靠治疗扛）；Magic's Bane 对蓝条职业额外伤害无处理（靠治疗）。
- 整体判断：**本副本最容易的一关**，适合作为 FoS/PoS 的第一只。

---

## 2. Devourer of Souls（36502 / 37677，HARD_RESET）

### 2.1 脚本（boss_devourer_of_souls.cpp）

- **开战前**：`Reset()` 去 root、恢复转向、REACT_AGGRESSIVE。unit_flags 64，**普通 pull**。
- **`CanAIAttack(target)` = `target->GetPositionZ() > 706.5`**：只打站在 boss 台子（z≈708.9）上的目标。大厅地面（守卫巡逻路径 z705.9）上的玩家**不会被它攻击**。所以坦克必须站上台子开怪，否则 boss 找不到可攻击目标 → evade → HARD_RESET 下线。
- 技能（`JustEngagedWith` 起算）：
  - Phantom Blast 68982 / 英雄 70322：5 秒首发，每 5 秒，打 victim（可打断；英雄命中过则成就失败）。
  - **Mirrored Soul 69051**：9 秒首发，每 20–30 秒，90 码内随机玩家；boss 引导（期间照常近战和 Phantom Blast）。**期间打 boss 的伤害有一部分转给被链接的玩家**（69023/69034）。
  - **Well of Souls 68820**：6–8 秒首发，每 25–30 秒，40 码内随机玩家脚下召一口井（地面持续伤害区，summon + 周期）。
  - **Unleashed Souls 68939**：18–20 秒首发，每 30–40 秒，boss 自身光环数秒，召 **Unleashed Soul 36595**（unit_flags 33554432 不可选中；`JustSummoned` 给最近玩家加 10 万仇恨并 `AttackStart`）。
  - **Wailing Souls 68899**：**65 秒首发，之后每 80 秒**，其它事件推迟到至少 20 秒后。随机选 1 个目标（68912），boss 面向他、root、禁止转向、REACT_PASSIVE，然后施 Wailing Souls：周期 dummy 光环 34 跳，前 30 跳每跳转 π/60（共 90°，方向随机左或右），每跳对正前方锥形施 68873 / **英雄 70324**（100 码）。第 33 跳解除 root 恢复追击。**机制要求：全员站到 boss 背后/侧后，躲开 90° 扫过的扇区。**
- `EnterEvadeMode`：解除 root / 转向锁，调 BossAI → CreatureAI → **HARD_RESET 分支 `DespawnOnEvade()`**。
- boundary：平行四边形（见 §0.1），boss 自己被拉出界就 evade。
- 成就：Three Faced（英雄全程不被 Phantom Blast 命中）。
- 任务 Tempering the Blade：有任务的玩家在场时召 Crucible of Souls 37094，与测试无关。

### 2.2 附近的怪（spawn 80 码内：**没有**）

Devourer 80 码内**一只 DB 生物都没有**。最近的是大厅里巡逻的 Spectral Warden 36666（英雄 37563，SmartAI：Veil of Shadow、Wail of Souls），都**无编队、单只巡逻**：

| guid | 路径 | 范围 | 离 Devourer 最近 |
|---|---|---|---|
| 201687 | 2016870 | (5552.7–5618.5, 2417–2452.5, 705.9)，在 (5589.4,2417.1) 停 5 秒/2 秒，**端点 (5618.5, 2452.5) 就是 Devourer 厅的入口**（outroSpawnPoint 5618.1, 2451.9 同点） | ≈70 码 |
| 201737 | 2017370 | (5484.5–5532.2, 2461–2497, 706) | ≈130 码 |
| 201796 | 2017960 | (5483.6–5526, 2513–2570, 706) | ≈140 码 |

再往西是走廊（201700 巡逻的东端 (5454.5, 2471.8, 706)）。

### 2.3 场景建议

- **框架**：无阻塞。`EngageTrigger=pull`、`BossEntry=36502`。HARD_RESET 由 `ResolveOrRestoreSpawn()` 处理（与 AN/AK 同类，已验证过的路径）；每次 attempt 后确认 snapshot 里 201736 被恢复。
  - **注意 `CanAIAttack` 的 z 门槛**：开怪点和坦克站位必须在 z>706.5 的台子上。准备点可以在大厅地面（z705.9，boss 打不到，反而安全）。
- 准备点候选 **(5618, 2452, 705.9)**（厅入口、201687 巡逻端点、离 boss 约 70 码；需先移除 201687）；开怪点候选 **(5648, 2490, 708.9)**（台上、离 boss 约 22 码）。全部**待实测**（台子边缘、z 值、los）。
- 前置 / 夹具候选：`FixtureDespawnSpawns = 201687`（巡逻经过入口）。201737、201796 离 130 码以上，先不处理。
- bot 覆盖与缺口：
  - 覆盖：Mirrored Soul 期间 DPS 转身停手（检测成立，但只挡得住需面向的出手）。
  - **缺口 1（大，英雄决定性）**：Wailing Souls 完全没有处理。英雄 70324 每跳伤害高，全队站在 boss 正面或侧面时 90° 扇扫会连续多跳命中。要处理需要：读 boss root + 68899 施法/光环 → 全员移到 boss 背后（扇区旋转方向随机，站正背后最安全）。这属于 bot 战斗行为，应在 playerbots 开发分支实现。
  - 缺口 2（中）：Unleashed Soul 追着最近玩家打，没有专门处理（靠 AoE/通用目标选择）；Well of Souls 靠 `MasterlessAvoidAoe=1` 的通用躲地面（**待实测**：井是 summon 还是 dynobject，avoid aoe 能否识别）。
  - 缺口 3（小）：Phantom Blast 打断靠职业通用逻辑。
- 首轮建议：先跑 ilvl200 基线，统计 70324 命中次数/每次 Wailing 的总伤害与死亡时点，再决定是否先做 Wailing 躲避。

---

## 3. mod-raidtest 能力对照

| 需求 | 现有键 | 在 FoS 上是否可用 | 缺什么 |
|---|---|---|---|
| 坦克正常拉怪 | `EngageTrigger=pull` | 两个 boss 都可用 | — |
| HARD_RESET 恢复 | `ResolveOrRestoreSpawn()`（自动） | Devourer 需要，已有 | — |
| 开战/进度门禁 | — | 不需要（无 required boss、无剧情门禁） | — |
| boss 状态确认 / 夹具 | `EngageConfirmBossState`、`FixtureBossStates` | **可用**（本副本用 `SetBossNumber`） | 不需要 |
| 剧情 NPC | `EventStarterEntry` | 不需要（开场 gossip 纯装饰；且该键只调 `AI()->sGossipSelect`，而 FoS 领袖用的是 `CreatureScript::OnGossipSelect`，调了也不会触发） | — |
| 移除夹具 / 前置 / 准备点 | `FixtureDespawnSpawns`、`PrerequisiteSpawns`、`Preparation*` | 可用 | — |

## 4. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| Bronjahm | `heroic-fos-bronjahm-h5g` | 隔离（可选移除 201700/201757） | 待建 | 无 | 实测准备点/平台边缘 → 首轮基线，看碎片处理 |
| Devourer of Souls | `heroic-fos-devourer-h5g` | 隔离（移除 201687） | 待建 | bot：Wailing Souls 躲避（英雄可能决定性） | 实测台上开怪点 → 首轮基线，量 70324 伤害 |

共用事实：只有 Devourer 是 HARD_RESET（普通 entry 带标志，英雄同样生效）；instance 用 BossState（`*BossState` 键有效）；没有 required-boss 检查；boundary 两只都有；开场剧情不影响开战；策略 `wotlk-fos` 由 map 632 自动挂载，覆盖 Bronjahm 大部分机制与 Devourer 的 Mirrored Soul，缺 Wailing Souls。
