# Campaign：英雄 安卡赫特：古代王国（Ahn'kahet: The Old Kingdom / map 619）

> 本文件是副本级索引；逐次实验写进各 encounter README（尚未拆分，首轮事实暂记于此）。
> 运行机：**my-mac**（第二台开发机，run id 从 100000 起），2026-09-25 起。

## 固定边界

| 字段 | 值 |
|---|---|
| campaign key | `heroic-ak` |
| map / 难度 | `619 / heroic` |
| roster 与装备档 | `heroic5gear-n5talents-v1`（ilvl 200，天赋/雕纹/补给同 normal5-v1；**用户指定**），场景后缀 `-h5g` |
| cheat / fixture | `BotCheats=""`；无 fixture |
| 验收目标 | per-boss（boss 机制口径，不是整本自主全清） |
| 二进制/配置边界 | my-mac 构建：core `69f271af6` / playerbots `aabfd58f` / raidtest `61f345d`；场景模板/观察 raidtest `mymac/dev` `a1f9749`；playerbots `mymac/tank-skip-passive` `65862743` → `mymac/ak-amanitar-mushroom` `62af45c0`（均只在 my-mac，未推送） |
| 策略 | `wotlk-ok`（`getName()` 与 Context 键一致，`RuntimeStrategyName` 无需映射） |

## Encounter 矩阵

| encounter | scenario | 范围 | 当前状态 | 下一步 |
|---|---|---|---|---|
| 纳多克斯长老 29309 | `heroic-ak-nadox-h5g` | 平台 + 蛋厅 6 只虫群前置 | **10/10 kill、0 死**（run100005–100006、100008–100014、100018；63.2–76.8 秒） | 完成（ilvl 200 档） |
| 塔达拉姆王子 29308 | `heroic-ak-taldaram-h5g` | 中央大厅 + 两个装置高台（25 只前置 + 两个装置） | v1 run100015 清怪期团灭；v2 run100020 清怪 600 秒超时 | 查清大厅与下层走廊的连通性（见下） |
| 耶戈达·寻影者 29310 | — | — | **未建**：开场的 15 个暮光信徒是脚本召唤物，无 DB spawn，`PrerequisiteSpawns` 指不到 | 需要 raidtest 支持「按 entry+半径 的前置怪」，要编译 |
| 阿曼尼塔 30258（仅英雄） | `heroic-ak-amanitar-h5g` | v4：洞穴 4 只洞穴兽前置 + `ObserveAuras` | v3 boss 阶段 **4/4 kill**、清怪 6 次失败；坦克修复后（v4）boss 阶段 **2/2 kill**，清怪 3 次失败，轮次被用户中止 | 清怪稳定性；编蘑菇策略 `62af45c0` 做第二变量；坦克修复回归纳多克斯/沃拉兹 |
| 传令官沃拉兹 29311 | `heroic-ak-volazj-h5g` | 房间 + 走廊两只巡逻被遗忘者前置 | **10/10 kill、0 死**（run100017、100021–100026、100028、100029、100031；188–230 秒；两次疯狂均出现，扭曲幻象造成伤害）；run100027 作废（准备点距 boss 实际位置仅 16.49 码） | 完成（ilvl 200 档）；再跑前把准备点南移到 30 码外 |

作废样本：run100007（my-mac 系统睡眠 11 分钟，timeout 636.9 秒），不入任何分母。

## 共用场景事实

- **vmap 地面**：纳多克斯平台、耶戈达、阿曼尼塔一带 `raidtest los` 的 `vmap_floor` 返回 -200000（静态 vmap 树里查不到地面），z 只能取 spawn 高度；塔达拉姆大厅、装置圆台、沃拉兹房间能实测。
- **HARD_RESET**：耶戈达、沃拉兹带 `flags_extra 0x80000000`；raidtest `ResolveOrRestoreSpawn` 已处理（沃拉兹冒烟正常）。
- **纳多克斯**：`EVENT_CHECK_HOME` 在 z<24 或离家 >110 码时上 Enrage；平台外走廊 z≈23，boss 不能被拖出平台。
- **塔达拉姆机关**：两个古代蛛魔装置 193093/193094（spawn 67331/67332）的 SmartAI 挂在 On Gossip Hello 上 → `SetData(SPHERE1/2)`；核心 `GameObject::Use` 在处理 DOOR 类型前先调 `AI()->GossipHello`，所以 `PrerequisiteGameObjects` 走正常交互路径（凯利丝塔萨先例）。
- **塔达拉姆大厅布局**：平台在中央大厅（z≈11）；装置各在一侧坡道上的圆台（z≈18，半径≈18 码）。两队 5 只一队的掠夺幽魂（groupAI=514）巡逻线一直走上圆台，碎骨者 131904/131905 在下层（z≈-3）巡逻。run100020：碎骨者 131905 走到大厅北口外低处（533,-803→548,-781，z 4.4→-3）后已进战斗，但坦克在大厅里 58 码外无视线、走不过去，352 次 pull 被拒，600 秒超时——大厅与该低处走廊在导航网格上可能不直连。
- **阿曼尼塔**：三只洞穴兽围着 boss（东北/正北/正南），清怪路线必须绕开 boss 22 码仇恨半径；框架量得 v1 准备点距 boss 实际位置 19.22 码（与 spawn 算出的 26 码不符，boss 实际站位有偏差）。v2 从北口进、先北后东北再南，已能清完。
- **阿曼尼塔 timeout 分析（run100019，单场）**：boss 战 420 秒全程 boss 血量每分钟降 7–23%，boss 战总输出仅约 40 万（≈960 DPS）；Mini(57055) 全队 AoE 6 次。Mini 需吃健康蘑菇(30391)的 Potent Fungus 解除，playerbots `AKStrategy.cpp` 对阿曼尼塔是 `TODO`。**假说未量化**：需先量 bot 身上 Mini 的覆盖率与覆盖期间 DPS。

## 阿曼尼塔：Mini 覆盖率与坦克目标（2026-09-25）

测量：raidtest `mymac/dev` `a1f9749` 新增只读 `ObserveAuras`（boss 战每秒记每个 bot 的 Mini 57055 / Potent Fungus 56648、当前目标 entry、离 boss 距离）；
分析脚本 my-mac `~/wow335-work/aura_report.py <run...>`。机制（Spell.dbc + SmartAI）：Mini = 造成伤害 -75%、永久、半径 50000 码，
boss 每 30–45 秒检查「有人没 Mini」才重放；健康蘑菇死亡时对 3 码内玩家施放 Potent Fungus（+100%，2 分钟）；毒蘑菇被打或有人进 3 码即触发，并移除附近玩家的 Potent Fungus。

| 指标 | 修复前 v3（run100030/32/33/35，4 kill） | 坦克修复后 v4（run100041/44，2 kill） |
|---|---|---|
| 坦克以 boss 为目标 | 5–35 秒 / 186–317 秒（2–11%），其余打蘑菇 | **197/197、249/249 秒（100%）** |
| Mini 施放次数 | 5–8 | 1–3 |
| DPS 的 Mini 覆盖 | 47–92%（有 Mini 时对 boss DPS 为无 Mini 的 18–33%） | 72–88%（首次施放后全程） |
| Potent Fungus 覆盖 | 0–13% | 0–3% |
| boss 阶段时长 | 186–317 秒 | 197、250 秒 |

根因（playerbots 共享层）：`FindTankTargetSmartStrategy` 把「坦克没拉住仇恨」的单位排在最前；被动、没有 victim 的蘑菇永远拉不住，恒压过 boss，且原地重刷。
修复：playerbots `mymac/tank-skip-passive` `65862743`（跳过 REACT_PASSIVE 且无 victim 的生物），**尚未在纳多克斯/沃拉兹回归**。
第二变量（已写、只做了编译检查、未实跑）：`mymac/ak-amanitar-mushroom` `62af45c0`，DPS 在有 Mini 时走到离 boss 最近的健康蘑菇 2 码内击杀它。

v4 这轮（坦克修复二进制，场景只改清怪范围）：run100041 kill、100042 清怪超时、100043 / 100045 清怪减员、100044 kill；**run100046 在进行中被用户叫停（my-mac 关机），finished_at 为 NULL，是占位行，不计**。
清怪仍是阿曼尼塔场景的主要失败源（v3 6/10、v4 3/5），与坦克修复无关（修复只改 boss 阶段目标选择，失败都发生在 boss 开怪前）。

## 工具

my-mac `~/wow335-work/`：`los_probe.py`（批量 `raidtest los`，从日志收结果）、`batch.sh <scenario> <n> <map>`（逐场清锁定、等 `finished_at`）。操作 my-mac 一律 `ssh -n`，否则 `restart_world.sh` 的后台子进程会挂住 ssh 会话。

## 变更日志

| 日期 | 变化 | 影响的口径 | 链接 |
|---|---|---|---|
| 2026-09-25 | 新建 campaign；Nadox 10/10；Volazj 冒烟 kill；Amanitar/Taldaram 场景迭代中 | 新 cohort（ilvl 200，my-mac） | 本文件 |
| 2026-09-25 | Volazj 10/10；Amanitar 加 ObserveAuras，定位坦克打蘑菇并修复（v4 boss 阶段 2/2）；轮次在 run100046 被中止 | 坦克修复为新二进制 cohort | 本文件 |
