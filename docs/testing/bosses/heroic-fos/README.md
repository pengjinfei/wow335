# 英雄灵魂洪炉（Forge of Souls，map 632）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），隔离 boss 战，`MasterlessAvoidAoe=1`。勘察见 [SURVEY](SURVEY.md)。

| boss | 场景 | 结果 | 状态 |
|---|---|---|---|
| Bronjahm | `heroic-fos-bronjahm-h5g` | 0/3：run1114 超时（守卫 201706/201764 被连带拉起，已扩大清怪）、run1120 47%、run1125 25% | 跳过待确认（BACKLOG 16） |
| Devourer of Souls | `heroic-fos-devourer-h5g` | 0/2：run1115 38%（未开 avoid aoe，萨满在灵魂之井里 33 跳）、run1121 22% | 跳过待确认（BACKLOG 17） |

## Bronjahm

- 清怪：`FixtureDespawnSpawns` 扩到 boss 周围约 65 码内的 Watchman/Animator/Horror/Apparition（9 只）。run1120 起无小怪卷入。
- run1125：171 秒进二阶段（34%），158.9 秒的 Corrupt Soul 生出的碎片在 172.97 秒走到 boss 身上（Consume Soul 69047），boss 回到 61%。7 个碎片中 6 个被打掉。二阶段牧师先死：Magic's Bane 69050 共 11.5 万、Shadow Bolt 69049。
- run1120：牧师 147.5–188.6 秒不施法、满蓝满血，期间补了一次耐力；run1125 开引擎日志后未复现，原因未查明。

## Devourer of Souls

- run1121 承伤：幽灵冲击 70322 压坦克，灵魂之井（NPC 36536，70323）约 11 万分散在各人，哀嚎之魂 70324 约 13 万。治疗全程在施法，瓶颈是承伤总量。
- 现有策略只处理 Mirrored Soul（非坦克背对 boss）。
