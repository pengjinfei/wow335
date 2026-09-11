# 清怪控制链：正确的开怪流程（设计，**未实现**）

更新：2026-09-11。**这是下一步要做的事，也是对本项目此前三轮清怪战术尝试的方向性更正。**

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
