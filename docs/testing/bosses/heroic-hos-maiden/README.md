# 英雄岩石大厅 / Maiden of Grief（27975）

状态：隔离 boss 基线已达击杀稳定（5/5）；不是完整房间或副本通关。

## 固定口径

- map 599、Heroic、normal5-v1、`AiPlayerbot.BotCheats=""`、`GearProfile=none`。
- 不改装备、难度、cheat、boss 数值或核心脚本；无 fixture。
- 任何隔离结果与 Krystallus 的证据房间样本分账，也不能改写完整房间范围。

## 静态勘测

- DB boss spawn：`126789` / entry 27975，`(842.632,666.047,190.116)`，静止。
- 最近东侧组：27969 `126736`（巡逻）及 27972 `126747/126748`、32258 `126683`，约 63 yd 于 boss
  初始位置；其是否在 Maiden 完整房间范围内尚未实测，不能预填 `PrerequisiteSpawns`。
- 候选开怪点 `(867,666,190.31)`：先用 vmap 取得真实 floor 190.31，再以真实 z 测得至 boss 24.4 yd、LOS=true；
  至 126736 38.2 yd、LOS=true。它在约 22 yd 仇恨半径外且在正常拉怪范围内，但静态 LOS 不是导航/assist 证明。

## 机制与现有策略

- core：Storm of Grief `50752`（6–10 秒）、Pillar of Woe `50761`（7–15 秒）、Shock of Sorrow `50760`
  （14–29 秒）、英雄 Parting Sorrow `59723`（27–45 秒）。
- `WotlkDungeonHoSStrategy` 对 Maiden 只有 `TODO: Jump into damage during shock of sorrow?`；当前没有 Maiden
  trigger/action/multiplier。首场只观察机制覆盖、伤害、死亡、导航和外怪来源，不能暗示已有 Shock 应对。

## 隔离 boss 基线：run708–712（5 个有效样本）

- 每场均为 Heroic / normal5-v1 / `BotCheats=""`、无 fixture；boss source=91/spawn=126789。
  `run708`–`712` 全部 kill：61.909、63.104、59.678、51.288、62.107 秒，**5/5 kill、1 death（run710）**。
- 所有五场对队伍的敌对伤害均只有 27975；无 126736/126747/126748/126683 或其他外来 creature source，
  所以隔离口径成立。此结论不推断东侧组不是完整房间前置。
- 机制覆盖：五场各有 Parting Sorrow 59723×1；Shock 59726 为 1–2 次、Pillar 59727 为 3–5 次、
  Storm 59772 为 3–4 次。现有 HoS 策略对 Maiden 没有专门应对。
- run710 唯一死亡为 DPS 818 于 57.354 秒、boss 段，直接致死事件为 Maiden 对 818 的 **1,350** 伤害。
  因果链可闭合到“低血后续 boss 伤害”：54.005 秒 Maiden 对 818 施 Pillar（59727）并造成 3,538；
  818 HP 从 9,850（53.262 秒）降至 5,131（54.262）、3,950（55.259）、2,435（56.264）、1,254
  （57.270），57.353 秒的 1,350 伤害击杀。43.921–57.354 秒没有 healer→818 的治疗记录；不过
  `OnDamage` 没有 spellId，不能把最后一击或这段治疗空档严格归给 Shock。故它是“Pillar 后低血 + 治疗
  空档”的单例，不足以声称 Shock 策略缺陷。

## 下一步

1. 隔离基线的击杀稳定已达到 n=5，但非零死亡；若目标是零死亡，再单独量 death 的伤害/治疗/控制因果。
2. 要建立完整房间，先实测东侧 126736、126747、126748、126683 的路径、assist 与 boss 段参战；出现则按
   spawnId/summoner 定义前置，不能用 fixture 删除。
3. Shock 策略是否需新增须先有可复现机制失败证据。
