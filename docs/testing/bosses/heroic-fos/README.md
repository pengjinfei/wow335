# 英雄灵魂洪炉（Forge of Souls，map 632）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），隔离 boss 战，`MasterlessAvoidAoe=1`。勘察见 [SURVEY](SURVEY.md)。

| boss | 场景 | 结果 | 状态 |
|---|---|---|---|
| Bronjahm | `heroic-fos-bronjahm-h5g` | 改前 0/3（run1114 超时、run1120 47%、run1125 25%）；playerbots `fdd4ff99` 后 **4/5**（run1293–1296 击杀，run1297 53%） | **基本稳定** |
| Devourer of Souls | `heroic-fos-devourer-h5g` | 改前 0/2（run1115 38%、run1121 22%）；`fdd4ff99` 后 **3/5**（run1299/1300/1302 击杀，run1298 59%、run1301 13%） | **基本稳定** |

## Bronjahm

- 清怪：`FixtureDespawnSpawns` 扩到 boss 周围约 65 码内的 Watchman/Animator/Horror/Apparition（9 只）。run1120 起无小怪卷入。
- run1125：171 秒进二阶段（34%），158.9 秒的 Corrupt Soul 生出的碎片在 172.97 秒走到 boss 身上（Consume Soul 69047），boss 回到 61%。7 个碎片中 6 个被打掉。二阶段牧师先死：Magic's Bane 69050 共 11.5 万、Shadow Bolt 69049。
- run1120：牧师 147.5–188.6 秒不施法、满蓝满血，期间补了一次耐力；run1125 开引擎日志后未复现，原因未查明。

- **修复**（`fdd4ff99`）：Corrupt Soul 目标在整个 debuff 期间离 boss 25 码（原来只在读条时逃 15 码），碎片出生点更远；DPS 直接攻击碎片（原来只挂骷髅标记，run1125 一只挨了 4 万伤害的碎片仍走进 boss）。改后 5 场 4 杀，唯一团灭 run1297 53%。

## Devourer of Souls

- run1121 承伤：幽灵冲击 70322 压坦克，灵魂之井（NPC 36536，70323）约 11 万分散在各人，哀嚎之魂 70324 约 13 万。治疗全程在施法，瓶颈是承伤总量。
- 现有策略只处理 Mirrored Soul（非坦克背对 boss）。
- **修复**（`fdd4ff99`）：哀嚎之魂读条（68899）或周期伤害（68875/68876）期间，非坦克站到 boss 背后 6 码。run1121 这一项吃了 12.7 万；改后 5 场 3 杀，两场团灭 run1298 59%、run1301 13%。
