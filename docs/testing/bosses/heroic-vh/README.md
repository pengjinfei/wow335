# 英雄紫罗兰监狱（Violet Hold，map 608）

> 2026-09-26，ilvl 200 档（`heroic5gear-n5talents-v1`），隔离 boss 战，`MasterlessAvoidAoe=1`。勘察见 [SURVEY](SURVEY.md)。

## 隔离方式

牢房 boss 随机抽进副本持久数据槽 0/1，由 Azure Saboteur 在第 6/12 波调用 `DoAction(ACTION_RELEASE_BOSS=3)` 放出。raidtest `12711a0` 新增两个通用夹具键：`FixturePersistentData = 1:<BOSS_* 3..8>` 写槽 1，`FixtureInstanceAction = 3` 放出（波数为 0 时放槽 1）。开怪点 = boss 放出落点往房间中央 10 码。隔离形态，没有传送门波次，结论口径降级。

同批修了两个框架问题：
- 开怪重试时整段开场（事件总线、夹具）每 tick 重跑，`DoAction` 被反复重发，重试预算也不累计（run1140）。改为只做一次开场（`12711a0`）。
- 全员阵亡后 bot 在副本外灵魂医者处复活、boss 脱战后整体重生，团灭判据凑不齐，run1166 记成 480 秒超时。改为“有过死亡且每人都已死或不在场景地图”即判团灭（`2301862`）。

## 结果

| boss | 场景 | 基线 | 时长 | 机制核对 |
|---|---|---|---|---|
| Ichoron | `heroic-vh-ichoron-h5g` | **5/5**，0 死（另 1 次开怪失败 run1148） | 100–162 秒 | Ichor Globule 64 只 |
| Lavanthor | `heroic-vh-lavanthor-h5g` | **5/5**，0 死 | 49–53 秒 | — |
| Moragg | `heroic-vh-moragg-h5g` | **5/5**，0 死 | 42–47 秒 | Optic Link 等技能正常施放 |
| Erekem | `heroic-vh-erekem-h5g` | **5/5**，0 死 | 52–69 秒 | 2 名 Erekem Guard 参战 |
| Xevozz | `heroic-vh-xevozz-h5g` | **4/5**（run1166 团灭，5 人 50–54 秒内阵亡） | 57–59 秒 | Ethereal Sphere 召出 |
| Zuramat | `heroic-vh-zuramat-h5g` | **5/5**，0 死 | 46–55 秒 | 虚空球召出 |
| Cyanigosa | `heroic-vh-cyanigosa-h5g` | **6/6**（run1364–1369） | 0 死，72–85 秒 | 隔离：房间中央直接召出（见下） |

- run1148 开怪失败：boss 进战后 8 秒内目标不是坦克，疑为门口友方守卫与放出的 boss 互殴（勘察已提示），6 个 boss 共 31 次开战中只此 1 次。
- Xevozz 的团灭是英雄模式 Ethereal Sphere 与 boss 合体叠 Arcane Power，bot 没有风筝球的逻辑（勘察记为缺口）。

## Cyanigosa（隔离）

- 原流程：第 18 波 Sinclari 召出、跳到房间中央 (1892.29, 805.70, 38.44)，10 秒后施 58668（光环 56，只换模型），再 2.5 秒去 `NON_ATTACKABLE`。
- 场景：`FixtureSummonCreature` 在房间中央召出（夹具同样去掉不可攻击/免疫并置主动），少了换模型；script 模式、pull 开战。跳过 18 波与两个牢房 boss。
- 技能都出现了：Arcane Vacuum 58694（拉人 + 清仇恨）、英雄 Mana Destruction 59374、Blizzard、Tail Sweep、Uncontrollable Energy。
- 第一次冒烟开怪点 z 配成 37，bot 站到地板下看不到 boss（run1363 `pull failed`）；los 探针实测地面 38.65 后修正。
