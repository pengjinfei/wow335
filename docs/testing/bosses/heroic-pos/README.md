# 英雄萨隆矿坑（Pit of Saron，map 658）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），隔离 boss 战，`MasterlessAvoidAoe=1`。勘察见 [SURVEY](SURVEY.md)。
> 进本门槛：任务 Echoes of Tortured Souls（24499/24511）。已在数据库给测试角色 851–855 补完成记录（同时补了映像大厅的 24710/24712）。

| boss | 场景 | 结果 | 状态 |
|---|---|---|---|
| Forgemaster Garfrost | `heroic-pos-garfrost-h5g` | 改前 0/6（42%、25%、36%、72%、43%、77%）；改后 1/3（run1137 击杀；run1138 21%、run1139 55%）；试过近战也躲岩石 0/5（run1288–1292），已撤回 | 跳过待确认（BACKLOG 19） |
| Ick + Krick | `heroic-pos-ick-h5g` | 改前 0 次开战；开怪点移到 Ick 20 码处（raidtest `862dc13`）后 **5/5**（run1283–1287，零死亡，99–106 秒） | **完成** |
| Tyrannus | `heroic-pos-tyrannus-h5g` | **5/6**（run1329、1331–1334 击杀，0–2 死，144–165 秒；run1330 49% 团灭） | **基本稳定（隔离，跳过隧道）** |

## Garfrost

- **驱散死循环**（run1122）：永冻（70336）每 2 秒在有视线时重挂，牧师前 47 秒几乎只放驱散魔法 988，盗贼整场只挨 1.6 万也死了。playerbots 把 permafrost 加进不驱散名单。
- **躲岩石**：脚本 `spell_garfrost_permafrost` 跳过非近战、且萨隆岩石（GO 196485）在其与 boss 连线 4 码内的目标。第一版远程+治疗都躲（run1131）：治疗在岩石后看不见坦克，整场 14 个法术，72%。第二版只让远程 DPS 6 层起躲，run1137 击杀，法师永冻降到 12–24 跳。
- **近战也躲**（8 层起，run1288–1292）：0/5，比只让远程躲的 1/3 更差，已撤回并在代码注释里记下结果。
- **剩余**：近战与坦克躲不掉，run1138 盗贼 13.2 万、坦克 11.7 万永冻，两场团灭都是近战先死。

## Ick

- 前置怪 202156 距 Ick 8 码，清它会拉起 boss；改为全部 despawn（5 只 Horror）。
- 之后三场 8 秒内坦克无伤害：引擎日志每 tick `reach melee`/`reach spell` USELESS、`melee` FAILED，实际距离 42 码。
- **真因不是载具**：共享层的追击拴绳在治疗（坦克的锚点）离目标超过治疗距离时拒绝追击，而治疗站在 42 码外的旧开怪点。开怪点移到 Ick 20 码处后 5/5。

## Tyrannus

- 隔离形态：`FixtureInstanceData = 0:3,1:3,4:5`（Garfrost/Ick DONE、progress 5），跳过隧道 gauntlet；队伍传到 AT 5633 内，坦克发 AT 包开战，约 38 秒剧情后 Tyrannus 从 Rimefang 上跳下。移除奴隶刷点旁编队 202248/202163/202246/202165。
- 框架：Tyrannus 是 Rimefang 的载具乘客、无 DB spawn，用 `BossSpawnMode=script`；raidtest `9f59430` 放开 script 模式可配 `EngageTrigger=areatrigger`。开战确认在 AT 触发时即成立（boss_in_combat），38 秒无伤害阶段未被误判卡住。
- bot 未改。承伤：Icy Blast 地面区域（69628）击杀场约 4 万，团灭场 run1330 **14.6 万**（站在冰区里）；Overlord's Brand 复制伤害（69189）2–4 万，不是瓶颈。
