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

UK 三个 boss 的普通档基线已经全部跑完（2026-09-10）：

| 场景 | 结果 | 判定 |
|---|---|---|
| `heroic-uk-keleseth-n5`（run322） | 4 击杀 / 0 团灭，四场零死亡 | 不是瓶颈 |
| `heroic-uk-skarvald-dalronn-n5`（run323） | **5/5 击杀**，五场零死亡 | 不是瓶颈 |
| `heroic-uk-ingvar-n5`（run316→317/318/321） | 20% → 10/15 = **67%**，4 场零死亡 | **唯一瓶颈** |

也就是说 **UK 里只有因格瓦尔受装备档位影响**，另两个照抄英雄场景换 roster 就直接过，
不需要为它们改 bot 策略。Ingvar 的 67% 来自三轮 80/80/40，15 个样本不足以定到个位数精度。

推进建议（新会话可按此展开）：

1. **Ingvar 的真凶已定位：Woe Strike（59735）。** 因格瓦尔英雄 P2 每 15–20 秒给坦克挂
   一次（每场 4–7 次），挂着期间**治疗每治疗坦克一次，就有一份暗影伤害直接打回治疗
   身上**（触发 59736）。所以治疗站在 24.68 码外仍在持续挨 boss 伤害，**八场团灭治疗
   全部阵亡、五场是第一个死的**。反射伤害是干净判据：击杀场 1,432–19,175，团灭场
   **21,311–60,098**。
   Woe Strike 的 `Dispel = 2` 是**诅咒**（牧师驱散魔法无效），能解的是**法师的解除诅咒
   475**；法师确实在用（合计 74 次），但**每场 4–7 次上身只解掉 0–4 次**——3 秒内被解的
   窗口 proc 0–7 次，一直没解的窗口 proc 3–24 次。**法师漏解的原因已定位：视线。**
   法师自己的判据说「有可解诅咒」，但它自己的取值上下文在 14 个诅咒秒里有 11 秒选不出
   目标——卡在 `PartyMemberValue::Check` 硬性要求的 `IsWithinLOS`。run329/seq2 里
   Woe Strike 整 10 秒走完、法师全程 `los=false`；同场 27–30 码时 `los=true` 就正常解掉，
   所以不是距离。两场团灭的无视线秒数是 9 和 4，唯一击杀是 0。遮挡物**推断**是平台柱子
   （UK 策略源码原注释：「柱子似乎不算 gameobject」）。也就是说
   **上一轮为躲前锥加的散开逻辑把法师推到柱子后，而它只校验落点几何、不校验对队友视线**。
   **修之前先补样本**：目前只有 3 场 25 个诅咒秒，只够定性；另有 4 个「有视线仍选不出」
   未解释（疑为 `PartyMemberToDispel` 的 1000ms 缓存）。可选修法：散开落点加入视线校验，
   或给驱散补「移动到能看见」动作。

   同日已证伪、**不要重走**的三条（数据见 Ingvar 记录）：
   - `HealerAutoSaveManaMultiplier` 掐掉快速治疗 → 补上门槛重编后指标零变化，已回退；
     快速治疗的真实拒绝原因是 GCD、`UNIT_STATE_LOST_CONTROL` 与自身苦修引导。
   - 治疗空转 → 第一版把治疗死后的时间算成了空档；按存活期重算，GCD 利用率击杀 60.3%、
     团灭 62.7%（团灭反而更高），最长真实空档 9.4 秒。真正的差别是治疗活多久。
   - 治疗拉仇恨 → boss 仇恨采样 133 个样本里 132 个当前目标是坦克。

2. **新缺陷：bot 战斗外低于 `LowMana` 阈值仍不喝水**（run322/attempt1 唯一非击杀的
   直接原因）。包里有 20 个蜜风茶，牧师 11.9% 法力，回蓝曲线全程恒定 ~78/s 没有加速段。
   五人本连打时它直接决定下一场能不能开，前置怪越多越严重。属 mod-playerbots，优先修。
3. 扩到 UK 以外的英雄本时，逐本重复同一套流程：先建场景 + 跑基线 → 定位死因 →
   只在 mod-playerbots 修 → 重测 → 记录。**不要**先写策略再找问题。UK 的经验是：
   多数 boss 在普通档下直接过，先跑基线能省掉大量无用的策略改动。

### 本轮留下的两件半成品（下次接手先处理）

- **运行配置被改过**：`env/dist/etc/modules/playerbots.conf` 的
  `AiPlayerbot.LogInGroupOnly` 已由 1 改为 **0**（否则 `Engine::lastAction` 恒为空，
  取不到引擎判定）。诊断做完必须改回 1。改前副本见会话 scratchpad。
- **mod-raidtest 有未提交的只读采样改动（已编译、已验证行为中立）**：`AttemptObserver`
  新增 `heal_strategies` / `heal_actions`（治疗的 `Engine::lastAction`）与 `boss_threat`
  （boss 的 `GetLastVictim()`、仇恨表前二、坦克/治疗的仇恨值与到 boss 距离）。两者都只
  回读现成状态，不触发 `isUseful/CheckCast`，不改任何既有 tank_* 证据。对照组 run324
  为 3/5，与 65% 基线一致。重编命令：
  `nice -n 10 cmake --build var/build/obj --target worldserver -j4`（约 5 个 TU + 链接），
  编译前须征得用户同意。
- 普通档 Ingvar 的固定二进制基线现为 run317/318/321/324 合计 **13/20 = 65%**
  （run325 带过一处已回退的改动，不计入；run326 为加了仇恨采样后的 3/5）。

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
