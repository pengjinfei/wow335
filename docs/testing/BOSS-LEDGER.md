# Boss 验证台账（当前索引）

更新：2026-09-21。这里是跨副本的**当前结果索引**，不是 run 日志。证据、失败时间线和假说只写在链接的 campaign/encounter README；冻结的旧逐 run 台账见 [`archive/BOSS-LEDGER-2026-09-21.md`](archive/BOSS-LEDGER-2026-09-21.md)。状态定义见 [`README.md`](README.md)。

默认基线为 Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none`；凡范围、fixture、预算或二进制不同，均在行内注明，不能混算。

## 当前工作面

| campaign | encounter | 当前证据 | 状态 | 下一步 |
|---|---|---|---|---|
| [英雄岩石大厅](bosses/heroic-hos/README.md) | [Tribunal of Ages](bosses/heroic-hos-tribunal/README.md) | r32 lifecycle **1/5 DONE**（run745）；run746/748/750/751 为有效动态 wipe。Sjonnir 已因同实例前置后的无自主路线、且 raidtest 不可代移而跳过（无战斗样本）。 | **调查中** | 仅在新的单一、可观测证据支持假说下重启 Tribunal 调查；r34 继续排除 lifecycle。 |

run761 是隔离 Dark Matter observation/execution smoke：bot action 与 28237 非零命中均已验到，但其 wipe 永久排除 lifecycle，未推断效果；server 已恢复 r32、ready/IDLE。Tribunal 的当前增量与诊断边界见 [`HANDOVER-2026-09-21-HOS-TRIBUNAL.md`](HANDOVER-2026-09-21-HOS-TRIBUNAL.md)。

## 5 人 campaign 矩阵

| 副本 / campaign README | encounter | 当前结果与范围 | 状态 |
|---|---|---|---|
| [乌特加德城堡](bosses/heroic-uk/MECHANICS-AUDIT.md) | [凯雷塞斯](bosses/heroic-uk-keleseth/README.md) | 完整遭遇战，run322 4 kill、0 wipe、零死亡；冰墓实际被全队转火。 | **完成** |
| 同上 | [斯卡瓦尔德&达隆](bosses/heroic-uk-skarvald-dalronn/README.md) | 完整遭遇战（10 前置 + 双 boss），run323 5/5、零死亡。 | **完成** |
| 同上 | [因格瓦尔](bosses/heroic-uk-ingvar/README.md) | 隔离 boss 战当前构建累计 22/30 kill（73%，CI 56–86%）；不能等同完整副本。 | **调查中** |
| [魔枢](bosses/heroic-nexus/FIXTURE-SURVEY.md) | [泰蕾斯特拉](bosses/heroic-nexus-telestra/README.md) | 完整链路已有击杀；run409 控制链 3 kill、2 作废。 | **当前配置击杀** |
| 同上 | [阿诺姆鲁斯](bosses/heroic-nexus-anomalus/README.md) | 正常规则；300s 档 9/10，420s 档 4/5（不同预算 cohort）。 | **完成** |
| 同上 | [奥莫洛克](bosses/heroic-nexus-ormorok/README.md) | 完整链路 6/8，0 boss-stage wipe；2 场清怪减员。 | **当前配置击杀** |
| 同上 | [凯利丝塔萨](bosses/heroic-nexus-keristrasza/README.md) | 隔离形态（三球体 DONE fixture）run422 5/5、零死亡；端到端链式未验。 | **稳定击杀（隔离）** |
| [艾卓-尼鲁布](bosses/heroic-an/README.md) | [阿努巴拉克](bosses/heroic-an-anubarak/README.md) | 完整遭遇战有 kill；历史优化与共享层证据见 README。 | **调查中** |
| 同上 | [哈多诺克斯](bosses/heroic-an-hadronox/README.md) | 隔离形态基线 0/5；完整前置含 spawnId=0 召唤物，框架尚不能表达。 | **框架阻断 / 策略待审计** |
| 同上 | [克里克希尔](bosses/heroic-an-krikthir/README.md) | 完整遭遇战有一次 kill；清怪稳定性未验。 | **调查中** |
| [达克萨隆要塞](bosses/heroic-dtk-trollgore/README.md) | Trollgore / [Novos](bosses/heroic-dtk-novos/README.md) / [Tharon'ja](bosses/heroic-dtk-tharonja/README.md) / [King Dred](bosses/heroic-dtk-dred/README.md) | 四 boss 均已有正常规则隔离 boss 战通过；Dred 经共享 LOS 修复后 15/16。 | **完成（boss 机制口径）** |
| [古达克](bosses/heroic-gd/README.md) | [斯拉德兰](bosses/heroic-gd-sladran/README.md) | 隔离 boss 战合并后 3/5；平台阵位 0/5 已回退。 | **调查中** |
| 同上 | [莫拉比](bosses/heroic-gd-moorabi/README.md) | 完整遭遇；旧 cohort 16/20，当前局部修复 run685 5/5、零死；不可与旧样本合并称稳定。 | **当前配置击杀** |
| 同上 | [德拉克瑞巨像](bosses/heroic-gd-colossus/README.md) | 隔离 boss 战 5/5、零死亡；移除了非机制常驻单位，原生 Mojo 链保留。 | **稳定击杀（隔离）** |
| 同上 | [迦尔达拉](bosses/heroic-gd-galdarah/README.md) | 隔离 boss 战累计 10/10、零死亡；载具移除后骑手仍可能参战，范围已如实记录。 | **稳定击杀（隔离）** |
| 同上 | [凶残的艾克](bosses/heroic-gd-eck/README.md) | 正常规则原生召唤链累计有效 10/10 kill、零死；无 DB spawn 的框架问题已另行记录。 | **完成（boss 机制口径）** |
| [岩石大厅](bosses/heroic-hos/README.md) | Krystallus / [Maiden](bosses/heroic-hos-maiden/README.md) / [Tribunal](bosses/heroic-hos-tribunal/README.md) / [Sjonnir](bosses/heroic-hos-sjonnir/README.md) | Krystallus 5/5（总2 death，证据边界）；Maiden 隔离 5/5（1 death）；Tribunal r32 1/5 DONE、未完成；Sjonnir 因正常规则同实例续链无自主路线而跳过、无战斗样本。 | **未完成** |

## 团队副本 / 非当前队列

| campaign | 当前结论 | 状态 |
|---|---|---|
| Naxxramas：Loatheb / Patchwerk | Loatheb 仅 fixture 编排历史证据；Patchwerk 待固定 roster/正常规则基线。 | **待审计** |

## 口径规则

- “完成”只指本表写明的 campaign 验收范围；当前五人线一般是独立 boss 机制验证，**不是整本自主全清**。
- 隔离、fixture、不同 roster、预算、装备或 binary 的样本单独分 cohort；不得合并成击杀率。
- `kill` 必须由 encounter 的真实完成条件确认；运行中 `aborted/0` 只是占位，不能计结果。
- 新 boss/团队 campaign 依 [`CAMPAIGN-TEMPLATE.md`](CAMPAIGN-TEMPLATE.md) 建副本矩阵，依 [`BOSS-TEMPLATE.md`](BOSS-TEMPLATE.md) 建 encounter 证据记录。
