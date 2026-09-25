# 英雄冠军的试炼（Trial of the Champion，map 650）建场景前勘察

> 2026-09-26，只读勘察。资料来自源码（core 脚本 `src/server/scripts/Northrend/CrusadersColiseum/TrialOfTheChampion/`、mod-playerbots `src/Ai/Dungeon/TOC`、mod-raidtest `Scenario.cpp` / `AttemptRunner.cpp` / `AttemptObserver.cpp`）和 world DB（acore_world）。
> 没有向 worldserver 发命令，没有编译，也没有做 `raidtest los` 实测。下文所有**建议坐标都未经 los 和地面高度实测（待实测）**。建场景时必须按[准备点四关](../../LESSONS.md)和 los 两遍法逐点验证。
> 下文 `inst:` = `instance_trial_of_the_champion.cpp`，`gc:` = `boss_grand_champions.cpp`，`ac:` = `boss_argent_challenge.cpp`，`bk:` = `boss_black_knight.cpp`，`toc:` = `trial_of_the_champion.cpp`，`h:` = `trial_of_the_champion.h`。

## 0. 总览

| 遭遇 | 普通 entry | 英雄 entry | DB spawn | 开战方式 | 死还是投降 | HARD_RESET | 结论 |
|---|---|---|---|---|---|---|---|
| Grand Champions（骑乘 3 波小怪 + 3 冠军骑乘 → 3 冠军地面） | 部落方冠军 Mokra 35572 / Eressea 35569 / Runok 35571 / Zul'tore 35570 / Visceri 35617（联盟队伍打的就是这 5 个）；联盟方 Jacob 34705 / Ambrose 34702 / Colosos 34701 / Jaelyne 34657 / Lana 34703 | 36089 / 36085 / 36090 / 36091 / 36084；36088 / 36082 / 36083 / 36086 / 36087 | **无**，gossip 后由副本脚本召出，5 选 3 随机 | 播报员 gossip（要求说话的玩家**骑在载具上**） | **投降**（地面阶段致命伤害被吞，变 NON_ATTACKABLE；三只都投降才算完） | 否 | 骑乘阶段：**大工程**；地面阶段隔离：**需小框架改动** |
| Argent Confessor Paletress | 34928 | 35517 | 无 | 通过 Grand Champions 后第二次 gossip，先打 9 只 Argent 士兵 | **投降** | 否 | 隔离（直接召 boss）：**现在能建** |
| Eadric the Pure | 35119 | 35518 | 无 | 同上（与 Paletress 二选一，`urand(0,1)`） | **投降** | 否 | 隔离：**现在能建** |
| The Black Knight | 35451（乘客；载具 Skeletal Gryphon 35491） | 35490 | 无 | 通过 Argent Challenge 后第三次 gossip → 骷髅狮鹫降落 → 剧情约 30 秒 → 自己 `DoZoneInCombat` | **真死**（前两次"死"是假死换阶段） | 否（但 `EnterEvadeMode` 里自己 despawn） | 走副本自己的事件：**现在能建**（每个 run 只能稳定打出 1 次击杀，见 §4.4；多次重复要小改） |

- 所有 boss 模板 `flags_extra` 都没有 0x80000000（普通 entry 为 0，英雄 entry 为 1 = INSTANCE_BIND）。`unit_flags` 全是 2（NON_ATTACKABLE），开战时由脚本移除。
- **访问要求**：`dungeon_access_template` id 112（普通，75 级，ilvl 180）/ id 113（英雄，80 级，**平均 ilvl 200**），`dungeon_access_requirements` 里**没有**行（无任务/物品/成就要求）。与 FoS（107）、PoS（115）同档，h5g 装备档可进。
- 队伍阵营决定打哪一方：`GetTeamIdInInstance()` 取进本玩家阵营。h5g roster（`mod-raidtest-roster-heroic5gear-n5talents-v1.conf`）是 dwarf/human/draenei = **联盟**。于是：
  - 冠军与小怪保持部落 entry（`inst:111-153` 只有队伍是部落时才 `UpdateEntry` 成联盟冠军）；
  - 播报员 Jaeren Sunsworn 35004 在 `Reset` 里 `UpdateEntry(NPC_ARELAS 35005)`（`toc:122-123`）；
  - 队伍能骑的是 **Argent Warhorse 35644**（faction 1），冠军换坐骑找的是 **Argent Battleworg 36558**（`gc:562`、`gc:712`），践踏判定看的是玩家坐在 Warhorse 上（`gc:686`）；
  - Black Knight 复活的是 Risen Arelas 35564（`bk:162`）。

### 0.1 副本脚本（instance_trial_of_the_champion.cpp）：对框架最关键的几点

- **没有 `SetBossNumber` / `SetBossState`**。进度存在自己的 `m_auiEncounter[3]`（`BOSS_GRAND_CHAMPIONS=0`、`BOSS_ARGENT_CHALLENGE=1`、`BOSS_BLACK_KNIGHT=2`）和 `InstanceProgress` 里（`inst:58-60`）。`SetBossState(id)` 对 `id >= bosses.size()` 是空操作（`InstanceScript.cpp:400-402`），所以 **`FixtureBossStates` / `EngageConfirmBossState` / `EventCompletionBossState` 全部无效**。
- **`GetData` 只暴露两个值**（`inst:437-448`）：`DATA_INSTANCE_PROGRESS=4`、`DATA_TEAMID_IN_INSTANCE=14`。`m_auiEncounter[]` 读不到，所以 `EngageConfirmInstanceData` 只能用 `4:<progress>`。
- `InstanceProgress` 取值（`h:50-62`）：0 INITIAL → 1 GRAND_CHAMPIONS_REACHED_DEST → 2/3/4 CHAMPION_GROUP_DIED_1/2/3 → 5 CHAMPIONS_UNMOUNTED → 6 CHAMPIONS_DEAD → 7 ARGENT_SOLDIERS_DIED → 8 ARGENT_CHALLENGE_DIED → 9 FINISHED。**没有直接写它的 SetData**，只能靠下面这些"事件回报"的 SetData 推进。
- `SetData` 各入口（id 取 `h:27-48` 的枚举值），**都不检查调用者是谁**，框架的 `FixtureInstanceData` 可以直接调：

  | id | 名字 | 作用（`inst:463-679`） |
  |---|---|---|
  | 1 | BOSS_ARGENT_CHALLENGE | 写 `m_auiEncounter[1]`；=3(DONE) 时**无条件**把 progress 置 8、开入口门、排 `EVENT_ARGENT_CHALLENGE_RUN_MIDDLE`（`inst:637-647`） |
  | 2 | BOSS_BLACK_KNIGHT | 写 `m_auiEncounter[2]`；NOT_STARTED 关入口门；DONE → progress 9（`inst:656-670`） |
  | 6 | DATA_ANNOUNCER_GOSSIP_SELECT | **就是播报员 gossip 选项的全部效果**（`toc:98-101` 只多了一步 `RemoveNpcFlag(GOSSIP)`）。按当前 progress 分三段：0 → 开 Grand Champions（值 0 = 完整 RP，值 1 = "跳过 RP"短版本）；6 → 开 Argent Challenge；8 → 开 Black Knight（`inst:467-526`） |
  | 7 | DATA_GRAND_CHAMPION_REACHED_DEST | 非短版本下：值 2 **无条件**把 progress 置 1 并排第 1 组小怪出场（`inst:527-549`） |
  | 8 | DATA_MOUNT_DIED | progress 1–4 时计数，满 3 进下一段；满 3 于 progress 4 时置 5 并 **despawn `VehicleList` 里全部载具**（`inst:550-592`） |
  | 11 | DATA_GRAND_CHAMPION_DIED | `++Counter >= 3` 时：progress 置 6、`m_auiEncounter[0]=DONE`、召 Champion's Cache、英雄下 `PermBindAllPlayers`（`inst:596-627`）。**不检查当前 progress** |
  | 12 | DATA_ARGENT_SOLDIER_DEFEATED | `++Counter >= 9` 时 progress 置 7、boss 前压（`inst:628-636`）。**不检查当前 progress** |

- `Counter` 是**一个共用的 uint8**（`inst:65`），同时用作：骑乘阶段的"本组死了几只"、地面阶段"投降了几只"、士兵计数，以及 **Argent Challenge 选谁**（gossip 时 `Counter = urand(0,1)`，4 秒后 `Counter ? EADRIC : PALETRESS`，`inst:511`、`inst:1027`）。§3.3 利用这一点强制指定 boss。
- **清场/复位只有一个入口**：`EVENT_CHECK_PLAYERS` 每 5 秒检查一次，**地图里没有活着的非 GM 玩家**时调 `InstanceCleanup()`（`inst:768-776`、`inst:269-290`），按 progress 回滚：
  - 1–4：despawn 全部载具/冠军/小怪，播报员 3 秒后重生，progress 回 0（`inst:301-331`）；
  - 5：despawn 冠军并在 `NPC_GrandChampionGUID[]` 记录的三只基础上**原地重召地面形态冠军**（`inst:332-372`）；
  - 6/7：despawn 士兵与 Argent boss，progress 回 6（`inst:373-399`）；
  - 8：despawn 黑骑士及其狮鹫，播报员 3 秒后重生（`inst:400-420`）。
  - 冠军 `EnterEvadeMode` 是空函数（`gc:593`），**Grand Champions 团灭后不会自己复位，只能等全员死亡触发 InstanceCleanup**。框架如果在 5 秒检查前就复活 bot，清场可能不发生（待实测）。
- 没有 boss boundary。门：Main Gate 195647（guid 150077，(746.7, 677.5)，boss 从门后 `SpawnPosition` (746.67, 684.08, 412.5) 召出，`inst:25`）、North Portcullis 195650（guid 150076，(807.8, 618.1)，入口门，开场开着）、South/East Portcullis（常关）。竞技场地面 z≈411.2–412.5，中心约 (746.6, 618)。
- 播报员 Jaeren 35004 guid **200038**（(748.31, 619.49, 411.17)，`spawntimesecs=999999`）。Tirion 33628 guid 1971379 在看台 (746.4, 557.5, 435.4)，只负责喊话。
- 竞技场里有 **24 辆 DB 载具**：Argent Warhorse 35644 guid 200026–200037、Argent Battleworg 36558 guid 200014–200025，都 `spawntimesecs=999999`。它们在 progress < 5 且 `m_auiEncounter[0]==NOT_STARTED` 时被登记进 `VehicleList`（`inst:175-182`）。**4 个 Lance Rack GO 196398**（guid 150063–150066，type 22 施法者，spell 64682 给 Argent Lance 46106）。

### 0.2 mod-playerbots 策略（Ai/Dungeon/TOC）

- context key 与 `getName()` 都是 **`wotlk-toc`**（`DungeonStrategyContext.h:62`，`TOCStrategy.h:16`），`PlayerbotAI.cpp:1781-1782` 在 `case 650` 自动挂载。RuntimeStrategyName 恒等。
- 全部内容（`TOCStrategy.cpp:9-26`，无 multiplier）：

  | trigger → action（优先级） | 内容 |
  |---|---|
  | `toc lance` → `toc lance`（RAID+5） | 不在载具上、100 码内**同时**有 Warhorse 和 Battleworg、没装备 Argent Lance → 背包里有就换上主手，没有就走到 Lance Rack 使用（`TOCTriggers.cpp:12-37`，`TOCActions.cpp:14-89`） |
  | `toc ue lance` → `toc ue lance`（RAID+2） | 载具都没了还拿着枪 → 跑 `EquipUpgradeAction` 换回武器（`TOCActions.cpp:91-102`） |
  | `toc mount near` → `toc mount`（RAID+4） | 走到最近的**友方、有空位**的 Warhorse/Battleworg，`HandleSpellClick` 上车（`TOCActions.cpp:178-241`） |
  | `toc mounted` → `toc mounted`（RAID+6） | 在车上：Defend 叠到 3 层 → 目标距离 >5 码用 Charge → 目标有 defend 用 Shield-Breaker → Thrust。目标只认冠军和小怪 entry（`TOCTriggers.h:82-87`，`TOCActions.cpp:104-176`） |
  | `toc eadric` → `toc eadric`（RAID+3） | Eadric 读 Radiance 时 `SetFacingTo` 背对他（`TOCActions.cpp:243-262`） |

- **没有**：践踏（骑车压过下马步行的冠军，`gc:668-701`）、Paletress 的 Memory 转火/护盾处理、Hammer of the Righteous 回扔、黑骑士任何机制（食尸鬼爆炸、Desecration、Death's Bite）。
- **对隔离场景的重大副作用**：`toc lance` / `toc mount near` 只看"100 码内有两种载具"，不看遭遇阶段。竞技场里 24 辆 DB 载具一直在（除非走过骑乘阶段被 despawn），所以**在 Argent Challenge / Black Knight 隔离场景里，bot 会跑去拿枪换主手、骑马**。这两个场景必须配 `FixtureDespawnSpawns=200014,…,200037`（§3.4、§4.3）。

---

## 1. Grand Champions

### 1.1 开战流程（完整版）

1. 玩家与播报员对话。progress 0 时**说话的玩家必须在载具上**才出选项，否则只给"先上马"文本（`toc:59-73`）。两个选项：`GOSSIP_START_EVENT_1A`（完整 RP）/ `1B`（Skip roleplay，`toc:36`）。选中后 `SetData(6, 0|1)`（`toc:100`）。
2. 短版本（值 1，`inst:484-506`）：三只冠军（5 选 3，`urand`）各带 3 只同阵营小怪一次召出，progress 直接置 1，10 秒后第 1 组小怪走到中场、3 秒后解除免疫 `DoZoneInCombat`。完整版（值 0）是 Tirion 喊话后逐个召冠军、走 escort 路点，最后一只到位才置 progress 1（`inst:527-549`）。
3. 骑乘阶段（progress 1→5）：
   - 小怪 `npc_toc5_grand_champion_minion`（35314/35323/35325/35326/35327 等，**没有英雄 entry**，HealthModifier 5.95）每 5 秒自挂 Defend 64100，技能是 Charge 63010（8–25 码，随机挑玩家或玩家坐骑，清仇恨）/ Shield-Breaker 68504（10–30 码，只打坐骑）/ Thrust（`gc:246-327`）。三只都死 → 下一组（`inst:550-579`）。
   - 三组小怪清完 → 三只冠军骑马参战（`inst:905-931`）。冠军骑乘时致命伤害被吞：下马、NON_ATTACKABLE+免疫、步行去找最近的 Battleworg（`gc:537-570`）；走到就 `SetHealth(50000)` 重新上马，并 `SetData(DATA_REACHED_NEW_MOUNT)` 把计数减 1（`gc:614-639`、`inst:593-595`）。**只有三只同时处于下马状态计数才到 3**。
   - 反制手段是**践踏**：步行途中 5 码内有玩家骑着 Warhorse → 冠军被晕 15 秒（`gc:668-701`）。
   - 三只同时下马 → progress 5，`VehicleList` 全部载具 despawn（玩家也被迫下车），冠军 `DoAction(1)`（回满血、清光环）走到两侧，15 秒后 `DoAction(2)` 地面开打（`inst:580-590`、`inst:932-969`、`gc:477-496`）。
4. 地面阶段：三只冠军同时打，`JustEngagedWith` 里 `CallForHelp(100)`（`gc:407-411`）。职业技能见 `gc:413-453`、`gc:784-930`：法师（Fireball / Blast Wave / Haste / Polymorph）、萨满（Chain Lightning / Earth Shield / Healing Wave 奶队友 / Hex of Mending）、猎人（Lightning Arrows / Multi-Shot）、盗贼（Eviscerate / Fan of Knives / Poison Bottle）、战士（Mortal Strike / Bladestorm / Intercept）。
5. 致命伤害 → 该冠军投降（NON_ATTACKABLE+免疫、停战，`gc:571-590`），`SetData(11)`；第三只投降 → progress 6、`m_auiEncounter[0]=DONE`、召 Champion's Cache、英雄 `PermBindAllPlayers`（`inst:596-627`）。**没有任何一只真死**。

### 1.2 能不能合规跳过骑乘阶段

- **不能**。正常规则下唯一的选项是"跳过 RP"（`1B`），它只省掉开场喊话和 escort，不省骑乘战。骑乘阶段是遭遇本体。
- 夹具层面能"跳过"，但都属隔离形态（口径降级）：见 §1.4 方案 B。

### 1.3 bot 能不能打骑乘阶段（推断，未实测）

- 有 lance/上车/四技能循环（§0.2）。但**没有践踏**：步行冠军是 NON_ATTACKABLE+免疫，不会出现在 `possible targets no los` 里，bot 不会主动靠近 → 冠军会一再重新上马（每次 50000 血），三只"同时下马"很难凑齐 → 骑乘阶段大概率永远结束不了。
- 治疗骑在马上不能治疗，全队只能靠载具技能。
- 结论：**骑乘阶段是 playerbots 的大缺口**（需要"压过步行冠军"的行为），属大工程。

### 1.4 场景建议

- **方案 A（完整遭遇，大工程）**：`FixtureInstanceData=6:1`（等价于选"跳过 RP"；只省掉"说话的人要在车上"这一条前置检查，记录为隔离形态）+ bot 自己拿枪上马。框架缺口：
  1. `BossEntry` 只能填一个，冠军是 5 选 3 随机 → 要支持"任一 entry"（小）；
  2. 被绑定的冠军要到骑乘阶段末尾才可攻击，框架的 pull / 坦克仇恨确认会失败 → 需要"开战确认 = `GetData(4) >= 1`"（现有 `EngageConfirmInstanceData` 是 `==`，progress 一路涨，要支持 `>=`，小）；
  3. 击杀判定要"三只都投降"→ 需要"完成 = `GetData(4) >= 6`"（小）；
  4. 现有 `EventStarterEntry` gossip 路径调的是 `starter->AI()->sGossipSelect`（`AttemptRunner.cpp:2496`），而播报员的选项写在 `CreatureScript::OnGossipSelect`（`toc:89-106`），AI 上没有 → 走不通，只能用 `FixtureInstanceData=6:x` 代替，或框架改走 `sScriptMgr->OnGossipSelect`（小）。
  - 加上 §1.3 的 bot 缺口，整体是**大工程**。建议暂缓。
- **方案 B（只测地面阶段，隔离，需小框架改动）**：
  - 夹具推进到 progress 5 且**不产生任何冠军/小怪**：
    `FixtureInstanceData = 7:2,8:0,8:0,8:0,8:0,8:0,8:0,8:0,8:0,8:0,8:0,8:0,8:0`
    - `7:2`（非短版本分支）置 progress 1，排的第 1 组出场事件对空 GUID 无效（`inst:538-546`、`inst:819-852`）；
    - 注意 `7:2` 只有在**播报员活着**时才会置 progress（代码在 `if (announcer)` 里，`inst:539-546`）。
    - 12 次 `8:0`：每 3 次进一段，第 12 次置 progress 5 并 despawn 全部 24 辆载具（顺带解决 §0.2 的拿枪副作用），排的"移动/攻击"事件对空 GUID 都是空操作。全部在同一 tick 完成，早于任何事件执行。若上一场超时留下 `Counter` 非零，只会提前到 5，多出的 `8:0` 在 progress 5 下是空操作，序列本身是稳的。
    - 副作用：约 11.5 秒后 `EVENT_GRAND_GROUP_1_ATTACK` 会把 `Counter` 清零（`inst:850`），开怪太快、11.5 秒内就有冠军投降的话计数会丢（不太可能，首轮看日志）。
  - 再用 `FixtureSummonCreature` 在两侧点召三只指定冠军（固定组合，便于复现），例如战士/萨满/法师：
    `35572:736.70,650.02,412.40,4.71;35571:756.32,650.05,412.40,4.71;35569:746.50,650.65,411.70,4.71`（坐标取自 `inst:347-365`，**待实测**）。
    召出时 AI 初始化走 `Reset()`，progress==5 分支会自己 `DoAction(1)`+`DoAction(2)`、去掉 NON_ATTACKABLE/免疫、置 AGGRESSIVE（`gc:388-399`）——和副本在 progress 5 团灭后重召冠军（`inst:339-367`）是同一条路。
  - 仍缺的框架能力（都小）：
    1. **三只都投降才算击杀**：`KillOnBossSurrender` 只看绑定的那一只，先投降的那只会被判击杀。需要"完成 = `GetData(4) == 6`"之类的判据；
    2. **清掉上一场留下的召唤物**：冠军投降后不会 despawn（`NPC_GrandChampionGUID[]` 为空，`inst:605-614` 的 `MovePoint(9)` 走不到它们），团灭也不会 evade（`gc:593`）。下一场 `FindBossNear` 可能绑到上一场 1 血、NON_ATTACKABLE 的旧冠军 → **立刻误判投降击杀**。需要召唤前 despawn 同 entry 的旧召唤物；
    3. 三只 boss 的 `BossEntry` 只填一只（取战士 35572 做"主 boss"），承伤/输出统计口径要说明。
  - 每场重放同一串 `FixtureInstanceData` 可重复：`7:2` 无条件把 progress 拉回 1（`inst:541`），英雄下每场都会 `PermBindAllPlayers` 并召一个 Champion's Cache（不影响测试）。
  - 准备点候选 (746.5, 612, 411.3)、开怪点 (746.5, 638, 411.6)（离三只冠军 12 码）——**待实测**。

---

## 2. 士兵阶段（Argent Challenge 前半）

- 第二次 gossip（progress 6，`SetData(6,*)`）→ 播报员喊 Eadric 或 Paletress 的介绍（`inst:508-519`）、关入口门、开 Main Gate，在门后召 **9 只士兵**（每组 Argent Lightwielder 35309 / Monk 35305 / Priestess 35307，英雄 35310/35306/35308），escort 到三处站位 x≈716–778、y≈645–660（`inst:984-1022`、`ac:542-594`）；4 秒后召 boss 到 (746.88, 660.26, 411.7)（`inst:1023-1033`）；12.5 秒后士兵解除 NON_ATTACKABLE、置 AGGRESSIVE，**但不 `DoZoneInCombat`**（`inst:1048-1063`，那行被注释掉了）——要队伍自己去拉。
- 英雄额外技能：Monk 致命伤害时 Divine Shield + Final Meditation（一次，`ac:596-606`、`ac:615-616`）、Priestess Mind Control（`ac:622-623`）、Lightwielder Unbalancing Strike（`ac:628-629`）。Priestess 的 Fountain of Light 召唤物 35311。
- 9 只全死（`SetData(12)` ×9）→ boss 前压到 (746.88, 635.26, 411.7)，3 秒后解除免疫、`DoZoneInCombat`（`inst:1064-1085`）。
- 框架缺口：士兵是副本 `instance->SummonCreature` 召出的，没有 spawn id，**`PrerequisiteSpawns` 用不了**；`EngageTrigger=summon` 只认"场景 boss 召出的临时单位"（`Scenario.h:87-88`、`AttemptRunner.cpp:2429`），这些士兵的召唤者不是 boss。boss 在士兵死光之前 NON_ATTACKABLE，pull 会失败。要走完整流程需要"拉取副本召唤的前置怪（按 entry）"+"开战确认 `GetData(4)>=7`"——**中等框架改动**。建议先做 §3 的隔离 boss 战。

## 3. Argent Confessor Paletress / Eadric the Pure

### 3.1 脚本

- 两者都：`Reset()` 置 REACT_PASSIVE、`SetData(1, NOT_STARTED)`；`JustEngagedWith` 置 IN_PROGRESS；**致命伤害被吞、投降**：伤害改成 `hp-1`，施遭遇/成就信用法术（Eadric 68575 + `UpdateEncounterState(68574)`，Paletress 68574），改友好阵营、`_EnterEvadeMode`、NON_ATTACKABLE+免疫、`SetData(1, DONE)`（`ac:129-150`、`ac:269-296`）。→ progress 8，boss 走到中场、6 秒后放宝箱（要播报员在）、再 4 秒走回门口 3 秒后 despawn（`inst:1086-1121`）。**投降后自己清场**。
- 没有覆写 `EnterEvadeMode`：团灭后普通 evade 回家（家 = 召唤点）。
- **Eadric**（英雄 35518，HealthModifier **55.2**）：Vengeance 自身光环；**Radiance 66935** 每 16 秒，只打面朝他的目标（`spell_eadric_radiance` 过滤 `HasInArc(M_PI, caster)`，`ac:719-740`）——背对即可躲；**Hammer of Justice**（晕）+ **Hammer of the Righteous** 每 25 秒随机 55 码目标，被锤的人动作条出现回扔技能 66904/66905（回扔 15k 伤害，`ac:123-127`、`ac:171-180`）。bot 只有"背对 Radiance"（§0.2），不会回扔（非必需）。
- **Paletress**（英雄 35517，HealthModifier 12）：Smite（随机 50 码）、Holy Fire（随机 30 码 DoT）；**血量 <25% 一次**：Holy Nova、给自己上 **Reflective Shield 66515**（吸收伤害并把 25% 反射给攻击者，`ac:767-795`）、从 25 种 Memory 里随机召一只（`ac:305-310`、`ac:319-331`）、Confess；Memory 5.5 秒后参战（Old Wounds / Shadows of the Past / Waking Nightmare，`ac:374-460`）；Memory 死 → 去掉护盾（`ac:250-257`、`ac:397-403`）。期间 Renew 奶自己或 Memory。bot 没有"转火 Memory、别打盾"的逻辑，缺口在这里（中）。
- 击杀判定：投降后 hp=1、带 NON_ATTACKABLE → 正好命中 `KillOnBossSurrender`（`AttemptObserver.cpp:814-827`：hp_min ≤10% 且 NON_ATTACKABLE）。

### 3.2 方案 1（推荐，现在能建）：直接召 boss，跳过士兵

- `BossSpawnMode=script`、`FixtureSummonCreature` 在 boss 原本前压到的位置召出（夹具会解除 NON_ATTACKABLE/免疫、置 AGGRESSIVE，`AttemptRunner.cpp:853-877`；AI 的 `Reset` 在召唤时已跑过，不会再置回 PASSIVE）、`KillOnBossSurrender=1`、`EngageTrigger=pull`。
- **同时配 `FixtureInstanceData=11:0,11:0,11:0`**：把 progress 置 6（模拟 Grand Champions 已完成）。好处：团灭（全员死）时 `InstanceCleanup` 走 6 分支，把 `NPC_ArgentChampionGUID`（`OnCreatureCreate` 对召出的 Eadric/Paletress 也会记，`inst:156-159`）despawn 掉，下一场不会有两只 boss。没全灭的超时中止仍会留一只满血 PASSIVE 的旧 boss，要看首轮日志（待实测）。
- **必须配 `FixtureDespawnSpawns=200014,200015,200016,200017,200018,200019,200020,200021,200022,200023,200024,200025,200026,200027,200028,200029,200030,200031,200032,200033,200034,200035,200036,200037`**：否则 bot 会去拿枪骑马（§0.2）。载具 `spawntimesecs=999999`，`ResetInstance` 只恢复 boss/前置怪 spawn，不会把它们摆回来。
- 召唤点：(746.88, 635.26, 411.70, 4.71)（`inst:1068`，朝南）；开怪点 (746.9, 623, 411.5)；准备点 (746.6, 600, 411.4)——**待实测**。
- 两个场景：`heroic-toc5-paletress-h5g`（`BossEntry=34928`）、`heroic-toc5-eadric-h5g`（`BossEntry=35119`）。`Strategy=wotlk-toc`、`MasterlessAvoidAoe=1`、`TimeoutSeconds=480`。口径：隔离（跳过士兵）。

### 3.3 方案 2（更贴近原流程，现在能建，但要实测验证）：走副本 gossip 流程并强制指定 boss

- 利用共用 `Counter`（§0.1）：gossip 时 `Counter = urand(0,1)`，4 秒后按 `Counter` 非零选 Eadric。
  - **强制 Eadric**：`FixtureInstanceData = 11:0,11:0,11:0,6:0,12:0` → 最后一步把 {0,1} 变成 {1,2}，必为 Eadric。
  - **强制 Paletress**：`FixtureInstanceData = 11:0,11:0,11:0,6:0,12:0,12:0,12:0,11:0` → 三次 `12` 把 {0,1} 变成 {3,4}，再一次 `11` 时 `++Counter >= 3` 必然清零（{3,4}→0）。副作用：多召一个 Champion's Cache、重复一次 `PermBindAllPlayers`、15 秒后播报员 gossip 标志被恢复（均不影响战斗）。
  - 12.5 秒后 `EVENT_ARGENT_SOLDIER_GROUP_ATTACK` 把 `Counter` 清零，后续士兵计数照常（`inst:1050`）。
- 这条路会召出 9 只士兵，受 §2 的框架缺口限制（士兵拉不了、boss 在士兵死光前不可攻击）。**只有补上 §2 的框架改动后才有意义**；在那之前可以只用它验证"选谁"是否如预期（看 `fixture_instance_data` 事件与出现的 boss entry）。

### 3.4 小结

- 现在：方案 1 两个场景可以直接建。
- 之后：补 §2 的框架改动 + 方案 2，才是"正常规则"口径的 Argent Challenge。

---

## 4. The Black Knight

### 4.1 开战流程

- progress 8 时 gossip（`SetData(6,*)`）→ Tirion 喊话，3 秒后播报员在 (769.83, 651.92, 447.04) 召 **Skeletal Gryphon 35491**，`vehicle_template_accessory` 把 Black Knight 35451 装在 seat 0（`inst:520-524`、`inst:1122-1143`）。
- 狮鹫走 `script_waypoint` 35491（19 点，第 11/12 点 (753.8, 634.5, 411.6) 落地）→ `SetData(13)`（`bk:344-357`）→ 3 秒后黑骑士下车跳到 (751.0, 638.1)、2 秒后对播报员施法、再 1 秒狮鹫飞走、4 秒后走向 (746.81, 623.15, 411.42) 并**杀死播报员**、14 秒后喊话、5 秒后 `ReplaceAllUnitFlags(NONE)`、AGGRESSIVE、对最近目标 `AttackStart` + `DoZoneInCombat` + `DoAction(1)`（`inst:1144-1219`）。从 gossip 到开打约 **3 + 飞行（待实测）+ 29 秒**。
- `DoAction(1)`：置 IN_PROGRESS、施 Raise Dead（联盟队伍复活出 **Risen Arelas 35564**，英雄 35568）、despawn 播报员、排一阶段技能（`bk:149-173`）。

### 4.2 机制

- 一阶段：Plague Strike / Icy Touch / **Death's Respite**（随机 50 码）/ Obliterate；复活的播报员食尸鬼会 Leap（5–30 码）+ Claw（Claw 每次清仇恨随机换目标，`bk:449-470`）。
- 致命伤害（阶段 1、2）：伤害置 0、回满血、NON_ATTACKABLE、晕住、对召唤物施 **Ghoul Explode 67751**（所有食尸鬼自爆，Explode 67729 / 英雄 67886，炸到玩家则成就"I've Had Worse"失败）、假死 67691（`bk:122-147`）。复活法术 67693 命中自己后进入下一阶段（`bk:175-219`）。
- 二阶段（骷髅）：Army of the Dead 67761（大量 Risen Champion 35590/英雄 35717）+ **Desecration** 67778（地面区域，随机 50 码）+ 一阶段技能（去掉 Death's Respite）。
- 三阶段（幽灵）：**Death's Bite** 67808 每 2–4 秒全体 AoE、**Marked for Death** 67823 每 9 秒。
- 真死：`JustDied` 施信用法术 68663、`SetData(2, DONE)`（`bk:298-306`）。
- `EnterEvadeMode` 里先 `DespawnOrUnsummon(1ms)`（`bk:116-120`）：团灭即消失，效果类似 HARD_RESET，但不是模板标志。

### 4.3 场景建议（现在能建）

- 走副本自己的事件：`FixtureInstanceData = 1:3,6:0`。`1:3` 无条件把 progress 置 8（`inst:637-647`；排的 RUN_MIDDLE 找不到 Argent boss，空操作），`6:0` 就是第三次 gossip 的效果。黑骑士是副本自己召、自己开战，**战斗本体完全是正常规则**；只跳过了前两个遭遇（隔离口径）。
- `BossSpawnMode=script`、`BossEntry=35451`、`ScriptBossAppearTimeoutSeconds=90`（狮鹫一召出就能被 200 码网格找到，但要等 30+ 秒才可攻击）、`ScriptBossRequireActive=1`（开打前是 PASSIVE）、`ScriptBossAcceptAutoEngage=1`（原生设计就是他自己 `DoZoneInCombat` 找上队伍，同 PoS Tyrannus 的情况）、`EngageTrigger=pull`、**`KillOnBossSurrender=0`**（阶段转换时他血量打到很低后变 NON_ATTACKABLE 假死，开了会误判击杀）。
- 同样**必须配 §3.2 的 24 个载具 `FixtureDespawnSpawns`**。
- 开怪点 (746.81, 623.15, 411.42)（他最后走到的点）；准备点 (746.6, 605, 411.4) 或竞技场南侧——**待实测**（要确认降落/剧情期间 bot 不会提前打狮鹫或黑骑士，他们在剧情中是 PASSIVE + NON_ATTACKABLE）。
- 观察项：假死期间 bot 是否丢目标、observer 是否把"boss 不在战斗"当成卡住（待实测）；Risen Champion 数量与 Desecration 承伤；三阶段 Death's Bite 的治疗压力。

### 4.4 重复 attempt 的限制

- 事件依赖**活着的播报员**（`inst:1124`）。播报员在剧情中被杀、开打时又被 `DoAction(1)` despawn，`spawntimesecs=999999`。
  - **团灭**：全员死亡 → `InstanceCleanup` 走 8 分支，`DespawnOrUnsummon(0ms, 3s)` 让播报员 3 秒后重生（`inst:412-417`），下一场可以再来（前提是 bot 在 5 秒检查前没被复活，待实测）。
  - **击杀**：progress 9，不会清场，播报员不回来 → **同一个 run 里击杀后的下一场会以"boss 未出现"中止**。
- 解决：框架加一个"开场按原始 DB spawn 恢复指定 spawn"的夹具（复用 `ResolveOrRestoreSpawn`，恢复 guid 200038）——**小改动**。在那之前，每个 run 只能稳定拿到 1 次击杀，或击杀后靠新 run 重来。

---

## 5. 结论与优先级

| 遭遇 | 结论 | 需要什么 |
|---|---|---|
| Eadric the Pure | **现在能建**（隔离：跳过士兵） | `FixtureSummonCreature` + `KillOnBossSurrender=1` + `FixtureInstanceData=11:0,11:0,11:0` + 24 载具 `FixtureDespawnSpawns` |
| Argent Confessor Paletress | **现在能建**（同上） | 同上；bot 缺口：Memory 转火 / 反射盾（中） |
| The Black Knight | **现在能建**（走副本事件，战斗本体正常规则） | `FixtureInstanceData=1:3,6:0` + script 模式 + 24 载具 despawn；击杀后重复要小改（恢复播报员 spawn） |
| 士兵阶段 + Argent Challenge 完整流程 | **中等框架改动** | 拉副本召唤的前置怪（按 entry）、开战确认 `GetData(4) >= 7`；boss 选择可用 §3.3 的 Counter 夹具 |
| Grand Champions 地面阶段（隔离） | **小框架改动** | "三只都投降"完成判据、召唤前清旧召唤物；夹具序列见 §1.4 方案 B |
| Grand Champions 完整（含骑乘） | **大工程** | 框架：多 entry、`>=` 型开战确认、完成判据、gossip 走 `OnGossipSelect`；bot：践踏步行冠军（playerbots 缺口） |

建议顺序：Eadric → Paletress → Black Knight（一个 run 一次击杀先测基线）→ 视结果决定是否做 Grand Champions 地面隔离的小改动。骑乘阶段先记为已知缺口，不做。
