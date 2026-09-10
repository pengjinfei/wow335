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
| modules/mod-playerbots | codex/heroic-uk-ingvar | `67ac953c`（P2 两个走位缺陷修复；**已推送到 fork `mine`**；本轮未改） |
| modules/mod-raidtest | dev | `dfc7372`（三组只读采样 + 夹具死亡误判修复 + 两个 n5 场景） |

mod-playerbots 有两个 remote：`origin` 是**上游** `mod-playerbots/mod-playerbots`（无写权限），
`mine` 才是 fork `pengjinfei/mod-playerbots`。分支 upstream 已固定到 `mine`，直接 `git push` 即可。
其余源码提交仍为本地分支提交，未同步或合并上游。`env/dist` 下的日志、角色 TSV 与场景快照为可再生成测试工件，不纳入提交；接手时仍需逐库执行 `git status`。

## 历史基线（英雄档 heroic5-v1，供追溯）

英雄五人基线（ilvl 200 上限、零 cheat）下 UK 三 boss 均已通关：凯雷塞斯 run273/274 两次
零死亡击杀、斯卡瓦尔德&达隆 run286–288 三次完整链路零死亡击杀、因格瓦尔 run265–272 八次
冷启动 8/8。这一档的全部证据保留，**不被 normal5-v1 覆盖**。寻径方面 map 574 上下端已实测
在同一 Detour 连通分量，但三骑手平台缺 mmap 覆盖，跨房间自主行进仍被资产阻塞。
细节见各 boss 记录与 [UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)。

## 当前目标（2026-09-10 用户指定）

**以 normal5-v1 普通五人本毕业装备，打通全部英雄五人本。**

装备档位固定为 [normal5-v1](testing/fixtures/normal5-v1/README.md)（ilvl 上限 187，普通本掉落上限；
英雄档 heroic5-v1 及其全部证据原样保留，不覆盖）。boss 难度仍为英雄。也就是说：
**难度不再靠装备补，只能靠 bot 策略。** 不得用作弊、难度开关或临时调装换击杀率。

### UK 已收尾（2026-09-10），下一步换本

| 场景 | 结果 | 判定 |
|---|---|---|
| `heroic-uk-keleseth-n5`（run322） | 4 击杀 / 0 团灭，四场零死亡 | **正常规则通关**（含 4 只前置怪 + 冰墓） |
| `heroic-uk-skarvald-dalronn-n5`（run323） | **5/5 击杀**，五场零死亡 | **正常规则通关**（含 10 只前置怪 + 双 boss） |
| `heroic-uk-ingvar-n5` | 固定二进制 13/20 = **65%** | **未通关**，根因已定位未修 |

冰墓机制本轮一并验收通过：四场击杀里冰墓每场生成，五名成员全部对其输出，是转火拆而非硬扛。

**因格瓦尔剩下的事（不阻塞换本，详见台账与 Ingvar 记录）**：根因是 Woe Strike(59735) 诅咒
挂坦克身上时治疗每治疗坦克一次就有一份暗影伤害打回治疗，法师能解但近六成诅咒时间对坦克
无视线（散开落点不校验视线），无视线秒数与成败 Fisher **p = 0.015**（11 场）。
**没动手修**，因为散开逻辑正是上一轮 20%→67% 的来源，加视线约束可能把成员推回前锥——
改的话必须同时回归「前锥 effect-0 命中率」，并先补一轮干净的 10–15 场。

下一步（新会话按此展开）：

1. **换下一个英雄五人本，先建场景跑基线。** 照
   `mod-raidtest-scenario-heroic-uk-*-n5.conf.dist` 复制一份，只把 `RosterFile` 指向
   `mod-raidtest-roster-normal5-v1.conf`，boss、难度、前置怪、准备点全部照抄官方场景。
   **UK 的经验是：多数 boss 在普通档下直接过（三个里只有一个需要深挖），先量基线能省掉
   大量无用的策略改动。不要先写策略再找问题。** 候选按邻近度：魔枢、艾卓-尼鲁布、
   安卡赫特、violet hold。
2. **跑之前的固定动作**：清 `account_instance_times` 与 `instance WHERE map=<mapid>`，
   重启 worldserver；确认 `AiPlayerbot.AutoEquipUpgradeLoot = 0`（否则 bot 会捡装备穿上、
   静默顶破 187 装备档）；结果一律等 `raidtest_runs.finished_at` 非空再统计。
3. **跨本很可能复用的两个已知缺陷**（都还没修，遇到再一起解决收益更大）：
   - **bot 战斗外低于 `LowMana` 阈值仍不喝水**（run322/attempt1 唯一非击杀的直接原因；
     包里有 20 个蜜风茶，回蓝曲线恒定 ~78/s 无加速段）。前置怪越多越严重。
   - **散开落点不校验对队友的视线**，导致驱散/治疗类目标选择静默失败
     （`PartyMemberValue::Check` 硬性要求 `IsWithinLOS`）。因格瓦尔上已量化。
4. 因格瓦尔的收尾修复（散开加视线约束 + 前锥命中率回归）可以等积累了其它副本的样本
   之后再一起做——如果同一个缺陷在多个本里都出现，修一次的收益更大。

### 环境与基线状态（接手时重新核对）

- 运行配置本轮改过三处，接手时按此核对
  （`azerothcore-wotlk/env/dist/etc/modules/playerbots.conf`）：
  `LogInGroupOnly = 1`（诊断时临时置 0，测完必须改回）、
  `AutoEquipUpgradeLoot = 0`（**必须保持**，否则 bot 会捡装备穿上、静默破坏固定装备档，
  run330 因此报废）、`SelfBotLevel = 2`（由 1 改，让真人用的 RAIDTEST 账号也能发
  `.playerbots bot self` 把自己的角色交给 AI；只放开这一件事，不授予其它 GM 权限，
  见 [真人流程 4b](testing/HUMAN-SESSION.md)）。`BotCheats = ""` 不变。
- 角色 guid 会随 `--force-recreate` 变化，当前为 **791–795**（账号号与角色名不变）；
  按 guid 查数据前先核对。
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

5. **要深挖时**，mod-raidtest 已有三组只读采样可直接用（提交 `14282f3`）：
   `heal_actions`（治疗的引擎决策，需 `LogInGroupOnly=0`，测完改回 1）、
   `boss_threat`（boss 当前目标 + 仇恨表前二）、`curse_watch`（可解诅咒 + 解咒者的判据/视线）。
   引擎自己的拒绝原因还可从 `Playerbots.log` 按 `spellid: <id>` 统计（`LogInGroupOnly=0` 时）。

6. **修复只在 mod-playerbots 做**，从已记录基线开 `codex/<boss>-<fix>` 分支；框架只编排和观察。
   编译前须征得用户同意，用增量目标：
   `nice -n 10 cmake --build var/build/obj --target worldserver -j4`。

7. **样本纪律（本轮踩过的坑）**：先量化再下结论。本轮有三条假设是「看着像」但被实测推翻的
   （`save mana` 乘子、治疗空转、Woe 伤害阈值），都写在 Ingvar 记录里，别重走。

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

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md 和 docs/testing/BOSS-LEDGER.md，
> 再逐库检查仓库状态与当前运行任务。目标是**以 normal5-v1 普通五人本毕业装备打通全部英雄
> 五人本**：装备档位固定不变，难度只能靠 bot 策略解决，不得用作弊、难度开关或调装换击杀率。
> **UK 已收尾（凯雷塞斯、斯卡瓦尔德&达隆通关，因格瓦尔 65% 根因已定位未修），下一步是换新
> 副本**——按 START-HERE 的「新副本快速开始」建场景、跑基线，先量出实际击杀率再决定要不要修，
> 不要先写策略再找问题。区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。
> 只在已验证修复、基线变化或关键验收节点更新文档并提交，不依赖旧聊天。
