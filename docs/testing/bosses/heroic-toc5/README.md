# 英雄冠军的试炼（Trial of the Champion，map 650）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），**隔离 boss 战**，`MasterlessAvoidAoe=1`，策略 `wotlk-toc`。勘察见 [SURVEY](SURVEY.md)。

## 隔离方式

Eadric / Paletress 用 `FixtureSummonCreature` 召到副本召唤点 (746.88, 635.26, 411.7)，跳过大勇士与 9 只 Argent 士兵；`FixtureInstanceData=11:0,11:0,11:0` 把进度置 6。两人都不会死、会投降，用 `KillOnBossSurrender`。竞技场 24 匹坐骑（guid 200014–200037）必须清掉，否则 `wotlk-toc` 会让 bot 去拿枪骑马。

## 结果

| boss | 场景 | 基线 | 时长 |
|---|---|---|---|
| Eadric the Pure | `heroic-toc5-eadric-h5g` | **5/5**，0 死（另冒烟 1/1） | 83–91 秒 |
| Argent Confessor Paletress | `heroic-toc5-paletress-h5g` | 修复前 **0/3**（24%、23%、23%）；修复后 **5/5**（2 死） | 93–115 秒 |
| The Black Knight | 未建 | 借副本事件可建，每个 run 只能打一次 | — |
| Grand Champions | 未建 | 骑乘阶段需要践踏等 bot 逻辑（大改），地面阶段需小框架改动 | BACKLOG 21 |

## Paletress：反射护盾

25% 时她上 Reflective Shield（66515）并召出 Memory。修复前 bot 照打不误，run1211 反射 884 跳、15.2 万伤害，Memory 另打出 29 万。playerbots `647c9c66`：护盾在且 Memory 活着时，打她的 bot 转火 Memory，针对她的攻击/施法权重清零。第一版“护盾在就不打”会僵持：护盾只能靠吸收伤害打破，她每 15–17 秒 Renew，run1223/1224 从 23% 回到满血；改成 Memory 死后回头破盾。
