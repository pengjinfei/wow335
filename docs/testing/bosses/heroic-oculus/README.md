# 英雄魔环（The Oculus，map 578）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），`MasterlessAvoidAoe=1`，策略 `wotlk-occ`。勘察见 [SURVEY](SURVEY.md)。

| boss | 场景 | 形态 | 基线 | 时长 |
|---|---|---|---|---|
| Drakos the Interrogator | `heroic-oc-drakos-h5g` | 完整（地面，90 码内无敌对怪） | **5/5**（1 死；另 1 次开怪失败 run1214） | 76–111 秒 |
| Varos Cloudstrider | `heroic-oc-varos-h5g` | **地面隔离（非设计形态）**：`FixtureInstanceData` 写 10 次 `5:3` 满足构造体门禁，清掉平台 80 码内的 Azure Ring Guardian | **5/5**，0 死 | 45–48 秒 |
| Mage-Lord Urom | `heroic-oc-urom-h5g` | **隔离**：跳过三个外环台（原设计骑龙），`0:3,1:3` 解门禁，清掉 DB Urom、在内环点召一只（脚本判为阶段 3） | **5/5**，0 死 | 55–75 秒 |
| Ley-Guardian Eregos | `heroic-oc-eregos-h5g` | 龙背战（设计形态）：bot 无 master 自行上龙、飞行、开怪（`EngageTrigger=self`） | **0/9**，最好 37%（BACKLOG 20） | — |

- Drakos 的 Unstable Sphere 伤害（50759）每场都有（40 跳级别）。
- Urom 的 Frostbomb、Time Bomb、传中心 + Empowered Arcane Explosion 都放了；爆炸没打到人（bot 策略的内环安全点挡住了视线）。
- Varos 的 Energize Cores 锥形每场都在放（触发法术 54069/56251 各 7 次），但 bot 站位恰好不在扫过的象限里，没有吃到 50785 伤害；设计上的龙战没有验证。
