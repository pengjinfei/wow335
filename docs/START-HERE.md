# 新会话接手

更新：2026-09-21。此文件只保留当前工作面和操作边界；跨副本结果在 [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)，文档组织规则在 [`testing/README.md`](testing/README.md)，冻结的旧入口在 [`testing/archive/START-HERE-2026-09-21.md`](testing/archive/START-HERE-2026-09-21.md)。

## 当前 campaign：英雄岩石大厅 / Tribunal of Ages（回归调查）

先读：

1. [`testing/LESSONS.md`](testing/LESSONS.md)
2. [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)
3. [`testing/bosses/heroic-hos/README.md`](testing/bosses/heroic-hos/README.md)
4. [`testing/bosses/heroic-hos-tribunal/README.md`](testing/bosses/heroic-hos-tribunal/README.md)
5. [`testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md`](testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md)
6. Sjonnir 的正常规则框架 blocker：[`testing/bosses/heroic-hos-sjonnir/README.md`](testing/bosses/heroic-hos-sjonnir/README.md)

### 当前事实

- 基线为 r32：Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none` / 无 fixture / `PrerequisiteTimeoutSeconds=300`。
- Tribunal r32 lifecycle 为 **1/5 DONE**：run745 是 491.468 秒零玩家死亡的真实 Brann DONE；run746、run748、run750、run751 是完成前置和两次真实 gossip 后的有效动态 wipe。该基线未通过；按用户指示先暂缓 Tribunal，转审 Sjonnir，Tribunal 与 HoS 仍未完成。
- r34 LOS-reacquire 只是一项**未验收候选**。run759 的零死 kill 是预声明不计分 smoke，且没有 dispatch 归因；run760（470.622s 动态 wipe）全场 dispatch telemetry=0，严格 finder/action 未触发。不得把 r34 用于 lifecycle sample，也不得从 run759/run760 推效果或外推到 Sjonnir。
- 已恢复 r32，worldserver 应为 ready/IDLE。开始任何命令前重新核对进程、FIFO、`raidtest status` 和 DB `finished_at`。
- Sjonnir 已**跳过（框架阻断）**、没有策略或战斗样本：同实例 Tribunal 前置后，raidtest 不能代移，playerbots 亦无自主 post-event 路线。不能用 fixture/强制移动绕过。无后续 boss 可选，按 ledger 回归未完成的 Tribunal；保持 r32。
- `raidtest_events` 于 2026-09-23 做过历史保留清理：已删除已终态 run723–744 的 2,212,322 条事件，保留了全部 run/attempt 摘要及当前 Tribunal 范围 run745–772 的 2,460,177 条事件。旧 run 的结论仍以仓库证据文档为准，不能假定其原始事件行还在本机数据库。
- clean retry `worldserver -j4` 已在清理后成功构建；配置根为项目 `env/dist`，binary SHA-256=`4aeff160792dca9860e4017d822b0d6c9d2e9760acbcb348938ed711edda629f`，含 Dark Matter 和 survivor-retry markers。其来源为 core `c747f55ca`、playerbots `2dba88eb`的仅7个HoS Dark Matter文件、raidtest `4751ef8`；受控替换后 worldserver ready、Tribunal scenario加载、FIFO IDLE。排除 lifecycle 的run773终态为451.525秒/5 deaths wipe，8条Dark Matter action（7 true/1 false）且28237→roster非零4,628，故retry-clean action+hit gate通过；它永不入任何cohort。已预声明Dark Matter+survivor-retry R1 effect cohort（0/5）；首场run774/attempt1788427997已进入observing（真实gossip0/1=172.584/196.788秒）；R1首场run774/attempt1788427997已终态并合格：459.407秒、boss_hp_min=100%、5 deaths wipe；8条Dark Matter action（7 true/1 false）及28237→roster伤害9,510，故R1为**0/1 DONE**。单场不推断效果；同边界的R1第二候选run775已启动（5人preflight、`prerequisites_start`），165秒后仍为`prerequisites`（167.362秒；一次4/5 pull后的共同接近重试）；其后前置恢复完成，真实gossip0/1=188.567/212.773秒；324.949秒为`observing`，动态资格已达；run775已终态并合格：495.494秒、boss_hp_min=100%、5 deaths wipe；10条action（7 true/3 false），28237 roster damage=0，故R1为**0/2 DONE**。两场均wipe不推断效果；同边界R1第三候选run776已启动（5人preflight、`prerequisites_start`），170.161秒仍为`prerequisites`（一次4/5 pull后的party approach）；其后前置恢复完成，真实gossip0/1=186.305/210.511秒；328.526秒为`observing`，动态资格已达；run776已终态并合格：519.256秒、boss_hp_min=100%、5 deaths wipe；10条action（7 true/3 false），28237 roster damage=0，故R1为**0/3 DONE**。三场均wipe不推断效果；只读核对52–56的instance-time仍各2行、未清理后，R1第四候选run777已启动（5人preflight、`prerequisites_start`），168.228秒仍为`prerequisites`（全员对preclear目标正常近距/LOS=true）；其后真实gossip0/1=170.375/194.575秒；run777已终态并合格：417.620秒、boss_hp_min=76%、5 deaths wipe；13条action（11 true/2 false）及28237 roster damage=558，故R1为**0/4 DONE**。这不是效果结论；最后一场预声明候选run778已启动（5人preflight、`prerequisites_start`），174.904秒仍为`prerequisites`；其后真实gossip0/1=190.590/214.794秒；run778终态合格：475.249秒、boss_hp_min=100%、5 deaths wipe；4条action（3 true/1 false）、28237 roster damage=0。R1候选预算已用完，永久关闭为**0/5 DONE**（run774–778全为动态5-death wipe；仅run777 hp_min=76%）；效果未验收，不得重跑R1。下一步是基于关闭证据审计新的单一正常规则假说。

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
| 管理库 | `7814e0a` |
| azerothcore-wotlk | `c747f55ca` |
| mod-playerbots | `a846c3da` |
| mod-raidtest | `5c1a28f` |

运行日志、`raidtest-rosters/`、`raidtest-scenes/` 等 core 未跟踪生成物不等同源码改动，仍须如实报告，不能删除他人资产。

## 常用操作纪律

- worldserver 控制 FIFO 是 `/tmp/ac_world_fifo`；读端为 `scripts/fifo_relay.py`。发送后必须以 `raidtest status` 回读。
- 每轮前按场景需要清 `account_instance_times` 与对应 map instance；这不是规则变更。
- 新 boss：先用 [`testing/CAMPAIGN-TEMPLATE.md`](testing/CAMPAIGN-TEMPLATE.md) 建副本矩阵，再依 [`testing/WORKFLOW.md`](testing/WORKFLOW.md) 建场景、跑基线、量化假说。
- 新团队副本：另固定 raid size、roster、分组、锁定/CD 复位和验收范围；不可拿五人 roster 或独立 boss 结论外推。
