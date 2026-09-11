# 清怪控制链：正确的开怪流程（设计 + 实现记录）

更新：2026-09-11 晚。前半部分是设计与方向性更正（保留原文），末尾「实现与实测」一节记录 2026-09-11 晚的
实现、七轮迭代踩到的坑与当前数字。**代码已实现并推到工作区（未提交），流程已能跑通但稳定性未验收。**

## 为什么要写这份文档

2026-09-11 我（上一轮会话）实现的控制是**错误的形状**：在战斗已经打起来、全队 AoE 满天飞
的时候，往里插一次控制，再用一个乘子去「保护」它。实测拿到了决定性反例：

> run392 / attempt 3 —— 14.443s 圣骑铺下**奉献(48819)**；14.637s 法师**变形术**落在
> guid 98 上（`miss=0`）；**14.639s** 该目标挨了奉献一跳 51 点；`cc_watch`（1 Hz）
> 一格都没采到。**羊存活 < 2 毫秒。**

原因是结构性的：`CrowdControlProtectionMultiplier` 压的是「**要不要发起一次新的 AoE 施法**」，
但**已经铺在地上的持续性 AoE（奉献、暴风雪）不会因此停下**。控制只要落进一块已生效的
AoE 区域，下一跳就没了，乘子根本没有介入机会。

用户随后指出了正确的流程，本文档记录它：

> 应该是坦克发出控制信令，让法师羊、萨满妖术、盗贼闷棍，然后坦克开怪，
> 然后大家都不要放 AOE，然后一个一个怪击杀，而且羊可以反复控制，可以最后击杀。

也就是说：**这不是「怎么保护控制」的问题，是「开怪流程」的问题。**

## 目标流程

1. **脱战时**，坦克指派：法师羊 A、萨满妖术 B、盗贼闷棍 C；
2. 控制落在**满血、没人打、尚未进入战斗**的怪身上；
3. 坦克**再**开怪；
4. **只要还有任何一只被控住，全队一律不放 AoE**；
5. 单体、按指定顺序一个个击杀；
6. 控制掉了就重新上；被控的怪**最后**才杀。

## 上游已有的底座（**本轮复查确认，别重写**）

| 能力 | 位置 | 说明 |
|---|---|---|
| 每个 bot 各有一个击杀图标与一个控制图标 | `RtiValue` / `RtiCcValue`（`src/Ai/Base/Value/RtiValue.h`） | `rti` 默认骷髅、`rti cc` 各自可设。**法师=月亮、萨满=方块、盗贼=十字是天然可行的**，不需要改共享层 |
| 按图标取目标 | `RtiTargetValue`（`src/Ai/Base/Value/RtiTargetValue.cpp`）、值名 `"rti target"` / `"rti cc target"` | 读 `group->GetTargetIcon(index)`，带死亡/视线/距离校验 |
| **DPS 不打被控的怪** | `FindNonCcTargetStrategy::IsCcTarget`（`src/Ai/Base/Value/TargetValue.cpp:62-85`） | **已经**排除「任何队友的 `rti cc` 图标目标」以及硬编码的月亮(index 4)。这一条不用写 |
| 控制动作基类 | `CastCrowdControlSpellAction`（`GenericSpellActions.h:371`） | 目标走 `"cc target"`；术士 banish/fear、德鲁伊 roots/hibernate/cyclone 已改用 `"rti cc target"` |
| 法师变形术 | `CastPolymorphAction`（`MageActions.h:222`） | 已经是 `CastCrowdControlSpellAction`，直接可用 |
| 打标记的动作 | `MarkRtiAction` / `MarkRtiStrategy`（`RtiAction.cpp`、`MarkRtiStrategy.cpp`） | 现有实现只处理单个击杀图标 |
| **开怪前的窗口** | mod-raidtest `CombatTrigger::HoldFollowerAttackTagged`（`CombatTrigger.cpp:147`） | 只摘掉 `attack tagged` 这一个非战斗策略，**不阻止施法**；`RestoreHeldFollowerStrategies()` 已被推迟到真正开怪那一刻。**框架一行都不用改** |

## 缺的四块（要实现的）

| | 内容 | 落点 |
|---|---|---|
| **A 指派** | 坦克脱战、前方成组敌人 ≥3 只时打标记：骷髅=先杀、月亮=羊、方块=妖术、十字=闷棍；并把各 CC bot 的 `rti cc` 设成对应图标 | mod-playerbots 共享层 |
| **B 开怪前上控** | 非战斗状态下各 CC 职业对自己的图标目标施放控制。法师复用上游动作；**萨满妖术、盗贼闷棍要补两个同形状的 `CastCrowdControlSpellAction` 派生** | mod-playerbots |
| **C 有控制就不放 AoE** | **把 `CrowdControlProtectionMultiplier` 的几何判据整个换掉**：只要本次拉怪里还有任何一只带友方控制光环，全队所有 `IsTargetingArea()` 的负面法术相关度归零 | 替换现有乘子 |
| **E 重新上控** | 控制光环掉了、且该目标还不是当前击杀目标时补上 | mod-playerbots |

（D「按序单体击杀、不碰被控的」上游已有；只需让选目标优先骷髅。）

## 两个必须先知道的约束

1. **盗贼闷棍(Sap) 要求盗贼处于潜行、且目标未进入战斗**，所以盗贼得先潜行；闷棍只对人型有效。
   泰蕾斯特拉那 4 只守卫全是人型，可用；**奥莫洛克那组的 `Crystalline Keeper`(26782) 是元素
   (type 4)，只能致盲**。
2. **脱战放羊/妖术会把那只怪拉进战斗**（它被控着不动）。这就是真人打法，但坦克开怪必须
   紧接着，否则控制会在坦克还没抓住仇恨时就空转掉。

## 待用户决定的一件事：代码放哪

- **塞进已有文件**（`RtiAction.cpp/h`、`GenericTriggers`、`CombatStrategy` 等）：
  增量编译约 2 分钟，文件划分不干净。
- **按上游风格新建文件**（如 `Ai/Base/Strategy/TrashCcStrategy.*`）：新增源文件需要 cmake
  重新配置 → `revision.h` 重生成 → **接近全量重编，40 分钟以上**（本项目有「禁止全量编译」
  的约定，此前踩过一次）。

上一轮会话的建议是：**先塞进已有文件把流程跑通验证，确认有效后再单独做一次文件归位。**

## 验证方法（已就绪，不用再搭）

- 测试床：场景 **`heroic-nexus-telestra-trash`**（mod-raidtest `f0dad96`）——前置 = 泰蕾斯特拉
  那 4 只**站桩**守卫，拉怪点与准备点同坐标 (519,110,-16.04)，`BossEntry = 26723`
  （被冰冻牢笼锁着、打不动），于是清完后那次拉怪以 `pull failed (boss not engaged)` 干净收场，
  队伍**全程不接近任何 boss**。每场 ≈ 清怪 + 短恢复。`raidtest_accounts` 已映射到共用的
  guid 796–800（萨满 800 会妖术 51514、法师 799 会变形术 118/12824/12825/12826）。
- 观察：mod-raidtest 的 1 Hz **`cc_watch`** 采样（`AttemptRunner::SampleInterruptWatch` 内）
  输出前置怪身上的脱战类控制光环、`remaining_ms` / `max_ms` / 施法者 / `breakable` / 血量。
  控制被打破的表现 = 采样突然断掉而 `remaining_ms` 还很大。
- 判读基线（同一测试床，三轮共 15 场）：

  | | 到达 boss | 清怪时长均值 |
  |---|---|---|
  | 基线（无任何控制规则，完整场景 12 场） | 9/12 | 33.4 秒 |
  | run390（只妖术） | 5/5，零死亡 | 33.7 秒 |
  | run391（妖术+羊，羊没放出来） | 3/5 | 36.6 秒 |
  | run392（妖术+羊，羊放出 1 次） | 5/5，零死亡 | 35.2 秒 |

  **半套实现（只做输出侧）的效果在噪声内**：合计 13/15 对基线 9/12，33.4 → 35.0 秒。

## 相关但未解决的两条

1. **妖术早掉的根因未定位。** `Auras.log`（临时开 `Logger.spells.aura=5` 采到）显示移除模式是
   `AURA_REMOVE_BY_DEFAULT`，发生在暴风雪(42938) 对 4 个目标结算伤害的中途，卸掉的正是 Hex
   的两个效果（aura type 56 `TRANSFORM` + 60 `MOD_PACIFY_SILENCE`）。但妖术
   **没有** `AURA_INTERRUPT_FLAG_TAKE_DAMAGE`（客户端 `Spell.dbc` 解出 51514 =
   `0x80000`，只有 `CHANGE_MAP` 一位；变形术 12826 = `0x80002` 才有 `TAKE_DAMAGE`），
   且它在 run390/attempt2 里扛住了 5.2s、7.7s 两次伤害才掉，**「任何伤害都打破」解释不了**。
   已排除：递减抗性（`max_ms=30000`）、死亡、采样中断、小怪驱散（Spellbreaker/Arcane Torrent
   施放时刻逐场比对，没有一次落在消失窗口内）、`acore_world.spell_dbc` 覆盖（无该行）、
   `AuraInterruptFlags` 路径。**下一步只能在 `Unit::_UnapplyAura` 临时打印调用方。**
2. **核心判断「控制会不会被伤害打破」本身会漏判。** `Unit::HasBreakableByDamageCrowdControlAura()`
   （`Unit.cpp:949-970`）用的就是 `AuraInterruptFlags & AURA_INTERRUPT_FLAG_TAKE_DAMAGE`，
   对妖术会报 false，而妖术实测会掉。任何基于这个判据的保护逻辑都要知道这一点。

## 相关文档

- [清怪战术三个假设的完整记录](bosses/heroic-nexus/TRASH-TACTICS.md)（含三轮实测数据与被推翻的结论）
- [泰蕾斯特拉](bosses/heroic-nexus-telestra/README.md)、[奥莫洛克](bosses/heroic-nexus-ormorok/README.md)、[凯利丝塔萨](bosses/heroic-nexus-keristrasza/README.md)


---

## 实现与实测（2026-09-11 晚，run393–run406）

### 落点（都塞进已有文件，未新增源文件）

| 块 | 位置 | 说明 |
|---|---|---|
| A 指派 | mod-playerbots `Ai/Dungeon/Nex/NexActions.cpp` `TrashCcMarkAction` | 坦克脱战、且编排层把拉怪目标钉在它的 `pull target` 上时打标记：十字（闷棍）先分给离盗贼最近的一只；月亮（羊）、方块（妖术）按「治疗 > 有法力 > 其它」取 30 码内第一只，够不着就不分；**骷髅等分出去的控制全部落地后再标**（上游 `AttackersValue` 会把骷髅当攻击者、`DpsTargetValue` 直接走图标捷径，标早了 DPS/治疗开怪前就动手）。战斗中骷髅死了：先挪到没有控制图标的活怪，没有就按 十字→方块→月亮 放出来打 |
| B 开怪前上控 | 同目录 `TrashCcCastAction`（羊/妖术，`CastSpellAction` 派生）、`TrashCcSapAction`（`MovementAction` 派生：潜行→走到 11 码→闷棍） | 目标直接读队伍图标（`TrashCcIconUnit`），不走基于仇恨表的 `cc target`。**顺序：闷棍先**（不进战斗），羊/妖术最多等它 9 秒；羊一落地整组 2 秒内就进战斗（实测），之后闷棍不可能 |
| C 有控制不放 AoE | `Ai/Base/Strategy/CrowdControlProtectionMultiplier.*`（重写） | 判据换成全局状态：附近有怪带友方控制光环、或被月亮/方块/十字钉着 → 所有多目标法术归零。多目标 = `IsTargetingArea() || IsAffectingArea()`（暴风雪/奉献是 PERSISTENT_AREA_AURA，只看 `IsTargetingArea` 会漏，run393 羊就是被暴风雪打掉的）`|| ChainTarget > 1`（闪电链、正义之锤、复仇者之盾）`||` 名单（活体炸弹、剑刃乱舞、杀戮盛宴、熔岩图腾等间接 AoE）。Playerbots.log 实测每场压住数十到上百次 |
| D 单体按序 | `NexStrategy::AppendTargetExclusions` | DPS 排除三个控制图标目标；坦克只排除**此刻真被控着**的（松掉的归坦克抓）；开怪前连骷髅也排除 |
| E 重新上控 | 与 B 同一动作，战斗中判据加了「不是当前击杀目标 / 不是最后一只」 |
| 编排 | mod-raidtest `AttemptRunner::CcPullGateReady` + 场景键 `PrerequisiteCcWaitSeconds` | 把拉怪目标钉在坦克 `pull target` 当信号；等到「控制图标目标全部带控制光环」或「有**未被控**的怪进战斗」再开怪；开怪目标 = 骷髅 → 未控的怪 → 十字/方块/月亮；坦克 10 秒内没标记视为无计划直接开。**交接文档里「框架一行不用改」是错的**：原流程在传送后第一个 tick 就对全队下拉怪令 |

同时加的框架能力：`raidtest los <map> <x1> <y1> <z1> <x2> <y2> <z2>` 控制台视线探针（只读，按需加载 vmap 瓦片）；
`AttemptStartDelaySeconds`（测试床用它让妖术 45 秒冷却在连续场次间复位）；每场开始清空队伍图标；
控制链门禁下拉怪被拒只接近到仇恨半径外（`kCcApproachDistance = 24`），首次开怪就无视线直接作废并说明；
`BeginPullForAll` 把「已在打同一目标」算作成功（与 `BeginAssistForAll` 一致）。

### 七轮迭代各自撞上的事（别重走）

1. **run393**：准备点 (519,110) 距最近守卫 17 码，在 20 码仇恨半径内，任何走动/转身都拉怪。
2. **run394 / probe-cc-l1…l5**：北侧走廊 x∈[515,527]、y∈[116,121] 对守卫全部**无视线**；拉怪被拒后旧的
   `ApproachPrerequisiteTarget` 带全队走到目标脚下，一路拉进 boss 房间。
3. **run401**：`pack_engaged` 把被羊的那只自己算进去，羊落地同一毫秒开怪；骷髅死后按配置顺序拉了被妖术的。
4. **run402**：`AttackersValue` 把骷髅目标塞进 attackers，坦克一标骷髅治疗就用魔杖射它。
5. **run402 (509,116)**：施法怪朝远离队伍方向后撤 = 朝 boss 退，三场把泰蕾斯特拉拉进来。选点要让怪的后撤方向
   背离 boss；最终用 `raidtest los` 扫 1255 组数据选了守卫西南 (509,62)。
6. **run404**：同一 spawn 跨实例 GUID 相同，上一场的骷髅图标在新实例里指向活怪，DPS 落地 2.5 秒就开火。
7. **run405**：闷棍目标分在怪堆深处，盗贼穿过整组被发现；「羊等闷棍」的计时按 GUID 记首见时刻，跨实例算成上一场。

### 数字（同一测试床 `heroic-nexus-telestra-trash`，每轮 5 场）

| run | 二进制 | 清完 | 零死亡清完 | 备注 |
|---|---|---|---|---|
| 基线（此前 12 场） | 无控制链 | 9/12 | — | 33.4 秒均值 |
| 401 | 门禁 v1 | 0 | 0 | 羊每场落地，但开怪过早 |
| 402/403 | 骷髅延后、准备点 (509,116)/(509,62) | 0 | 0 | 视线/后撤方向/旧图标 |
| 404 | 闷棍先、开场等待 40 秒 | 2/5 | 2/5 | 首次零减员清完，79 秒 |
| 405 | 清图标 | 2/5 | 1/5 | 闷棍目标在怪堆深处 |
| 406 | 闷棍最近优先、计时带实例 | 1/5 | 0/5 | 闷棍首次落地（3/5 场）；门禁超时时骷髅未标，框架/坦克把被控的怪放出来打 |
| **407** | 骷髅按期限必标、兜底不拉带图标的怪、等待 25 秒 | **5/5** | **4/5** | 清怪 69–81 秒；唯一死亡在清完之后（泰蕾斯特拉被拖入，见下） |
| 412 / **413（链式）** | 闷棍绕背后（已退回） | 测试床 2/3；链式第一组零死亡 | 测试床 2/3 | 闷棍 4 场 0 次；链式随后被框架直接拉 boss 作废 |
| **409（完整场景 telestra-n5）** | + 链式准备（近战不追被控怪、boss 跳过门禁） | 清怪 4/5、boss **3 击杀** | 清怪段 4/4 零死亡 | 第 4 场放最后一只羊时 boss 参战，第 5 场开局 boss 已在战斗 |
| 408 | + 间接 AoE 名单先于 IsPositive（剑刃乱舞） | 4/5 | 4/5 | 剑刃乱舞在控制期间 0 次（407 里每场 1 次）；2 场清完后恢复期被泰蕾斯特拉缠住到超时，第 4 场开局 0.5 秒她就在对队伍读条（日志显示是新实例 7，原因未查清），2 死 |

run407 每场击杀顺序都符合设计：骷髅（治疗 g64）→ 放出十字（闷棍/Ascendant）→ 方块（妖术/Steward）→ 月亮（羊/治疗 g65）
最后；闷棍 3/5 场落地并撑到被放出（30–40 秒），羊 5/5 落地且全程不被自家 AoE 打掉（cc_watch 连续 50 格），
妖术 5/5 放出但常在开怪后 2–3 秒被打掉（详见下条）。Playerbots.log（`LogInGroupOnly = 0`）里乘子每场压住
暴风雪/烈焰风暴/活体炸弹/闪电链/刀扇/奉献/复仇者之盾/正义之锤合计数十到上百次。

### 还没解决的（接手从这里继续）

1. **清完后被 boss 拖入**（run407 a1 萨满死于泰蕾斯特拉、a4 恢复期超时；run408 a2/a3 同样恢复期被她缠住 190 秒，a4 开局 0.5 秒她已在对队伍读条，日志显示是新实例，原因未查清）：**这是当前测试床与链式场景的头号问题**。已写好（未编译）「近战/坦克不追被放出的被控怪，由远程先打破、怪自己跑到队伍」的排除规则；最后一只是被羊的治疗，
   羊状态下乱走，队伍追杀它时进了 boss 的 22 码仇恨半径。测试床准备点 (509,62) 距 boss 30.6 码本身够，
   是**追击路线**的问题。可选：放出羊之前坦克把它拉回（真人会用远程拉），或把「放出月亮」改成先由坦克
   用远程技能打破羊、等它跑到坦克身上再让 DPS 动手。
2. **妖术在开怪后 2–3 秒就掉**（cc_watch 3–4 格）：run407 里方块目标是近战 Steward，开怪后它就在坦克身边挨顺劈/
   奉献余波？还是被坦克的正义防御/圣印命中——`raidtest_events` 的 damage 行没有 spell_id，要开 Auras.log 才能定位。
   之前台账里「妖术早掉根因未定位」这条仍然成立。
3. ~~剑刃乱舞每场开怪 15 秒左右都放出来了~~ 已修并验证（run408 控制期间 0 次）：名单先于 `IsPositive()` 判断。
4. **清怪用时 69–81 秒**（基线 33 秒）：闷棍走位约 9 秒 + 羊/妖术读条 + 单体按序，是设计本身的代价；
   后续如果要压时间，可从「羊/妖术与闷棍同时进行、只是羊晚 1 秒出手」入手，不要回到 AoE。
5. 妖术的 `Spell not has cooldown`（45 秒冷却）在连续 attempt 之间是测试床伪影，用 `AttemptStartDelaySeconds = 40` 压掉了；
   完整场景 `heroic-nexus-telestra-n5` 的清怪点仍是 (519,110)，**它在仇恨半径内，套用控制链前必须换成 (509,62) 并加
   `PrerequisiteCcWaitSeconds`**。奥莫洛克那组要另外勘测（守卫是元素，只能致盲；且它们巡逻）。
6. 施法怪的沉默（Arcane Torrent 47779、Spellbreaker 47780/47781）是治疗/施法者减员的直接机制：run406 a2 治疗 22 秒内
   只放出一个法术、坦克没奶死。控制链把这两类怪控住就是在解决它；被放出来打的那只仍会沉默近身的施法者。
