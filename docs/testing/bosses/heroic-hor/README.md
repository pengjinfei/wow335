# 英雄映像大厅（Halls of Reflection，map 668）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），`MasterlessAvoidAoe=1`，策略 `wotlk-hor`。勘察见 [SURVEY](SURVEY.md)。

| boss | 场景 | 结果 | 状态 |
|---|---|---|---|
| Frostsworn General | `heroic-hor-general-h5g` | **5/5**（run1343–1347，0 死，60–67 秒）；核心修复前的 4 场反射体从未参战 | **完成（隔离）** |
| Falric | `heroic-hor-falric-h5g` | **3/18**（run1339、1353、1362）；多数团灭在 Falric 0–5%，也有死在波次里 | 跳过待确认（BACKLOG 23） |
| Marwyn | 未建 | 单独隔离无干净入口（跳过前 5 波靠副本私有变量），需链式场景 | 未开始 |
| 巫妖王逃亡 | 未建 | 框架要走 `sScriptMgr->OnGossipSelect` 并等 gossip 标志；bot 缺躲 LK / 打墙逻辑 | 未开始（大改） |

## 前置改动

- playerbots `cf1871ea`：map 668 原本没有副本策略，raidtest 开怪前的策略门会拦下所有场景；加空的 `wotlk-hor`。
- raidtest `9555799`：`EngageConfirmInstanceDataAtLeast=1`（开战确认与“遭遇进行中”用 `>=`）。Falric 的波次计数（instance data 8）第 2 波起不再等于 1。

## Frostsworn General（隔离）

- 夹具：`FixtureBossStates=1:3`（Marwyn DONE）+ 移除隐身的 DB 将军 1972019 + 在原位召一只（script 模式，pull 开战）。
- **核心脚本缺陷**（核心 `12c3ed4b7`）：两个反射体模板（37068/37721）都带 `UNIT_FLAG_IMMUNE_TO_PC`，`ACTION_SPIRITUAL_REFLECTIONS_ACTIVATE` 从不清掉——反射体进战斗、跳下来，但选不了玩家目标、也打不了。修复前 4 场（run1335/1337/1340/1341）队伍只打了将军本人，反射体零伤害；修复后 5 只全部激活、参战并被击杀（每只约 10 万血），反射体对队伍约 2.2 万伤害。这与隔离无关，正常流程同样如此。

## Falric

- 夹具：`FixturePersistentData=0:1` → 副本原生的“团灭后重开”：全员活着站在大厅中心 40 码内，约 19 秒后第 1 波自己开始（只跳过一次性剧情）。`EngageTrigger=self`。
- 结构：第 1–4 波 3/3/4/4 只灵魂（英雄 DamageModifier 13），每波约 45 秒；Falric 在 218–265 秒出手。
- 承伤：Defiling Horror（72452）每场约 23 万，是最大项。它的机制是 **Horror（24）不是 Fear（5）**，战栗图腾、防护恐惧结界都挡不住。Hopelessness 在 67/34/11% 把伤害和治疗砍 20/40/60%，多数团灭停在 0–5%。
- **英勇时机**（playerbots `0fc1b7ad`）：通用爆发触发器只在 `balance<=50` 时放，单个 5 人本 boss 永远达不到（见 BACKLOG 22），所以英勇每场都交在第 1 波小怪上。改为波次期间压住、Falric 可攻击后萨满直接放：行为正确（4/4 场在 Falric 开打时放出），但击杀率没变（改前 1/5、改后 1/5）。瓶颈是整场总吞吐，波次本身也会团灭（run1359 死在 200 秒）。
