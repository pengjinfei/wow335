# 英雄闪电大厅（Halls of Lightning，map 602）/ campaign

口径：ilvl 200 档（`mod-raidtest-roster-heroic5gear-n5talents-v1.conf`，天赋/雕文/补给同 normal5-v1），英雄难度、5 人、`BotCheats=""`；隔离 boss 战（不连续通关）。勘测见 [SURVEY.md](SURVEY.md)：四个 boss 均无 HARD_RESET、无前置 boss 要求、无 boss 边界；策略键 `wotlk-hol`。

## Encounter 矩阵

| encounter | 场景 | 当前结论 | 状态 | 下一步 |
|---|---|---|---|---|
| General Bjarngrim | `heroic-hol-bjarngrim-h5g` | **5/5 kill、0 死，63–75 秒**（run1073–1077，核心修复后）；三种姿态各切换 1–1.6 次/场，两只副官参战 | **完成（ilvl 200 档）** | — |
| Volkhan | `heroic-hol-volkhan-h5g` | **5/5 kill、0 死，42–51 秒**（run1061–1065）；Temper 2/场、Heat 1.4/场、Shattering Stomp 1/场、Molten Golem Blast Wave 10.6/场 | **完成（ilvl 200 档）** | — |
| Ionar | `heroic-hol-ionar-h5g` | **5/5 kill、0 死，112–132 秒**（run1066–1070）；每场分裂 1 次，Spark 伤害约 90 次/场 | **完成（ilvl 200 档）** | — |
| Loken | `heroic-hol-loken-h5g` | **5/5 kill、1 死，73–82 秒**（run1051–1055）；Pulsing Shockwave 约 215 次/场、Lightning Nova 5.6/场、Arc Lightning 12/场 | **完成（ilvl 200 档）** | — |

冒烟（不计入基线）：Bjarngrim run1071 因核心脚本死循环中止、run1072 修复后 kill（76 秒、0 死）；Loken run1046 kill（88 秒、1 死）；Ionar run1049 kill（133 秒、0 死）；Volkhan run1050 kill（84 秒、0 死）。

## 场景要点

- **Loken**：45 码内无小怪，不设前置；无前置时队伍停在准备点开怪，故准备点即开怪点 (1160,34,60.73)（los 实测、距 26.5 码）。
- **Volkhan**：初版准备点 (1308,-137,52.02) 在下层，bot 传送落地即死且**没有任何伤害或死亡事件**（run1057–1060：牧师尸体恰在准备点，法师死后释放灵魂回诺森德墓地 map 571），疑为熔岩/坠落环境致死。现版不设前置、准备点=上层开怪点 (1320,-123,56.71)，西侧三只与南环巡逻编队全部夹具移除（非机制单位）。
- **Ionar**：两只 Stormfury Revenant 与一只巡逻 Storming Vortex 离开怪点 3–11 码，作前置先清。分裂时 playerbots HoL 策略把全队拉到 `DISPERSE_POSITION` (1161,-261.6,53.2)，那里有一堆怪（5 Cyclone + Vortex + Revenant）；正常通关路线上这堆怪在到达 Ionar 前已清，场景以夹具移除代表“已清”。**策略缺陷如实记录**：若那堆怪存在，分裂会把全队带进怪堆。

## 本轮框架修正（raidtest `73cc994`）

- 下线前复活死亡 bot：以鬼魂下线的角色下一场复活不生效（穿装备报 `EQUIP_ERR_YOU_ARE_DEAD`，run1048）。
- 开场核对每名成员存活且在场景地图上，否则 `scene_invalid` 并写明角色与地图（此前那行“all N bot(s) on map”只打印人数，run1047 法师在 7850 码外的墓地）。
- 恢复阶段只等本场有死亡记录的成员复活；无记录的死亡直接判场景无效（见 BACKLOG 12、13）。

## 核心脚本缺陷：Bjarngrim 副官无限重召（core `4048589b3`）

- **现象**：run1071 开怪后框架报 `pull failed (tank did not establish aggro)`；事件显示 Bjarngrim 每秒约 95 次 Battle Stance（53792）、副官 29240 以新 GUID 每秒约 165 次交战。
- **根因**：`boss_bjarngrim::UpdateAI` 在 `UpdateVictim()` 失败时调用 `Reset()`，而 `Reset()` 会收回并重召两只副官、重上战斗姿态。副官先于 boss 交战（离队伍 10–16 码）时 boss 处于战斗却无目标，于是每个 update 都重召副官，新副官立即再交战，永不结束。真人先惹副官同样触发。
- **修复**：无目标时直接 `return`；真正的 evade 经 `EnterEvadeMode` 本就会调用 `Reset()`。按用户授权在核心 fork 修（见 memory server-bugs-fix-in-core-fork）。修后冒烟 kill，Battle Stance 全场 2 次。
- **场景**：Bjarngrim 为 escortAI 无限巡逻，但每场 ResetInstance 把他放回南台出生点；不设前置、准备点=开怪点 (1262,-3,33.51)，传送后立即开怪；南台 6 只小怪夹具移除，副官保留。
