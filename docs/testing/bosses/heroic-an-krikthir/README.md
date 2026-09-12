# 英雄艾卓-尼鲁布 / 门卫克里克希尔（28684，map 601）

## 接手摘要

- 更新：2026-09-12 傍晚。**框架阻断已全部扫清，首轮基线 0/5 —— 卡在清怪段，boss 一次都没开上。**
- 已完成：上游 AC 崩溃已修；`ResetInstance` 改三趟后收敛（10/10 干净）；boss 悬垂 GUID 已按 entry 重寻址。
- 唯一下一步：**门厅的两组守望者（6 只）会在 3–5 秒内一起进战斗**，队伍五场只杀掉 2 只就倒下。
  这正是魔枢用清怪控制链解决过的同一类问题——`wotlk-an` 策略尚未继承 `TrashCcPullStrategy`。
- 阻塞：清怪打不过（战斗问题，不是框架问题）。另有一个次要框架问题见「仍未处理」。

## 场景（完整遭遇战，范围未改小）

| 项 | 值 |
|---|---|
| 场景 | `heroic-an-krikthir-n5` |
| map / boss | 601 / 28684（英雄 entry 31612） |
| 前置 | 守望者三组共 9 只：guid 12758–12766 |
| 准备点 / 开怪点 | (528, 690, 775.5) / (529.6, 656, 776.8) |
| TimeoutSeconds / PrerequisiteTimeoutSeconds | 420 / 200 |

这 9 只是 boss 脚本的一部分、不是路怪：实例脚本把它们的 evade 与死亡都接到 boss
（`OnCreatureEvade` → `krikthir->EnterEvadeMode`；`OnUnitDeath` → `ACTION_MINION_DIED` 触发补招），
boss 又在第一只随从进战斗后 60 秒/120 秒各派一批，**英雄 200 秒**时 `SetInCombatWithZone` 亲自下场
（`PrerequisiteTimeoutSeconds = 200` 就是对齐这个硬时限）。

编队表：三个守望者各带 2 只随从（leader 12758/12759/12760，`groupAI = 7`）；
**boss 本人不在任何编队里**（查过 `creature_formations`）。

## 本轮撞上的三层问题

### 1. 上游 AzerothCore 崩溃（已修，已验证）

run 424 首次冒烟即 **SIGSEGV**。栈：

```
AttemptRunner::ResetInstance → BossAI::_EnterEvadeMode(克里克希尔)
  → instance_azjol_nerub::OnCreatureEvade → CreatureGroup::DespawnFormation  ← 崩
```

`CreatureGroup::DespawnFormation` 用 range-for 遍历 `m_members`（std::map），而
`DespawnOrUnsummon(0ms, …)` 会同步走到
`ForcedDespawn → RemoveCorpse → Map::AddObjectToRemoveList → WorldObject::CleanupsBeforeDelete
→ Creature::RemoveFromWorld → FormationMgr::RemoveCreatureFromGroup → m_members.erase(member)`，
**释放迭代器正踩着的红黑树节点**；最后一个成员被移除时还会 `delete group`（即 `delete this`）。

指令级证据：崩溃 PC = `DespawnFormation+88` = `ldr x9, [x9]`，正是 `__tree_next` 的左下降；
故障地址 `0x f8` 是读到已释放节点的野值。

**这不是本项目特有**：正常玩家跑出门厅让克里克希尔 evade 走的是同一条路。
修复：遍历前先把成员表快照到 `std::vector`（`DespawnFormation` 与 `RespawnFormation` 同理）。
核心分支 `codex/an-formation-despawn-crash`。修复后 run 429/431 不再崩，9 只前置全部恢复（9/9）。

### 2. `RuntimeStrategyName` 硬编码表（已修，已验证）

见 [台账](../../BOSS-LEDGER.md)。换任何新副本都会撞。

### 3. `ResetInstance` 在 evade 串联下不收敛（已修，已验证）

原来 `ResetInstance` 单趟遍历，对每只 spawn「evade 完立刻清理并判定」。在 AN 里：

- 处理任一守望者 → `OnCreatureEvade(watcher)` → `krikthir->EnterEvadeMode()`
  → `OnCreatureEvade(krikthir)` → 对三组守望者 `DespawnFormation(0s, 20s)` → **9 只全下线**
- 处理 boss → 同样触发 `DespawnFormation`，随后 `AI()->Reset()` 又 `RespawnFormation(true)`

每处理一只就把别的打下去，单趟永远收敛不到「全部干净」。run431 是 5/5 场 `boss not found on map`。

**改法**：拆成三趟（mod-raidtest）——

1. **只 evade**：对所有目标 spawn 只调 `EnterEvadeMode()`，让脚本的连锁反应一次跑完。
   且**只对确实需要复位的目标**下 evade（在战斗 / 在 evade 态 / 掉血 / 已死）：
   对一只本来就干净的 HARD_RESET boss 调用它，会把它下线并压 20 秒重生
   （`Creature.h`: `DespawnOnEvade(Seconds respawnDelay = 20s)`），正是 run433/434 的作废原因。
2. **恢复并清理**：逐个 `ResolveOrRestoreSpawn` + 回满 + 清战斗 + 清仇恨 + 归位。
3. **只读校验 + 落快照**：单独一趟，因为第二趟里某只怪的 `AI()->Reset()` 仍可能动到别的怪
   （克里克希尔的 `Reset()` 会对三组守望者 `RespawnFormation`）。本趟不做恢复，
   还缺就如实报错。

目标列表按 spawnId 升序固定，免得 `GetAllCreatureData` 的容器序让每次 attempt 走不同路径。

**验证**：run435/436 的 reset 段 10/10 全部 `clean boss spawn`，流程首次进入 `prerequisites_start`。

### 4. 清怪期间 boss 的缓存 GUID 悬垂（已修，已验证）

`TickPrerequisites` 每 tick 用 `ResolveBoss` 按 **FindBoss 阶段缓存的 `ctx.bossGuid`** 重寻址，
一旦为空立刻 `Abort`。但带 `HARD_RESET` 的 boss 脱战一次就会被 `DespawnOnEvade()` 下线，
核心默认 **20 秒**后重新生成一只**新对象、新 GUID**——缓存的 guid 必然悬垂。
run434 就是清怪开始 4.6 秒时 boss 消失而作废（一个 bot 都没死）。

**改法**：`ctx.boss` 为空时先按 entry 用 `FindBossNear` 重寻址并更新 `ctx.bossGuid`；
一时找不到就给 30 秒重生预算（`kBossAbsentBudgetMs`），期间清怪照常进行
（后面的逻辑只在 `PrerequisiteMinBossDistance` 处用 `ctx.boss`，且已判空），超预算才判失败。
这是 boss 的正常复位，不是尝试失败。

## 首轮基线（run 436，2026-09-12 傍晚）

| 场 | 结果 | 用时 | 死亡 | 清掉的前置怪 | 备注 |
|---|---|---|---|---|---|
| 1 | 清怪失败 | 18.8 秒 | 3 | 0 | `prerequisite_failed: group lost` |
| 2 | 清怪失败 | 35.4 秒 | 4 | 1 | 同上 |
| 3 | 清怪失败 | 26.6 秒 | 3 | 1 | 同上 |
| 4 | 清怪失败 | 18.9 秒 | 2 | 0 | 同上 |
| 5 | 作废 | 0.0 秒 | 0 | — | `spawn disappeared without a recorded death`（见「仍未处理」） |

**boss 一次都没有被开上，因此本 boss 仍不产出任何 boss 战结论。**

### 死因：两组守望者同时进战斗

每一场，**五个不同 entry（= 纳吉尔组 + 加什拉组，共 6 只）都在 3.4–9.1 秒内先后开始输出**，
彼此间隔只有 3–5 秒：

| 场 | 各 entry 首次输出时刻（毫秒） |
|---|---|
| 1 | 28729 @3432 → 28732 @3523 → 28733 @6012 → 28730 @7302 → 28734 @8174 |
| 2 | 28732 @4940 → 28730 @5956 → 28734 @5969 → 28729 @6718 → 28733 @9121 |
| 3 | 28729 @3853 → 28732 @4064 → 28733 @5663 → 28734 @5954 → 28730 @5955 |
| 4 | 28732 @3789 → 28729 @4374 → 28733 @5421 → 28734 @6364 → 28730 @6480 |

纳吉尔 (511.8,666.5) 与加什拉 (526.7,663.6) 相距仅 **15.0 码**，队伍一接近就把两组都拉上。
两组的 `flags_extra` 是 `0x02000000`（DONT_CALL_ASSISTANCE），所以**不是求援**，是单纯的邻近仇恨。

四场合计全队承伤 **424,711**：

| entry | 名称 | 次数 | 承伤 | 单次最大 |
|---|---|---|---|---|
| 28732 | Anub'ar Warrior | 46 | 140,448 | **10,220** |
| 28733 | Anub'ar Shadowcaster | 26 | 85,633 | 5,821 |
| 28734 | Anub'ar Skirmisher | 28 | 74,166 | 6,412 |
| 28730 | Watcher Gashra | 41 | 66,718 | 5,131 |
| 28729 | Watcher Narjil | 30 | 57,746 | 5,608 |

normal5-v1 的血量是坦克 22,784、布甲 14,504 上下。**Warrior 一下 10,220** 对布甲就是七成血。
六只精英同时上、无任何控制，队伍五场只杀掉 2 只。

**下一步（需用户确认是否动手）**：这与魔枢泰蕾斯特拉守卫组是同一类问题，
[清怪控制链](../../TRASH-CC-PULL-DESIGN.md) 已经在 mod-playerbots 共享层
（`TrashCcPullStrategy`），复用是三步：`WotlkDungeonANStrategy` 继承它、调基类 `InitTriggers`、
登记治疗小怪 entry；场景再加 `PrerequisiteCcWaitSeconds`。
按项目规矩**先量化再写策略**——上面的量化已经有了。

## 仍未处理

`_prerequisiteGuids` 也是在清怪开始时缓存的 GUID 列表。AN 的 `DespawnFormation` 一旦触发
（任一守望者或 boss 脱战），9 只会被整体下线，这些 guid 同时悬垂，框架报
`prerequisite_invalid: spawn disappeared without a recorded death`（run436 第 5 场 2 毫秒即触发）。
与刚修掉的 boss 悬垂 GUID 是同一类问题，改法也同源：按 spawnId 重寻址而不是认死 GUID。
另外，清怪段 bot 死光时结果记为 `aborted` 而不是 `wipe`，对台账口径偏保守，一并待改。

## 交接

- 场景 conf 已提交并注册；准备点/开怪点已用 `raidtest los` 逐目标验证（9 只视线全通、距离全部 > 21 码）。
- 下一条安全操作：实现两趟 `ResetInstance`，编译后先跑 1 场冒烟确认能进 boss 战，再跑 5 场基线。
