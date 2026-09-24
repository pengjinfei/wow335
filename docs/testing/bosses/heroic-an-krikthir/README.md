# 英雄艾卓-尼鲁布 / 门卫克里克希尔（28684，map 601）

## 接手摘要

- 更新：2026-09-12 深夜。已套用清怪控制链。**有过一次完整击杀（run437：267.8 秒、零死亡），
  但 5 场基线 run442 仍是 0/5**；清怪从「一只没杀就倒」推进到「稳定清掉 6–7/9、130 秒」。
- 已完成：上游 AC 崩溃修复；`ResetInstance` 三趟；boss/前置怪的悬垂 GUID 按 spawnId 重绑；
  控制链接入并**实测生效**（束缚亡灵 5.4 秒落地、持续 38 秒未被自家 AoE 打掉、一组一组打）。
- 唯一下一步：清怪后半段仍会被打崩（run442 a1/a2 在 132 秒清到 6–7/9 时团灭）。
- 阻塞：无框架阻断。剩下的是战斗强度问题 + 一个记账问题（见「仍未处理」）。

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

## 套用清怪控制链（2026-09-12 深夜）

### 先量化：这个副本的控制到底能不能用

按项目规矩先查数据再写策略，结果直接推翻了「照搬控制链」这个前提：

**第一关 生物类型**。门厅 9 只全是**亡灵**（`creature_template.type = 6`）。
控制链原有的三个法术按 `Spell.dbc` 的 `TargetCreatureType`：

| 法术 | 掩码 | 含义 | 对亡灵 |
|---|---|---|---|
| 变形术 118/12826 | 193 | 野兽+人形+小动物 | **无效** |
| 妖术 51514 | 65 | 野兽+人形 | **无效** |
| 闷棍 51724 | 71 | 野兽+龙类+恶魔+人形 | **无效** |
| **束缚亡灵 9484/10955** | **32** | **只对亡灵** | **有效** |

> 顺带纠正共享层一条既有错误判据：原 `TrashCcSpellFits` 写的是「妖术没有生物类型限制」，
> 实际妖术是 65，**对元素也无效**。魔枢文档里「奥莫洛克那组（元素，只能妖术）」这句话据此是错的。

**第二关 机制免疫**。类型合法也未必控得住，查 `creature_immunities`：

| 怪 | 免疫集 | MechanicsMask | 结论 |
|---|---|---|---|
| 三个守望者（28729/28730/28731 及英雄 entry） | **-361** | `0x26CB3F7F` = CHARM/DISORIENTED/DISARM/DISTRACT/FEAR/GRIP/ROOT/SILENCE/SLEEP/SNARE/**STUN**/FREEZE/KNOCKOUT/**POLYMORPH**/**BANISH**/**SHACKLE**/TURN/HORROR/INTERRUPT/DAZE/**SAPPED** | **对全部控制免疫** |
| 六只蛛魔小怪（28732/28733/28734） | -93 | `0x800010` = FEAR\|HORROR | 束缚亡灵可以落 |

所以这一本唯一可用的控制是**牧师的束缚亡灵，且只能落在蛛魔小怪身上**。

### 共享层改动（mod-playerbots，分支 `codex/an-trash-cc-shackle`）

1. `TrashCcRole` 加 `targetTypeMask`，`TrashCcSpellFits` 改为按法术自己的 `TargetCreatureType` 判，
   不再手写生物类型清单（修掉上面那条妖术的错误判据）。
2. 新增**牧师 / 束缚亡灵 / 三角图标**这一分工：`TrashCcShackleAction`、`trash cc shackle`
   触发器与上下文注册、`TrashCcPullStrategy` 多一条 TriggerNode、四处图标列表补上三角；
   `TrashCcIncapacitated` 认 `MECHANIC_SHACKLE`（束缚亡灵的光环是 `SPELL_AURA_MOD_STUN`，
   与闷棍同型，必须按机制区分，否则制裁之锤也会被当成控制）。
3. `TrashCcSpellFits` **再加一关机制免疫**（`IsImmunedToSpell`）。不加这一关时，
   坦克把三角分给了 `Watcher Narjil`，牧师每 tick 都是
   `A:trash cc shackle - IMPOSSIBLE` / `target is immuned to spell ... spellid: 10955`（run439 轨迹）。
4. `TrashCcMarkNeeded` 只统计「控制对这一组真的落得下去」的职业。否则法师/萨满/盗贼在场却全无效时，
   `assigned` 永远追不上 `casters`，坦克会每 tick 重标、永不开怪。
5. `WotlkDungeonANStrategy` 继承 `TrashCcPullStrategy` 并调基类 `InitTriggers`。
   门厅没有治疗小怪（技能只有致盲蛛网/缠网/毒液/暗影箭），不登记 `TrashCcRegisterHealerEntries`，
   按共享层默认「有法力 > 其它」排，暗影术士(28733) 会被优先控。

### 框架改动（mod-raidtest）

6. 控制链门禁遍历的图标由 `{4,5,6}` 改为 `{3,4,5,6}`，否则三角永远等不到。
7. 场景加 `PrerequisiteCcWaitSeconds = 25`。**这一项才是效果的主要来源**（见下）。
8. `_prerequisiteGuids` 悬垂时按 spawnId 重绑（`DespawnFormation` 后核心按原 spawn 重新生成的是新对象）。
9. `ValidateRaid` 在清怪阶段不再把「阵亡/正在传送墓地的 bot」判成队伍失效。
   run441 五场全栽在这上面，作废都发生在首个玩家阵亡后 3–33 秒，其中 a3 已清 7/9、只死 1 人。

## 效果：真正起作用的是「一组一组拉」，不是控制本身

`PrerequisiteCcWaitSeconds > 0` 会同时打开 `kCcApproachDistance = 24`：拉怪被拒时只接近到
仇恨半径之外，坦克在 24 码外用制裁之手远程开怪。对比同一场景的伤害时间线：

| | run436（无控制链） | run437（有控制链） |
|---|---|---|
| 第一组 | 28729/28732/28733 @3.4–6.0 秒 | 28729 @21.6、28732 @21.9、28733 @25.7 秒 |
| 第二组 | 28730/28734 @5.9–8.2 秒（**同时**） | 28734 @71.4、28730 @71.5 秒（**晚 50 秒**） |
| 第三组 | — | 28731 @128.2 秒 |
| boss | 从未开上 | 28684 @203.9 秒 |

run437 因此打出**首次完整击杀：267.8 秒、零死亡、boss 0%**。

控制本身在修好免疫判据后也确实生效（run440）：标记落到 `Anub'ar Warrior`（不是免疫的守望者），
束缚亡灵 5.4 秒落地、**只施放 1 次**、连续 38 个 1 Hz 采样都在（全程没被自家 AoE 打掉），
门禁由空等 17–19 秒变成 5.4 秒 `reason=cc_ready icons=1 landed=1`，那一组 3 只里 2 只被击杀、零死亡。

## 首轮基线（run 442，最终二进制）

| 场 | 结果 | 用时 | 死亡 | 清掉的前置怪 | 束缚亡灵施放 |
|---|---|---|---|---|---|
| 1 | 团灭 | 132.5 秒 | 5 | 6/9 | 5 |
| 2 | 团灭 | 133.4 秒 | 5 | **7/9** | 1 |
| 3 | 作废 | 55.3 秒 | 0 | 3/9 | 1 |
| 4 | 作废 | 32.0 秒 | 2 | 2/9 | 1 |
| 5 | 作废 | 110.6 秒 | 1 | 6/9 | 1 |

**0/5。** 但与 run436（一只没杀、18–35 秒就倒）相比，清怪已经能稳定推进到 6–7/9、130 秒。
三场作废是 `spawn disappeared without a recorded death`：日志确认是 spawn 12764 / 12766 / 12758
被实例脚本的 `DespawnFormation` 整组下线且未及时重生（重绑失败）。

**结论：boss 仍未通关（12 次尝试 1 次击杀）。** 控制链让清怪从「打不动」变成「差一口气」，
但这一本能上的控制只有一个（6 只可控怪里每组控 1 只，三个守望者完全免疫），
差距要靠别的手段补。

## 仍未处理

1. **清怪后半段被打崩**：run442 a1/a2 清到 6–7/9 时团灭。这是纯战斗强度问题。
2. **`DespawnFormation` 导致的作废**：按 spawnId 重绑只能救「已经重生回来」的情形；
   整组被下线且还没重生时仍然作废。可考虑等待重生（类似 boss 的 30 秒预算）而不是立即作废。
3. 清怪段 bot 死光记为 `wipe`（已比之前准确），但「清怪失败」与「boss 战团灭」在台账里仍需人工区分。


## 2026-09-24 ilvl 200 装备档复跑（独立 cohort）

- 场景 `heroic-an-krikthir-h5g`：由原 normal5 场景复制，**仅** `RosterFile` 换为 `mod-raidtest-roster-heroic5gear-n5talents-v1.conf`（天赋/雕文/补给同 normal5-v1，装备 17 件全 ilvl 200 已回读核对）。binary：playerbots `7e77a827`、raidtest `35ca8f5`（SHA `d3fbfef4…`）。
- 结果：**4/4 kill、0 死**（run838/840/841/842；7 次启动预算内 run836/837/839 三次 `prerequisite_invalid: spawn disappeared without a recorded death` 中止，只得 4 个合格样本）。对照 normal5 仅一次 kill。不与 normal5 任何 cohort 合算。
