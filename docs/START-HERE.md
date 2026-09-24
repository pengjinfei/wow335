# 新会话接手

更新：2026-09-24。此文件只保留当前工作面和操作边界；跨副本结果在 [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)，文档组织规则在 [`testing/README.md`](testing/README.md)，冻结的旧入口在 [`testing/archive/START-HERE-2026-09-21.md`](testing/archive/START-HERE-2026-09-21.md)。

## 当前 campaign：英雄岩石大厅 / Tribunal of Ages（回归调查）

先读：

1. [`testing/LESSONS.md`](testing/LESSONS.md)
2. [`testing/BOSS-LEDGER.md`](testing/BOSS-LEDGER.md)
3. [`testing/bosses/heroic-hos/README.md`](testing/bosses/heroic-hos/README.md)
4. [`testing/bosses/heroic-hos-tribunal/README.md`](testing/bosses/heroic-hos-tribunal/README.md)
5. [`testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md`](testing/HANDOVER-2026-09-21-HOS-TRIBUNAL.md)
6. Sjonnir 的正常规则框架 blocker：[`testing/bosses/heroic-hos-sjonnir/README.md`](testing/bosses/heroic-hos-sjonnir/README.md)

### 最新状态（2026-09-24，优先于下方历史事实）

- **装备才是 Tribunal 的主杠杆。** normal5-v1（ilvl≈183）下 Holy Shield uptime、r35 远程补视线两个单变量均 0/5（已关闭）；换用 `heroic5gear-n5talents-v1`（ilvl 200，天赋/雕纹/补给与 normal5 相同，刺杀贼换两把 ilvl 200 匕首）后，场景 `heroic-hos-tribunal-event-h5g` 两轮 **2/5 + 3/5 = 5/10 DONE**（第一轮含跟随修正回归 run802）。独立记账，不与 normal5 合算。
- 已提交：playerbots `7e77a827`（r35 远程补视线 + 远程空转 probe，注销未 dispatch 的 r34）；raidtest `c40a0d6`（EventFollowStarter 只在 starter 走动或 bot 掉队 >20 码时跟随，战斗中不再钉住 bot）、`41e385d`（脚本事件有人阵亡且残存者脱战 45 秒判 wipe，避免 900 秒 timeout）、`f2c8a50`（新阵容与场景 .conf.dist）。
- 运行中 binary 由隔离树 `/tmp/azerothcore-tribunal-retry-src`（模块软链到 `/tmp/mod-playerbots-tribunal-hs`、`/tmp/mod-raidtest-tribunal-r32`）构建；`41e385d` 已编译（SHA `d3fbfef4…`），其停滞判定尚未在实战中触发验证。
- **ilvl 200 档复跑（2026-09-24）**：斯拉德兰 5/5、因格瓦尔 5/5、阿努巴拉克 4/5、克里克希尔 4/4（3 次前置 spawn 消失中止）、泰蕾斯特拉 5/5、奥莫洛克 5/5、莫拉比 5/5；normal5 下卡住的 boss 在 ilvl 200 档基本全部稳定击杀。场景均为 `*-h5g`，独立记账。
- **Sjonnir 隔离 boss 战 5/5**（场景 `heroic-hos-sjonnir-iso-n5`，normal5，run814–818）；正常规则续链仍框架阻断。岩石大厅四个 boss 均已有结论：Krystallus 5/5、Maiden 隔离 5/5、Tribunal normal5 不稳定 / ilvl 200 档 5/10、Sjonnir 隔离 5/5。
- 下一步候选：h5g 档继续积累样本；在 ilvl 200 档复跑其他英雄本 boss 基线。详见 Tribunal README 末尾各节。

### 当前事实（2026-09-23 暂停前，历史）

- 基线为 r32：Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none` / 无 fixture / `PrerequisiteTimeoutSeconds=300`。
- Tribunal r32 lifecycle 为 **1/5 DONE**：run745 是 491.468 秒零玩家死亡的真实 Brann DONE；run746、run748、run750、run751 是完成前置和两次真实 gossip 后的有效动态 wipe。该基线未通过；按用户指示先暂缓 Tribunal，转审 Sjonnir，Tribunal 与 HoS 仍未完成。
- r34 LOS-reacquire 只是一项**未验收候选**。run759 的零死 kill 是预声明不计分 smoke，且没有 dispatch 归因；run760（470.622s 动态 wipe）全场 dispatch telemetry=0，严格 finder/action 未触发。不得把 r34 用于 lifecycle sample，也不得从 run759/run760 推效果或外推到 Sjonnir。
- 已恢复 r32，worldserver 应为 ready/IDLE。开始任何命令前重新核对进程、FIFO、`raidtest status` 和 DB `finished_at`。
- Sjonnir 已**跳过（框架阻断）**、没有策略或战斗样本：同实例 Tribunal 前置后，raidtest 不能代移，playerbots 亦无自主 post-event 路线。不能用 fixture/强制移动绕过。无后续 boss 可选，按 ledger 回归未完成的 Tribunal；保持 r32。
- `raidtest_events` 于 2026-09-23 做过历史保留清理：已删除已终态 run723–744 的 2,212,322 条事件，保留了全部 run/attempt 摘要及当前 Tribunal 范围 run745–772 的 2,460,177 条事件。旧 run 的结论仍以仓库证据文档为准，不能假定其原始事件行还在本机数据库。
- clean retry `worldserver -j4` 已在清理后成功构建；配置根为项目 `env/dist`，binary SHA-256=`4aeff160792dca9860e4017d822b0d6c9d2e9760acbcb348938ed711edda629f`，含 Dark Matter 和 survivor-retry markers。其来源为 core `c747f55ca`、playerbots `2dba88eb`的仅7个HoS Dark Matter文件、raidtest `4751ef8`；受控替换后 worldserver ready、Tribunal scenario加载、FIFO IDLE。排除 lifecycle 的run773终态为451.525秒/5 deaths wipe，8条Dark Matter action（7 true/1 false）且28237→roster非零4,628，故retry-clean action+hit gate通过；它永不入任何cohort。已预声明Dark Matter+survivor-retry R1 effect cohort（0/5）；首场run774/attempt1788427997已进入observing（真实gossip0/1=172.584/196.788秒）；R1首场run774/attempt1788427997已终态并合格：459.407秒、boss_hp_min=100%、5 deaths wipe；8条Dark Matter action（7 true/1 false）及28237→roster伤害9,510，故R1为**0/1 DONE**。单场不推断效果；同边界的R1第二候选run775已启动（5人preflight、`prerequisites_start`），165秒后仍为`prerequisites`（167.362秒；一次4/5 pull后的共同接近重试）；其后前置恢复完成，真实gossip0/1=188.567/212.773秒；324.949秒为`observing`，动态资格已达；run775已终态并合格：495.494秒、boss_hp_min=100%、5 deaths wipe；10条action（7 true/3 false），28237 roster damage=0，故R1为**0/2 DONE**。两场均wipe不推断效果；同边界R1第三候选run776已启动（5人preflight、`prerequisites_start`），170.161秒仍为`prerequisites`（一次4/5 pull后的party approach）；其后前置恢复完成，真实gossip0/1=186.305/210.511秒；328.526秒为`observing`，动态资格已达；run776已终态并合格：519.256秒、boss_hp_min=100%、5 deaths wipe；10条action（7 true/3 false），28237 roster damage=0，故R1为**0/3 DONE**。三场均wipe不推断效果；只读核对52–56的instance-time仍各2行、未清理后，R1第四候选run777已启动（5人preflight、`prerequisites_start`），168.228秒仍为`prerequisites`（全员对preclear目标正常近距/LOS=true）；其后真实gossip0/1=170.375/194.575秒；run777已终态并合格：417.620秒、boss_hp_min=76%、5 deaths wipe；13条action（11 true/2 false）及28237 roster damage=558，故R1为**0/4 DONE**。这不是效果结论；最后一场预声明候选run778已启动（5人preflight、`prerequisites_start`），174.904秒仍为`prerequisites`；其后真实gossip0/1=190.590/214.794秒；run778终态合格：475.249秒、boss_hp_min=100%、5 deaths wipe；4条action（3 true/1 false）、28237 roster damage=0。R1候选预算已用完，永久关闭为**0/5 DONE**（run774–778全为动态5-death wipe；仅run777 hp_min=76%）；效果未验收，不得重跑R1。只读R1审计显示27983每场均为最大可归因伤害（196,184–249,320），但run749已否定简单TankTarget强制优先级且有reach-leash安全拒绝；不得重开该变量。已为既有28265 Gaze flee action仅加实际MoveAway INFO telemetry；clean retry `worldserver -j4`通过，构成新telemetry-only binary边界。Gaze telemetry binary SHA-256=`287a76ef…ebded5`已在备份R1 binary后受控替换；PID29466 ready、playerbots config与FIFO IDLE gate均通过。现预声明唯一排除所有cohort的Gaze execution smoke，门槛为至少一条`tribunal-searing-gaze` INFO；28265伤害仅观测。该唯一排除smoke run779/attempt`1788428002`已完成前置、recovery及真实gossip0，并于215.130秒进入observing；排除smoke run779已终态：483.925秒/5-death wipe；Gaze action=16（13 true/3 false）；28265有10条damage event（830的8条非零合计11,058；827两条value=0）。静态/事件审计显示spawn后约0.5秒首tick，且830第三次spawn后2秒仍距0；当前action日志不能精确关联tick。已实施仅增加同单调时间源/GUID/movement-state的timing-observation binary（playerbots action与raidtest spawn/tick）；两tree diff-check及隔离`worldserver -j4`通过；timing binary SHA=`dae4aafb…f0536`已备份旧binary后受控替换，PID59960 ready/playerbots/FIFO IDLE。timing-smoke启动run780遭`enter_reason=8`，终态0ms teleport-stage abort，未进前置/动态且不消费smoke gate；52–56各4条instance-time。静态确认live limit=5，core拒绝路径与enter_reason=8一致；4行最早自然release为14:00:59。未清理；自然过期后FIFO IDLE并成功进入run781（5人/map599/`prerequisites_start`），确认入口恢复。run781/attempt`1788428004`已终态（468.984秒/5-death wipe），timing关联gate已闭合但没有效果证据。按用户指示暂停 Tribunal 的 Gaze/诊断链，不再启动run；接手读 `testing/HANDOVER-2026-09-23-HOS-TRIBUNAL-PAUSE.md`。

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
| 管理库 | `main` 最新 |
| azerothcore-wotlk | `c747f55ca` |
| mod-playerbots | `7e77a827`（分支 `codex/gd-takeover`） |
| mod-raidtest | `125ccc2`（分支 `codex/gd-takeover`） |

运行日志、`raidtest-rosters/`、`raidtest-scenes/` 等 core 未跟踪生成物不等同源码改动，仍须如实报告，不能删除他人资产。

## 常用操作纪律

- worldserver 控制 FIFO 是 `/tmp/ac_world_fifo`；读端为 `scripts/fifo_relay.py`。发送后必须以 `raidtest status` 回读。
- 每轮前按场景需要清 `account_instance_times` 与对应 map instance；这不是规则变更。
- 新 boss：先用 [`testing/CAMPAIGN-TEMPLATE.md`](testing/CAMPAIGN-TEMPLATE.md) 建副本矩阵，再依 [`testing/WORKFLOW.md`](testing/WORKFLOW.md) 建场景、跑基线、量化假说。
- 新团队副本：另固定 raid size、roster、分组、锁定/CD 复位和验收范围；不可拿五人 roster 或独立 boss 结论外推。
