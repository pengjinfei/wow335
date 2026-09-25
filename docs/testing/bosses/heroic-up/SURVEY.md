# 英雄乌特加德之巅（Utgarde Pinnacle，map 575）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `Northrend/UtgardeKeep/UtgardePinnacle/`、mod-playerbots `Ai/Dungeon/UP`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp`）、world DB 和客户端 DBC（`data/world/dbc`）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。

## 0. 总览

| boss | 普通 entry | 英雄 entry | spawn guid | 坐标 (x, y, z, o) | HARD_RESET | 脚本基类 | 开战方式 | 现框架能否正常开战 |
|---|---|---|---|---|---|---|---|---|
| Svala Sorrowgrave | 29281「Svala」→ 剧情后 `UpdateEntry(26668)` | 30809 → 30810 | 126115 | (296.632, -346.075, 90.631, 4.608) | 否（0 / 1） | ScriptedAI | **AreaTrigger 5140** 触发约 72 秒剧情，剧情结束后她自己攻击 100 码内的随机玩家 | **不能**：bot 不发 AreaTrigger 包，她永远 ImmuneToAll |
| Gortok Palehoof | 26687 | 30774 | 126102 | (320.791, -453.145, 104.806, 3.142) | 否（0 / 1） | ScriptedAI | **使用 GO 188593 Stasis Generator**（guid 65513）→ 依次唤醒 4 只小 boss（英雄）→ 最后唤醒 Gortok | **不能**：没有「用 GO 开战」的触发方式；boss 在前 4 只小 boss 期间不可选中 |
| Skadi the Ruthless | 26693 | 30807 | 126103 | (343.02, -507.325, 104.567, 2.967) | **是**（两个 entry 都带 0x80000000） | ScriptedAI（+ Grauf 26893/30775，VehicleAI，VehicleId 40） | AreaTrigger 4991 **或**任何人打她（`JustEngagedWith`）→ 她骑上 Grauf 飞走，地面刷怪；**Grauf 只能被鱼叉打**，被打下来后 Skadi 才可攻击 | 部分：pull 能开战，但坦克仇恨校验必失败；bot 不会用鱼叉，所以打不死 |
| King Ymiron | 26861 | 30788 | 126255 | (392.835, -286.809, 109.284, 4.782) | 否（0 / 1） | ScriptedAI | 普通 pull | 只有在 **Skadi 已 DONE** 时才行：否则 `UNIT_FLAG_NOT_SELECTABLE`；`FixtureBossStates` 在本副本无效（见 §0.1） |

- 英雄 entry 的 `flags_extra` 都含 1（`INSTANCE_BIND`）。**只有 Skadi 带 HARD_RESET**：evade 时 `CreatureAI::EnterEvadeMode` 末尾会 `DespawnOnEvade()`（参见 memory「换新副本必查的坑」第 1 条，框架 `ResolveOrRestoreSpawn()` 已有处理，但 Skadi 还有一个**每 6 秒自检一次**的 evade 路径，见 §3）。
- 模板 `unit_flags`：Gortok 与 4 只小 boss 都是 33554752（NOT_SELECTABLE | IMMUNE_TO_PC | UNK_6），由脚本解除；Skadi/Grauf 是 320（IMMUNE_TO_PC | UNK_6），Skadi 在 Reset 里 `SetImmuneToPC(false)`，**Grauf 始终免疫玩家**；Ymiron 是 64。
- 副本共 205 条 `creature` 记录。另有 76 个 Flame Breath Trigger（28351，guid 5300600–5300674）沿 Skadi 走廊排成两行，下文列怪时已排除。

### 0.1 instance 脚本（instance_utgarde_pinnacle.cpp）——对框架最关键的一点

- **没有 `SetBossNumber`，也不用 `SetBossState`**。进度存放在自己的 `Encounters[4]` 数组里，用 `SetData/GetData(0..3)` 读写：`DATA_SVALA_SORROWGRAVE=0`、`DATA_GORTOK_PALEHOOF=1`、`DATA_SKADI_THE_RUTHLESS=2`、`DATA_KING_YMIRON=3`。
  - 因此 `InstanceScript::GetBossState(id)` 在本副本**永远返回 TO_BE_DECIDED**（`bosses` 为空），`SetBossState` 直接 `return false`。
  - mod-raidtest 里读写 boss 状态的键**全部依赖 `GetBossState/SetBossState`**：`EngageConfirmBossState`（`AttemptRunner.cpp:919`）、`EventCompletionBossState`/`EventPhases`（`AttemptObserver.cpp:785`、`AttemptRunner.cpp:2325`）、`FixtureBossStates`（`AttemptRunner.cpp:761`）。**这些键在 UP 上要么是空操作，要么永远等不到。**
- 没有覆盖 `CheckRequiredBosses`，没有 boss boundary。
- `SetData(DATA_SKADI, DONE)` 会打开 Skadi 门，并**直接去掉 Ymiron 的 `UNIT_FLAG_NOT_SELECTABLE`**。Ymiron 的 `Reset()` 和 `JustEngagedWith()` 也按 `GetData(DATA_SKADI)==DONE` 决定是否可选中。
- 门：
  - `GO_SKADI_THE_RUTHLESS_DOOR` 192173 guid 65440 (477.50, -477.18, 103.06)：Skadi 死后打开。它在走廊东端，也是 Skadi 刷怪点 SpawnLoc (477.58, -484.56) 的位置，通往 Ymiron 那一侧。
  - `GO_KING_YMIRON_DOOR` 192174 guid 65472 (445.06, -325.52, 100.95)：Ymiron 死后打开（出口）。
  - 隔离场景直接传送，门不挡路。链式场景要靠 Skadi 死亡开门。
- `GO_SVALA_MIRROR` 191745 guid 65434：只作剧情视觉。
- 全副本的 AreaTrigger（`areatrigger` 表，map 575）：
  - **5140** (312.646, -291.173, 104.702)，盒子 37.29 × 13.79 × 35.23，o=0：SmartTrigger → 对 guid 126115（Svala）`SetData(1,1)`，也就是 Svala 的剧情开关。
  - **4991** (330.903, -508.43, 104.272)，盒子 31.62 × 21.84 × 30，o=0（x 315.1–346.7，y -519.3 – -497.5）：SmartTrigger → `SMART_TARGET_INSTANCE_STORAGE(2, creature)` → Skadi `DoAction(1)` = 开始遭遇。Skadi 自己就站在盒子里。
  - 4743 (595.19, -328.29)：入口传送。
- **AreaTrigger 是客户端驱动的**：服务器只在收到 `CMSG_AREATRIGGER` 时校验 `IsInAreaTriggerRadius` 再执行脚本，AC 没有服务器端扫描。mod-playerbots 只在 master 客户端发来 AreaTrigger 包时让 bot 跟着发（`ReachAreaTriggerAction`，WorldPacketHandlerStrategy）。**全 bot 队伍走进 5140/4991 什么都不会发生。**
- `spell_area`：47546「Utgarde Pinnacle Gauntlet Periodic」，area 1196（= map 575 整个区域），autocast。每 5 秒触发一次 47547「Gauntlet Effect」，给玩家 40 码内的 Breath Trigger 挂一个 dummy 光环。Skadi 的 reset 自检依赖这个光环（§3）。bot 是 Player，理论上同样会被挂上（**待实测：bot 身上是否有 47546**）。

### 0.2 mod-playerbots 策略

- context key 与 `getName()` 都是 **`wotlk-up`**（`DungeonStrategyContext.h:60`，`UPStrategy.h`）。`PlayerbotAI.cpp:1724` 在 `case 575` 自动挂载。RuntimeStrategyName 恒等，不用补表。
- 全部内容如下（只覆盖 Skadi 和 Ymiron）：

| boss | trigger → action（优先级） | multiplier |
|---|---|---|
| Svala | **无** | 无 |
| Gortok | **无** | 无 |
| Skadi | `freezing cloud` → `avoid freezing cloud`（RAID+5：Grauf 带 47592 吐息光环，或附近 Breath Trigger 带 Freezing Cloud 47579/60020 时，离最近的 Breath Trigger 5 码）；`skadi whirlwind` → `avoid skadi whirlwind`（RAID+4：离 Skadi 7 码，坦克 12 码） | `SkadiMultiplier`：Grauf 在场（飞行阶段）时，把以 Skadi/Grauf 为目标的 `AttackAction` 置 0；落地后旋风斩期间只放行 avoid 移动 |
| Ymiron | `ymiron bane` → `drop target`（RAID+5，Bane 48294/59301 施法或光环期间） | `YmironMultiplier`：Bane 期间所有 `AttackAction` 置 0 |

- `UPStrategy.cpp` 自带注释：`// TODO: Harpoons launchable via GameObject. For now players should do them`。**鱼叉完全没有实现**。
- 所有 trigger 都用 `find target` 按名字找 boss，没有作用域隔离。

---

## 1. Svala Sorrowgrave（29281 → 26668 / 英雄 30809 → 30810）

### 1.1 脚本（boss_svala.cpp）

- **开战前状态**：spawn 的是 29281「Svala」（faction 21，模板 unit_flags=0）。`Reset()` 在 `Started==false` 时 `SetImmuneToAll(true)`，所以**剧情开始前打不动**。
- **开战方式**：`SetData(1,1)`，唯一调用方是 AreaTrigger 5140 的 SmartTrigger（离 Svala 57.2 码，在北侧 z104.7 的高台上）。条件是 `!Started` 且 `GetData(DATA_SVALA) != DONE`。调用后：
  - 召 Image of Arthas 29280 于 (295.81, -366.16, 92.57)，定时 59 秒消失。
  - `SetData(DATA_SVALA, IN_PROGRESS)`，镜子动画开始。
  - 剧情时间线（events2）：5s 开场 → 8s 阿尔萨斯说话 → 9s 变身施法 → 3s 悬浮（hover 6） → 9s `UpdateEntry(26668)`，让 100 码内的 Dragonflayer Spectator 26667 `SetData(1,2)`（SmartAI：走开后消失） → 2s → 12s → 9s → 13s 下落 → 2s 解除 ImmuneToAll，`SelectTargetFromPlayerList(100)` 后 `AttackStart`。**从踩 AT 到她主动开打约 72 秒。**
- **战斗事件**（`JustEngagedWith`，`SetInCombatWithZone`）：
  - Sinister Strike 3s 首发，之后每 3–5s。
  - Call Flames（48258，发送 event 17841：在 (307,-357.5,91.08) 与 (285.6,-357.5,91.08) 召 2 个 Flame Brazier 27273）：11s 首发、每 8–12s；每次 0.5/2.5/4.5 秒由随机火盆施 Ball of Flame 48246（单目标）。
  - **Ritual of the Sword**：25s 首发。随机选一个目标，把他传送到 (296.632, -346.075, 90.63)（=spawn 点，脚下有 Ritual Target 27327 guid 126172），Svala 自己瞬移到 z110 并 root。在 `RitualChannelerLoc`（(296.42,-355.01,90.94)、(302.36,-352.01,90.54)、(291.39,-350.89,90.54)）召 **3 只 Ritual Channeler 27281/30804**（NullCreatureAI，对目标加 1000 万仇恨并施 Paralyze 48278；**英雄模式自带 Shadows in the Dark 59407**）。施 Ritual Strike 48331（持续伤害，英雄每跳 2000；另有 dummy 效果对生物打 7000）。其它事件整体推迟 25 秒；25 秒后 root 解除、恢复追击，并清掉 channeler。**机制要求：25 秒内打死 3 只 channeler，救下被献祭的人。**
- `EnterEvadeMode`：解除 root 后调用基类。`Started` 是 AI 成员变量，同一个 AI 实例内不会复位：evade 后她已是 26668、可攻击、悬浮。但**新建实例或重生时需要重新走剧情**。
- 成就：Svala 击杀 Scourge Hulk 26555（The Incredible Hulk）。

### 1.2 附近的怪（spawn 45 码内）

| guid | entry | 名称 | 坐标 | 距离 | 巡逻 / formation |
|---|---|---|---|---|---|
| 126172 | 27327 | Ritual Target | (296.7, -346.3, 91.4) | 0.2 | 触发器，不动 |
| 126073/126069/126071/126067/126068/126070/126065/126072/126074/126066 | 26667 | Dragonflayer Spectator ×10 | (306–320, -308 – -323, 87.0) | 27.6–42.2 | 静止，unit_flags 768（免疫玩家/NPC），剧情里走开后消失；**不是战斗怪** |
| 126054/126061/126062 | 14881 | Spider | — | 28–41 | 小动物 |
| 126083 | 26670 | Ymirjar Flesh Hunter | (281.2, -383.6, 90.3) | 40.5 | **formation leader**，path 1260830：楼梯来回 (248.6–281.5, -381.8 – -400.7, z75–105)，其中 (281.1,-384.5,90)、(281.5,-396.9,90) 与 Svala 同层，距她约 41 码 |
| 126087 / 126088 | 26672 | Bloodthirsty Tundra Wolf ×2 | (281.6/278.3, -380.6/-383.3, 90.1) | 37.7 / 41.5 | 126083 的成员（groupAI 514） |
| 126075 | 26669 | Ymirjar Savage | (264.2, -376.3, 75.2) | 44.3 | 下层（z75，低 15 码） |

→ 唯一需要处理的是 **126083 + 126087 + 126088 这一组巡逻**（前置或夹具移除）。

### 1.3 场景建议

- **阻塞（框架）**：没有 AreaTrigger 开战方式，Svala 永远免疫。需要框架新增一个能力：让一个站在 AT 盒子里的 bot 走一遍正常的 `WorldSession::HandleAreaTriggerOpcode`（核心会自己校验 `IsInAreaTriggerRadius`，等价于真人客户端走进去，不是 DoAction）。拟用 `EngageAreaTrigger = 5140`。
- 剧情开战后 boss 自己 `AttackStart` 随机玩家，所以开战确认要看她进战斗，**不能要求坦克先拿仇恨**。可以沿用 summon 确认预算的思路，但预算要不少于 75 秒。
- `BossEntry` 建议填 29281：`FindBossNear` 按 `GetEntry()` 匹配，剧情前是 29281；剧情后 entry 变 26668，但 guid 不变。**待实测**：变身后观察器与击杀判定是否只看 guid。
- 触发点（AT 盒内）**(312.6, -291.2, 104.7)**。开怪 / 战斗站位候选 **(296.6, -335.0, 90.6)**（Svala 以北 11 码，同层）。两者都待实测。
- 前置：126083（连带 126087、126088，同编队）。
- bot 缺口：没有「献祭期间优先打 Ritual Channeler」的逻辑。3 只 channeler 带 1000 万仇恨、不移动，bot 会不会自己切目标是**本 boss 的主要风险**。Ball of Flame 是否需要躲，也待观察。

---

## 2. Gortok Palehoof（26687 / 30774）

### 2.1 脚本（boss_palehoof.cpp）

- **开战前**：`Reset()` 给自己挂 Freeze 16245（`creature_addon` 也带），设 `NON_ATTACKABLE | NOT_SELECTABLE`，`SetData(DATA_GORTOK, NOT_STARTED)`。重置球体：去掉 `GO_FLAG_NOT_SELECTABLE`，置 `GO_STATE_READY`。4 只小 boss 回到 home，死了的重生，重新冰冻。`MoveInLineOfSight` 在 NON_ATTACKABLE 时直接返回（不会被靠近激活）。
- **小 boss（都不在 formation 里，无巡逻）**：

  | guid | entry（普通/英雄） | 名称 | 坐标 | 技能（解冻后） |
  |---|---|---|---|---|
  | 126091 | 26683 / 30772 | Frenzied Worgen | (262.195, -440.502, 104.82) | Mortal Wound 3s/4–7s、Enrage 12s/15s、Enrage2 10s/10s |
  | 126092 | 26684 / 30803 | Ravenous Furbolg | (262.119, -463.103, 104.787) | Chain Lightning 3s/4–7s、Crazed 12s/8–12s、Terrifying Roar 10s/10–15s |
  | 126093 | 26685 / 30790 | Massive Jormungar | (290.781, -440.816, 104.816) | Acid Spit 3s/2–4s、Poison Breath 10s/8–12s、Acid Splatter 12s/10–15s（每次召 6 只 Jormungar Worm 27228，进 zone 战斗） |
  | 126094 | 26686 / 30770 | Ferocious Rhino | (291.549, -462.653, 104.824) | Stomp 3s/8–12s、Gore 12s/13–17s、Grievous Wound 10s/18–22s |

- **开战方式——球体（精确）**：
  - 球体是 **gameobject 188593「Stasis Generator」**，spawn guid **65513**，坐标 (238.518, -460.827, 105.476)，o=1.553，type 18（SUMMONING_RITUAL），`gameobject_template_addon.faction=35`，flags 0，ScriptName **`go_palehoof_sphere`**。它在 Gortok 以西 82 码、房间西端。
  - `GameObject::Use(player)` 一开始就调 `sScriptMgr->OnGossipHello(player, go)`（`GameObject.cpp:1476`），所以玩家右键点它就会进入 `go_palehoof_sphere::OnGossipHello`：如果 Gortok 活着，就给 GO 加 `NOT_SELECTABLE`、置 `GO_STATE_ACTIVE`，然后 `Gortok->AI()->DoAction(ACTION_START_EVENT=1)`。模板 Data1=48055「Start Gortok Event」（SEND_EVENT 17728）与 Data2=48048 Orb Channel 这两条仪式路径因为脚本 `return true` 而**不会执行**。
  - `DoAction(START)`：Gortok 在 (238.608, -460.71, 109.567) 召一个 **World Trigger 22515 作为「球」**，挂 Orb Visual 48044，飞到房间中心 **(275.4, -453, 110)**。Gortok `SetImmuneToPC(false)`、**`SetInCombatWithZone()`**、stun 住自己。10 秒后第一只小 boss 解冻。
  - 解冻流程：球对随机小 boss 施 Awaken Subboss 47669，并 `DoAction(UNFREEZE)`（去 NON_ATTACKABLE）；6 秒后 `DoAction(UNFREEZE2)`：去 Freeze、去 NOT_SELECTABLE、`SetImmuneToPC(false)`、`SetInCombatWithZone()`，开始放技能。
  - 小 boss 死亡 → `Gortok->DoAction(MINIBOSS_DIED)`：`Counter > (英雄 ? 3 : 1)` 时，3 秒后球唤醒 Gortok，再 6 秒后 Gortok 解除 stun 和两个 flag，清空仇恨；否则 3 秒后解冻下一只。**英雄 = 4 只小 boss 全打完才轮到 Gortok；普通 = 2 只。** 顺序每次 Reset 随机。
- **Gortok 技能**（解冻后）：Withering Roar 10s/8–12s、Impale 12s/8–12s（随机目标）、Arcing Smash 15s/13–17s。
- **`UpdateAI` 以 `if (!UpdateVictim()) return;` 开头**：用球之后他靠 zone 战斗留在战斗中。全队死亡或脱战时 `UpdateVictim` 失败 → evade → `Reset()`，球和小 boss 全部复位，可以在同一实例里重来（不是 HARD_RESET）。
- `JustEngagedWith` → `SetData(DATA_GORTOK, IN_PROGRESS)`；`JustDied` → DONE。

### 2.2 附近的怪

Gortok spawn 45 码内：

| guid | entry | 名称 | 坐标 | 距离 | 巡逻 / formation |
|---|---|---|---|---|---|
| 126120 | 15475 | Beetle | (303.2, -463.6) | 20.5 | 小动物 |
| 126086 | 26672 | Bloodthirsty Tundra Wolf | (295.1, -452.3, 104.7) | 25.7 | **formation leader**，path 1260860：房间东西贯穿 (236.4–310.8, -467.4 – -435.6, z104.7)，**东端 (310.8,-451.6) 离 Gortok 10 码，西端 (238.1,-450.7) 就在球旁边** |
| 126078 | 26669 | Ymirjar Savage | (298.9, -446.4, 105.5) | 22.9 | 126086 成员 |
| 126082 | 26670 | Ymirjar Flesh Hunter | (298.4, -458.5) | 23.0 | 126086 成员 |
| 126081 | 26670 | Ymirjar Flesh Hunter | (288.1, -452.0) | 32.7 | 126086 成员 |
| 126093 / 126094 | — | Jormungar / Rhino（小 boss） | 见上 | 30.7–32.4 | 事件单位 |
| 126165 | 26555 | Scourge Hulk | (355.9, -445.5, 75.2) | 36.0 | 下层（低 30 码） |

45–80 码：两只小 boss（Furbolg 59.5、Worgen 59.9），Skadi 58.6，下层（z75）的 Berserker 编队 126111+126110（path 1261110）、Dusk Shaman、Necromancer（都低约 30 码，不同楼层）。

球体 40 码内：Beetle 126119、Furbolg 23.7、Worgen 31.2、Spider 126059，以及 126086 编队巡逻线的西端。

→ **126086 编队（126086、126078、126081、126082）必须前置或移除**，它的巡逻线横穿整个战斗区。

### 2.3 场景建议

- **阻塞（框架）**：现有键没有「用 GO 开战」。
  - `PrerequisiteGameObjects` 确实会调真实的 `GameObject::Use(bots.front())`（`AttemptRunner.cpp:1775`），能触发 `OnGossipHello`。但它只在**前置怪清完、进入 Recovery 之前**执行一次。之后 Gortok 已经 `SetInCombatWithZone`，10 秒后小 boss 解冻进场，框架却还在 Recovery（等脱战、回血回蓝），然后才去 pull 一个不可选中的 Gortok：`AwaitTankAggro` 要求 `boss->GetVictim()==tank`，8 秒内不满足就 abort。**这条路不通。**
  - 需要新增 `EngageTrigger = gameobject`（拟配 `EngageGameObjectSpawn = 65513`）：由站在球旁的 bot 执行一次正常的 `GameObject::Use`（与真人右键相同；GO 带 NOT_SELECTABLE 时核心自己会拒绝）。开战确认改为读**实例数据**（`GetData(1)==IN_PROGRESS(1)`，因为本副本没有 BossState），确认后放开队伍自行接敌。观察器在确认状态期间，不能把「boss 不可攻击 / 不在打坦克」判成卡住。击杀判定仍然是 Gortok 真实死亡。
- 开怪（用球）点 **(243, -458, 104.7)**：球东侧约 5 码（z 取房间地面 104.7，待实测）。战斗站位由 bot 自己决定，房间中心 (276, -452, 104.8) 到每只小 boss 15–19 码，离 Gortok 44.8 码。
- 准备点候选 **(240, -420, 104.7)**：房间西北，推测是从 Svala 楼梯上来的入口（楼梯路径点 (248.8,-384,104.8)）。离球 40.8 码，离 Gortok 87 码，离 126086 巡逻端点 (236.6,-435.6) 16 码。待实测。
- 前置：126086 编队。或者用 `FixtureDespawnSpawns=126086,126078,126081,126082` 做隔离档。
- bot 缺口：策略里没有 Gortok 相关内容。小 boss 都是普通近战/施法，技能靠通用 AI 应该能扛。Acid Splatter 的 6 只小虫是 AoE 目标；Terrifying Roar 是群体恐惧。**用球这一步属于「开战交互」**（与魔枢封印球同类），由框架做、如实记录；不能指望 bot 自己去点。

---

## 3. Skadi the Ruthless（26693 / 30807，HARD_RESET）+ Grauf（26893 / 30775）

### 3.1 脚本（boss_skadi.cpp）

- **开战前**：`Reset()` 设 `REACT_PASSIVE`，去 NOT_SELECTABLE，`SetImmuneToPC(false)`，`SetData(DATA_SKADI, NOT_STARTED)`。如果实例里没有 Grauf，就在 **GraufLoc (341.741, -516.955, 104.670)** 召一只（**Grauf 不是 DB spawn**，是 Skadi 的召唤物，会随 `_summons.DespawnAll()` 消失）。
- **开战方式**（两条都走 `DoAction(ACTION_START_ENCOUNTER)`，只执行一次）：
  1. AreaTrigger 4991（她所在的走廊西端盒子）——bot 不会触发；
  2. `JustEngagedWith`——**有人打她就开战**。她是 REACT_PASSIVE，不还手，但可以被攻击。
- **START 之后**：`SetUnitFlag(NOT_SELECTABLE)`，喊话，`SpawnFirstWave()`：在 SpawnLoc (477.581, -484.559, 104.822，东端门口) 召 10 只 Ymirjar Warrior 26690、1 只 Witch Doctor 26691、**2 只 Harpooner 26692**，分别走到 FirstWaveLocations（沿走廊 x 333–482 散开）。`SetData(DATA_SKADI, IN_PROGRESS)`，英雄开始成就计时。在 SpawnLoc 召 World Trigger 22515，挂 **Summon Gauntlet Mobs Periodic 59275**（每 25 秒按队列召 2 只：Warrior/Harpooner/Witch Doctor 的 W/E 变体，沿 path 2669000 从 (478.7,-505.6) 走到 (318.2,-503.9)，到终点后 `SetInCombatWithZone`）。再召 Combat Trigger 38667 并 `DoZoneInCombat`。2 秒后 `EnterVehicleUnattackable(grauf)`，Grauf 开始飞。
- **Grauf 飞行循环**（VehicleAI，run 速 2.5 倍，REACT_PASSIVE，**模板 IMMUNE_TO_PC**）：
  1. `PATH_INITIAL` 2689300：从 (310,-510,120) 绕到东端 **(523.2, -549.0, 114.9)**；
  2. 到达后喊「in range」（EMOTE_ON_RANGE），**悬停 10 秒**（这就是鱼叉窗口）；
  3. 随机左/右，走 BREACH 路径到 (496.4,-517.6,120) 或 (500.2,-501.7,120)，Deep Breath 喊话，2 秒后沿 `PATH_LEFT/RIGHT`（2689302/2689301）从东往西低空飞过走廊，并挂 Freezing Cloud 周期光环 10 秒（Breath Trigger 被命中后放地面冰云 47574/47594，按 y=-511 分左右半边）；
  4. 路径绕回 **(520.5, -541.6, 119.8)**，回到第 2 步。
- **鱼叉链（精确）**：
  1. Ymirjar Harpooner 26692 的 SmartAI：`On Just Died` → 施 **56789 Summon Harpoon**，在尸体处召 **gameobject 192539「Harpoon」**（type 10 GOOBER，无锁，Data10=56790）。
  2. 玩家右键这个 GO → 施 **56790 Create Harpoon**（SPELL_EFFECT_CREATE_ITEM）→ 得到物品 **37372「Harpoon」**（class 15，带使用法术 51355 Harpoon Launcher = OPEN_LOCK）。
  3. **Harpoon Launcher ×3**：gameobject **192175 / 192176 / 192177**，guid 65483 (491.494,-508.188,105.877)、65497 (488.826,-517.705,105.877)、65512 (480.35,-524.039,105.877)，type 10 GOOBER，flags 32，**lock 1777 = 需要物品 37372**，Data10 = **48641「Launch Harpoon Trigger」**。
  4. 48641 = SPELL_EFFECT 140（强制施法），目标是最近的 **World Trigger (Not Immune NPC) 19871**（conditions 限定）。每台炮旁边有一只：5300676 (490.5,-508.4,107.0,o=5.655)、5300677 (487.6,-517.3,106.8,o=5.550)、5300678 (480.2,-523.3,107.0,o=5.463)。19871 被迫施 **48642「Launch Harpoon」**：锥形 120°、半径 60 码（conditions 限定 Grauf 26893 / World Trigger 22515；spell script：命中 2 个以上目标时只保留 Grauf，伤害 = **Grauf 最大生命 35%**）。
  5. 三只 19871 都面朝东南（5.46–5.66 rad），「in range」悬停点 (520.5,-541.6) 与 (523.2,-549.0) 相对它们的方位是 5.39–5.86 rad，距离 40.9–52.1 码，都在锥形内。**也就是说：Grauf 在东端悬停的 10 秒内开炮，每发 35%，3 发打下来。**
  6. Grauf `JustDied` → Skadi `ExitVehicle()` 并 `DoAction(PHASE2)`：传送（61790），去 NOT_SELECTABLE，`SetImmuneToPC(false)`，`REACT_AGGRESSIVE`。**只有到这一步 Skadi 才可攻击。** Grauf 6 秒后消失。刷怪触发器 22515 被移除，停止刷新波次；已刷出的怪还在。
- **地面阶段**：Crush 8s/8s、Poisoned Spear 11s/10s（随机目标，附 DoT 50258）、Whirlwind 23s/15–20s（之后其它事件推迟 10 秒）。
- **evade / 重置路径（重要）**：
  - `EnterEvadeMode` 会 despawn 所有召唤物，然后调基类。因为 HARD_RESET，**基类末尾会让 Skadi 自己 despawn**。
  - **Gauntlet reset check**：START 后每 6 秒，最近的 World Trigger 23472（guid 126150，(397.0,-511.5,104.9)）施 49308。它统计全图带 47547 光环的 Breath Trigger；一个都没有、且 `GetData(DATA_SKADI)==IN_PROGRESS` 时，调 Skadi `EnterEvadeMode()`。47547 来自 `spell_area` 挂给副本内所有玩家的 47546（每 5 秒对玩家 40 码内的 Breath Trigger 施放）。**也就是说：只要队里没有人在走廊（x 324–490、y -506 – -518）40 码范围内，Skadi 就会重置并 despawn。**
- `JustDied`：DONE，开 Skadi 门，同时让 Ymiron 可选中（instance SetData）。

### 3.2 附近的怪

Skadi spawn 45 码内**只有两只 Black Rat**（126097 15.5 码、126101 32.5 码）。走廊里没有 DB 静态怪，全部是事件召唤物。东端炮位 45 码内只有 19871 ×3 和刷怪用 World Trigger 22515（126259，SpawnLoc）。

**Gortok 房间的 126086 编队巡逻东端 (310.8,-451.6) / (310.7,-467.4)，离 Skadi 约 45–58 码**；如果从 Gortok 房间进走廊，要把它算进来。

### 3.3 场景建议

- **阻塞（bot，决定性）**：playerbots 完全没有鱼叉逻辑（策略 TODO）。要完成这一关，bot 必须做到：打死 Harpooner → 去尸体旁点 GO 192539 拿到物品 37372 → 跑到东端炮位 → 在 Grauf 喊「in range」的 10 秒窗口内对 192175/6/7 使用（锁需要 37372） → 重复 3 次。
  - 通用拾取逻辑（`LootObjectStack`）只处理有 loot 表的 GO，Harpoon 192539 没有 loot id，**bot 不会自己捡**。
  - 可以参考的实现：`Ai/Raid/Uld/UldActions.cpp:930` `RazorscaleHarpoonAction`（找就绪的鱼叉 GO → 最近的远程走过去 → 发 `CMSG_GAMEOBJ_USE`/`CMSG_GAMEOBJ_REPORT_USE`），以及 `TOCActions.cpp:86` 的长枪架。**这是 bot 底层能力，应在 playerbots 开发分支实现，不能由 raidtest 代做。**
- **阻塞（框架）**：pull 本身能开战（坦克打她触发 `JustEngagedWith`）。但她随即 `NOT_SELECTABLE` 并上载具，且一直是 REACT_PASSIVE，`GetVictim()` 不会指向坦克。`AwaitTankAggro` 8 秒后会判「tank did not establish aggro」并 abort。需要一个按**实例数据**确认开战的方式（`GetData(2)==IN_PROGRESS`）。现有的 `EngageConfirmBossState` 读的是 `GetBossState`，而且只能配 summon，在 UP 上用不了。观察器还要容忍「boss 不可选中、在载具上」的一整个阶段。另外，memory 第 7 条提到的「boss 不可选中时放行跟随者」修复需要确认已经合入。
- 开怪点 **(330, -508, 104.5)**（AT 4991 盒子中心，离 Skadi 13 码）。鱼叉站位 **(485, -515, 105.8)**（三台炮之间）。准备点候选 **(316, -470, 104.7)**（走廊与 Gortok 房间之间，离 Skadi 46 码；但离 126086 巡逻点只有 5.9 码，必须先处理那一组）。全部待实测。
- 前置 / 夹具：126086 编队（在 Gortok 房间）。Gortok 本身冰冻且不可选中，不会被误拉。
- HARD_RESET 与每 6 秒自检：全灭、或整队离开走廊 40 码，都会让她 despawn。每次 attempt 后要确认 `ResolveOrRestoreSpawn()` 能把她（以及她召的 Grauf）恢复回来。
- 地面阶段（打下来之后）策略齐全：旋风斩躲避、冰云躲避、飞行期不打 boss。

---

## 4. King Ymiron（26861 / 30788）

### 4.1 脚本（boss_ymiron.cpp）

- **可选中门禁**：`Reset()` 先设 `NOT_SELECTABLE`，只有 `GetData(DATA_SKADI)==DONE` 才去掉。instance 在 Skadi DONE 时也会直接去掉。`creature_addon.emote=426`。faction 14，开局敌对。
- `JustEngagedWith`：喊话，`SetData(DATA_KING_YMIRON, IN_PROGRESS)`。Fetid Rot 8s/10–13s，Bane 18s/20–25s，Dark Slash 28s/30–35s（伤害 = 目标当前生命的一半），每秒检查一次血量。
- **船阶段**：英雄每掉 20%（80/60/40/20）一次，普通每掉 33.4% 一次。其它事件推迟 12 秒，自己 NON_ATTACKABLE + DISABLE_MOVE，施 Screams of the Dead 51750，走到这一轮随机选中的船前（(404.4,-335.3)、(380.8,-335.1)、(381.5,-314.4)、(404.3,-314.8)，z104.756）；上一条船点火（Flames 39199 触发器，30 分钟）。到达后对船上的国王（126147 Haldor、126128 Bjorn、126148 Ranulf、126149 Tor，都是 NOT_SELECTABLE 的布景）引导，6 秒后召国王灵魂，恢复可攻击和追击，获得该国王的能力：
  - Ranulf：Spirit Burst 每 10s；
  - Torgyn（Tor）：每 15s 召 4 只 Avenging Spirit 27386（进 zone 战斗）；
  - Bjorn：召 1 个 Spirit Fount 27339（不可选中，0.4 速跟随坦克，自带光环伤害）；
  - Haldor：Spirit Strike 每 5s（打坦克）。
  - 新国王的能力会替换上一个（`CancelEventGroup(1)`）。
- 没有 boundary，evade 走默认（去 DISABLE_MOVE 后调基类）。

### 4.2 附近的怪（spawn 45 码内；Ymiron 在 z109 的王座上，大厅地面 z104）

| guid | entry | 名称 | 坐标 | 距离 | 巡逻 / formation |
|---|---|---|---|---|---|
| 126104 | 26694 | Ymirjar Dusk Shaman | (392.4, -310.0, 104.1) | 23.2 | 静止，无编队 |
| 126112 | 26696 | Ymirjar Berserker | (389.0, -314.7, 104.1) | 28.2 | 静止 |
| 126113 | 26696 | Ymirjar Berserker | (395.3, -315.5, 104.1) | 28.8 | 静止 |
| 126147 / 126128 | 27307 / 27303 | King Haldor / King Bjorn | 船上 z107.3 | 35.2 | 布景（NOT_SELECTABLE），**脚本要用，不能移除** |
| 126154 | 26550 | Dragonflayer Deathseeker | (399.8, -250.2, 104.8) | 37.3 | 静止（北侧一组） |
| 126163 | 26554 | Dragonflayer Seer | (405.7, -251.1) | 38.0 | 静止 |
| 126158 | 26553 | Dragonflayer Fanatic | (402.8, -246.7) | 41.4 | 静止 |
| 126159 | 26553 | Dragonflayer Fanatic | (408.6, -247.9) | 42.0 | path 1261590：x 408.6–439.9、y ≈ -246 往返 |
| 126257 | 22515 | World Trigger | (392.5, -324.9) | 38.1 | 触发器 |

45–80 码：Ranulf / Tor（布景）、Scourge Hulk 126169 / 126170（59–62 码，北侧）、Mindless Servant 126129 (454.2,-302.5) 63 码、东北 Dragonflayer 三只（126156/126161/126151，66–69 码）、Hulk 126171 (458.7,-325.9) 77 码。都没有 formation。

### 4.3 场景建议

- **阻塞（框架）**：隔离档需要把 Skadi 标成 DONE，但 `FixtureBossStates` 调的是 `SetBossState`，在 UP 上是空操作。需要新增 `FixtureInstanceData = 2:3`（走 `InstanceScript::SetData(2, DONE)`，属于隔离形态，结论要降级），或者只做链式档（同一实例先正常打死 Skadi）。
  - 注意 `SetData(DATA_SKADI, DONE)` 还会打开 Skadi 门并 `SaveToDB`，副作用与真实击杀相同。Ymiron 的 `Reset()` 里也会读这个值，所以置位后任意一次 evade 都能保持可选中。
- 可选中之后就是普通 pull，不需要其它新能力。
- 开怪点 **(392.8, -303, 104.1)**（王座前、大厅地面，离 Ymiron 16 码；前提是 126104/126112/126113 已清掉）。准备点候选 **(440, -285, 105)**：离 Ymiron 47 码，离 Mindless Servant 126129 22.5 码，离 126159 巡逻端点 39 码，离 Hulk 126171 45 码。全部待实测。入口方向推测在大厅东侧（Skadi 门以北的路线上还有 Necromancer/Berserker 组和 Dragonflayer 组）。
- 前置：126104、126112、126113（王座前 23–29 码，**必须**处理）；北侧 Dragonflayer 组 126154、126163、126158、126159（37–42 码，前置或移除）；126129（离准备点近）。
- bot 缺口：只有 Bane 处理。Spirit Fount 跟随坦克、Avenging Spirit 小怪、Dark Slash 都靠通用逻辑。上一条船的火焰触发器能否被 avoid aoe 识别，需要开 `MasterlessAvoidAoe=1` 后观察。

---

## 5. mod-raidtest 能力对照

| 需求 | 现有键 | 在 UP 上是否可用 | 缺什么 |
|---|---|---|---|
| 坦克正常拉怪 | `EngageTrigger=pull` | Ymiron 可用（前提是 Skadi DONE）；Skadi 能开战但会在仇恨校验处 abort | Skadi 需要按实例数据确认开战 |
| 召唤物开战 | `EngageTrigger=summon` + `SummonTriggerEntry` + `EngageConfirmBossState` | 不适用；`EngageConfirmBossState` 读 `GetBossState`，UP 永远是 TO_BE_DECIDED | — |
| 剧情 gossip 开战 | `EventStarterEntry` / `EventCompletionBossState` / `EventPhases` / `EventFailureEscortEntry` / `EventTrackEntries` / `EventFollowStarter` | 不适用：只对**生物**调 `sGossipSelect`，还要求 escort 与 BossState；UP 没有 gossip NPC | — |
| 用 GO | `PrerequisiteGameObjects`（真实 `GameObject::Use`，尊重 NOT_SELECTABLE） | 只在前置清完后执行一次，接着 Recovery 和 pull，与 Gortok 的时序冲突 | `EngageTrigger=gameobject`（用 GO 作为开战动作） |
| AreaTrigger | 无 | — | `EngageAreaTrigger=<id>`：站在盒内的 bot 走正常的 `HandleAreaTriggerOpcode` |
| 进度门禁夹具 | `FixtureBossStates` + `FixtureBossNotify` | 空操作（`SetBossState` 返回 false） | `FixtureInstanceData=<id>:<value>`（`SetData`） |
| 开战确认 / 完成判据 | `EngageConfirmBossState`、`EventCompletionBossState` | 读不到 | 相应的 `...InstanceData` 版本（`GetData`） |
| 移除夹具 / 前置 / 分职责准备点 / 导航 | `FixtureDespawnSpawns`、`PrerequisiteSpawns`、`Preparation*`、`Tank/NonTankPreparation*`、`Navigation*` | 可用 | — |

以上新增能力都属于「编排：替真人做一次开战交互，或者读取状态」，不代替 bot 做战斗决策。鱼叉属于战斗中的持续交互，归 playerbots。

## 6. campaign 矩阵草案

| encounter | scenario（拟） | 范围 | 当前状态 | 阻塞 | 下一步 |
|---|---|---|---|---|---|
| King Ymiron | `heroic-up-ymiron-disc-h5g` | 隔离（Skadi DONE 夹具 + 王座前 3 只前置） | 待建 | 框架：`FixtureInstanceData` | 加实例数据夹具 → 实测开怪点/准备点 → 首轮基线 |
| Gortok Palehoof | `heroic-up-gortok-h5g` | 完整（126086 编队作前置）或隔离 | 待建 | 框架：GO 开战 + 实例数据确认 | 加 `EngageTrigger=gameobject` → 实测球旁站位 |
| Svala Sorrowgrave | `heroic-up-svala-h5g` | 完整（126083 编队作前置） | 待建 | 框架：AreaTrigger 开战；bot：献祭期打 channeler | 加 `EngageAreaTrigger` → 首轮看 channeler 是否被打 |
| Skadi the Ruthless | `heroic-up-skadi-h5g` | 完整（走廊无静态怪） | 待建 | bot：鱼叉（决定性）；框架：实例数据确认开战 | playerbots 开发分支实现鱼叉 → 再建场景 |

共用事实：只有 Skadi 是 HARD_RESET；instance 不用 BossState（所有 `*BossState` 键失效）；没有 required-boss 检查，但 Ymiron 用实例数据做了门禁；没有 boundary；AreaTrigger 只能由客户端包触发；策略 `wotlk-up` 由 map 575 自动挂载，只覆盖 Skadi（不含鱼叉）和 Ymiron 的 Bane。
