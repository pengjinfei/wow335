# 英雄冠军的试炼（Trial of the Champion，map 650）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），**隔离 boss 战**，`MasterlessAvoidAoe=1`，策略 `wotlk-toc`。勘察见 [SURVEY](SURVEY.md)。

## 隔离方式

Eadric / Paletress 用 `FixtureSummonCreature` 召到副本召唤点 (746.88, 635.26, 411.7)，跳过大勇士与 9 只 Argent 士兵；`FixtureInstanceData=11:0,11:0,11:0` 把进度置 6。两人都不会死、会投降，用 `KillOnBossSurrender`。竞技场 24 匹坐骑（guid 200014–200037）必须清掉，否则 `wotlk-toc` 会让 bot 去拿枪骑马。

## 结果

| boss | 场景 | 基线 | 时长 |
|---|---|---|---|
| Eadric the Pure | `heroic-toc5-eadric-h5g` | **5/5**，0 死（另冒烟 1/1） | 83–91 秒 |
| Argent Confessor Paletress | `heroic-toc5-paletress-h5g` | 修复前 **0/3**（24%、23%、23%）；修复后 **5/5**（2 死） | 93–115 秒 |
| The Black Knight | `heroic-toc5-blackknight-h5g` | **5/5**（3 死）：`1:3,6:0` 走副本自己的事件（狮鹫落地、杀播报员、自行进战），战斗本体按正常规则；三阶段、两次假死都走到 | 107–115 秒 |
| Grand Champions（地面阶段） | `heroic-toc5-champions-ground-h5g` | **6/6**（run1323–1328，0 死，102–111 秒）；骑乘阶段未做 | 地面阶段完成（隔离）；骑乘阶段 BACKLOG 21 |

## Paletress：反射护盾

25% 时她上 Reflective Shield（66515）并召出 Memory。修复前 bot 照打不误，run1211 反射 884 跳、15.2 万伤害，Memory 另打出 29 万。playerbots `647c9c66`：护盾在且 Memory 活着时，打她的 bot 转火 Memory，针对她的攻击/施法权重清零。第一版“护盾在就不打”会僵持：护盾只能靠吸收伤害打破，她每 15–17 秒 Renew，run1223/1224 从 23% 回到满血；改成 Memory 死后回头破盾。

## Grand Champions 地面阶段（隔离）

- 夹具：`FixtureInstanceData = 7:2,8:0×12` 把进度推到 5（骑乘阶段结束、地面阶段待开），不产生冠军和小怪，顺带 despawn 24 匹坐骑；再用 `FixtureSummonCreature` 在两侧召固定组合的战士 35572 / 萨满 35571 / 法师 35569（召出时 `Reset()` 的 progress==5 分支自行去掉不可攻击并置主动）。
- 完成判据：新框架键 `KillOnInstanceData = 4:6`（raidtest `049620f`）——第三只冠军投降时副本置 progress 6。只看绑定的战士会在他先投降时误判。
- 结果：6 场全杀，0 死；三只冠军都有输出（run1323：法师 6.3 万、萨满 4.7 万、战士 13.5 万）。
- 口径：跳过骑乘阶段（正常规则下不可跳过），只证明地面三冠军战。骑乘阶段需要 bot 驾驶、按距离选目标、践踏步行冠军并让三只同时下马，属大改，BACKLOG 21 待确认。
