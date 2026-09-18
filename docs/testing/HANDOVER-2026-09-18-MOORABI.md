# 莫拉比交接（2026-09-18，晚更新）

## 当前结论

英雄古达克莫拉比（`heroic-gd-moorabi-n5`，Heroic / normal5-v1 / 无 cheats / 完整遭遇战）**前置拉怪缺陷已定位并修复**，
修复后 **run664 = 5/5 零死亡击杀**（160.700/201.156/213.071/242.489/216.814 秒），前置清怪 53.160–74.637 秒。
run662/663 另有 3 场击杀。**待独立复现一轮 5 场才能写进台账结论。**

boss 阶段的 `CanNotReachTarget`（run640 seq4）本轮**未复现、也仍未归因**，与本次修复是两件事，不要合并。

## 本轮结论：交接文档留的开放问题已可回答

原问题：「run661 是 spawn 从未重载，还是已重载但队伍无法再拉怪？」

**两个选项都不成立。** run661 的 25 秒 spawnId 重绑等待根本没被触发（没有 spawn 消失）；
真正原因是上一轮那两处未提交改动**自身的暴露面**。

`AttemptRunner::ApproachPrerequisiteTarget` 在普通（无 CC 门禁）前置接近时只让 `ctx.bots.front()`（坦克）
沿路径探路，其余 4 人留在准备点，并用 `HoldFollowerAttackTagged` 压制他们的 `attack tagged`。
run661 日志逐行坐实：

| 时刻 | 事件 |
|---|---|
| 33.5–39.6s | 三次 `prerequisite approach`，目标都是东侧**上层平台**的 127062 Fire Weaver（z=129.29）；坦克被单放到下层走廊 `(1787,841,124.4)`→`(1793,857,124.4)`，全部 `los=false` |
| 同时 | `HoldFollowerAttackTagged: held 4 follower bot(s)`；4 人全程 `combat=false target=none` 钉在 `(1772,877)` |
| 39.6s | `BeginPullForAll` 只有 leader 成功，4 个跟随者 `could not initiate attack ... continuing`——**框架仍把这次拉怪记为已发出** |
| 81.7s | 坦克单人在 `(1803.96,856.80,129.20)` 被 29819 Lancer 打死 |
| 200.003s | `prerequisite_failed: clearing timeout`（坦克 1 死，`boss_hp_min=100`） |

run659 的 3 死同一路径。

## 本轮代码

`mod-raidtest`（均已提交）：

### `3189b9a` 前置清怪拉怪必须全队一起上

1. 普通前置接近的落点改由 leader 的可走路径决定、**全队共用**，删掉 `HoldFollowerAttackTagged` 压制。
2. `BeginPullForAll` 之后**校验每个活着的 bot 都真的拿到这次拉怪目标**（`current target` 或 `victim`），
   不足就按接近流程重试——这正是 run661 缺的那道门。
3. 共同落点用路径上**第一个**可见点（能开怪的最短走法）。用最后一个可见点（≈怪脚下）会把全队多拖一段路：
   run663 seq3 就是这样被拖到平台西侧、把**不在前置表里**的西侧那组卷进来，3 死超时。

### `aa01349` boss 重新解析时必须同步换绑事件总线

run665 seq2 暴露：清怪期间 boss 脱战被 `DespawnOnEvade` 下线、按原 spawn 重生后，`AttemptRunner`
重新寻址到了新对象（`Low 65 → 240`，缺席 19713ms），但**只更新了 `ctx.bossGuid`，没更新
`CombatEventBus` 的 `_bossGuid`**。新 GUID 既不在 `_bossGuid` 也不在 `_botGuids`，`IsMember` 把 boss 的
全部事件丢掉：`boss_hp` 事件 **0 条**（同轮 kill 场有 3–6 万条）、真死亡事件的 `source` 对不上
`_bossGuid` 所以 `_bossDeathSeen` 永不置位 → `AttemptObserver` 看到 `hp=0%` 却拿不到死亡确认，
40 个采样后记 `boss lost combat state (stuck/reset)`——**已经把 boss 打死却被记成失败**（同场
`dropped=30350`，kill 场只有 1506–4710）。新增 `CombatEventBus::RebindBoss` 修复。

## 最近证据

| run | 形态 | 结果 |
|---|---|---|
| 662 | 共同落点 = 最后一个可见点 | 1/1 kill，261.516s 零死亡 |
| 663 | 同上 | 2/5：seq1 kill 166.732s、seq2 kill 149.097s（均零死亡）；seq3 卷入西侧那组 3 死超时；seq4 spawn 重绑 25s 超时；seq5 前置减员 |
| 664 | 共同落点 = **第一个**可见点 | **5/5 kill 零死亡**，160.700–242.489s |
| 665 | 同上 | 4/5 + seq2 总线 bug（实为击杀） |
| 666 | 同上 | 2/5 + 1 wipe（前置清怪强度，见下） |
| 667 | 同上 + 总线修复 | **5/5 kill 零死亡**，137.244–220.702s |

**修复后（664–667）合计 20 场：16 击杀（80%）、2 场前置有玩家死亡。** run667 seq3 在**真实触发点**上复现了
run665 那个 `Low 65 → 240` 重绑并击杀（`boss_hp` 61,653 条）——总线修复不只是「没复现」，是正面验证。

## ⚠ 仍未解决：前置清怪本身会打输（独立待办，与本修复不是一回事）

| 时段 | 样本 | 前置有玩家死亡 | 前置死亡人数 | 击杀率 |
|---|---|---|---|---|
| A `639–654`（提交基线） | 25 | 6 (24%) | 15 | 68% |
| C `662–663`（最后一可见点） | 6 | 3 (50%) | 9 | 50% |
| D `664–667`（本修复） | 20 | 2 (10%) | — | 80% |

Fisher 检验：前置死亡率 A vs D **p=0.64**，击杀率 A vs D **p=0.50**，**统计上不可区分**。
也就是说：本修复把「坦克单挑必输」换回了「正常五人清怪」，**但清怪本身仍有约 1/5 的场次会打输**——
这正是修复前基线本来就有的水平。**清怪强度是 bot 策略问题，不是框架缺陷，不得靠改装备/难度/cheat 解决。**

run666 的三场失败细节（都**不是**框架问题）：

- seq1 / seq5：**五只全清完**，在恢复期被 29819 Lancer 连续击倒盗贼（1 死）。
- seq2：**只清掉 2/5** 就被团灭。治疗(797) 的 heal 采样在 **13.6s–39.5s 之间有 26 秒完全空档**
  （对照 kill 场前 60s 有 38 个采样），同期全队对目标的 `preclear_target` 采样 `los=true`——
  **治疗不是看不见怪，是看不见队友**。

### 首选单变量是接控制链，**不是** LESSONS 待办第 0 条

前置五只 `creature_template.type = 7`（Humanoid），**变形/妖术/闷棍按类型都有效**（不像艾卓-尼鲁布
那本全是亡灵、只有束缚亡灵能用）。但目前：

- 莫拉比场景 conf **没有 `PrerequisiteCcWaitSeconds`**（对比克里克希尔/泰蕾斯特拉/奥莫洛克/凯利丝塔萨都是 25）；
- `GDStrategy.h` 基类是裸 `Strategy`，`GDStrategy.cpp` 里 `// Moorabi` 下面是**空的**——共享层的
  `TrashCcPullStrategy::InitTriggers` 在古达克**根本没挂**（对照 `NexStrategy` / `ANStrategy` 是 `TrashCcPullStrategy`）。

**run637 那条「接入失败、反复 `no_plan`」的结论不能直接搬来否掉控制链**：那次用的是**旧的接近逻辑**
（每个 bot 各自找路、只走到 24 码外），而 `no_plan` 的直接成因正是「那个坐标看不到目标」——
本轮已把接近改成「leader 选共同落点、全队一起走到能开怪的点」。所以接控制链需要**重测**，不是已被否掉。

⚠ LESSONS 第六节待办第 0 条（施法型取值补「走过去」链条）管的是**驱散/复活/团队 buff**——
隔墙放不出去。run666 seq2 不是那条：那里全队对怪 `los=true`，是**看不见队友**，属于另一条链路。

## 下一步（按序）

1. **接控制链重测前置清怪**（首选单变量，见上）。两步：mod-playerbots 把
   `WotlkdungeonGDStrategy` 改成继承 `TrashCcPullStrategy` 并调 `TrashCcPullStrategy::InitTriggers`
   （参照 `NexStrategy` / `ANStrategy`）；场景 conf 加 `PrerequisiteCcWaitSeconds = 25`。
   需编译，得单独授权。
2. **boss 阶段 `CanNotReachTarget`（run640 seq4）仍未归因**，本轮未复现，与前两项是不同的事。
   只有复现该异常时才重接临时日志：启动后、**排队前**执行 `server set loglevel 1 movement.chase 3`，
   在 `TargetedMovementGenerator` 的 accessibility 与 path-failure 分支分别记录源/目标状态与 path type；
   结束立即撤回并重编译。
3. 不要改装备、难度、cheat、怪物属性或把未死亡 spawn 记为击杀。

## 仓库状态

- 管理库：`main`，本交接与 Moorabi 文档、BOSS-LEDGER、START-HERE 已更新。
- core：`main` `c747f55ca`，仅有本地运行日志/快照未跟踪。
- mod-playerbots：`codex/gd-takeover` `f0e08d97`，无本轮源码改动。
- mod-raidtest：`codex/gd-takeover`，本轮两个提交 `3189b9a` + `aa01349`（**未推 fork**）。

## 环境坑（本轮新踩，影响每次跑测试）

`scripts/restart_world.sh` 用 `tail -n 0 -f /tmp/ac_world_fifo | worldserver` 作 FIFO 读端。
**`tail` 写管道时是块缓冲（16KB）**，`raidtest run` 这类短命令会永远停在缓冲区里——本会话三次发命令
都没进控制台（日志无 `Orchestrator` 行、数据库无新 run），一度误判为「启动期吞命令」。
改用 `scripts/fifo_relay.py`（`O_RDWR` 自持写端 + 逐行 flush）后一次即通。
**该修复已提交进 `restart_world.sh`（`8396a02`）并实机验证**，下一个会话不必手工起 relay。
⚠ 不能用 `perl -e '$|=1; while(<STDIN>){print}'`：写端关闭时它会收到 EOF 并退出。
