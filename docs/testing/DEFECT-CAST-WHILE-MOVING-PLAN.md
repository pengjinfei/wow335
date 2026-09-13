# 修改计划：bot 为施法让出「走位型」移动（共享层）

> 状态：**已实现、已编译（两次，573–577 TU）、已验证行为正确；对阿努巴拉克无可观测收益**（结果见 §10）。
> 代码在 mod-playerbots 工作区 9 个文件，**未提交**。
> 对应缺陷：[DEFECT-CAST-WHILE-MOVING.md](DEFECT-CAST-WHILE-MOVING.md)。
> 起草于 2026-09-12 深夜。所有"行号"以 mod-playerbots `codex/an-trash-cc-shackle`
> 与 core `codex/an-formation-despawn-crash` 当前工作区为准。
>
> **用户决定（2026-09-12）**：按最合适的改法做，不为编译成本牺牲合理性。因此 §3.1 的枚举放在
> `LastMovementValue.h` 里 `MovementPriority` 旁边（不另开头文件），§3.4 的两个判定函数做成
> `PlayerbotAI` 成员（`IsCastBlockedByMovement` / `TryYieldMovementForCast`），编译扇出按 §7 的
> 574 TU 计。AN 两个闪避已表态 SURVIVAL。

## 0. 一句话

给每次移动打上「意图」标签（走位 / 战术 / 保命），`CastSpell` 在 bot 移动时只对**走位型**移动
`Clear + StopMoving` 后继续施法，其余移动维持今天的行为（放弃施法）。默认标签是「战术」，
所以 460 处没写优先级的副本机制走位**一行不改也不会被施法打断**。

## 1. 调查结论——先纠正缺陷文档里的三处偏差

这些都会改变落点，务必先看。

### 1.1 `:3735` 那段是死代码，真正拒绝施法的是 core 的 `Spell::prepare`

`Spell::GetCastTime()` 返回 `m_casttime`，而 core 在构造函数里写死 `m_casttime = 0`
（`Spell.cpp:669`，注释原话 "setup to correct value in Spell::prepare, must not be used before"），
`prepare()` 里才算出来（`:3557`）。第一处重载（治疗走的那条）的判断在 `prepare()` **之前**，
所以 `bot->isMoving() && spell->GetCastTime()` 永远为假——它一次也没执行过。

治疗真正失败在 `Spell::prepare` `:3564-3573`：

```cpp
if ((m_spellInfo->IsChanneled() || m_casttime) && m_caster->IsPlayer() && m_caster->isMoving()
    && m_spellInfo->InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT && !IsTriggered())
{
    if (m_casttime || !m_spellInfo->IsActionAllowedChannel())
        return SPELL_FAILED_MOVING;     // -> 模块 result != SPELL_CAST_OK -> return false -> FAILED
}
```

三个推论：

1. **引导法术同样被拒**（苦修、心灵鞭笞、希望圣歌、奥术飞弹、暴风雪……），只要没有
   `SPELL_ATTR5_ALLOW_ACTION_DURING_CHANNEL`。缺陷文档把苦修算成"瞬发"是错的，run456 苦修 43 次 FAILED
   大概率同源。修复的触发条件必须**镜像 core 这个条件**，而不是只看 `GetCastTime()`。
2. 修复必须在 `prepare()` **之前**停步，原因见 1.3。
3. 第二处重载（地面目标）的判断在 `prepare()` **之后**，`m_casttime` 已有值，是活的；但它在 `prepare()`
   之后 `delete spell`——`prepare()` 一开始就把 Spell 挂进了 `SpellEvent`（`Spell.cpp:3502`），
   事件析构时会再 `delete`（`:8200-8208`）。**这是一个潜在的双重释放**，只在"移动中放地面目标读条法术"时触发。
   本计划把这块判断挪到 `prepare()` 之前，顺手消掉。（未复现，按源码判断。）

### 1.2 `MovementPriority` 是"锁序"，不是"重要度"，不能拿来判断该不该让路

`LastMovementValue.h:17-25` 的注释就一句：*High priority movement can override the previous low priority one*。
它唯一的消费者是 `IsWaitingForLastMove(priority)`（`MovementActions.cpp:930`）：上一次移动的
`msTime + lastdelayTime` 未到期时，**优先级不高于它的新移动被拒绝**。仅此而已。

实际用法把"该不该让路"两头都占了：

| 移动 | 优先级 | 该为施法让路吗 |
|---|---|---|
| `combat formation move`（`FleePosition`，牧师的主要移动来源） | **COMBAT** | 该让 |
| `reach spell` / `reach party member to heal`（`ReachCombatTo`） | **COMBAT** | 该让 |
| `anub'arak dodge impale` / `dodge pound`（走 `Move()`，无参） | **NORMAL（默认）** | 不该让 |
| Dungeon/Raid 下 519 处移动调用 | **460 处默认 NORMAL**，59 处显式 | 绝大多数是机制，不该让 |
| `follow`（`MoveFollow`，根本不写 LastMovement） | 无 | 该让 |

所以缺陷文档"方向 3：按 MovementPriority 判定"不可行；改优先级语义会同时动 519 处调用的锁行为。
本计划**不动优先级**，另立一个正交的标签。

顺带发现（本计划不修，单独记）：AN 的两个闪避用默认 NORMAL，会被在飞行中的 COMBAT 阵型移动的锁拒掉
（`IsWaitingForLastMove`）。这可能是 run456 `dodge impale` 18 次 PREREQ 只有 4 次 OK 的原因之一，
应该单独提到 FORCED，但和本改动分开验，免得混淆归因。

### 1.3 引擎与 core 的既有行为决定了"怎么停"

- **读条期间引擎不跑任何动作**：`PlayerbotAI::UpdateAIInternal :278-360`，当前法术处于
  `SPELL_STATE_PREPARING` 时直接 `YieldThread` 返回。所以停步施法后，模块自己不会再发新移动把读条打掉。
  副作用：读条期间也**不会评估闪避触发器**（见 §5 二阶效应）。
- **同一 tick 里 `Spell::update` 先于 `MotionMaster::UpdateMotion`**（`Unit::Update` 顺序），
  `Spell::update :4409-4418` 看到 `isMoving()` 就 `cancel`。所以停步必须发生在**我们自己的 AI tick 里、
  `prepare()` 之前**；指望 core 生成器"看到在施法就停"来不及。
- `Unit::StopMoving()`（`Unit.cpp:13048`）→ `MoveSplineInit::Stop()` **同步**清掉
  `MOVEMENTFLAG_FORWARD|BACKWARD|SPLINE_ENABLED`（`MoveSplineInit.cpp:156`）并把 spline 置 Done，
  `isMoving()` 立刻为假。可靠。
- 三种生成器对"正在施法"的态度不同：
  - `PointMovementGenerator`（模块所有 `MoveTo` 都走它）：`DoUpdate :119` 见 `IsMovementPreventedByCasting()`
    就 `StopMoving` 并保活；spline 已 Done 且 `i_recalculateSpeed=false` 时**不会重新起步**，读条结束后自然过期。
    所以对点移动，`StopMoving()` 就够，但为确定性仍先 `MotionMaster::Clear()`（模块 `DoMovePoint` 自己也是先 Clear）。
  - `FollowMovementGenerator<Player>`：`TargetedMovementGenerator.cpp:592` 只对**生物**检查施法；玩家 bot
    停步后下一次 `PositionOkay()` 不满足就重发 spline → 读条被打掉。**跟随必须 `Clear()` 掉生成器**，
    读条完由 `FollowAction` 重新 `MoveFollow`（`Follow()` 里已有"当前不是 FOLLOW 就 Clear 再 MoveFollow"的逻辑）。
  - `ChaseMovementGenerator<Player>`：同上不检查施法。本计划**不让 chase 让路**（近战追击，维持今天行为）。
- 模块现有政策：`Follow()`（`MovementActions.cpp:1275`）和 `ChaseTo()` 都先 `bot->CastStop()`——
  "移动赢过施法"是既有约定；本计划只在"走位型移动"这一类上把方向反过来，其余不碰。
- 上游 `origin/master` 的 `src/Bot/PlayerbotAI.cpp:3738/3951` 与本地完全一致，是上游活着的缺陷，修好后值得回推。

## 2. 目标 / 非目标

**目标**

- 有读条/受移动打断的引导法术，在 bot 因**走位型**移动而处于移动状态时，能停下来放出去。
- 机制闪避、逃跑、追击、击退、冲锋等**一律保持今天的行为**。
- 每次"让路 / 拒绝"都有一条可统计的 debug 日志，验证靠数数不靠感觉。

**非目标（本轮不做，§6 记为扩展）**

- 读条中途为保命移动而主动打断读条（二阶效应，要动引擎的 preparing 分支）。
- 近战 chase 让路。
- 改任何副本策略、任何 `MovementPriority`。
- AN 闪避优先级提升（单独一条改动）。

## 3. 设计

### 3.1 概念：移动意图 `MovementIntent`

```cpp
// src/Ai/Base/Value/LastMovementValue.h，紧挨 MovementPriority（最终落点；见文首用户决定）
enum class MovementIntent : uint8
{
    TACTICAL,     // 默认。战术走位：逃跑、拉脱接触、副本机制、任何没表态的动作。既不为施法让路，也不打断施法。
    POSITIONING,  // 走位：阵型、够距离、跟随、随机走动、碰撞挪位。为施法让路。
    SURVIVAL,     // 保命：躲地刺、出锥。第一阶段行为同 TACTICAL；第二阶段可打断读条（§6）。
};
```

三档而不是一个 bool，是为了把"该让路"（POSITIONING）和"该打断读条"（SURVIVAL）用同一个标签表达，
第二阶段不用再发明一套。**默认 TACTICAL** 是本设计的安全阀：不表态的 460 处副本移动行为不变。

### 3.2 数据：`LastMovement` 记下意图和发起者

`LastMovementValue.h` 增两个字段（`clear()`、拷贝构造、`operator=` 同步）：

```cpp
MovementIntent intent = MovementIntent::TACTICAL;
std::string issuer;      // 发起动作名，仅用于日志归因（例 "combat formation move"）
```

### 3.3 设置点：`MovementAction` 一个虚函数 + 一个统一记录函数

```cpp
// MovementActions.h
virtual MovementIntent GetMovementIntent() const { return MovementIntent::TACTICAL; }
void RecordLastMovement(uint32 mapId, float x, float y, float z, float delay, MovementPriority priority);
```

`RecordLastMovement` 替换 `MoveTo` 三个分支（`:228/:251/:280`）和 `JumpTo`（`:96`）里的四处
`AI_VALUE(LastMovement&, "last movement").Set(...)`，在 `Set` 之后写 `intent = GetMovementIntent()`、
`issuer = getName()`。四处合一，以后加字段只改一处。

**第一批表态为 POSITIONING 的动作（都在共享层，逐个说明理由）：**

| 动作类 | 覆盖 | 理由 |
|---|---|---|
| `CombatFormationMoveAction` | 含派生 `TankFaceAction`、`SetBehindTargetAction` | 牧师最大移动来源（run456 168 次）；纯阵型 |
| `ReachTargetAction` | `reach melee/spell/party member to heal/to resurrect`、`ReachPullAction` | "去够距离"途中有别的目标能治就该停；人也这么打 |
| `FollowAction` | 含 `FleeToGroupLeaderAction`（仅覆盖它走 `MoveTo` 的远距/尸体分支；`MoveFollow` 分支由 3.4 按生成器类型识别） | 团灭后补 buff 补不上、跟随中上不了坐骑都是它 |
| `MoveOutOfCollisionAction` | — | 挪半步而已 |
| `MoveRandomAction` | — | 非战斗闲逛 |

**明确保持 TACTICAL（不让路）的：** `FleeAction`/`FleeWithPetAction`（模块指定的保命动作）、
`AvoidAoeAction`、`MoveOutOfEnemyContactAction`、`RunAwayAction`、所有 Dungeon/Raid 动作、
`AttackAction` 系（chase）。
`FleeToGroupLeaderAction` 继承 `FollowAction` 会连带成 POSITIONING，它的语义是"逃到队长身边"，
偏保命——**在它上面显式覆写回 TACTICAL**。

AN 的 `AnubarakDodgeImpaleAction` / `DodgePoundAction` 可以顺手表态 SURVIVAL：第一阶段零行为差异，
只让日志能区分"被保命移动拒绝"和"被战术移动拒绝"。放不放进本次改动由你定，建议放（不影响归因）。

### 3.4 判定点：两个 `PlayerbotAI` 成员，供两处 `CastSpell` 调用

最终落点：`PlayerbotAI` 成员函数（`PlayerbotAI.h` 声明、`PlayerbotAI.cpp` 实现，紧挨 `RequestSpellInterrupt`）。
初稿为省 574 TU 扇出想放自由函数，用户否决（合理性优先）：

```cpp
// 法术在移动中会被 core prepare 拒绝吗？完全镜像 Spell::prepare :3564-3573
bool PlayerbotAI::IsCastBlockedByMovement(SpellInfo const* spellInfo) const;
//   !(InterruptFlags & SPELL_INTERRUPT_FLAG_MOVEMENT) -> false
//   CalcCastTime(bot) > 0                              -> true
//   IsChanneled() && !IsActionAllowedChannel()         -> true
//   否则 false

// 当前移动能为施法让路就让，返回让路后是否已不再移动
bool PlayerbotAI::TryYieldMovementForCast(SpellInfo const* spellInfo);
```

`TryYieldMovementForCast` 的判定顺序：

1. `bot->GetVehicle()` → 拒绝（载具另有施法路径）。
2. `type = GetCurrentMovementGeneratorType()`：
   - `FOLLOW_MOTION_TYPE` → 让路（意图视作 POSITIONING，issuer 记 "follow"）。
   - `POINT_MOTION_TYPE` 且 `!HasUnitState(UNIT_STATE_CHARGING)` → 看 `LastMovement.intent == POSITIONING`。
   - 其余（CHASE、击退/坠落造成的 `isMoving`、IDLE 但有残留 flag、FLIGHT…）→ 拒绝。
3. 让路动作：`GetMotionMaster()->Clear()`；`bot->StopMoving()`；`lastMovement.lastdelayTime = 0`
   （释放锁：这次移动已不在飞行中，别让它的 COMBAT 锁再拒后面的 NORMAL 闪避 5 秒）。
4. 返回 `!bot->isMoving()`。
5. 无论让路还是拒绝，都打一条 debug 日志（门控与 `Engine::LogAction` 一致：
   `!logInGroupOnly || (group && HasGameClientMaster())`）：

```
cast-vs-move bot=<name> spell=<id> (<name>) generator=<type> issuer=<action> intent=<T|P|S> result=yield|refuse
```

### 3.5 两处 `CastSpell` 的改法

**第一处 `CastSpell(uint32, Unit*, Item*)`（`:3735`）**——把死块换成活块，位置不变（`prepare()` 之前）：

```cpp
if (bot->isMoving() && IsCastBlockedByMovement(bot, spellInfo) && !TryYieldMovementForCast(this, spellInfo))
{
    SetNextCheckDelay(sPlayerbotAIConfig.reactDelay);
    delete spell;                      // 尚未 prepare，没有 SpellEvent，直接删安全
    return false;
}
```

**第二处 `CastSpell(uint32, float, float, float, Item*)`（`:3948`）**——整块**挪到 `spell->prepare(&targets)` 之前**，
内容同上（去掉 `spell->cancel()`）。这同时消掉 1.1 第 3 点的双重释放。

不动 `Follow()`/`ChaseTo()` 里的 `CastStop()`，不动引擎。

### 3.6 为什么不选缺陷文档里的方向 1/2

- 方向 1（治疗动作自己停）：只救治疗，救不了输出法系（上一轮结论"瓶颈转为输出"），也救不了 buff/坐骑。
- 方向 2（给 `CastSpell` 加"允许停步"参数）：调用方是法术动作，它不知道**当前是谁在移动**；该表态的是移动的发起者，不是法术。
- 本设计把表态权放在移动发起者（动作类）上，法术侧只问一句"现在这个移动让不让"。

## 4. 场景矩阵

| # | 场景 | 现在 | 改后 | 依据 |
|---|---|---|---|---|
| 1 | 治疗被阵型移动推着走，需要 2.5s 强效治疗 | FAILED，永不停 | Clear+Stop，施法 | 3.3/3.4 |
| 2 | 治疗正在"够距离"去治 A，B 在范围内掉血 | FAILED | 停下治 B，下 tick 再去够 A | 人也这样；看日志 issuer 是否出现来回抖动 |
| 3 | 正在躲地刺 / 出践踏锥 | FAILED | **FAILED（不变）** | 默认 TACTICAL/SURVIVAL 不让路 |
| 4 | 躲地刺**期间**被 COMBAT 阵型锁拒绝 | 存在 | 略缓解（让路时释放锁） | 3.4 第 3 步；根治要提 AN 闪避优先级（单独） |
| 5 | 读条中地刺冒出来 | 不会发生（从不读条） | **吃地刺**（引擎读条期间不评估触发器） | §5 二阶效应，验收项 2 专门量它 |
| 6 | 非战斗跟随中补 buff / 复活 / 上坐骑 | 跟随 CastStop，永远放不出 | Clear 跟随 → 施法 → FollowAction 重新跟 | 1.3 跟随生成器分析 |
| 7 | 主人一直在跑，bot 停下来 buff | — | bot 落后 2–3 秒再追 | 可接受；若不接受可把跟随排除出让路 |
| 8 | 近战 chase 中想放有读条的治疗（增强萨、惩戒骑） | FAILED | **FAILED（不变）** | chase 生成器不会为施法停 |
| 9 | 被击退 / 坠落中（`isMoving` 因 FALLING） | FAILED | FAILED（不变） | 生成器不是 POINT/FOLLOW |
| 10 | 冲锋（POINT + `UNIT_STATE_CHARGING`） | — | 拒绝 | 显式排除 |
| 11 | 载具内 | 走 `CastVehicleSpell` | 不变 | 显式排除 |
| 12 | 定身/眩晕/变形 | `CanMove` 假，不会有点移动 | 不变 | — |
| 13 | 引导法术（苦修、心灵鞭笞、圣歌） | 移动时 prepare 拒绝 | 走位型移动时停下引导 | 1.1 镜像 core 条件 |
| 14 | 有读条但没有 MOVEMENT 打断标志的法术 | core 不拒（模块死块不生效） | 不停步直接施法（同今天） | `IsCastBlockedByMovement` 返回 false |
| 15 | 停下后 prepare 仍失败（视线/距离） | — | 白停一次，下 tick 动作重新发移动 | `IsDuplicateMove` 同目的地 5 秒内不重发；阵型/够距离目的地每次重算，影响小 |
| 16 | `stay` 策略 | 不移动 | 不变 | — |
| 17 | 随机 bot（`MaxRandomBots=0`，本机没有） | — | 若开启，野外跟随/闲逛也会为施法停 | 属于预期行为，但回归面扩大，记录在案 |

## 5. 已知二阶效应（不是回归，是新暴露的问题）

bot 一旦真的读条，读条那 1.5–2.5 秒里引擎不评估任何触发器（`UpdateAIInternal` preparing 分支直接 yield），
所以**不会为躲地刺而取消读条**。真人会取消。预期 `dodge impale` 命中次数上升、承伤上升。
验收项 2 就是量这个。这不该阻止本改动落地——37% 的 GCD 利用率是更大的洞——但要在结果里单列。

对应的第二阶段（§6.1）已经有现成钩子：`PlayerbotAI::RequestSpellInterrupt()` + preparing 分支里的
`spellInterruptRequested` 处理。

## 6. 扩展路线（本轮不做，但设计给它留了位）

1. **SURVIVAL 移动打断读条。** 在 preparing 分支里跑一次受限的引擎评估：只允许
   `GetMovementIntent()==SURVIVAL` 的动作参与；命中就 `RequestSpellInterrupt()`，下 tick 正常执行闪避。
   标签已经在了，改动集中在 `UpdateAIInternal` 和 `Engine`。
2. **chase 让路。** 若近战混合职业的读条治疗也重要，`TryYieldMovementForCast` 对 CHASE 做
   `Clear()`，读条完由 `AttackAction`/`reach melee` 重新追。单独验近战 DPS 不掉。
3. **副本策略按 boss 覆写。** 某 boss 要求"移动优先于一切施法"（例如全程跑位阶段），可以在该副本的
   `Multiplier` 里把施法相关性压到 0——现有机制，不需要新开关。反过来"这段走位可以让路"就是把动作的
   `GetMovementIntent()` 覆写成 POSITIONING。
4. **配置开关 `AiPlayerbot.YieldMovementToCast`。** 需要改 `PlayerbotAIConfig.h`（574 TU 扇出），本轮不加；
   A/B 用 `git revert` + 182 TU 重编（≈3 分钟）代替。
5. **AN 闪避优先级提到 FORCED**（1.2 顺带发现）。独立小改动，独立验。
6. **上游回推。** 上游同代码；本设计不依赖本地任何私有改动，可整体成 PR。

## 7. 改动清单与编译成本

| 文件 | 改动 | 说明 |
|---|---|---|
| `src/Ai/Base/Value/LastMovementValue.h/.cpp` | +19 行 | `MovementIntent` 枚举 + 两个字段，三处同步 |
| `src/Ai/Base/Actions/MovementActions.h` | +6 行 | 虚函数、`RecordLastMovement`、五个类的覆写 |
| `src/Ai/Base/Actions/MovementActions.cpp` | +70 / −8 行 | 四处 Set 合一；两个自由函数实现 + 日志 |
| `src/Ai/Base/Actions/ReachTargetActions.h`、`FollowActions.h` | +4 行 | 覆写；`FleeToGroupLeaderAction` 覆写回 TACTICAL |
| `src/Bot/PlayerbotAI.h/.cpp` | +7 / +77 −14 行 | 两个成员函数；两处 `CastSpell` |
| `src/Ai/Dungeon/AN/ANActions.h` | +2 行 | 两个闪避表态 SURVIVAL（已做） |

**编译扇出（用 `var/build/obj` 的 `.d` 依赖文件数出来的，不是估的）：**

| 被改头文件 | 依赖它的 TU |
|---|---|
| `PlayerbotAI.h` | **574**（本计划刻意不碰） |
| `LastMovementValue.h` | **182** |
| `MovementActions.h` | 172（是 182 的子集） |
| `ReachTargetActions.h` | 31 |
| `FollowActions.h` | 17 |

最终改了 `PlayerbotAI.h`，所以是一次 **≈574 个 TU 重编 + 链接 worldserver**（几乎整个 mod-playerbots，
core 与 mod-raidtest 不受影响），Release、`nice -n 10 -j4`，按每 TU 3–4 秒线性外推约 8–12 分钟。
不是全量，但比往常大得多，**动手前要你点头**。之后每次微调若只动 `.cpp`，回到 1–2 分钟。

## 8. 验证计划

### 8.1 编译前一次开齐的诊断开关

`env/dist/etc/modules/playerbots.conf`：`AiPlayerbot.LogInGroupOnly = 0`（新日志和逐动作 OK/FAILED 都靠它）。
用完改回 `1`。日志在 `azerothcore-wotlk/Playerbots.log`。

### 8.2 统计脚本（在缺陷文档脚本上加两段）

```bash
cd azerothcore-wotlk && python3 - <<'EOF'
import re, collections
act=re.compile(r"(\w+) A:(.+?) - (OK|FAILED|IMPOSSIBLE|USELESS|PREREQ)")
yld=re.compile(r"cast-vs-move bot=(\w+) spell=(\d+) \((.+?)\) generator=(\w+) issuer=(.*?) intent=(\w) result=(\w+)")
a=collections.defaultdict(collections.Counter); y=collections.Counter(); by_issuer=collections.Counter()
for line in open('Playerbots.log',errors='ignore'):
    m=act.search(line)
    if m: a[(m.group(1),m.group(2).strip())][m.group(3)]+=1; continue
    m=yld.search(line)
    if m: y[(m.group(1),m.group(3),m.group(7))]+=1; by_issuer[(m.group(5),m.group(6),m.group(7))]+=1
for k in ["greater heal on party","flash heal on party","penance on party","power word: shield on party"]:
    for (bot,name),c in a.items():
        if name==k: print(bot,k,dict(c))
print("--- yield/refuse by spell"); [print(k,v) for k,v in sorted(y.items(), key=lambda kv:-kv[1])[:20]]
print("--- by issuer"); [print(k,v) for k,v in sorted(by_issuer.items(), key=lambda kv:-kv[1])[:20]]
EOF
```

`by issuer` 那张表回答"到底是谁在推着治疗走"——这是本轮**第一次**能直接量到的东西
（`combat formation move` 永远返回 false，从 OK/FAILED 里看不出它动没动）。

### 8.3 验收口径（沿用缺陷文档三条，补样本量）

1. **`heroic-an-anubarak-n5` 5 场 ×2 轮**（同一二进制跑两轮，防 0/5、2/2、1/5 那种波动被单轮读歪）：
   - 主指标：`greater heal / flash heal / penance on party` 的 OK 次数与 FAILED 次数（基线 0/3/8 OK，单场 258 秒）。
   - 次指标：`cast-vs-move ... result=yield` 与 `refuse` 的比例；`refuse` 里 `issuer` 若出现走位型动作名，是分类漏了。
   - 击杀率只作参考，不作判据（约束 4）。
2. **闪避没被破坏**：`dodge impale` 命中次数与承伤对比 run449（8 次 / 46,759）。预期**略升**（§5），
   升多少决定第二阶段的优先级；若升到接近无闪避水平（79 次 / 439,741）则本改动要配合 §6.1 一起上。
3. **旧 boss 回归**（共享层，回归面是全部）：优先治疗压力大、且有走位的——
   `heroic-nexus-keristrasza-disc-n5`（run422/426 基线 117–134 秒零死亡）、
   `heroic-nexus-anomalus-n5`、`heroic-uk-skarvald-dalronn-n5`（5/5 零死亡）。各 3 场，看零死亡是否保持、时长是否变短。
4. **非战斗抽查**：任一场景准备阶段看 `follow` 后能否补齐团队 buff（观察 `power word: fortitude on party` 等由 IMPOSSIBLE/FAILED 变 OK）。

### 8.4 回退

改动全部在 mod-playerbots 一个提交里，`git revert` + 182 TU 重编即可；不涉及 core、mod-raidtest、数据库、配置。

## 9. 风险清单

| 风险 | 概率 | 缓解 |
|---|---|---|
| 分类漏了某个走位型基础动作，它继续挡施法 | 中 | 日志 `refuse` + `issuer` 一眼看出，补一行覆写 |
| 分类错把某个保命动作标成走位 | 低（第一批只 5 类，都读过实现） | 同上，看 `yield` 的 issuer |
| 够距离↔施法来回抖动 | 低 | issuer 表里 `reach *` 的 yield 次数异常高即是信号；对策：`ReachTargetAction` 改回 TACTICAL |
| 跟随让路造成野外 bot 掉队 | 本机无随机 bot | 若启用随机 bot 再评估；可把 FOLLOW 分支单独关掉 |
| 读条期间吃机制（二阶效应） | 高 | 已预告，验收项 2 量化，§6.1 是后手 |
| 182 TU 编译期间机器变慢 | 确定 | `nice -n 10 -j4`，期间不跑别的重活 |

## 10. 实测结果（2026-09-13，run 457 / 459）

- 第一次编译的二进制（run 457）暴露了计划漏掉的**第三道闸**：`CanCastSpell` 在 `isPossible()` 阶段就按
  `(读条 || 自动射击) && isMoving()` 判 IMPOSSIBLE，`CastSpell` 的让路根本不可达。已补：`CanCastSpell` 两处闸改为
  `isMoving() && !CanYieldMovementForCast()`；判定抽成无副作用的 `JudgeMovementForCast()`（`.cpp` 匿名命名空间），
  `TryYieldMovementForCast` 只做副作用；`IsCastBlockedByMovement` 加入自动射击（镜像 `Spell::CheckCast`）。
- run 459（完整修复）1346 秒战斗里 `result=yield` **0 次**，`refuse` 2 次（苦修在逃跑中，正确）。
  全队"读条时在移动"拦截 70 次，45 次在穿刺触发期间，其余是战术移动——全是设计上不该让路的场景。
- 结论：机制正确、无误让路；但在本 boss 上没有可观测收益，牧师瓶颈在 GCD 争用/苦修引导，详见阿努巴拉克记录第四轮。
  §5 预告的二阶效应（读条期间吃穿刺）因为读条本来就没多起来，也没显现。
- 顺带发现：`raidtest_events.damage.spell_id` 全为 0，验收项 2 的"穿刺承伤"没法按法术切分；只能看 `dodge impale` OK 次数
  （457：157 次，459：133 次，战斗总时长 1436 vs 1346 秒）。
- 未解：牧师所有治疗（含瞬发）的 FAILED 在 459 比 457 高 3–5 倍，与本改动无关（瞬发不经过任何移动闸），
  说明 FAILED 来自 prepare 的其它拒绝码。**下一步先放开 `CastSpell` 里注释掉的 prepare 结果码日志。**

## 11. run 460 补记（2026-09-13 上午）

按 §10 "下一步"放开了 `CastSpell` 两处 `prepare()` 失败的结果码日志（`Spell prepare failed. ... result: N`，
门控同 `CanCastSpell`）。5 场里牧师 365 次 FAILED 全部是 `SPELL_FAILED_NO_POWER`——**缺陷文档的原始现象
（读条治疗放不出去）根因是牧师 150–210 秒耗尽法力**，与移动无关。本计划的改动保留（行为正确、上游同缺口），
后续方向转到夹具药水 / 牧师策略盾频率 / `ConserveManaStrategy` 被注释的乘子，见阿努巴拉克记录。

方法论教训（写进记忆）：引擎日志里 IMPOSSIBLE 是 `isPossible()` 为假，不是"触发器没触发"；FAILED 在补结果码日志之前
不可归因。两处误读叠加，让一份"已量化"的缺陷文档指向了错误的根因。

## 12. 顺带的共享层改动：`MovementAction::IsSameFloorDestination`（同层守卫，2026-09-13 下午）

**现象**：阿努巴拉克 run 457–470 共 8 人次"活着掉出平台"，轨迹完全一致——x/y 几乎不动、z 以 **4.5 码/秒匀速**下降
（= MOVE_RUN_BACK 后退跑速度），掉落前没有任何承伤，两例前 1–5 秒有 `flee - OK`。机制：远程站在西沿（x≈526，导航网格尽头）
被小怪贴身 → `FleeAction` → `MoveAway(target, 5, backwards=true)` → `CheckCollisionAndGetValidCoords` 用 Detour 射线取终点 z，
那里平台层没有网格，吸附到平台下方的地形（z≈0）→ `MoveTo(exact)` 直线 spline 倒着走进深渊。

**改动**（`MovementActions.cpp/.h`）：`MoveTo` 的两个分支（exact 用调用方 z、path 用 `SearchForBestPath` 的 modifiedZ）
在发出移动前调用 `IsSameFloorDestination(x, y, z)`：二维距离 < 30 码且 |Δz| > max(6, 0.8×dist2d) 的目标视为"另一层地面"，
拒绝并记 `floor-guard ...` 日志（门控同引擎日志）。飞行/游泳、以及 ≥30 码的长距离移动不受影响（那些本来就允许换层）。

**实测**：run 471 前三场守卫命中 10 次，全部是牧师的 `flee` 目标点 (x≈520–524, z=0)，即本会掉落 10 次；同期活着掉落 0 人次。

**回归面**：所有走 `MoveTo` 的短距离移动。0.8 的坡度阈值相当于 39°：普通楼梯/坡道（UK、魔枢的坡 ≤ 20°）不受影响，
45° 的螺旋楼梯 10 码内的目标会被拒——回归旧 boss 时若出现 bot 在楼梯口不动，先看 `floor-guard` 日志。
