# 新会话接手（更新：2026-09-10）

## 目标与阅读顺序

验证机器人能否按正常规则处理 WLK 副本机制并通关，必要时在自己的 mod-playerbots/core 开发分支修复。框架不得代选技能、代走位、修改仇恨或削弱 boss。

1. 本文件：当前状态与下一步。
2. [boss 台账](testing/BOSS-LEDGER.md)：哪些结果已证实。
3. [测试与修复流程](testing/WORKFLOW.md)：新 boss、复现、fork 修复和交接。
4. [代码覆盖与辅助行为](testing/SOURCE-COVERAGE.md)：不能把策略文件存在当作正常机制通关。
5. 仅按需要读取 [角色验收](investigations/roster-fixture/README.md)、[登录竞态](investigations/roster-fixture/GROUP-LOGIN-RACE.md)、[就绪评估](investigations/roster-fixture/READINESS.md)。

## 已知基线（接手时重新核对，不当作运行中进程的自动证明）

| 仓库 | 分支 | 最近确认的 HEAD |
|---|---|---|
| 管理库 | main | `aac1cbd`（normal5-v1 档位 + P2 走位优化收尾） |
| azerothcore-wotlk | Playerbot | `516b14df1`（map 574 诊断与长路线容量，本轮未改） |
| modules/mod-playerbots | codex/heroic-uk-ingvar | `67ac953c`（P2 两个走位缺陷修复；**已推送到 fork `mine`**） |
| modules/mod-raidtest | dev | `5620b0d`（开怪门槛假阴性修复 + normal5-v1 阵容/场景） |

mod-playerbots 有两个 remote：`origin` 是**上游** `mod-playerbots/mod-playerbots`（无写权限），
`mine` 才是 fork `pengjinfei/mod-playerbots`。分支 upstream 已固定到 `mine`，直接 `git push` 即可。
其余源码提交仍为本地分支提交，未同步或合并上游。`env/dist` 下的日志、角色 TSV 与场景快照为可再生成测试工件，不纳入提交；接手时仍需逐库执行 `git status`。

## 当前进展与待办（2026-09-09）

五人基线为 heroic、5 人、early-WLK heroic 装备（ilvl 200 上限）；已核验的 run79/80/86 五人快照有效 cheat 掩码均为 0。历史 Loatheb 使用的十人高装等基线和其 cheat 审计保留在台账中，不作为当前五人线的通关证据。

- 凯雷塞斯：run86 完整链路零死亡击杀，run91/92 共三场零死亡击杀；2026-09-09 回归 run273/274 再得两次零死亡击杀（含 4 只前置怪清理）。冰墓尚待验收。
- 斯卡瓦尔德与达隆：**完整链路（10 只前置怪 + 双 boss）三次零死亡击杀**（run286/287/288，86.1/80.6/90.1 秒，前置 35.2 秒清完）。此前该场景自 `c460d05` 起从未启动过，根因有两条并已修好：准备点 `(75,0,117)` 距最近可走多边形 8.3 码（bot 被传送进几何体，故对小怪和 boss 的 LoS 全为 false），已改为核心 `findNearestPoly` 实测投影 `(81.50,-5.13,118.90)`；房间是 L 形的，没有任何单一坐标能看到全部前置目标，故编排层新增「目标超出视线时带队接近并重试」，上限仍是 `PrerequisiteTimeoutSeconds`。详见 [UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)。
- 因格瓦尔：平台角色分离 fixture 已持续通过 5/5 位置门禁；坦克闪避修复后**八次独立冷启动 8/8 击杀**（93.9–112.3 秒，4 场零死亡）。P1 的旧共同前方出生点问题已由 fixture 隔离；P2 仍有暗影斧、治疗余量和 `59709` 控制窗口的组合风险。2026-09-09 的只读时序归因已收敛方向：第一把斧在六场中固定落在首次 `59709` 之后 +2.00 秒（必定处于正常 stun 中）且从未致死，第二把斧（102–109 秒）无论是否撞控制窗口都会致死；三场团灭停在 Boss 7%/10%/13%。P2 输出只有 P1 的一半左右，原因是 `59709` 自读条起始即把全队（含 28.83 码外的治疗）置为 `can_move=false`，而 P1 的 `59706` 不会。致死条件是「同半径内有第二个人」加「命中时仅 45–55% 血」，因此下一步是散开与治疗余量，不是移动优先级。详见 Ingvar 记录末尾。
- 寻径：map 574 的上下端已实测在同一 4,562-poly Detour 连通分量；此前失败分别是 1,024 查询节点耗尽与 148-poly 输出截断，而非已证实的楼梯断网。核心现为长路线提供 4,096 节点查询和 playerbots 512-poly/point 容量；run168 已取得完整地面路径。首段 NavigationOnly 通过同实例门禁，但会进入斯卡瓦尔德/达隆近战范围，故尚不能作为完整副本安全通行证据。

## 当前目标（2026-09-10 用户指定）

**以 normal5-v1 普通五人本毕业装备，打通全部英雄五人本。**

装备档位固定为 [normal5-v1](testing/fixtures/normal5-v1/README.md)（ilvl 上限 187，普通本掉落上限；
英雄档 heroic5-v1 及其全部证据原样保留，不覆盖）。boss 难度仍为英雄。也就是说：
**难度不再靠装备补，只能靠 bot 策略。** 不得用作弊、难度开关或临时调装换击杀率。

已完成的起点（UK 因格瓦尔，场景 `heroic-uk-ingvar-n5`）：

| 阶段 | 击杀率 |
|---|---|
| 换普通装备（run316） | 1/5 = 20% |
| 修 P2 两个走位缺陷后（run317/318/321） | 10/15 = **67%**，4 场零死亡 |

三轮跨度为 80/80/40，15 个样本不足以把击杀率定到个位数精度；要报稳定值需要更多样本。

推进建议（新会话可按此展开）：

1. 先把 UK 另外两个 boss（凯雷塞斯、斯卡瓦尔德&达隆）也切到 normal5-v1 跑基线——
   只需照 `mod-raidtest-scenario-heroic-uk-ingvar-n5.conf.dist` 复制场景并指向
   `normal5-v1` 阵容，不改 boss 与规则。先量出普通装下的实际击杀率，再决定要不要修。
2. Ingvar 剩余团灭的靶子已经明确且与站位无关：**Dreadful Roar 的全队 6.6k–10.8k 伤害**。
   run318/seq4 全队以 84/74/77/**50**/94% 血进这一记，法师被 10,766 打死；同期戒律牧师
   放了 19 次射击（Shoot）、全场**零次群体治疗**。方向是「利用 2 秒读条把队伍垫起来」
   （预读条群疗或全队套盾），不是继续调站位。
3. 扩到 UK 以外的英雄本时，逐本重复同一套流程：先建场景 + 跑基线 → 定位死因 →
   只在 mod-playerbots 修 → 重测 → 记录。**不要**先写策略再找问题。

**避坑（本轮踩过的）**：查 attempt 结果必须等 `raidtest_runs.finished_at` 非空；
跑动中 attempt 行会显示为 `aborted/0/NULL` 占位值，我据此把 run321 统计成了 2/2，
实际是 2/3。另外连续 cold start 会触发副本创建限流（`teleport stage timeout`），
每轮前 `DELETE FROM acore_characters.account_instance_times;`。

接续顺序（历史脉络，供追溯）：

1. Ingvar 提高击杀率（第一轮已实施，见 Ingvar 记录 2026-09-09 两节）。已确认只有 10 码前锥与 5 码斧区域可以靠站位规避；`59709` 的全队 2 秒昏迷（200 码）与 Dreadful Roar（60 码）无站位解法。已实施：远程/治疗外移到 13 码脱离前锥半径、非坦克远程互散 8 码、治疗法力与全员资源的只读采样。结果为 6 场 **4/6 击杀**，与改动前 2/3 在此样本量下无法区分，**不宣称击杀率已提升**；但五次冷启动中 effect-0 再未命中治疗或远程 DPS，失败窗口从第二把斧（102–110 秒）前移到首把斧与首次 `59709`（65–75 秒）。接续顺序：
   1. **（第二轮已完成）** 近战前锥：核心 `WorldObjectSpellConeTargetCheck` 的判定是 `IsWithinBoundaryRadius(target) || isInFront(...)`，而 `IsWithinBoundaryRadius` 对玩家是 **2.0 码且绕过角度**。所以「绕背」从来不是近战的答案，「离开 2.0 码」才是；近战安全带是中心距 (2.0, 5.0)。后弧落点 7.0→3.5 码、贴身清理阈值 1.5→3.0 码后，五场冷启动中盗贼 effect-0 命中 **0 次**（此前 2/5）。两轮合计 11 场 7/11 击杀，仍不宣称击杀率提升。
   2. **（第三轮已完成，Ingvar 现为 8/8 击杀）** 坦克不是只能硬吃猛击：root 窗口从结算前 3.005 秒开始、Boss 被定身且 `DisableRotate`，坦克 `can_move` 全程为 true，2 秒全队昏迷属于结算的一部分。而 P2 的 `59709` 是**暗影**伤害（P1 的 `59706` 是物理，护甲减 70% 到 7k–13.5k），坦克实收 22,891–25,787、血上限仅 28,884，每 9–11 秒一次；此前的存活是 `66233` Ardent Defender（60 秒一次）撞上了。原因是 `IngvarDodgeSmashAction::isUseful` 用 `!behind` 判据（43 次里 32 次被判「在背后=安全」跳过），且落点正好停在 2.0 码旁路阈值上。改为后弧 3.5 码、`MOVEMENT_FORCED`、判据换成两个真实选中条件后：**八次独立冷启动 8/8 击杀、93.9–112.3 秒、4 场零死亡、56 次猛击仅 1 次 effect-0**；坦克承伤 40k–59k（原 90k–144k）、治疗输出 68k–120k（原 112k–209k）、8 场中 6 场在第二把斧前结束。上一轮列为第一优先的「治疗对坦克优先级」随之不再是瓶颈。
   3. 仍未解决：斧的「7 码内不起手新非瞬发法术」效果未被单独证明（须 A/B 或删除）；`PlayerbotAI::UpdateAI` 在 `SPELL_STATE_PREPARING` 时不跑引擎、而 `RequestSpellInterrupt()` 无调用点这处互锁仍在，只是不再是 Ingvar 的瓶颈；run270 的那 1 次 effect-0 需在后续样本确认。
   4. 三骑手前置已定位为**资产阻塞**，不是策略或编排问题：`PrerequisiteX/Y/Z = 252,-350,185.8` 在导航网格上没有任何投影（`polyRef=0`、`find_path=0x00000000`、`component=disconnected`），成员到达即坠落（run296：1.41 秒自伤 26,324 打死坦克）。改从下层集结则对骑手无视线（骑手高 5 码），180 秒超时 0 死亡。官方场景 1/5。**下一步是补 map 574 上层平台的 mmap 覆盖**，与跨房间自主行进是同一个阻塞点；之后再补「前置完成后重新按角色分离传送」（`ValidateRoleSeparatedPreparation` 只是门禁，不传送）。详见 Ingvar 记录末尾。
2. 以同一 fixture、heroic、ilvl 200、零 cheat 做新的独立 cold-start 回归；不得与 6577–6579 之前或单场诊断样本混算稳定率。稳定标准与样本数在执行前写入 Ingvar 记录。
3. 完整副本自主通关：在安全的前置怪清理链与可验证移动段下，继续验证斯卡瓦尔德/达隆房间至平台的实际行走。利用已确认的完整 Detour 路线做分段到达和危险半径门禁；不得用猜测楼梯点、跨层传送或空房间传送伪造行走。
4. Ingvar 机制稳定且跨房间移动安全后，才将“凯雷塞斯→双 boss→三骑手→Ingvar”的完整链路列入验收；随后回到凯雷塞斯冰墓和双 boss 房间清怪的机制验收。

## 记录与提交规则

临时扫描、探针、日志和猜测性实现只用于定位，完成当轮后删除或保留在未提交工作区；不要为它们单独提交文档或代码。只在以下节点提交：可复现的问题根因及其已验证修复、改变复现基线的框架/配置、或 boss 验收结论与其必要证据。文档与代码在同一关键节点一起更新，避免按试验次数堆叠提交。

入口：[真人实机验证流程](testing/HUMAN-SESSION.md)、[heroic5-v1 配置](testing/fixtures/heroic5-v1/README.md)、[normal5-v1 配置](testing/fixtures/normal5-v1/README.md)、[凯雷塞斯王子记录](testing/bosses/heroic-uk-keleseth/README.md)、[斯卡瓦德&达尔隆](testing/bosses/heroic-uk-skarvald-dalronn/README.md)、[因格瓦尔](testing/bosses/heroic-uk-ingvar/README.md)、[UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)。

之前的“先复测 Patchwerk”计划暂后移。新会话优先按上面「当前目标」推进，并查实际运行是否已结束；不要同时启动另一轮。

## 新会话第一轮

- 逐库读 git status/branch/HEAD；检查是否有其他测试占用 worldserver。
- 先读 `raidtest status`，再查询数据库 run 的 finished_at。活动 attempt 行可能暂为 aborted/0/NULL，占位行不代表最终失败。
- 进程、FIFO 和 /tmp 日志均需重新核验，不能依赖上一会话 PID。
- 提交结果保存在 docs；完整事件在本地 MySQL，角色 TSV 在 worldserver 工作目录。跨机器需另行导出数据/配置/快照；只克隆管理库无法重现全部运行环境。

## 可复制给新会话的启动指令

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md 和 docs/testing/BOSS-LEDGER.md，再检查各仓库状态与当前运行任务。目标是**以 normal5-v1 普通五人本毕业装备打通全部英雄五人本**：装备档位固定不变，难度只能靠 bot 策略解决，不得用作弊、难度开关或调装换击杀率。按 START-HERE 的「当前目标」推进，区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。只在已验证修复、基线变化或关键验收节点更新文档并提交，不依赖旧聊天。
