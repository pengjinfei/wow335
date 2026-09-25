# Boss 验证台账（当前索引）

更新：2026-09-21。这里是跨副本的**当前结果索引**，不是 run 日志。证据、失败时间线和假说只写在链接的 campaign/encounter README；冻结的旧逐 run 台账见 [`archive/BOSS-LEDGER-2026-09-21.md`](archive/BOSS-LEDGER-2026-09-21.md)。状态定义见 [`README.md`](README.md)。

默认基线为 Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none`；凡范围、fixture、预算或二进制不同，均在行内注明，不能混算。

## 当前工作面

| campaign | encounter | 当前证据 | 状态 | 下一步 |
|---|---|---|---|---|
| [英雄岩石大厅](bosses/heroic-hos/README.md) | [Tribunal of Ages](bosses/heroic-hos-tribunal/README.md) | r32 lifecycle **1/5 DONE**（run745）；run746/748/750/751 为有效动态 wipe。Dark Matter fixed cohort **0/4**、retry R1 **0/5**均已关闭；Gaze smoke只闭合执行/时序观测，未验收效果。Holy Shield uptime（2026-09-23）执行门槛通过但效果 cohort **0/5**，已关闭。r35 远程补视线（含 survivor-retry）中间量达标但 cohort **0/5**，已关闭。**装备档 heroic5gear-n5talents-v1（ilvl 200，天赋/雕纹同 normal5）+ r35 + 框架跟随修正：5/10 DONE**（cohort1 2/5 含框架回归 run802；cohort2 3/5），独立记账。上游同步后 cohort3 0/5、cohort4 5/7，**四 cohort 合计 10/22（45%）**；承伤 52% 来自 Protector，其中过半打非坦克（单坦克拿不住多精英仇恨）。Sjonnir 隔离 boss 战 5/5（正常规则续链仍框架阻断）。 | **ilvl 200 档 5/10；normal5 不稳定** | h5g 档继续积累样本，或推广 ilvl 200 档到其他英雄本。 |

run761 是隔离 Dark Matter observation/execution smoke：bot action 与 28237 非零命中均已验到，但其 wipe 永久排除 lifecycle，未推断效果；cohort run762 是合格的首场动态 wipe；run763 是前置超时诊断，未入 cohort 分母；run764 是合格的第2场动态 wipe；其28237伤害为0，未从n=2推断效果；run765 是第二个前置超时诊断，未入 cohort 分母；run766 为合格第3场动态wipe（5 deaths；action 11=8 true/3 false；28237 damage 6,994），n=3不推断效果；run767为第三个preclear timeout diagnostic（1 death/action=0），未入cohort；已定位死亡bot使共同接近预检提前return的前置框架候选；已build survivor-only retry；diagnostic server启动中，run768 smoke在1 death后五次survivor retry并完成前置（171.392秒），终态因roster casualty aborted；执行通过，仍不入Dark Matter cohort；恢复固定原binary后run769为0ms teleport-stage diagnostic，未入cohort；run770重复0ms teleport-stage diagnostic；已定位为`CANNOT_ENTER_TOO_MANY_INSTANCES`；已清五个测试账号instance times；run771为合格动态wipe（12 action，28237伤害5,038），effect cohort为0/4；run772为preclear casualty diagnostic，固定cohort候选预算耗尽且效果未验收；若继续须从clean modules重建单变量版本化binary后，再以零开始的新cohort；clean retry binary曾因ENOSPC失败；空间恢复后两次继续隔离构建，均于链接 `modules/libmodules.a` 因 `No space left on device` 失败；最近一次从约11 GiB可用空间开始、失败后约5.5 GiB，故11 GiB仍不足。其后用户明确授权删除未使用的26 GiB diagnostic build及14 GiB非live debug build（live server仍来自`var/build/obj`），可用空间约45 GiB；clean retry binary已成功构建、marker/provenance及ready/IDLE启动门已通过；排除样本run773（451.525秒/5 deaths wipe）以8 action（7 true/1 false）及28237→roster非零4,628闭合新binary action+hit gate。已预声明Dark Matter+survivor-retry R1 effect cohort；R1已关闭：run774–778均为合格动态5-death wipe（action=8/10/10/13/4；28237 roster damage=9,510/0/0/558/0）；仅run777 boss_hp_min=76%，故R1为**0/5 DONE**且效果未验收，不混入旧fixed cohort或smoke。Tribunal 的当前增量与诊断边界见 [`HANDOVER-2026-09-21-HOS-TRIBUNAL.md`](HANDOVER-2026-09-21-HOS-TRIBUNAL.md)。

## 5 人 campaign 矩阵

| 副本 / campaign README | encounter | 当前结果与范围 | 状态 |
|---|---|---|---|
| [乌特加德城堡](bosses/heroic-uk/MECHANICS-AUDIT.md) | [凯雷塞斯](bosses/heroic-uk-keleseth/README.md) | 完整遭遇战，run322 4 kill、0 wipe、零死亡；冰墓实际被全队转火。 | **完成** |
| 同上 | [斯卡瓦尔德&达隆](bosses/heroic-uk-skarvald-dalronn/README.md) | 完整遭遇战（10 前置 + 双 boss），run323 5/5、零死亡。 | **完成** |
| 同上 | [因格瓦尔](bosses/heroic-uk-ingvar/README.md) | 隔离 boss 战当前构建累计 22/30 kill（73%，CI 56–86%）；不能等同完整副本。 **ilvl 200 档：10/10 kill**（上游同步前 5/5、后 5/5）。 | **完成（ilvl 200 档口径，2026-09-25 用户确认）；normal5 73%** |
| [魔枢](bosses/heroic-nexus/FIXTURE-SURVEY.md) | [泰蕾斯特拉](bosses/heroic-nexus-telestra/README.md) | 完整链路已有击杀；run409 控制链 3 kill、2 作废。 **ilvl 200 档：5/5 kill、0 死**。 | **当前配置击杀** |
| 同上 | [阿诺姆鲁斯](bosses/heroic-nexus-anomalus/README.md) | 正常规则；300s 档 9/10，420s 档 4/5（不同预算 cohort）。 | **完成** |
| 同上 | [奥莫洛克](bosses/heroic-nexus-ormorok/README.md) | 完整链路 6/8，0 boss-stage wipe；2 场清怪减员。 **ilvl 200 档：5/5 kill、1 死**。 | **当前配置击杀** |
| 同上 | [凯利丝塔萨](bosses/heroic-nexus-keristrasza/README.md) | 隔离形态（三球体 DONE fixture）run422 5/5、零死亡；端到端链式未验。 | **稳定击杀（隔离）** |
| [艾卓-尼鲁布](bosses/heroic-an/README.md) | [阿努巴拉克](bosses/heroic-an-anubarak/README.md) | 完整遭遇战有 kill；历史优化与共享层证据见 README。 **ilvl 200 档：53 kill / 61 启动（87%）**；失败为 7 次潜地期间全员脱战致 boss 复位（`SelectVictim` 无目标 evade，战斗引用断开原因未找到，最近 20 场未复现）+ 1 次超时；躲 AoE 无收益。 | **调查中** |
| 同上 | [哈多诺克斯](bosses/heroic-an-hadronox/README.md) | 完整遭遇（召唤物开怪 + 实例状态确认），ilvl 200 档 + MasterlessAvoidAoe + 坦克离云 + 克里克希尔节点作用域修正：**5/5、0 死，144–189 秒**（run915–919）。此前各 cohort 在 DPS 被克里克希尔节点劫持下测得，已作废。 | **稳定击杀（ilvl 200 档）** |
| 同上 | [克里克希尔](bosses/heroic-an-krikthir/README.md) | 完整遭遇（含 9 只前置守望者）。ilvl 200 档 + 开怪门禁 `PrerequisiteRepullDelaySeconds=20`（raidtest `4790175`）：**17/20 启动 kill**（run950–982，原 15/30）；进入 boss 战后全部击杀。剩余中止为全员脱战时 boss 自身 evade。 | **基本稳定（ilvl 200 档）** |
| [达克萨隆要塞](bosses/heroic-dtk-trollgore/README.md) | Trollgore / [Novos](bosses/heroic-dtk-novos/README.md) / [Tharon'ja](bosses/heroic-dtk-tharonja/README.md) / [King Dred](bosses/heroic-dtk-dred/README.md) | 四 boss 均已有正常规则隔离 boss 战通过；Dred 经共享 LOS 修复后 15/16。 | **完成（boss 机制口径）** |
| [古达克](bosses/heroic-gd/README.md) | [斯拉德兰](bosses/heroic-gd-sladran/README.md) | 隔离 boss 战合并后 3/5；平台阵位 0/5 已回退。 **ilvl 200 档：10/10 kill、0 死**（上游同步前 5/5、后 5/5）。 | **完成（ilvl 200 档口径，2026-09-25 用户确认）；normal5 不稳定** |
| 同上 | [莫拉比](bosses/heroic-gd-moorabi/README.md) | 完整遭遇；旧 cohort 16/20，当前局部修复 run685 5/5、零死；不可与旧样本合并称稳定。 **ilvl 200 档：5/5 kill、0 死**。 | **当前配置击杀** |
| 同上 | [德拉克瑞巨像](bosses/heroic-gd-colossus/README.md) | 隔离 boss 战 5/5、零死亡；移除了非机制常驻单位，原生 Mojo 链保留。 | **稳定击杀（隔离）** |
| 同上 | [迦尔达拉](bosses/heroic-gd-galdarah/README.md) | 隔离 boss 战累计 10/10、零死亡；载具移除后骑手仍可能参战，范围已如实记录。 | **稳定击杀（隔离）** |
| 同上 | [凶残的艾克](bosses/heroic-gd-eck/README.md) | 正常规则原生召唤链累计有效 10/10 kill、零死；无 DB spawn 的框架问题已另行记录。 | **完成（boss 机制口径）** |
| [安卡赫特：古代王国](bosses/heroic-ak/README.md)（my-mac） | 纳多克斯 / 塔达拉姆 / 耶戈达 / 阿曼尼塔 / 沃拉兹 | **仅 ilvl 200 档**（用户指定）：纳多克斯 **10/10、0 死**；沃拉兹 **10/10、0 死**；阿曼尼塔 boss 阶段 6/6 kill（含坦克修复前 4 场），但清怪不稳，已定位并修复坦克被被动蘑菇勾走（共享层，待回归）；塔达拉姆场景未打通（清怪路线/连通性）；耶戈达未建（开场信徒是召唤物，需框架支持）。 | **调查中** |
| [闪电大厅](bosses/heroic-hol/README.md) | Bjarngrim / Volkhan / Ionar / Loken | **仅 ilvl 200 档**：Bjarngrim **5/5**（0 死，核心脚本副官重召死循环已修 `4048589b3`）、Volkhan **5/5**（0 死）、Ionar **5/5**（0 死）、Loken **5/5**（1 死），均隔离 boss 战、机制已核对触发。 | **完成（ilvl 200 档）** |
| [乌特加德之巅](bosses/heroic-up/README.md) | Svala / Gortok / Skadi / Ymiron | **仅 ilvl 200 档**：Svala **5/5**（1 死，AT 开战+走到开怪点）、Gortok **5/5**（0 死，宝珠开战）、Ymiron **4/5**（Bane 修复后，隔离）；Skadi **跳过待确认**（需 bot 鱼叉链，BACKLOG 14）。 | **3/4 完成（ilvl 200 档）** |
| [灵魂洪炉](bosses/heroic-fos/README.md) | Bronjahm / Devourer of Souls | **仅 ilvl 200 档**：Bronjahm **0/3**（最好 25%：二阶段碎片回血 34%→61%，BACKLOG 16）、Devourer **0/2**（最好 22%：哀嚎之魂站位，BACKLOG 17）；均**跳过待确认**。 | **未通过（跳过待确认）** |
| [萨隆矿坑](bosses/heroic-pos/README.md) | Garfrost / Ick / Tyrannus | **仅 ilvl 200 档**：Garfrost **1/3**（不驱散永冻+远程躲岩石后首杀；近战/坦克叠层仍致死，BACKLOG 19）；Ick 开怪失败 **跳过待确认**（载具 boss，BACKLOG 18）；Tyrannus 未建场景（载具乘客 + AT 开战 + Rimefang，见 SURVEY）。 | **未通过（跳过待确认）** |
| [紫罗兰监狱](bosses/heroic-vh/README.md) | Moragg / Erekem / Ichoron / Lavanthor / Xevozz / Zuramat / Cyanigosa | **仅 ilvl 200 档，隔离（夹具放出牢房 boss）**：Ichoron / Lavanthor / Moragg / Erekem / Zuramat 各 **5/5**（0 死），Xevozz **4/5**；Cyanigosa 未建（第 18 波才出现）。 | **6/7 完成（ilvl 200 档，隔离）** |
| [净化斯坦索姆](bosses/heroic-cos/README.md) | Meathook / Salramm / Epoch / Mal'Ganis / Infinite Corruptor | **仅 ilvl 200 档，隔离（夹具召出，跳过护送与波次）**：五个 boss 各 **5/5**（0 死）；Mal'Ganis 用投降判据。 | **完成（ilvl 200 档，隔离）** |
| [岩石大厅](bosses/heroic-hos/README.md) | Krystallus / [Maiden](bosses/heroic-hos-maiden/README.md) / [Tribunal](bosses/heroic-hos-tribunal/README.md) / [Sjonnir](bosses/heroic-hos-sjonnir/README.md) | Krystallus 5/5（总2 death，证据边界）；Maiden 隔离 5/5（1 death）；Tribunal r32 1/5 DONE、未完成；Sjonnir **隔离 boss 战 5/5**（fixture 预置 Tribunal DONE+开门；正常规则续链仍框架阻断）；Tribunal ilvl 200 档 5/10。 | **完成（boss 机制口径；Maiden/Sjonnir 隔离，Tribunal 需 ilvl 200 档）** |

## 团队副本 / 非当前队列

| campaign | 当前结论 | 状态 |
|---|---|---|
| Naxxramas：Loatheb / Patchwerk | Loatheb 仅 fixture 编排历史证据；Patchwerk 待固定 roster/正常规则基线。 | **待审计** |

## 口径规则

- “完成”只指本表写明的 campaign 验收范围；当前五人线一般是独立 boss 机制验证，**不是整本自主全清**。
- 隔离、fixture、不同 roster、预算、装备或 binary 的样本单独分 cohort；不得合并成击杀率。
- `kill` 必须由 encounter 的真实完成条件确认；运行中 `aborted/0` 只是占位，不能计结果。
- 新 boss/团队 campaign 依 [`CAMPAIGN-TEMPLATE.md`](CAMPAIGN-TEMPLATE.md) 建副本矩阵，依 [`BOSS-TEMPLATE.md`](BOSS-TEMPLATE.md) 建 encounter 证据记录。
