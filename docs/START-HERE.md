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
| 管理库 | main | UK 收尾提交（见 `git log -1`） |
| azerothcore-wotlk | Playerbot | `516b14df1`（map 574 诊断与长路线容量，本轮未改） |
| modules/mod-playerbots | **codex/nexus-anomalus-rift-focus** | `34886ce1`（阿诺姆鲁斯裂隙转火判据修复，基于 `67ac953c`；**已推送到 fork `mine`**） |
| modules/mod-raidtest | dev | `1036eb3`（策略名映射 `"wotlk-nex" -> "nexus"`、四个 `heroic-nexus-*-n5` 场景、开怪时机门禁 `PrerequisiteMinBossDistance` + 延迟恢复自主选怪） |

mod-playerbots 有两个 remote：`origin` 是**上游** `mod-playerbots/mod-playerbots`（无写权限），
`mine` 才是 fork `pengjinfei/mod-playerbots`。分支 upstream 已固定到 `mine`，直接 `git push` 即可。
其余源码提交仍为本地分支提交，未同步或合并上游。`env/dist` 下的日志、角色 TSV 与场景快照为可再生成测试工件，不纳入提交；接手时仍需逐库执行 `git status`。

## 历史基线（英雄档 heroic5-v1，供追溯）

英雄五人基线（ilvl 200 上限、零 cheat）下 UK 三 boss 均已通关：凯雷塞斯 run273/274 两次
零死亡击杀、斯卡瓦尔德&达隆 run286–288 三次完整链路零死亡击杀、因格瓦尔 run265–272 八次
冷启动 8/8。这一档的全部证据保留，**不被 normal5-v1 覆盖**。寻径方面 map 574 上下端已实测
在同一 Detour 连通分量，但三骑手平台缺 mmap 覆盖，跨房间自主行进仍被资产阻塞。
细节见各 boss 记录与 [UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)、[魔枢夹具勘测](testing/bosses/heroic-nexus/FIXTURE-SURVEY.md)、[泰蕾斯特拉](testing/bosses/heroic-nexus-telestra/README.md)、[阿诺姆鲁斯](testing/bosses/heroic-nexus-anomalus/README.md)、[奥莫洛克](testing/bosses/heroic-nexus-ormorok/README.md)、[凯利丝塔萨](testing/bosses/heroic-nexus-keristrasza/README.md)。

## 当前目标（2026-09-10 用户指定）

**以 normal5-v1 普通五人本毕业装备，打通全部英雄五人本。**

装备档位固定为 [normal5-v1](testing/fixtures/normal5-v1/README.md)（ilvl 上限 187，普通本掉落上限；
英雄档 heroic5-v1 及其全部证据原样保留，不覆盖）。boss 难度仍为英雄。也就是说：
**难度不再靠装备补，只能靠 bot 策略。** 不得用作弊、难度开关或临时调装换击杀率。

### UK 已收尾（2026-09-10）

| 场景 | 结果 | 判定 |
|---|---|---|
| `heroic-uk-keleseth-n5`（run322） | 4 击杀 / 0 团灭，四场零死亡 | **正常规则通关**（含 4 只前置怪 + 冰墓） |
| `heroic-uk-skarvald-dalronn-n5`（run323） | **5/5 击杀**，五场零死亡 | **正常规则通关**（含 10 只前置怪 + 双 boss） |
| `heroic-uk-ingvar-n5` | 固定二进制 13/20 = **65%** | **未通关**，根因已定位未修 |

因格瓦尔剩下的事见 [台账](testing/BOSS-LEDGER.md) 与 [Ingvar 记录](testing/bosses/heroic-uk-ingvar/README.md)：
根因是 Woe Strike(59735) 诅咒的反射伤害 + 法师近六成诅咒时间对坦克无视线（Fisher p = 0.015），
**没动手修**，因为散开逻辑正是上一轮 20%→67% 的来源，改动必须同时回归「前锥 effect-0 命中率」。

### 第二个副本：英雄魔枢（The Nexus，map 576）首轮已完成（2026-09-10）

四个场景已建好并跑出基线，详见 [夹具勘测](testing/bosses/heroic-nexus/FIXTURE-SURVEY.md)
与四个 boss 记录。**四个 boss 里三个已通关**（泰蕾斯特拉、阿诺姆鲁斯、奥莫洛克），
只剩凯利丝塔萨被三球体进度门禁挡住。阿诺姆鲁斯靠改 bot 策略修好（0/5 → 稳定可杀），
奥莫洛克靠框架的「择时开怪」修好（0/5 → 6/8，**bot 策略一行未改**）。

| boss | 场景 | 结果 | 判定 |
|---|---|---|---|
| 泰蕾斯特拉 | `heroic-nexus-telestra-n5` | 7 场 -> 4 击杀 / 1 团灭 / 2 场未进 boss | **完整链路击杀**，稳定性未验收 |
| 阿诺姆鲁斯 | `heroic-nexus-anomalus-n5` | 300 秒档 10 场 9 击杀；**420 秒档** 5 场 4 击杀 | **正常规则通关** |
| 奥莫洛克 | `heroic-nexus-ormorok-n5` | **8 场 6 击杀 / 0 团灭**（run367+368） | **完整链路正常规则击杀** |
| 凯利丝塔萨 | `heroic-nexus-keristrasza-n5` | 无法开怪 | **框架阻断**（三球体进度门禁） |

**下一步需要用户先决定两件事（都不是配置问题）：**

1. **凯利丝塔萨的进度门禁。** 她默认 `UNIT_FLAG_NON_ATTACKABLE` + 冰冻牢笼，解除条件是
   三个 ORB 状态全 DONE，而 ORB 只能由**点击三个球体 gameobject** 置位、球体又要对应 boss
   先死（代码位置见 [她的记录](testing/bosses/heroic-nexus-keristrasza/README.md)）。
   两条路线：(a) 给 mod-raidtest 加**同一实例内的多 boss 链式场景 + gameobject 使用步骤**
   （贴近「打通副本」原意，工作量大）；(b) 加一个夹具键直接置 ORB 状态做**隔离形态**
   （便宜，但结论只能记「隔离 boss 战」，参照 `heroic-uk-ingvar-disc` 的记账先例）。
2. ~~奥莫洛克的守卫组择时开怪~~ **已解决（2026-09-11）**：mod-raidtest 新增
   `PrerequisiteMinBossDistance`（前置目标距 boss 不足 24 码就不开怪，等巡逻走远）+
   把「恢复 bot 自主选怪」推迟到真正开怪那一刻，清怪点用位移探针勘测出
   (287,-260,-12)。完整链路 8 场 6 击杀 / 0 团灭。详见
   [奥莫洛克记录](testing/bosses/heroic-nexus-ormorok/README.md)。

**阿诺姆鲁斯已修好（2026-09-10）**：根因是转火裂隙的判据太晚——只在 boss 挂护盾时才转火，
而英雄难度每 15 秒生一个裂隙、每个裂隙每 5/10 秒各召一只怨魂，护盾只在所有裂隙死完才解。
改成「45 码内有存活裂隙就转火」+ 坦克排除 + 让 `dps assist` 在裂隙存活期让路，
**0/5 → 10 场 9 击杀、零团灭**。mod-playerbots 分支 `codex/nexus-anomalus-rift-focus`
@ `34886ce1`（已推 fork `mine`，未建 PR）。唯一非击杀是**框架 300 秒预算超时**
（boss 停在 2%、只死 1 人）；击杀区间 177–260 秒。要不要把该场景 `TimeoutSeconds`
提到 420 属基线改动，**需用户决定**，且不得与现有 10 场混算。
详见 [阿诺姆鲁斯记录](testing/bosses/heroic-nexus-anomalus/README.md)。

### 环境与基线状态（接手时重新核对）

- 运行配置本轮改过三处，接手时按此核对
  （`azerothcore-wotlk/env/dist/etc/modules/playerbots.conf`）：
  `LogInGroupOnly = 1`（诊断时临时置 0，测完必须改回）、
  `AutoEquipUpgradeLoot = 0`（**必须保持**，否则 bot 会捡装备穿上、静默破坏固定装备档，
  run330 因此报废）、`SelfBotLevel = 2`（由 1 改，让真人用的 RAIDTEST 账号也能发
  `.playerbots bot self` 把自己的角色交给 AI；只放开这一件事，不授予其它 GM 权限，
  见 [真人流程 4b](testing/HUMAN-SESSION.md)）。`BotCheats = ""` 不变。
- 角色 guid 会随 `--force-recreate` 变化；按 guid 查数据前先核对。UK 的 n5 线是
  **791–795**（`*nfive`），**魔枢四个场景共用 796–800**（`*nfivc`，账号 52–56）——
  按用户要求「一套普通五人本毕业装备只要一套角色」，不再每个场景各建一套；
  10 人本/更难的副本再另建账号。原因与做法见
  [魔枢夹具勘测](testing/bosses/heroic-nexus/FIXTURE-SURVEY.md) 的 roster 一节。
- mod-raidtest 已提交三组只读采样（`heal_actions` / `boss_threat` / `curse_watch`，提交
  `14282f3`）与夹具死亡误判修复（`dfc7372`）。采样只回读现成状态，不触发
  `isUseful/isPossible/CheckCast`；对照组 run324 为 3/5，与基线一致。
- **未定位的编排不稳**：长时间连续运行后首场会 300 秒超时（boss 打到低血后 `boss_hp`
  采样中断），或卡在 `role-separated preparation position gate failed`。缓解靠每轮前清库
  + 重启，根因待查。

**避坑（本轮踩过的）**：查 attempt 结果必须等 `raidtest_runs.finished_at` 非空；
跑动中 attempt 行会显示为 `aborted/0/NULL` 占位值，我据此把 run321 统计成了 2/2，
实际是 2/3。另外连续 cold start 会触发副本创建限流（`teleport stage timeout`），
每轮前 `DELETE FROM acore_characters.account_instance_times;`。

因格瓦尔各轮改动的历史脉络（前锥模型、坦克闪避、三骑手资产阻塞等）已全部沉到
[因格瓦尔记录](testing/bosses/heroic-uk-ingvar/README.md)，本文件不再复述。

## 新副本快速开始（换本时照这个走）

1. **建场景**（不写任何策略）。复制一份官方场景模板，只改 roster：
   ```
   cd azerothcore-wotlk/modules/mod-raidtest/conf
   cp mod-raidtest-scenario-<本>-<boss>.conf.dist \
      mod-raidtest-scenario-<本>-<boss>-n5.conf.dist
   # 编辑：RosterFile = "mod-raidtest-roster-normal5-v1.conf"
   # 其余（MapId/BossEntry/难度/前置怪/准备点/超时）逐行照抄，不要动
   cp mod-raidtest-scenario-<本>-<boss>-n5.conf.dist \
      ../../../env/dist/etc/modules/mod-raidtest-scenario-<本>-<boss>-n5.conf
   ```
   场景是**启动时扫描注册**的（`RegisterAllScenarios`），**没有 reload 命令，新场景必须重启
   worldserver 才能跑**。用 `raidtest scenario list` 确认注册成功。

1b. **官方场景不存在、要自己定坐标时**（换新本最常见），先过这三关，**不要靠试**：

   **① 准备点必须在导航网格上。** 坐标看着在地上不代表 on-mesh。用核心 `findNearestPoly`
   取实测投影再写进 conf——斯卡瓦尔德&达隆的 `(75,0,117)` 距最近可走多边形 **8.3 码**，
   bot 被传送进几何体内部，对小怪和 boss 的 `los` 全为 false，两种拉怪都被拒，
   该场景因此从加入起就没启动过。改成投影 `(81.50,-5.13,118.90)` 才跑通。

   **② 准备点要在仇恨半径之外。** 核心 `Creature::CanStartAttack` 的判据是
   `IsWithinDistInMap(who, GetAggroRange(who) + m_CombatDistance, ...)`，而
   `Creature::GetAggroRange`：
   ```
   半径 = (detection_range − (玩家等级 − 怪等级) + 检测范围光环) × Rate.Creature.Aggro
          detection_range 默认 20.0（creature_template 可覆盖）
          下限 5 码，上限 45 码；本机 Rate.Creature.Aggro = 1
   ```
   **80 级玩家打 82 级英雄怪 → 20 − (80 − 82) = 22 码**，再加 `m_CombatDistance`。
   另有垂直保护：`GetDistanceZ(who) > CREATURE_Z_ATTACK_RANGE + m_CombatDistance` 时不拉仇恨。
   ⚠️ 源码里 `creatureLevel` / `playerLevel` 两个局部变量**名字是反的**
   （`creatureLevel` 存的是玩家等级），照名字读会算错方向。

   **③ 准备点要对拉怪目标有视线。** 房间是 L 形之类时，可能**不存在**能看到全部目标的
   单一坐标——这不是坐标没选好。编排层已有 `AttemptRunner::ApproachPrerequisiteTarget`
   （`AttemptRunner.cpp:1389`）：拉怪被拒时下达一次普通接近移动并重试，沿用整队全或无
   路线预检，上限仍是 `PrerequisiteTimeoutSeconds`。斯卡瓦尔德&达隆的 10 只前置怪就是
   靠它清掉的。

   **场景范围不能改小。** 如果因为小怪在仇恨半径内就把 `PrerequisiteSpawns` 删掉，
   那已经不是这个遭遇战了——见下面「场景范围与结论口径」。

2. **跑基线前的固定动作**：
   ```sql
   DELETE FROM acore_characters.account_instance_times;
   DELETE FROM acore_characters.instance WHERE map = <mapid>;
   ```
   确认 `AiPlayerbot.AutoEquipUpgradeLoot = 0`、`AiPlayerbot.BotCheats = ""`，重启 worldserver。

3. **先跑基线再找死因**：`raidtest run <场景> --attempts 5`。
   **UK 的经验是三个 boss 里只有一个需要深挖**——先量出实际击杀率，再决定要不要修。
   **不要先写策略再找问题。**

4. **判读结果**：一律等 `raidtest_runs.finished_at` 非空再统计；跑动中的 attempt 行会显示为
   `aborted/0/NULL` 占位值。`boss_hp_min=0` 不等于击杀（双阶段 boss 中途就会归零）。

4b. **选清怪点/拉怪点的三条硬约束（魔枢实测，跨副本可复用）**：距 boss > **22 码**
   （英雄 boss 仇恨半径 = detection 20 − 等级差 −2）、距目标小怪 < 20 码（拉得动）、
   **且把远程 bot 约 26 码的站桩距离算进去**（否则会多拉一组，run338 因此 5/5 报废）。
   验证坐标用导航探针：零位移探针只能证明「点在网格上」，**证不了连通性**
   （probe-g 的点零位移通过、实际是孤岛）；连通性要用位移探针（起点候选点、终点 boss 生成点）。
   配方见 [魔枢夹具勘测](testing/bosses/heroic-nexus/FIXTURE-SURVEY.md)。
   另外：小怪本身离 boss 太近时（如奥莫洛克的守卫 17.1 码），挨打后 90 毫秒 boss 就协助参战，
   **挪队伍位置无解**。

5. **要深挖时**，mod-raidtest 已有三组只读采样可直接用（提交 `14282f3`）：
   `heal_actions`（治疗的引擎决策，需 `LogInGroupOnly=0`，测完改回 1）、
   `boss_threat`（boss 当前目标 + 仇恨表前二）、`curse_watch`（可解诅咒 + 解咒者的判据/视线）。
   引擎自己的拒绝原因还可从 `Playerbots.log` 按 `spellid: <id>` 统计（`LogInGroupOnly=0` 时）。

6. **修复只在 mod-playerbots 做**，从已记录基线开 `codex/<boss>-<fix>` 分支；框架只编排和观察。
   编译前须征得用户同意，用增量目标：
   `nice -n 10 cmake --build var/build/obj --target worldserver -j4`。

7. **样本纪律（本轮踩过的坑）**：先量化再下结论。本轮有三条假设是「看着像」但被实测推翻的
   （`save mana` 乘子、治疗空转、Woe 伤害阈值），都写在 Ingvar 记录里，别重走。

### 场景范围与结论口径（**新建场景时最容易犯的错**）

**删掉遭遇战本该清的小怪 = 把它改成了隔离形态，结论口径必须跟着降级。**

改小场景范围（删 `PrerequisiteSpawns`、绕过 `KillGateSpawn`、跳过某个阶段）都属于
「不是这个遭遇战了」。这类结果**只能记「隔离 boss 战当前配置击杀」，不能记
「正常规则机制验收通过」**。

先例：因格瓦尔有两个场景并存——`heroic-uk-ingvar`（官方，带三骑手前置）与
`heroic-uk-ingvar-disc`（隔离）。隔离档 **9/9 击杀**，官方档只有 **1/5**，
台账里分开记、**不混算**。只看隔离档会得出「这个 boss 已经通关」的错误结论。

所以遇到「小怪在仇恨半径内没法干净开怪」时，正确顺序是：
1. 先按上面 1b 找一个 on-mesh、距目标 > 仇恨半径、且有视线的准备点；
2. 单点看不全就用 `ApproachPrerequisiteTarget` 分批接近；
3. **确实无解**再退到隔离形态——并且在 conf 注释与 boss 记录里**写死删了什么、为什么**，
   同时保留完整场景的条目，别让后来者把隔离档的击杀率当成通关证据。

## 记录与提交规则

临时扫描、探针、日志和猜测性实现只用于定位，完成当轮后删除或保留在未提交工作区；不要为它们单独提交文档或代码。只在以下节点提交：可复现的问题根因及其已验证修复、改变复现基线的框架/配置、或 boss 验收结论与其必要证据。文档与代码在同一关键节点一起更新，避免按试验次数堆叠提交。

入口：[真人实机验证流程](testing/HUMAN-SESSION.md)、[heroic5-v1 配置](testing/fixtures/heroic5-v1/README.md)、[normal5-v1 配置](testing/fixtures/normal5-v1/README.md)、[凯雷塞斯王子记录](testing/bosses/heroic-uk-keleseth/README.md)、[斯卡瓦德&达尔隆](testing/bosses/heroic-uk-skarvald-dalronn/README.md)、[因格瓦尔](testing/bosses/heroic-uk-ingvar/README.md)、[UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)、[魔枢夹具勘测](testing/bosses/heroic-nexus/FIXTURE-SURVEY.md)、[泰蕾斯特拉](testing/bosses/heroic-nexus-telestra/README.md)、[阿诺姆鲁斯](testing/bosses/heroic-nexus-anomalus/README.md)、[奥莫洛克](testing/bosses/heroic-nexus-ormorok/README.md)、[凯利丝塔萨](testing/bosses/heroic-nexus-keristrasza/README.md)。

之前的“先复测 Patchwerk”计划暂后移。新会话优先按上面「当前目标」推进，并查实际运行是否已结束；不要同时启动另一轮。

## 新会话第一轮

- 逐库读 git status/branch/HEAD；检查是否有其他测试占用 worldserver。
- 先读 `raidtest status`，再查询数据库 run 的 finished_at。活动 attempt 行可能暂为 aborted/0/NULL，占位行不代表最终失败。
- 进程、FIFO 和 /tmp 日志均需重新核验，不能依赖上一会话 PID。
- 提交结果保存在 docs；完整事件在本地 MySQL，角色 TSV 在 worldserver 工作目录。跨机器需另行导出数据/配置/快照；只克隆管理库无法重现全部运行环境。

## 可复制给新会话的启动指令

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md 和 docs/testing/BOSS-LEDGER.md，
> 再逐库检查仓库状态与当前运行任务。目标是**以 normal5-v1 普通五人本毕业装备打通全部英雄
> 五人本**：装备档位固定不变，难度只能靠 bot 策略解决，不得用作弊、难度开关或调装换击杀率。
> **UK 已收尾**（凯雷塞斯、斯卡瓦尔德&达隆通关，因格瓦尔 65% 根因已定位未修）；
> **第二个副本英雄魔枢首轮已完成**（泰蕾斯特拉完整链路 4/7 击杀，阿诺姆鲁斯 0/5、
> 奥莫洛克 0/5，凯利丝塔萨被三球体进度门禁挡住无法开怪）。接手后先看 START-HERE 里
> 「第二个副本」那一节的**两个待用户决定的框架问题**，不要自己扩框架；
> 可直接推进的策略线是阿诺姆鲁斯。区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。
> 只在已验证修复、基线变化或关键验收节点更新文档并提交，不依赖旧聊天。
