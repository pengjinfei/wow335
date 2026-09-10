# 英雄魔枢 / 阿诺姆鲁斯（Anomalus, 26763）/ `heroic-nexus-anomalus-n5`

## 接手摘要

- 更新日期 2026-09-10。状态：**策略失败（0/5）**，是本副本唯一**无小怪污染**的干净样本。
- 已完成：场景建立、拉怪点实测可用、5 场基线、输出/承伤归因到机制。
- 唯一下一步：查混乱空间裂隙（Chaotic Rift, 26918）的处理效率——bot 确实会转火裂隙
  （对裂隙/小怪输出占总输出 37–46%），但裂隙+召唤物承伤 664k 仍压过治疗量。
- 阻塞/需用户决定：是否投入 mod-playerbots 策略修复（属多轮工作）；本 boss 不阻塞。

## 可复现基线

- 装备档位 `normal5-v1`（ilvl 上限 187），boss 英雄难度（等级 82，`HealthModifier = 32`），
  `BotCheats = ""`，`AutoEquipUpgradeLoot = 0`。
- mod-raidtest `dev` @ `dfc7372` + 未提交的 `CombatTrigger` 策略名映射
  （`"wotlk-nex" -> "nexus"`，见 [夹具勘测](../heroic-nexus/FIXTURE-SURVEY.md)）。
  mod-playerbots `codex/heroic-uk-ingvar` @ `67ac953c`（本轮**一行未改**）。
  core `Playerbot` @ `516b14df1`。
- 场景：map 576 / boss 26763 / 英雄 / 5 人 / **无前置怪** / 拉怪点 (641.0,-285.0,-9.13,4.03)。
- 角色 guid 796–800（与本副本另外三个 boss 共用同一套，见夹具勘测）。
- **无前置怪不是省事**：该房间 60 码内唯一的非 boss 生成点是 `Crazed Mana-Wyrm`(26761)，
  z 从 −14.6 到 +29.2 分布在深渊上空（飞行单位），不是同层地面怪。战斗中出现的
  `Crazed Mana-Wraith` / `Crazed Mana-Surge` 是裂隙召唤物，属遭遇战机制本身。

## 机制与代码审计

| 机制 | trigger → action | 正常规则 | 运行证据 | 结论 |
|---|---|---|---|---|
| 混乱空间裂隙 | `chaotic rift` → `chaotic rift target`（`ACTION_RAID + 1`，`NexStrategy.cpp:28`） | 是（转火目标选择，不改仇恨） | 五场对裂隙/召唤物输出 162k–217k，占总输出 37–46% | **已触发且生效**，但不足以压住裂隙产出 |
| 裂隙召唤物 | 无专门 trigger（由上面的转火覆盖） | — | `Crazed Mana-Wraith` 184,635 + `Crazed Mana-Surge` 134,143 承伤 | 未单独验收 |
| Spark of Life / 移动 | 无 | — | 未采样 | **未覆盖** |

## 尝试记录

| run / attempt | 结果 | 时长 | 死亡 | boss HP | 备注 |
|---|---|---|---|---|---|
| 335 / 1（冒烟） | wipe | 90.5s | 5 | 40% | 验证坐标可用 |
| 342 / 1 | wipe | 83.7s | 5 | 45% | |
| 342 / 2 | wipe | 85.3s | 5 | 33% | 五场中最好 |
| 342 / 3 | wipe | 95.8s | 5 | 45% | |
| 342 / 4 | wipe | 76.4s | 5 | 36% | |
| 342 / 5 | wipe | 86.6s | 5 | 40% | |

**run 342 合计（5 场）**：0 击杀 / 5 团灭，boss 最低 33%，每场全灭。

输出侧（bot 造成，按目标拆分）：

| attempt | 对 boss | 对裂隙/召唤物 | 对小怪占比 |
|---|---|---|---|
| 1 | 233,548 | 172,426 | 42.5% |
| 2 | 276,249 | 189,067 | 40.6% |
| 3 | 236,029 | 205,724 | 46.6% |
| 4 | 275,793 | 162,054 | 37.0% |
| 5 | 257,375 | 216,814 | 45.7% |

承伤侧（5 场合计）：Anomalus 709,734 / Chaotic Rift 479,849 / Crazed Mana-Wraith 184,635 /
Crazed Mana-Surge 134,143。即**裂隙及其召唤物合计 798,627，超过 boss 本人**。

结论：不是「bot 不会打裂隙」，而是**裂隙的产出速度超过 5 人 ilvl 187 的清理与治疗速度**。
raid DPS 约 5,000–5,600，与 UK 同 roster 的 5,800–6,700 同量级，属该装备档的正常水平。

## 修复（未做）

- 未做任何 mod-playerbots 改动。可能方向（**均未验证，不要当结论**）：
  裂隙的转火优先级/打断、治疗在裂隙 AoE 下的站位、召唤物的 AoE 清理。
- 先决条件：本副本的夹具层已稳定（本 boss 已稳定），可以直接加采样做归因。

## 交接

- 场景模板与运行配置均已就位；`raidtest run heroic-nexus-anomalus-n5 --attempts 5` 可直接复现。
- 事件在本地 MySQL `acore_characters.raidtest_events`（run 335、342）。
- 新会话下一条安全操作：先读 [夹具勘测](../heroic-nexus/FIXTURE-SURVEY.md)，再决定是否开策略线。
