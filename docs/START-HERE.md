# 新会话接手

更新：2026-09-21。此文件只保留当前工作面和操作边界；跨副本结果在 [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)，文档组织规则在 [`testing/README.md`](testing/README.md)，冻结的旧入口在 [`testing/archive/START-HERE-2026-09-21.md`](testing/archive/START-HERE-2026-09-21.md)。

## 当前 campaign：英雄岩石大厅 / Tribunal of Ages

先读：

1. [`testing/LESSONS.md`](testing/LESSONS.md)
2. [`testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md`](testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md)
3. [`testing/bosses/heroic-hos-tribunal/README.md`](testing/bosses/heroic-hos-tribunal/README.md)
4. [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)

### 当前事实

- 基线为 r32：Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none` / 无 fixture / `PrerequisiteTimeoutSeconds=300`。
- r32 lifecycle 为 **1/5 DONE**：run745 是 491.468 秒零玩家死亡的真实 Brann DONE；run746、run748、run750、run751 是完成前置和两次真实 gossip 后的有效动态 wipe。Tribunal 与 HoS 均未完成。
- r34 LOS-reacquire 只是一项**未验收候选**。run759 的零死 kill 是预声明不计分 smoke，且没有 dispatch 归因；run760（470.622s 动态 wipe）全场 dispatch telemetry=0，严格 finder/action 未触发。不得把 r34 用于 lifecycle sample，也不得从 run759/run760 推效果。
- 已恢复 r32，worldserver 应为 ready/IDLE。开始任何命令前重新核对进程、FIFO、`raidtest status` 和 DB `finished_at`。
- 下一步不是再跑同类诊断或叠加变量；先形成一条新的、单一且可观测的证据支持假说。若无此假说，保持 r32 并只做已界定的 lifecycle 复验。

## 不可变规则

- 项目验证的是 `mod-playerbots` 在正常游戏规则下的策略；`mod-raidtest` 只能编排和观察，不能代选技能、走位、目标、仇恨、`DoAction` 或 boss 状态。
- 不自动同步上游；不靠装备、cheat、难度或 fixture 改动获得击杀。基线变化必须单独记录并重新分 cohort。
- 编译前须取得用户授权；获授权后只做目标增量构建，默认 `MTHREADS=4`。
- 结果只在 run 终态后统计：`raidtest_runs.finished_at IS NOT NULL`。运行中的 `aborted/0/NULL` 是占位。
- 每轮将结论写到 encounter README、摘要写到 ledger、当前动作写到本文件或 handover；临时日志不能是唯一证据。

## 工作树与已知提交

逐库重新确认 status、branch、HEAD；子仓库也遵守各自 `AGENTS.md`。

| 仓库 | 期望提交（接手时） |
|---|---|
| 管理库 | `8450336` |
| azerothcore-wotlk | `c747f55ca` |
| mod-playerbots | `a846c3da` |
| mod-raidtest | `5c1a28f` |

运行日志、`raidtest-rosters/`、`raidtest-scenes/` 等 core 未跟踪生成物不等同源码改动，仍须如实报告，不能删除他人资产。

## 常用操作纪律

- worldserver 控制 FIFO 是 `/tmp/ac_world_fifo`；读端为 `scripts/fifo_relay.py`。发送后必须以 `raidtest status` 回读。
- 每轮前按场景需要清 `account_instance_times` 与对应 map instance；这不是规则变更。
- 新 boss：先用 [`testing/CAMPAIGN-TEMPLATE.md`](testing/CAMPAIGN-TEMPLATE.md) 建副本矩阵，再依 [`testing/WORKFLOW.md`](testing/WORKFLOW.md) 建场景、跑基线、量化假说。
- 新团队副本：另固定 raid size、roster、分组、锁定/CD 复位和验收范围；不可拿五人 roster 或独立 boss 结论外推。
