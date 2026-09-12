# 英雄艾卓-尼鲁布 / 门卫克里克希尔（28684，map 601）

## 接手摘要

- 更新：2026-09-12。**尚无有效基线** —— 被框架缺陷挡住，未进入过 boss 战。
- 已完成：完整遭遇战场景建好、坐标勘测完毕；**定位并修好了一个上游 AzerothCore 崩溃**。
- 唯一下一步：**把 `AttemptRunner::ResetInstance` 改成两趟**（先全部 evade，再逐个恢复并校验），
  单趟遍历在 AN 的 evade 串联下收敛不了。
- 阻塞：上面这条，需要一次增量编译。

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

### 3. `ResetInstance` 在 evade 串联下不收敛（**未修，下一步**）

`ResetInstance` 单趟遍历所有 spawn，对每只调 `EnterEvadeMode()`。在 AN 里：

- 处理任一守望者 → `OnCreatureEvade(watcher)` → `krikthir->EnterEvadeMode()`
  → `OnCreatureEvade(krikthir)` → 对三组守望者 `DespawnFormation(0s, 20s)` → **9 只全下线**
- 处理 boss → 同样触发 `DespawnFormation`，随后 `AI()->Reset()` 又 `RespawnFormation(true)`

于是每处理一只就把别的打下去，单趟遍历永远收敛不到「全部干净」。
run 431 日志可见：boss 先判干净，9 只守望者逐个「restored original boss spawn」，
其中 12760 还触发了 hard-reset 重载；等走到 Pull 阶段时 **boss 已经不在地图上**
（`boss entry 28684 not found near engage point`，5/5 场）。

**建议改法**：把 `ResetInstance` 拆成两趟——
第一趟只对所有目标 spawn 调 `EnterEvadeMode()`（让串联反应跑完），
第二趟再逐个 `ResolveOrRestoreSpawn` + 回满 + 清战斗 + 归位，最后统一校验。
本轮已经加好的 `ResolveOrRestoreSpawn()` 与失败归因日志可以直接复用。

## 尝试记录

| run | 结果 | 说明 |
|---|---|---|
| 424 | worldserver 崩溃 | 上游 `DespawnFormation` 段错误，见上 |
| 429 | 5/5 `scene_invalid` | 崩溃已修；boss 被 evade 串联打成 Corpse（`alive=false death_state=2` 满血） |
| 431 | 5/5 `boss not found on map` | HARD_RESET 重载已修；仍被 evade 串联带走，未进 boss 战 |

**没有任何一场进入过 boss 战，因此本 boss 不产出任何战斗结论。**

## 交接

- 场景 conf 已提交并注册；准备点/开怪点已用 `raidtest los` 逐目标验证（9 只视线全通、距离全部 > 21 码）。
- 下一条安全操作：实现两趟 `ResetInstance`，编译后先跑 1 场冒烟确认能进 boss 战，再跑 5 场基线。
