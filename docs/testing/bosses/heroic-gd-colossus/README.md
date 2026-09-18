# 英雄古达克 · 德拉克瑞巨像 Drakkari Colossus（29307）

## 接手摘要

- 场景 `heroic-gd-colossus-n5` 已建；run651–652 的同口径样本为 **5/5 零死亡击杀**，64.374–68.137 秒；隔离 boss 战基线通过。
- run647–648 证明 `EngageTrigger=summon` 精确选中了巨像（29307）自己召出的 Living Mojo（29830）；将确认窗改成真实
  时间后，run649 观测到临时 Mojo 合并、巨像获得全队威胁、约 3.5 秒后解除不可攻击。
- run651 的夹具已移除 4 只常驻 Living Mojo 与巨像编队的 2 只 Drakkari Golem；这六只均在 0ms 的事件流中留痕，未参与伤害事件。

## 原生机制与场景口径

巨像 `Reset()` 时处于冻结/不可攻击，并召五只临时 Living Mojo。这里的关键不是击杀五只：
任意 Mojo 被玩家拉到后，它的 `JustEngagedWith()` 会对 summoner 调 `ACTION_INFORM`；巨像
`SetInCombatWithZone()`、命令 Mojo 合并，并计划在 3.5 秒后可攻击。

场景的 `EngageTrigger=summon` 只检索 `entry=29830` 且 `GetSummonerGUID()==bossGuid` 的活体，再由坦克发起
一次原生 `AttackAction`。这不生成/删除/改写任何怪，也不代替机器人选择技能或走位。房间西侧四只同 entry 的
数据库刷怪（127076–127079）不是候选。

## 开战时序：run647–648（2026-09-17）

| 项目 | 证据 |
|---|---|
| 角色夹具 | 五个独立 normal5 角色成功建立；此前新场景因角色名前缀碰撞而无法创建。 |
| 目标选择 | `summon_trigger: entry=29830 ... owner=29307`；目标 GUID 为 boss 直接召唤物。 |
| run647 | `combat_start` → `combat_end` 98ms，无伤害、无死亡、boss HP 100%。 |
| run648 只读诊断 | 20 个空载 world tick 只过 34ms；boss 全程无 combat/victim/threat，触发 Mojo 仍在战斗，证明坦克尚未来得及实际接敌。 |

## 首个 boss 战：run649（2026-09-17）

| 项目 | 证据 |
|---|---|
| 原生触发 | 临时 Mojo 合并消失；巨像获得 5 个玩家威胁引用，约 3.5 秒后移除 `NON_ATTACKABLE`；坦克随后取得威胁。 |
| 战斗结果 | 23.018 秒全灭，boss 最低 73%。 |
| 污染来源 | 常驻 Mojo spawn 127076–127079 中至少 3 只也造成伤害并参战；它们是房间路怪，而非 boss 召唤的机制 Mojo。 |

`20` 个 tick 不是可靠的时间预算。该场景现按 6 秒真实经过时间等待坦克自身的原生 AttackAction；框架不再需要也没有
向巨像注入零威胁战斗引用。

## 常驻 Mojo 隔离：run650（2026-09-17）

| 项目 | 证据 |
|---|---|
| 夹具 | `FixtureDespawnSpawns=127076,127077,127078,127079`，事件流在 0ms 逐只记录 4 次 `fixture_despawn`。临时 Mojo 没有数据库 spawn，仍正常触发、合并与解锁。 |
| 结果 | 89.722 秒、零死亡击杀。 |
| 仍存污染 | 巨像 127046 是两只 Drakkari Golem（127080/127081，entry 29832）的 formation leader，`groupAI=1`；两只在 run650 均造成伤害并参战。 |

因此 run650 只能说明“巨像 + 两只石魔”在 normal5-v1 下可零死亡击杀，不能代表巨像本体的隔离击杀率。

## 完整隔离：run651（2026-09-18）

| 项目 | 证据 |
|---|---|
| 夹具 | `FixtureDespawnSpawns=127076,127077,127078,127079,127080,127081`；六次 `fixture_despawn` 都在 0ms。前四只为常驻 Mojo，后两只为 formation 石魔。 |
| 原生链 | 巨像自身召唤的 5 只临时 Mojo 不具数据库 spawn，未被夹具影响；仍触发、合并，巨像解除不可攻击后开战。 |
| 结果 | `attempt_id=1788427797`：64.374 秒击杀、boss 最低 HP 0%、0 死亡。 |
| 复核 | 伤害事件源没有六个被移除单位；记录到的是巨像、临时机制单位和五名机器人。 |

这是一项明确记录的**隔离 boss 战基线**：只移除房间路怪和 boss 编队附属物，未跳过临时 Mojo 机制，未改装备、难度、cheat 或 boss 仇恨。

## 同口径复验：run652（2026-09-18）

| seq | attempt_id | 结果 | 时长 | 死亡 | 夹具核对 |
|---|---:|---|---:|---:|---|
| 1 | 1788427798 | kill | 68.137 秒 | 0 | 6 次 `fixture_despawn`，均为 0ms |
| 2 | 1788427799 | kill | 66.837 秒 | 0 | 6 次 `fixture_despawn`，均为 0ms |
| 3 | 1788427800 | kill | 65.119 秒 | 0 | 6 次 `fixture_despawn`，均为 0ms |
| 4 | 1788427801 | kill | 67.397 秒 | 0 | 6 次 `fixture_despawn`，均为 0ms |

加 run651，完全相同的 normal5-v1 / Heroic / 无 cheat 隔离基线为 **5/5 零死亡**、64.374–68.137 秒
（平均 66.373 秒，Wilson 95% CI 57–100%）。每场均保留巨像自身 5 只临时 Mojo 的原生触发、合并和解锁链，
而房间常驻 Mojo 与编队石魔均在开战前移除。

## 结论与下一步

巨像在这一明确记录的**隔离 boss 战基线通过**。这不代表连续清完整副本：房间路怪和编队附属物被夹具移除，
因此不能与 run649–650 混算。若继续巨像，应另建“完整房间”口径；不能跳过五只临时 Mojo、改装备/难度/cheat，或伪造 boss 仇恨。
