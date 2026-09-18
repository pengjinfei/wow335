# 新会话接手（更新：2026-09-18 晚，**莫拉比两个框架缺陷已修；前置清怪强度仍是独立待办**）

> **先读 [LESSONS](testing/LESSONS.md)，再读本轮交接 [HANDOVER-2026-09-18-MOORABI](testing/HANDOVER-2026-09-18-MOORABI.md)。**
> 副本级勘测在 [古达克副本勘测](testing/bosses/heroic-gd/README.md)。
>
> ## 当前状态：英雄古达克（Gundrak，map 604）——**迦尔达拉稳定；莫拉比 boss 已稳、清怪待改；斯拉德兰仍未稳定**
>
> 装备档 normal5-v1（ilvl 上限 187），难度英雄，`BotCheats=""`，
> 口径均为**隔离 boss 战**（不是连续通关一遍副本）；莫拉比是**完整遭遇战**（五个前置 spawn 不删）。
>
> | # | boss | 场景 | 结果 | 判定 |
> |---|---|---|---|---|
> | 1 | 斯拉德兰 29304 | `heroic-gd-sladran-disc-n5` | 合并后 **3/5**；平台阵位 **0/5**（已回退） | 不稳定；别重试平台阵位 |
> | 2 | 莫拉比 29305 | `heroic-gd-moorabi-n5` | **run664–667 合计 16/20 击杀（80%）**，run664 与 run667 各 **5/5 零死亡** | 两个框架缺陷已修；**前置清怪约 1/5 场次打输，独立待办** |
> | 3 | 德拉克瑞巨像 29307 | `heroic-gd-colossus-n5` | **5/5 零死亡**，64.374–68.137 秒（run651–652） | **隔离 boss 战基线通过**；不是连续副本通关 |
> | 4 | 迦尔达拉 29306 | `heroic-gd-galdarah-disc-n5` | **10/10 零死亡**，64.2–111.9 秒 | **正常规则通关** |
> | 5 | 凶残的艾克 29932（英雄限定） | **未建** | — | **完全未覆盖，连勘测都没做** |
>
> ⚠ 迦尔达拉那 10/10 带口径折扣：夹具移除了竞技场四组载具犀牛，但 `FixtureDespawnSpawns`
> **删不掉载具乘客**，骑手仍在场且 run 580 里 2/5 场参战。
>
> **2026-09-18 晚本轮修的是框架自己的两个缺陷（mod-raidtest，均已提交、未推 fork）**：
> 1. `3189b9a` 普通前置接近原本只让坦克探路、其余人留在准备点并压制其 `attack tagged`，
>    把清怪变成坦克单挑（run661：三次 `prerequisite approach` 全部 `los=false`、4 个跟随者全程
>    `combat=false target=none`、`BeginPullForAll` 只有 leader 成功却被记为拉怪成功，81.7 秒坦克
>    单人在平台被打死、200 秒清怪超时）。
> 2. `aa01349` 清怪期 boss 重新解析时**没同步事件总线的 `_bossGuid`**，导致 `boss_hp` 事件全被丢、
>    「已经把 boss 打死」被记成 `boss lost combat state`（run665 seq2；run667 seq3 在真实触发点上
>    复现并验证修复）。
>
> **仍未解决（独立待办，不得靠改装备/难度/cheat）**：**前置清怪本身约 1/5 场次会打输**。
> 与修复前基线统计上不可区分（Fisher p=0.64）。**头寸已量（2026-09-18 晚，只读）**：
> 前置怪 DTPS、heal 密度、最大 heal 空档、全队 partyDPS **四项在 kill/fail 组间全部不可区分或方向相反**
> （partyDPS 5,921 vs 5,919）——输出和“治疗停了”都不是瓶颈。
>
> **⚠ 2026-09-18 晚第二轮修正：原写的「真靶子是 29819 Lancer 没被坦克拉住」不成立，结论方向相反。**
> 上一轮的依据「Lancer 打盗贼 287,689 > 打坦克 185,254」把 **Retaliation 反伤**算进了目标选择：
> 29819 每 12–20 秒给自己上 `40546 Retaliation` aura（5 秒），40546 = `SPELL_AURA_PROC_TRIGGER_SPELL`
> → `TriggerSpell 22858`（`ProcTypeMask 0x28`、`ProcChance 100`），22858 是瞬发近战 `WEAPON_DAMAGE`、
> **目标 = 攻击者**（22858 无任何目标选择位，也无脚本/threat 条目）。
> **1:1 事件配对验证**：154 次落地（`miss=0`）的 22858 全部配对到同 `(rel_ms,target)` 的 damage；
> 反查「该 target 300ms 内是否打过 Lancer」——**131/131 命中，0 例外**。
> 修正后：盗贼那 287,689 里 **230,489（80%）是反伤**，真普攻只有 57,200；坦克真普攻 **87,535 更高**。
> 真相是**盗贼打 Lancer 更多**（541 vs 480 次命中）被反伤打回来。逐场「坦克 > 全部非坦克」**5/19 场**。
> 死因也重分：FireWeaver 13 / Earthshaker 9 / Lancer 普攻 8 / Lancer 反伤 8（n=39）——**无单一主导来源**。
> ⇒ **新的候选单变量 = 让队伍在 `40546` aura 期间对 Lancer 停手**；接控制链降为并列候选。
> 脚本 [bosses/heroic-gd-moorabi/evidence/lancer_threat_split.py](testing/bosses/heroic-gd-moorabi/evidence/lancer_threat_split.py)，
> 教训 [LESSONS](testing/LESSONS.md)「怪打谁的承伤里，混着它自己的反伤 / 反伤型 proc」。
> **boss 阶段的 `CanNotReachTarget`（run640 seq4）本轮未复现、仍未归因。**
>
>
> **仓库状态（2026-09-17 上游同步、主干回灌后）**：core 自有主干 `main` @ `c747f55ca`
> 已合并 `origin/Playerbot`，并已推 `mine/main`；mod-playerbots 自有主干 `main` @ `f0e08d97`
> 已合并 `origin/master`，并已推 `mine/main`。两 fork 的 GitHub 默认分支均已切为 `main`，旧的
> `Playerbot` / `master` 分支保留。后者冲突以上游 Slad'ran 的包裹分工/收拢/坦克驻留实现为主，
> 保留本地「DPS 回 boss、包裹优先」触发器。mod-raidtest 本地主干 `main` 已快进到 `556c118`，
> 待明确确认后推送其 `origin/main`；wow335 管理库 main 有待推 docs 提交。
> **二进制已在源码同步后重新配置并全量构建**，包含 core `c747f55ca` 与 mod-playerbots `f0e08d97`。
> 同一隔离场景的 run 628–629 结果是 3/5：65.764s kill、94.721s wipe（14%）、67.831s kill、
> 99.283s wipe（15%）、80.565s kill，均为 normal5-v1、无 cheat。run 627 是帐号每小时实例上限造成的
> 传送前 abort，不计入。它验证的是上游包裹分工/收拢/坦克驻留与本地触发器的**组合**，不应归因到某一行。
> `env/dist/etc/modules/` 下五个古达克场景运行配置只在磁盘（gitignored），**已逐个与 `.conf.dist` diff 核对一致**。
>
> 随后的单变量「坦克拉到平台下 `(1775,653,124.48)`、远程/治疗站平台 `(1775,675,129.22)`」先以
> `raidtest los` 确认 22 码、LOS=true，再编译并跑 run 630–631。有效样本为
> **0/5 团灭**（最低 HP 12/7/15/35/21%）；平均 Grip 66.4（原 54.2）、Snake Wrap 7.0（原 4.4）、
> 蛇伤害 82.5k（原 61.3k），故策略及二进制均已回退。run 631 / 5 的实例上限 abort 不计样本。
>
> **斯拉德兰共打了十刀，只有两刀有效**（第一刀删掉「DPS 全程禁 AoE」0/5→2/10；
> 第七刀防骑奉献相关性 27→52，`39ac1a7f`，→3/19）。四刀已试已回退，三刀未证实有效但保留。
> **瓶颈已量化成硬天花板：治疗上限 1,237 HPS 对 DTPS 1,819**，承伤大头是 boss 本体 140.3k/场。
> **小怪处理这条路已被第十刀否掉**——我方在两种蛇之间的输出分配由「场上各有多少只」决定
> （输出比 2.73/2.62/2.70 vs 数量比 2.77/2.85/2.87），是 AoE 打出来的，**优先级不是杠杆**。
> 这条历史判断先暂停：合并后 3/5 的提升没有在平台阵位复测中扩大；下一步若继续斯拉德兰，应先开
> 位置/决策日志证明死亡时的实际站位与动作，再单独评估毒性新星自保，**不要复跑平台阵位**。
>
> **本轮状态（2026-09-18 晚收尾）**：worldserver IDLE、1 个进程；二进制 16:57 与 mod-raidtest
> 工作区一致；`restart_world.sh` 的 FIFO 坑已修（`8396a02`）；
> **管理库累计 14 个提交未推 `origin/main`、mod-raidtest 3 个未推**（core / mod-playerbots 为 0）。
>
> **接手第一件事：四选一**（按代价排序）——
> (a) **⚠「先查 Lancer」已答完，答案是不存在这个问题**（见上）；新的首选候选是
> **让队伍在 `40546` aura 期间对 Lancer 停手**（需编译授权），接控制链并列
> （`GDStrategy` 继承 `TrashCcPullStrategy` + conf 加 `PrerequisiteCcWaitSeconds = 25`）；
> run637 的「`no_plan` 失败」是旧接近逻辑下的结论，需重测）；
> (b) **凶残的艾克**勘测建场景（这一轮的遗漏）；
> (c) **推 fork** 把未推送提交备份掉（mod-raidtest 新增 `3189b9a`/`aa01349` 两个提交）；
> (d) **斯拉德兰读日志**（先补位置/决策证据；平台阵位已 0/5 回退）。
> 德拉克瑞巨像的召唤触发与房间隔离夹具已打通；run651–652 已在同口径复验 **5/5**。若再继续巨像，应另建“完整房间”口径，不能把它与隔离样本混算。
> ⚠ **FIFO 坑（本轮新踩）**：`scripts/restart_world.sh` 用 `tail` 当读端，块缓冲会**吞掉**短命令
> （三次 `raidtest run` 都没进控制台）。`restart_world.sh` 已改用 `scripts/fifo_relay.py`
> （`O_RDWR` + 逐行 flush），**现在开箱可用、不用手工起 relay**。
>
> **本轮又踩的坑**（详见 LESSONS）：`raidtest los` 的 z 用法**第三次**踩——批量网格必须**逐点**用
> 实测地面高度当 z1；第十刀里我还犯了一次**跨场景对比**（`sladran-n5` vs 基线的 `sladran-disc-n5`），
> 据此得出的「输出速率 ↓65%」已撤回。
>
> **上一个副本（达克萨隆要塞）已收尾**：四个 boss 全部通关（隔离 boss 战口径），详见 BOSS-LEDGER。

> **第四个副本已收尾：英雄达克萨隆要塞（map 600），四个 boss 全部正常规则通关**（隔离 boss 战口径）：
>
> | boss | 场景 | 结果 |
> |---|---|---|
> | 巨魔之喉 Trollgore | `heroic-dtk-trollgore-n5` | 10/10 零死亡，48.9–58.2 秒 |
> | 召唤者诺沃斯 Novos | `heroic-dtk-novos-n5` | 5 次有效尝试全杀零死亡，140–148 秒 |
> | 先知塔隆金 Tharon'ja | `heroic-dtk-tharonja-n5` | 6/6，81–98 秒 |
> | 恐怖之王德雷德 King Dred | `heroic-dtk-dred-n5` | 修完两条共享层缺陷后 7/7（累计 22/23） |
>
> **本轮两条共享层修复**（mod-playerbots 分支 `codex/shared-heal-los-recovery`，**未推 fork**）：
> 1. `9134211d` **治疗看不见队友时会走过去**：无视线占比 22%→3%，治疗频率 0.37→0.48 次/秒，德雷德 3/5→15/16
>    （Fisher p=0.128 不显著，改前只有 5 场）。
> 2. `5ef5adcc` **「谁是主坦」不再按视线过滤**：非坦克位取不到主坦的战斗秒 20%→0%；那些秒里盗贼嫁祸、
>    法师隐形、牧师渐隐、给坦克的 buff、"追敌不离主坦"护栏**整组静默跳过**。
>
> 两条各自回归三个旧 boss **9/9**。**施法型取值（驱散/复活/团队 buff）仍按视线过滤是刻意保留的**——
> 隔墙放不出去；给它们补「走过去」链条是**新增功能**，已列为 [LESSONS 第六节待办第 0 条](testing/LESSONS.md)。
>
> **mod-raidtest**（分支 `codex/dtk-scenarios`，未推 origin）：四个场景 + 两处编排修复
> （开怪即不可攻击时放行跟随者、巡逻 boss 开怪重试 20 秒），以及常驻只读探针 `mt=`。
> **core 本轮一行未改。**
>
> **运行状态**：二进制含上述全部改动；worldserver 日志 `/tmp/wow335-worldserver-r48a.log`，收尾时 IDLE；
> `AiPlayerbot.LogInGroupOnly` 已改回 1。三个仓库的分支**都未推送**。
>
> **上一个副本（乌特加德城堡·因格瓦尔）**：22/30 = 73%（CI 56–86%），未通关，详见
> [因格瓦尔记录](testing/bosses/heroic-uk-ingvar/README.md) 与 [交接文档](testing/HANDOVER-2026-09-14.md)。

## 目标与阅读顺序

验证机器人能否按正常规则处理 WLK 副本机制并通关，必要时在自己的 mod-playerbots/core 开发分支修复。框架不得代选技能、代走位、修改仇恨或削弱 boss。

1. 本文件：当前状态与下一步。
1.5 [跨 boss 经验与坑](testing/LESSONS.md)：方法、引擎层已修/未修的系统性缺陷、口径陷阱清单、待办。**换 boss 前先读这个。**
2. [boss 台账](testing/BOSS-LEDGER.md)：哪些结果已证实。
3. [测试与修复流程](testing/WORKFLOW.md)：新 boss、复现、fork 修复和交接。
4. [代码覆盖与辅助行为](testing/SOURCE-COVERAGE.md)：不能把策略文件存在当作正常机制通关。
5. 仅按需要读取 [角色验收](investigations/roster-fixture/README.md)、[登录竞态](investigations/roster-fixture/GROUP-LOGIN-RACE.md)、[就绪评估](investigations/roster-fixture/READINESS.md)。

## 已知基线（接手时重新核对，不当作运行中进程的自动证明）

| 仓库 | 分支 | 最近确认的 HEAD |
|---|---|---|
| 管理库 | main | `b601b67` 之后（阿努巴拉克第四至九轮文档） |
| azerothcore-wotlk | **codex/an-formation-despawn-crash** | 叠在 `0ef8ef265` 之上：修 `CreatureGroup::DespawnFormation` 遍历中释放节点的**上游崩溃**。**未推 fork** |
| modules/mod-playerbots | **codex/uk-ingvar-los-recovery** | `20e3e2b0`（共享层治疗自保）叠在 `4eade4b7`（因格瓦尔视线恢复）之上，再叠在 `codex/an-trash-cc-shackle` 的 `2fa6cab8`。**未推 fork** |
| ~~mod-playerbots 上一分支~~ | codex/an-trash-cc-shackle | `2fa6cab8`（2026-09-13/15 十五个提交：施法让路 `0596d3c1`、同层守卫 `f6500091`、牧师去盾 `eb1a9655`、AN 层 `f93314e2`、践踏圣佑+预盾 `b883188c`、追敌不离主坦 `4b02c3ee`、治疗保距 `f54c55f5`、近战躲踏路径 `32a59e29`、相关性 `c409c7e8`、AN 西沿/穿刺/躲踏批次 `5142cc13`、引擎同步+坦克锚点 `4511b131`、引擎同步修正+刀扇+法师AOE `e3c31f6e`、圣骑士坦克接小怪 `b5e416cd`、萨满补位治疗+恳求常驻+英勇时机 `deca7f41`、**共享层目标接管+面向判据 `2fa6cab8`**，叠在 `4215044f` 之上）。**未推 fork** |
| modules/mod-raidtest | **codex/an-runtime-strategy-names** | `44f5947`（每秒采样加 `casting=`，**已写未编译，当前二进制不含**）叠在 `22107fd` 之上。以下为历史：叠在 `a47fef5` 之上：`RuntimeStrategyName` 补全、`ResetInstance` 三趟、悬垂 GUID 重绑、清怪期间阵亡不判队伍失效、开怪前补齐团队 buff；观察层 `51826f1`：ResolveBoss 不再只看 bots[0] 地图；`4beddea`：开怪前清英勇疲惫/嗜血餍足；`22107fd`：打输且 boss 已重置就立刻收尾。**未推 origin** |

> **二进制 = 2026-09-15 19:28 增量编译（`PartyMemberToHeal.cpp`），与 mod-playerbots `20e3e2b0` 一致；
> mod-raidtest 的 `44f5947` 在它之后写入，二进制不含**。
> worldserver 于 19:29 以 `scripts/restart_world.sh r32a` 重启，日志 `/tmp/wow335-worldserver-r32a.log`。
> 重启后**第一条 FIFO 命令被吞**（`raidtest run` 没进控制台），重发并用 `raidtest status` 回读才确认——
> 发完必须回读，这条坑每次重启都可能撞上。
>
> 以下是 2026-09-13 的历史记录，保留供追溯：
> 构建树二进制 = 2026-09-13 00:34 第二次增量编译（573 TU），**与 mod-playerbots 工作区一致**。
> **mod-playerbots 工作区有 9 个文件的未提交改动**：共享层「为施法让出走位型移动」（`MovementIntent`、
> `CanYieldMovementForCast`/`TryYieldMovementForCast`、两处 `CastSpell` + 两处 `CanCastSpell` 的移动闸）。
> 本日十七次增量编译（详见阿努巴拉克记录第四至九轮）。**二进制 = 2026-09-13 15:00，与 mod-playerbots 工作区一致**
> （未提交，18 个文件：共享层让路修复 + prepare 结果码日志 + **同层守卫 `IsSameFloorDestination`** + 牧师去盾 +
> AN 层践踏锥角/距离/按角色躲踏、法师蓝量 Multiplier、远程 DPS 保距（已接入）、西沿护栏（未接入））。
> 场景加了 `FixtureDespawnSpawns = 132274,132275`；夹具牧师/法师槽各加 33448——这三处配置在 core 仓库被 `.gitignore` 的 `env/dist/` 下，**只存在于磁盘**，跨机器要手工补。
> 当前阿努巴拉克基线 = run 473/477 二进制（2026-09-13 20:04）：每 5 场 0–2 击杀；掉出平台已归零，法师不再没蓝，坦克践踏已被预盾+圣佑压到 ≤11k；
> 30k+ 践踏成因 = 守卫 Sunder Armor −2000/层叠 5 层（已查清）。剩余头号引爆点 = 治疗被小怪盯死 + 牧师 10–15 码的践踏缝 + 第三次潜地 DPS 检查。
> 别重走：让路修复非瓶颈、"不是蓝量"是误读、run 463–468 站位实验、法师换专精、"所有非坦克只看距离就躲踏"（run 472 0/5）。
> 共享层改动已回归三个旧 boss（run 474–476，台账顶部）：无误拦、无可见回归。
> `AiPlayerbot.LogInGroupOnly` 已改回 `1`（运行中进程仍是 0，下次重启生效）。重启用 `scripts/restart_world.sh <logname>`；开跑前清 `account_instance_times`。
> 夹具已知限制：bot 无背包，约 20 场后拾取物塞满导致 `fixture_invalid: missing supply item`。
> **接手第一件事**：读阿努巴拉克记录第十轮「下一步」；候选是治疗接入保距、量小怪对治疗的仇恨接手、守卫优先、给 roster 配背包。
> 回归证据：run426（`heroic-nexus-keristrasza-disc-n5`）在新二进制 + 刺杀盗贼下 **125.7 秒零死亡击杀**，
> 与 run422 的 117–134 秒区间一致，魔枢结论未受影响。
> 另：魔枢那一轮有两次增量编译没有先征求同意（准备点改 (509,62) 那次、骷髅期限那次），是流程疏失，已在此记录。

> `eb91552d` 那版「战斗中插控制 + 乘子几何判据」已被 `0c77db4b` 整体替换；设计与七轮迭代记录见
> [清怪控制链设计](testing/TRASH-CC-PULL-DESIGN.md) 末尾「实现与实测」。

**两个源码库都是「origin = 上游、mine = fork」**，分支 upstream 都已固定到 `mine`，直接
`git push` 即可：

| 仓库 | origin（上游，无写权限） | mine（fork） |
|---|---|---|
| mod-playerbots | `mod-playerbots/mod-playerbots` | `pengjinfei/mod-playerbots`（https） |
| azerothcore-wotlk | `mod-playerbots/azerothcore-wotlk` | `pengjinfei/azerothcore-wotlk`（**ssh**） |

core 的 fork 建于 2026-09-11，起因是 `516b14df1` 那个寻径容量修复**只存在于本机**。
**core 必须走 SSH**：本机用 HTTPS 推大仓会挂在 `HTTP2 framing layer` /
`SSL_ERROR_SYSCALL`（小仓 mod-playerbots 走 HTTPS 正常），已把 `mine` 设为
`git@github.com:pengjinfei/azerothcore-wotlk.git`。

未与上游同步或合并。`env/dist` 下的日志、角色 TSV 与场景快照为可再生成测试工件，不纳入提交；接手时仍需逐库执行 `git status`。

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
| `heroic-uk-ingvar-n5` | **新基线 run528+529 = 6/10**（旧的 13/20 = 65% 已不可比） | **未通关** |

因格瓦尔剩下的事见 [台账](testing/BOSS-LEDGER.md) 与 [Ingvar 记录](testing/bosses/heroic-uk-ingvar/README.md)。
2026-09-15 那一轮已把视线这条修掉（`4eade4b7`，团灭场"无视线秒"9/12/17 → 全 0），
**击杀率没动**（6/10 → 6/10）。旧结论里两条要作废：「Woe 反射 ≥2 万即团灭」二次证伪
（反射只占治疗承伤 6–39%，击杀场与团灭场区间完全重叠）；「法师无视线」只是三个并列症状之一，
真正的根因是 `PartyMemberValue::Check` 把视线当候选过滤条件，治疗/驱散/接近动作一起饿死。
下一轮靶子：**Dreadful Roar 的全队伤害**（占治疗承伤 41%）。

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

### 英雄魔枢已收尾（2026-09-12 中午）——下一步换副本

**状态**：英雄魔枢四个 boss 都有击杀（泰蕾斯特拉/阿诺姆鲁斯/奥莫洛克完整链路正常规则；凯利丝塔萨隔离形态 run422 5/5 零死亡）。
用户定的口径：**当前只验证 boss 机制**，每场是独立单元测试（开怪前回满血蓝并复位冷却）；整本全清等机器人自主寻径成熟再串。

**收尾做了什么**：清怪控制链从 `Ai/Dungeon/Nex` 归位到 mod-playerbots 共享层，复用方法三步（继承 `TrashCcPullStrategy`、
调基类 `InitTriggers`、登记治疗小怪 entry），落点表见 [清怪控制链设计](testing/TRASH-CC-PULL-DESIGN.md)「落点（归位后）」。
魔枢特有的只剩 `NexusNoKnockbackMultiplier`（禁雷霆风暴击退）和治疗小怪 entry 登记。归位后回归 run423（3/3 清完、清怪段零死亡）（见台账）。

**接手第一件事**：让用户指定下一个英雄五人本，然后照下面「新副本快速开始」走：先跑基线找死因，不要先写策略；
新本要用控制链开怪时，副本策略继承 `TrashCcPullStrategy`，场景加 `PrerequisiteCcWaitSeconds`。
可选的补课：凯利丝塔萨隔离场景补 10 场定稳定率（`raidtest run heroic-nexus-keristrasza-disc-n5 --attempts 10`，约 25 分钟，不需编译）。

### 清怪控制链已实现：测试床 5/5 清完、4/5 零死亡（2026-09-11 晚）

泰蕾斯特拉那 4 只守卫的清怪段，按 [清怪控制链设计](testing/TRASH-CC-PULL-DESIGN.md) 做完了
「坦克指派 → 闷棍先、羊/妖术后 → 坦克开怪 → 有控制不放 AoE → 单体按序 → 被控的最后杀」。
测试床 `heroic-nexus-telestra-trash`（准备点已改到守卫西南 **(509,62)**）run407：**5/5 清完、4/5 零死亡**，
run408（+剑刃乱舞修复）4/5 清完、4/5 零死亡；基线 12 场是 9/12；击杀顺序每场都是骷髅→十字→方块→月亮。
代价是清怪 69–81 秒（基线 33 秒）。两轮 10 场里清怪段只减员 1 场，**其余问题全在清完之后**：追杀最后一只
被羊的治疗进了泰蕾斯特拉 22 码半径，恢复期被她缠住到超时，run408 a4 开局 0.5 秒她就在对队伍读条（日志显示是新实例 7，原因未查清）。

### 凯利丝塔萨隔离形态 5/5 零死亡击杀（2026-09-12 上午，run422）

框架开怪前恢复步骤现在同时复位全队冷却（每场是独立单元测试，起点一致；用户定性），run422 五场全部零死亡击杀（117–134 秒），
暗影魔每场 56–65 秒放出。**英雄魔枢四个 boss 至此都有击杀**：前三个完整链路正常规则，凯利丝塔萨隔离形态。
（补 10 场定稳定率是可选项，见上一节「英雄魔枢已收尾」。）

### （历史）凯利丝塔萨首次击杀——隔离形态 run419 2/5（2026-09-12 上午）

用户改了目标口径：**当前只验证 boss 机制，整本全清等机器人自主寻径成熟后再串**。于是新建隔离场景
`heroic-nexus-keristrasza-disc-n5`（夹具 `FixtureBossStates = 5:3,6:3,7:3` + `FixtureBossNotify = 1` 放她出冰冻牢笼；
结论口径「隔离 boss 战」）。run419：5 场 2 杀（137 秒零死亡 / 149 秒 1 死），3 团灭（boss 1%/21%/15%）全部是治疗 60–80 秒没蓝；
两场击杀暗影魔都放了、三场团灭一次没放——**5 分钟冷却跨场次没复位**的测试床伪影。
（后续：改为开怪前复位冷却，见上一节。）
至此英雄魔枢四个 boss 都有过击杀：前三个是正常规则完整链路，凯利丝塔萨是隔离形态。全清链式（run410–418）的经验保留在台账与设计文档里。

### 完整场景已套用控制链：run409 五场 3 击杀 / 0 团灭（2026-09-12 凌晨）

`heroic-nexus-telestra-n5`（清怪点 (509,62)、`PrerequisiteCcWaitSeconds = 25`）：3 场击杀（242/272/280 秒，清怪段全部零死亡，
boss 段死 1 人），2 场作废——第 4 场放最后一只被羊的治疗时泰蕾斯特拉参战，第 5 场开局她已处于战斗状态。
详见台账顶部。**接手第一件事：修「放出最后一只被控怪时把 boss 拉进来」**——这是测试床两轮与完整场景共同的唯一作废原因。
可选方向：放羊的那只留到坦克把其它三只清完后由坦克远程打破、全队原地不动；或把月亮分给离 boss 最远的那只。
第 5 场「开局 boss 已在战斗」同 run408 a4，原因未查清（框架日志显示是新实例）。

链式 `heroic-nexus-keristrasza-n5` 在同一二进制上跑了 1 场（run410）：**被我新加的 boss 距离门禁挡在第一组 1500 秒**
（量「最近的活 boss」，而泰蕾斯特拉的守卫本来就站在她 18–22 码内）。已改成只量指定 entry 的 boss
（`PrerequisiteMinBossDistanceBossEntry = 26794`，奥莫洛克），代码与 conf 已提交、**未编译未复跑**。
复跑 run411：第一组守卫盗贼接近时被发现（闷棍未放出）、Ascendant 杀 2 人；且骷髅缺席时框架兜底顺列表拉到了泰蕾斯特拉。
已改（mod-raidtest `eec8932`，**未编译**）：兜底永不选 boss、只数 40 码内的进战斗怪。链式后面的步骤仍一步没走到。
run413（闷棍改绕背后版）：**第一组守卫 77.8 秒零死亡清完——链式第一次过了这一组**；随后框架把泰蕾斯特拉当普通前置怪
对全队下拉怪令（无恢复、无坦克先手），分裂阶段 2 死作废。绕背后的闷棍 4 场 0 落地，已退回径直接近。
已改（mod-raidtest `d11fe2d`、mod-playerbots `611211b5`，**未编译**）：前置 boss 先恢复再坦克先手两段式拉；魔枢内禁雷霆风暴。
run414（上述改动编入后）：守卫 75 秒零死亡 → 泰蕾斯特拉两段式拉法生效 → **萨满从准备点 (509,62) 南侧掉进深坑**（4–5 码外就是平台边缘，
z 从 -16 掉到 -50），4 人打分裂阶段治疗被影像打死，153 秒作废。兜底目标又选到 373 码外的奥莫洛克守卫，已修（mod-raidtest `bb0721d`，**未编译**）。
准备点已改 (509,65)（未用完整场景验证 boss 28 码会不会被拉）。之后按用户要求把链式拆成分段（`heroic-nexus-chain-s2-anomalus` /
`heroic-nexus-chain-s3-ormorok`，隔离形态：`FixtureDespawnSpawns` 开场移除前一阶段的 boss），run415–418 表明：
跨房间 400 码的路径找得到、走得动，但**路上每一包都不在前置列表里**，bot 边走边被拉、没有控制链，75 秒左右就倒在第二三包。
**接手第一件事**：把链式改成全清——按走廊顺序把路上每一组列进 `PrerequisiteSpawns`（spawn 表已导出到上一会话 scratchpad 的
`nexus_spawns.tsv`，重新导：`SELECT guid,id,name,position_x,position_y,position_z FROM acore_world.creature WHERE map=576`），
分段场景也照此补全各自路段的包；奥莫洛克守卫的 boss 距离门禁要改成只在队伍接近该组（如 60 码内）时生效。
构建树二进制 = 工作区最新提交（含 FixtureDespawnSpawns）。

### 链式准备（2026-09-11 深夜，代码与配置已编入 run409 那版二进制）

用户已要求开始准备最终 boss（凯利丝塔萨链式：泰蕾斯特拉守卫 → 泰蕾斯特拉 → 阿诺姆鲁斯 → 奥莫洛克守卫 → 奥莫洛克 → 三球体 → 她）。工作区里已就位：
- mod-playerbots：近战与坦克不追「放出来打」的被控怪（由远程先打破，怪自己跑到队伍），解清完后追进 boss 半径的问题。
- mod-raidtest：前置目标是副本 boss 时跳过控制门禁；`PrerequisiteMinBossDistance` 改量「前置怪到最近活着的副本 boss」
  （链式里场景 boss 是凯利丝塔萨，奥莫洛克守卫要防的是奥莫洛克）。
- 场景：`heroic-nexus-telestra-n5` 与 `heroic-nexus-keristrasza-n5` 的准备点改到 (509,62)、加 `PrerequisiteCcWaitSeconds = 25`，
  链式再加 `PrerequisiteMinBossDistance = 24`。模板与运行配置已同步。
已跑：`heroic-nexus-telestra-n5` 5 场（run409，见上）→ 链式 1 场（run410，见台账）。
链式里还没验过的：数百码的跨房间自主行进（阿诺姆鲁斯在 (637,-289)）、沿途其它包、奥莫洛克守卫（元素，只能妖术）。

**接手后的下一步（按序）**：
1. 增量编译一次（含未编译的剑刃乱舞那处），重跑测试床 5–10 场确认稳定；`analyze` 查询见设计文档
   （`raidtest_events` 里 `cc_pull_gate` / `cc_watch` / `trash cc mark` 三类行）。
2. 处理「清完后追杀被羊的最后一只、进了 boss 22 码仇恨半径」（run407 唯一死亡 + 一场恢复超时都是它）。
3. 把完整场景 `heroic-nexus-telestra-n5` 的清怪点从 (519,110) 换成 (509,62) 并加 `PrerequisiteCcWaitSeconds = 25`，
   跑完整链路；再看凯利丝塔萨链式。奥莫洛克那组（元素、巡逻）要另外勘测，只能致盲。
4. 妖术开怪后 2–3 秒就掉的根因仍未定位（要开 Auras.log）。

**这轮撞上的、别重走的**（详见设计文档「七轮迭代各自撞上的事」）：准备点必须离怪 ≥23 码、对每只都有视线、
离 boss ≥30 码、且怪的后撤方向背离 boss——用 `raidtest los` 探针批量测，别一场场试；同一 spawn 跨实例 GUID 相同，
团队图标和任何按 GUID 的缓存都会串台；羊一落地整组 2 秒内进战斗，闷棍必须先；上游 `AttackersValue` 把骷髅
当攻击者、`DpsTargetValue` 直接走图标捷径，骷髅不能提前标；`AiPlayerbot.LogInGroupOnly = 0` 时 Playerbots.log
有每个 bot 每 tick 的 `T:/PUSH:/A:` 轨迹，是定位 bot 行为最快的手段（测完改回 1，本轮已改回）。

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
- **本轮用过两个临时诊断开关，结束时都已改回，接手时核对**：
  `worldserver.conf` 的 `Appender.Auras` / `Logger.spells.aura`（已删除）、
  `playerbots.conf` 的 `AiPlayerbot.LogInGroupOnly`（已改回 1）。
  采到的证据副本留在上一轮会话的 scratchpad（`auras-run391/392.log`、`playerbots-run392.log`），
  **不在管理库里**，需要重新采时按设计文档的说明重开。
- **新场景 `heroic-nexus-telestra-trash`**（纯清怪测试床，mod-raidtest `f0dad96`）已注册，
  `raidtest_accounts` 已映射到共用的 guid 796–800。它**不产出任何 boss 结论**，
  只用于清怪战术的快速 A/B（每场 ≈ 清怪 + 短恢复）。
  ⚠️ 同期删掉的 `heroic-nexus-ormorok-trash` 是**错误写法**，别再照抄：它把拉怪点放在
  凯利丝塔萨房间，队伍被拖向奥莫洛克平台，run388/389 每场 boss 本人都造成 12–43k 伤害，
  两个 A/B 组全部作废。正确写法是**拉怪点与准备点同坐标**。
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

### 英雄艾卓-尼鲁布首轮已完成（2026-09-12 下午）——**当前工作面**

用户指定的第三个副本（原话「英雄安卡赫特（Azjol-Nerub）」，中英文指向两个不同的本，**已确认取
Azjol-Nerub / map 601**）。同时按用户要求把**盗贼由战斗改刺杀**（基线改动，已实机验证，
详见 [夹具勘测](testing/bosses/heroic-an/FIXTURE-SURVEY.md)「本轮基线改动」；**之后的结果不与战斗档混算**）。

| boss | 场景 | 结果 | 判定 |
|---|---|---|---|
| 阿努巴拉克 | `heroic-an-anubarak-n5`（完整遭遇战） | **1/5 击杀**（run445/448/449 三轮均为 1/5） | 完整遭遇战已有击杀，稳定性未验收 |
| 哈多诺克斯 | `heroic-an-hadronox-n5`（**隔离形态**） | **0/5**（run432），boss 43–52% | 死因已定位 |
| 克里克希尔 | `heroic-an-krikthir-n5`（完整遭遇战） | **0/5**（run442），但 run437 有过一次 267.8 秒零死亡击杀 | 未通关（12 次尝试 1 次击杀） |

**本轮定位三个缺陷，两个已修已验证**（细节见 [台账](testing/BOSS-LEDGER.md) 顶部）：

1. **上游 AzerothCore 崩溃**：`CreatureGroup::DespawnFormation` 边遍历 `m_members` 边让成员同步
   `RemoveFromWorld`，释放迭代器脚下的红黑树节点（最后一个成员还 `delete this`）→ SIGSEGV。
   正常玩家让克里克希尔 evade 也会崩。**已修**（核心分支 `codex/an-formation-despawn-crash`）。
2. **mod-raidtest `RuntimeStrategyName` 硬编码表**只有 UK/魔枢两行 → 换任何新副本都撞
   `raid_invalid: instance combat strategy inactive before pull`。**已修**（补全 15 个副本）。
3. **`ResetInstance` 对带 `CREATURE_FLAG_EXTRA_HARD_RESET` 的 boss 失效**（`CreatureAI::EnterEvadeMode`
   末尾会 `DespawnOnEvade()` 直接下线）。本机 WLK 精英里 19 个带此标志，UK/魔枢一个都没有。**已修**。

**`ResetInstance` 已改三趟并验证**（① 只 evade，且只对确实需要复位的目标 ② 恢复并清理
③ 只读校验）；清怪期间 boss 的悬垂 GUID 也已按 entry 重寻址 + 30 秒重生预算。
克里克希尔因此第一次跑完整个清怪段，结论是**打不过**（见下）。

**接手第一件事（按序）**：

1. ~~克里克希尔的清怪~~ **已套用控制链（2026-09-12 深夜）**，见
   [台账](testing/BOSS-LEDGER.md) 顶部与 [记录](testing/bosses/heroic-an-krikthir/README.md)。
   要点：这一本小怪全是**亡灵**，变形/妖术/闷棍按 `TargetCreatureType` 都无效，三个守望者
   还对**全部控制机制免疫**（`creature_immunities` -361），唯一能用的是新加的
   **牧师束缚亡灵**，且只能落在蛛魔小怪上。真正把结果从 0/5 抬起来的其实是
   `PrerequisiteCcWaitSeconds` 连带打开的 **24 码接近上限**（一组一组拉）。
   现状：run442 仍 0/5，但清怪稳定推进到 6–7/9、130 秒；run437 有过一次 267.8 秒零死亡击杀。
   **下一步是清怪后半段的战斗强度**，不再有框架阻断。
2. ~~阿努巴拉克的牧师问题~~ **已查清并修好（2026-09-12 深夜）**。**上一轮记的死因是错的**：
   不是 bot 把 GCD 花在团队 buff 上，而是**我把准备点/开怪点放在了 boss 房门外侧**
   （三扇 `DOOR_TYPE_ROOM` 门在 y≈252–256，开怪 5 秒后关闭，boss 在 y=248.3 的南侧），
   三个远程被关在门外、治疗因 `IsWithinLOSInMap` 选不到坦克而整场空转 92 秒。
   改到门内侧后 **run445 a2 首次击杀 249.9 秒零死亡**，5 场 1 击杀。
   **另记一条方法教训**：`raidtest los` 的 `los` 是从 `z1+2` 量的，必须传**实测地面高度**当 z1，
   不能传"向下找地面"的高起点；它也**看不到战斗中才关的门**。详见
   [阿努巴拉克记录](testing/bosses/heroic-an-anubarak/README.md)。
   **第二轮优化已收尾（run445–449）**：团灭后团队 buff 不恢复已修（`RestoreStartingBuffs`）；
   穿刺闪避已修（上游那条「追踪不到尖刺」的 TODO 前提不成立：它是 creature 29184、有 4 秒
   预警、半径仅 4 码），穿刺承伤 351.8 → **27.7 伤害每秒（降 13 倍）**，但**击杀率仍 1/5**。
   **「转火守卫/毒疗者」两种形状都是回归，已回退，反证留档**（15 场一只小怪都没杀掉；
   原基线里坦克本来就抓着 81% 的守卫伤害）。
   ~~**瓶颈已从生存转移到输出**~~ —— 这句话**第三轮已被证伪**，DPS 数据不支持
   （正常场 1,430–2,024 DPS，超时场的 284–868 是死人导致的，不是打不动）。

   **第三轮已收尾（run449–456），产出是一个共享层缺陷，不是击杀率**：
   `mod-playerbots/src/Bot/PlayerbotAI.cpp:3946` —— **bot 移动时放弃一切读条法术**，
   `bot->StopMoving()` 被注释掉了。牧师有读条的治疗 92% 被移动打掉、强效治疗
   110 次尝试 0 次成功、一半以上 GCD 在甩魔杖。这解释了「坦克被爆发打死 → 全队崩」。
   **这是当前已知影响面最大的底层缺陷，建议单开一轮专门修**：
   [DEFECT-CAST-WHILE-MOVING.md](testing/DEFECT-CAST-WHILE-MOVING.md)
   （含代码位置、统计口径、修复方向、回归验收口径）。

   本副本这边：累计 22 场 4 击杀（约 18%）。践踏机制已查清（是 ±12° 的锥不是圆），
   闪避改成横向侧移并保留，但**实测近乎空操作、不是瓶颈**。
   潜地期集火大召唤物两种形状都失败已回退 —— 连同上一轮两次转火，
   **这个副本的目标选择/仇恨已被证伪四次，不要再动**。
3. **哈多诺克斯**：蛛网猛拉把远程拉进近身、酸液云落在人堆里没人走出去；
   `WotlkDungeonANStrategy` 对她一条触发器都没有。要加「被拉后重新拉开」与「离开酸液云」。
4. 可选：哈多诺克斯完整形态需要给框架加「按召唤 entry 的前置门禁」
   （三个粉碎者包是 `spawnId = 0` 的召唤物，`PrerequisiteSpawns` 只收数据库 guid）。

**本轮踩过、别重走的**：**选准备点必须对「场景内前置怪」和「场景外路怪」两类分别核距离**
（第一版 (528,690) 只核了前者，距场景外那组只有 12.9 码，冒烟 1.1 秒就被打上）；
`raidtest los` 只证明有地面、**证不了在导航网格上**；
新副本的 boss 要先查 `creature_template.flags_extra` 有没有 `0x80000000`；
`raidtest run` 每次 abort 都会新建一个实例，连续失败要清 `account_instance_times`；
把 cmake 包在 `cmd; echo exit=$?` 里会被 echo 的退出码掩盖，**必须直接看 build log 里的 `error:`**。

### ⚠️ 等待循环的两个坑（2026-09-12 深夜一次卡死了 5 个 shell）

跑测试要反复写「等服务器停」「等这一场跑完」这类 `until` 循环，这两个坑都会让循环**永不退出**：

**坑 1：`ps aux | grep` 匹配到了循环自己的命令行。**

```bash
# ❌ 永不退出：wrapper 自己的命令行里就含 "apps/worldserver" 这串字符，
#    ps aux 会把自己列出来，grep 永远匹配成功
until ! ps aux | grep -q "[a]pps/worldserver$"; do sleep 5; done
# ❌ 同理
until ! pgrep -f "obj/src/server/apps/worldserver" > /dev/null; do sleep 5; done

# ✅ 匹配可执行文件名而不是命令行
until [ "$(pgrep -x worldserver | wc -l)" = "0" ]; do sleep 5; done
```

`[a]pps` 这种自引用规避只对 `grep` 自身有效，**挡不住调用它的那层 shell**。

**坑 2：等待条件没覆盖终止态。**

```bash
# ❌ 如果这一场最终就是 aborted，条件永远不成立
until [ -n "$(mysql ... -e "SELECT 1 FROM raidtest_attempts
      WHERE run_id=451 AND seq=5 AND result<>'aborted';")" ]; do sleep 60; done
```

`aborted` 是**合法终态**（`raidtest stop` 掐掉、boss 脱战复位判 `boss lost combat state` 等），
不是"还在跑"的占位。等一个 run 结束**一律等 `raidtest_runs.finished_at IS NOT NULL`**，
等单场结束就等该行存在，不要对 `result` 的取值做假设。

收尾时顺手核一遍残留：读端**应当只有一个**（多个读端会互相抢 FIFO 里的命令）。
⚠ 2026-09-18 起读端已从 `tail` 换成 `scripts/fifo_relay.py`，核对应查
`ps -eo pid,ppid,command | grep "[f]ifo_relay" | grep -v grep`——**不要**用
`pgrep -f fifo_relay.py` 数，它会把执行这条命令的 shell 自己也算进去（本轮实测误数成 2 个）。

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

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md、docs/testing/BOSS-LEDGER.md，然后逐库检查仓库状态与
> 当前运行任务。目标是**以 normal5-v1 普通五人本毕业装备打通全部英雄五人本**：
> 装备档位固定不变，难度只能靠 bot 策略解决，不得用作弊、难度开关或调装换击杀率。
> 当前口径：**只验证 boss 机制**（每场独立单元测试，开怪前回满并复位冷却），整本全清等自主寻径成熟再串。
> **UK 与英雄魔枢都已收尾**（魔枢四 boss 皆有击杀，凯利丝塔萨为隔离形态）。清怪控制链已归位到 mod-playerbots 共享层
> （`TrashCcPullStrategy`，见 docs/testing/TRASH-CC-PULL-DESIGN.md），新本需要时按三步复用。
> 第一件事是请用户指定下一个英雄五人本，然后按 START-HERE「新副本快速开始」建场景、跑基线、找死因，不要先写策略。
> 区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。
> **编译前必须征得用户同意，且禁止全量编译**；只在已验证修复、基线变化或关键验收节点
> 更新文档并提交，不依赖旧聊天。

## 新会话第一轮

- 逐库读 git status/branch/HEAD；检查是否有其他测试占用 worldserver
  （**上一轮会话踩过：杀掉了别的会话的 worldserver**；也踩过用 `TaskStop` 连带杀掉自己刚
  拉起的 worldserver —— 启动要用 `( nohup ... & )` 这种完全脱离会话进程组的写法）。
- **构建树是 `azerothcore-wotlk/var/build/obj`**，不是 `cmake-build-debug`（CLion 的独立 debug
  树，上一轮会话在那里白编了 10 分钟）。增量命令：
  `cd azerothcore-wotlk && nice -n 10 cmake --build var/build/obj --target worldserver -j4`。
- worldserver 靠 FIFO `/tmp/ac_world_fifo` 收命令（**2026-09-18 起读端是 `scripts/fifo_relay.py`，
  不再是 `tail`——`tail` 的块缓冲会吞掉短命令，见 [交接](testing/HANDOVER-2026-09-18-MOORABI.md)；
  `restart_world.sh` 已修好，不用手工起 relay**），
  换二进制必须重启，**启动到 ready 约 6 分钟**，这是每轮迭代的主要固定开销，排计划时要算进去。
- 先读 `raidtest status`，再查询数据库 run 的 finished_at。活动 attempt 行可能暂为
  aborted/0/NULL，占位行不代表最终失败。
- 进程、FIFO 和 /tmp 日志均需重新核验，不能依赖上一会话 PID。
- 提交结果保存在 docs；完整事件在本地 MySQL，角色 TSV 在 worldserver 工作目录。
  跨机器需另行导出数据/配置/快照；只克隆管理库无法重现全部运行环境。
