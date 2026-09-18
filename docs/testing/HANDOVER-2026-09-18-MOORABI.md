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

`mod-raidtest` 的 `AttemptRunner.cpp/.h`（**已编译，未提交**）：

1. 普通前置接近的落点改由 leader 的可走路径决定、**全队共用**，删掉 `HoldFollowerAttackTagged` 压制。
2. `BeginPullForAll` 之后**校验每个活着的 bot 都真的拿到这次拉怪目标**（`current target` 或 `victim`），
   不足就按接近流程重试——这正是 run661 缺的那道门。
3. 共同落点用路径上**第一个**可见点（能开怪的最短走法）。用最后一个可见点（≈怪脚下）会把全队多拖一段路：
   run663 seq3 就是这样被拖到平台西侧、把**不在前置表里**的西侧那组卷进来，3 死超时。

另保留上一轮的两处（已一并编译）：前置 boss assist 每秒重试最多 8 秒；旧 runtime GUID 消失后按
`spawnId` 等最多 25 秒重绑（run663 seq4 实测触发一次、按设计作废）。

## 最近证据

| run | 形态 | 结果 |
|---|---|---|
| 662 | 共同落点 = 最后一个可见点 | 1/1 kill，261.516s 零死亡 |
| 663 | 同上 | 2/5：seq1 kill 166.732s、seq2 kill 149.097s（均零死亡）；seq3 卷入西侧那组 3 死超时；seq4 spawn 重绑 25s 超时；seq5 前置减员 |
| 664 | 共同落点 = **第一个**可见点 | **5/5 kill 零死亡**（见上）；`engaged only` 仅 1 次且下一 tick 补齐 |

## 下一步

1. **独立复现一轮 5 场**（不需编译；先清 `account_instance_times`）。
2. 只有复现 boss 阶段异常时才重接临时日志：启动后、**排队前**执行
   `server set loglevel 1 movement.chase 3`，在 `TargetedMovementGenerator` 的 accessibility 与
   path-failure 分支分别记录源/目标状态与 path type；结束立即撤回并重编译。
3. 不要改装备、难度、cheat、怪物属性或把未死亡 spawn 记为击杀。

## 仓库状态

- 管理库：`main`，本交接与 Moorabi 文档、BOSS-LEDGER、START-HERE 已更新。
- core：`main` `c747f55ca`，仅有本地运行日志/快照未跟踪。
- mod-playerbots：`codex/gd-takeover` `f0e08d97`，无本轮源码改动。
- mod-raidtest：`codex/gd-takeover` `8ec1420`，`src/Orchestrator/AttemptRunner.cpp/.h` 本轮改动。

## 环境坑（本轮新踩，影响每次跑测试）

`scripts/restart_world.sh` 用 `tail -n 0 -f /tmp/ac_world_fifo | worldserver` 作 FIFO 读端。
**`tail` 写管道时是块缓冲（16KB）**，`raidtest run` 这类短命令会永远停在缓冲区里——本会话三次发命令
都没进控制台（日志无 `Orchestrator` 行、数据库无新 run），一度误判为「启动期吞命令」。
改用 `python3 -u /tmp/fifo_relay.py`（`O_RDWR` 自持写端 + 逐行 flush）后一次即通。
⚠ 不能用 `perl -e '$|=1; while(<STDIN>){print}'`：写端关闭时它会收到 EOF 并退出。
