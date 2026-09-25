# 英雄净化斯坦索姆（Culling of Stratholme，map 595）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），**隔离 boss 战**，`MasterlessAvoidAoe=1`。勘察见 [SURVEY](SURVEY.md)。
> 五个 boss 都没有 DB spawn，原本由 Arthas 护送事件（或副本脚本）召出。这里全部跳过护送、小怪波次和 Arthas 协助，只验证 boss 本身的机制，结论口径降级。

## 隔离方式（raidtest）

- `31f5eed`：`BossSpawnMode=script` 不再强制要求前置怪；没有前置时直接进恢复阶段，等夹具召出的 boss 出现后绑定。
- `fdd3bb0`：`FixtureSummonCreature = <entry>:<x>,<y>,<z>,<o>` 把 boss 召到事件召唤点，并补上事件最后一步（解除剧情免疫、去 NON_ATTACKABLE、REACT_AGGRESSIVE；Epoch 模板带 IMMUNE_TO_PC|IMMUNE_TO_NPC，run1184/1185 不补这步开不了怪）。
- `fdd3bb0`：`KillOnBossSurrender = 1`：Mal'Ganis 不会死（致命伤害置 0 → 免疫、NON_ATTACKABLE、施放奖励法术后 evade），最低血量 ≤ 10% 且不可攻击即判击杀。
- 准备点都放在 boss 正面 25–40 码：Infinite Corruptor 召出瞬间 12 码内有 bot 会当场进战（run1175）。

## 结果

| boss | 场景 | 召出方式 | 基线 | 时长 |
|---|---|---|---|---|
| Infinite Corruptor（仅英雄） | `heroic-cos-corruptor-h5g` | `FixtureInstanceData=4:1`（副本脚本召唤），清掉身边 7 只 Risen Zombie | **5/5**，0 死 | 42–47 秒 |
| Meathook | `heroic-cos-meathook-h5g` | `FixtureSummonCreature` | **5/5**，0 死 | 47–51 秒 |
| Salramm the Fleshcrafter | `heroic-cos-salramm-h5g` | `FixtureSummonCreature` | **5/5**，0 死 | 47–71 秒 |
| Chrono-Lord Epoch | `heroic-cos-epoch-h5g` | `FixtureSummonCreature` + 解除免疫 | **5/5**，0 死 | 52–59 秒 |
| Mal'Ganis | `heroic-cos-malganis-h5g` | `FixtureSummonCreature` + `KillOnBossSurrender` | **5/5**，0 死 | 50–59 秒 |

## bot 侧

- playerbots `8158b1d8`：Salramm 的 `ExplodeGhoulTrigger` 比对的是 `NPC_RISEN_GHOUL`（26125，死亡骑士宠物），永远不触发，改成 Ghoul Minion 27733。Explode Ghoul（52480）是瞬发，而这套逻辑扫的是尸体，躲法本身是否有效未验证。
- 完整档（带护送、波次与 Arthas 协助）未做：Meathook/Salramm 前面各有 4 组分散的召唤小怪，Epoch 需要跟随 Arthas 打市政厅三场裂隙，都需要“跟随护送 NPC”的编排能力。
