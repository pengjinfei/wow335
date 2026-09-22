# 莫拉比交接（历史记录；最终状态见下）

> ## 最终更新（2026-09-19，切换下一个 boss 前）
>
> - 实际构建树 `var/build/obj` 已编译并部署；run685 是当前代码的清库样本：**5/5 kill、零死亡、零 follower-pull abort**。
> - `pull failed` 已归因：同点 Engage 传送可让 follower 已进 combat 但临时无 boss LOS；`MoveChase` 在 run684 不移动，已改为仅在精确 `combat && !los && current/victim=none && valid` 分支释放该 follower。
> - run681–683 的五个前置阵亡均为刺杀盗贼(798)在 29819 的 `40546→22858` 反伤窗口死亡；Lancer 仍以坦克为 victim，排除失仇/追杀。
> - map-604 的盗贼局部抑制已实现；run685 无该死亡。但 seq3 没有 Hex，且两个 40546 窗口仍有少量盗贼攻击，**不得声称莫拉比已稳定或过滤已完全覆盖**。
> - 下一会话若切换 boss，不要再继续修改莫拉比；其未闭环项在 `bosses/heroic-gd-moorabi/README.md` 与 `TODO-2eaa72a5`。



> ## ⚠ 2026-09-18 晚第二轮：交接里的「下一步 1（查 Lancer）」已执行完毕，**结论是那个问题不存在**
>
> 本文件下面「前置清怪头寸」与「下一步 1」写的是「真靶子是 29819 Lancer 没被坦克拉住」，
> 依据是「Lancer 打盗贼 287,689 > 打坦克 185,254」。**那个口径错了，结论方向相反。**
>
> **22858 不是目标选择技能，是 `40546 Retaliation` aura 的 proc 反伤（谁打我打谁）**：
> 29819 每 12–20 秒给自己上 `40546`（5 秒）；40546 = `SPELL_AURA_PROC_TRIGGER_SPELL(42)`
> → `TriggerSpell 22858`，`ProcTypeMask 0x28`（被近战/技能打中就 proc）、`ProcChance 100`；
> 22858 瞬发近战 `WEAPON_DAMAGE`，**目标 = 攻击者**。22858 `Attributes = 0x00040000`
> （仅 `DO_NOT_SHEATH`），无目标选择位；`spell_script_names` / `spell_target_position` /
> `spell_threat` 均无条目。
>
> **1:1 事件配对验证**：154 次落地（`miss=0`）的 22858 全部配对到同 `(rel_ms,target)` 的
> damage；反查「该 target 300ms 内是否打过 Lancer」——**131/131 命中，0 例外**。
>
> 修正后（run664–667）：**盗贼那 287,689 里 230,489（80%）是反伤**，真普攻只有 57,200；
> 坦克真普攻 **87,535 本来就高于盗贼**。真相是**盗贼打 Lancer 更多**（541 vs 480 次命中）
> 被反伤打回来。逐场「坦克普攻 > 全部非坦克」**5/19 场**（旧口径是 13/19）。
>
> **死因也重新分解**（窗口 `[t-12s,t+2.5s]`，n=39 场前置玩家死亡）：FireWeaver 13 /
> Earthshaker 9 / **Lancer 普攻 8 / Lancer 反伤 8** / Lancer 流血 1——**无单一主导来源**，
> 「先查 Lancer」这个排序本身来自错口径。
>
> ⇒ **新的候选单变量 = 让队伍在 `40546` aura 期间对 Lancer 停手**（对着 450,544 的反伤）；
> 接控制链降为并列候选。探针/触发器认 **40546**（自身 aura），不是 22858（反伤本体）。
>
> 复现脚本：[evidence/lancer_threat_split.py](bosses/heroic-gd-moorabi/evidence/lancer_threat_split.py)；
> 教训：[LESSONS](LESSONS.md)「怪打谁的承伤里，混着它自己的反伤 / 反伤型 proc」。
> 本文件以下内容保持原样作为历史记录。

## 当前结论（一句话）

英雄古达克莫拉比（`heroic-gd-moorabi-n5`，Heroic / normal5-v1 / 无 cheats / **完整遭遇战**）的
**两个框架缺陷已修并验证**：run664–667 合计 **16/20 击杀（80%）**，其中 run664 与 run667 各 **5/5 零死亡**
（137.2–242.5 秒）。**但前置清怪本身仍有约 1/5 场次会打输**——头寸已量，靶子是
**29819 Lancer 没被坦克拉住**（见下）。**下一步就是查它，不用编译。**

两件**未解决**的事，互相独立，不要合并：
1. 前置清怪强度（靶子 = Lancer，见「前置清怪头寸」节）。
2. boss 阶段 `CanNotReachTarget`（run640 seq4）本轮未复现、仍未归因。

口径提醒：这是**完整遭遇战**（五个前置 spawn 一个不删），不是隔离档；不能与隔离样本混算。

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

run666 的三场失败细节（都**不是**框架问题）：seq1 / seq5 是**五只全清完**后在恢复期被 29819 Lancer
连续击倒盗贼；seq2 是**只清掉 2/5** 就被团灭。三场的共同点见下一节——**都是 Lancer**。

### 控制链是第二变量（前置五只 `type=7`，确实可用）

前置五只 `creature_template.type = 7`（Humanoid），**变形/妖术/闷棍按类型都有效**（不像艾卓-尼鲁布
那本全是亡灵、只有束缚亡灵能用）。但目前：

- 莫拉比场景 conf **没有 `PrerequisiteCcWaitSeconds`**（对比克里克希尔/泰蕾斯特拉/奥莫洛克/凯利丝塔萨都是 25）；
- `GDStrategy.h` 基类是裸 `Strategy`，`GDStrategy.cpp` 里 `// Moorabi` 下面是**空的**——共享层的
  `TrashCcPullStrategy::InitTriggers` 在古达克**根本没挂**（对照 `NexStrategy` / `ANStrategy` 是 `TrashCcPullStrategy`）。

**run637 那条「接入失败、反复 `no_plan`」的结论不能直接搬来否掉控制链**：那次用的是**旧的接近逻辑**
（每个 bot 各自找路、只走到 24 码外），而 `no_plan` 的直接成因正是「那个坐标看不到目标」——
本轮已把接近改成「leader 选共同落点、全队一起走到能开怪的点」。所以接控制链需要**重测**，不是已被否掉。

⚠ 但头寸量完后它**不再是首选**（见下节）：它解决的是「同时接敌数量」，而瓶颈是单只 Lancer 的目标选择。

⚠ LESSONS 第六节待办第 0 条（施法型取值补「走过去」链条）管的是**驱散/复活/团队 buff**——
隔墙放不出去，与这里无关。

## 前置清怪头寸已量化（2026-09-18 晚，只读，未改代码）

窗口 = `[0, 前置怪最后一只死亡时刻]`。⚠ 不能用「boss 首次伤害」当边界：run664 seq2 的 29305
在 194ms 就有伤害事件（上一场残留），会把窗口压成 0.2 秒。

| 指标 | kill 组（n=16） | fail 组（n=4） | 判定 |
|---|---|---|---|
| 前置怪 DTPS | 1,529 | 1,776 | 不可区分 |
| heal 采样密度（次/10s） | 5.8 | **6.5** | fail 组治疗反而更多 |
| 最大 heal 空档 | 7.7s | **5.6s** | fail 组反而更短 |
| 全队输出 partyDPS | 5,921 | **5,919** | 完全相同 |

**四项全部不可区分或方向相反。** 输出不是瓶颈，「小怪撒着打不死」在这组上也不成立
（输出按目标分布健康：Earthshaker 29.7%/29.6%、FireWeaver 18.9%、Lancer 16.7%、Inciter 4.9%；
死亡顺序每场稳定为 Inciter→两只 Earthshaker→Lancer/FireWeaver）。

**真靶子是 29819 Lancer 没被坦克拉住**：它打盗贼 287,689（39.3%）> 打坦克 185,254（25.3%），
⚠ **这两行已被 2026-09-18 晚第二轮推翻，见文件开头**：那 287,689 里 80% 是 `40546` aura 的
proc 反伤（谁打我打谁），不是 Lancer 的目标选择；坦克的真普攻承伤（87,535）本来就高于盗贼（57,200）。
而其余三只（29829 对坦克 496,878、29822 对坦克 159,669）伤害主力都是坦克。
run666 seq1 盗贼死前 3 秒承伤 12,677、seq5 为 18,519，**100% 来自 Lancer**。
**稳健性**：逐场看「打盗贼 vs 打坦克」，**19 场里 13 场（68%）打盗贼更多**（中位 13,668 vs 9,542），
不是 run666 的偶发。

⚠ 同时纠正我自己的两处口径错误：① 用 `actor_entry=797` 统计玩家行为（应用 `source_guid`）；
② 说「26 秒 heal 空档」——漏看中间采样，实际 17.7 秒且发生在快团灭之后（结果非原因）。

## 下一步（按序）

1. ~~**先查 29819 Lancer 为什么没被坦克拉住**（零编译成本）~~ —— **已执行完毕，结论是「不存在这个问题」**：
   22858 是 `40546` aura 的 proc 反伤（谁打我打谁），不是无视仇恨的目标选择技能。
   详见文件开头的第二轮修正。**不需要**再加 threat 采样，也**不需要**开 `LogInGroupOnly=0`。
   ~~新的候选单变量改为：**让队伍在 `40546` aura 期间对 Lancer 停手**（需编译授权）。~~
   **第三轮已量化并降为不推荐**（见下条 1b）：代价 30% 输出、收益仅 4.1% 承伤，
   且实测 proc 率只 31.6%（剩下的 70% 命中照样挨打）。
   ~~分清是「无视仇恨的目标选择技能」（22858，前置窗口内 248 次施法、对盗贼 113 次 / 对坦克 95 次）
   还是「仇恨/嘲讽链缺陷」。建议起手：~~
   - ~~查 22858 在 `spell_dbc` 的 `Attributes`/`AttributesEx*` 有没有与目标选择相关的位，
     以及 `spell_target_position` / `spell_script_names` 里有没有脚本；~~（已查：无）
   - ~~现有 `boss_threat` 只采样场景 boss，**不覆盖小怪**。要看 Lancer 选目标那一刻的
     threat table，得新加只读采样或开 `LogInGroupOnly=0` 读 `Playerbots.log`
     （测完必须改回 1）。~~（不需要）
1b. **候选单变量已重排（2026-09-18 晚第三轮，只读量化，未编译）—— 结论是「不要再换靶子」**：

    ⚠ 本轮先提了「换成 29829 对坦克的 494,710」，**随后自己把这条也否掉了**（同一错误的第三种形态）。

    前置窗口内队伍承伤分解（run664–667，按 `(rel_ms,target)` 正确配对）：

    | | 反伤 | Lancer普攻 | 流血 | 29822 | **29829** | 合计 |
    |---|---|---|---|---|---|---|
    | tank | 69,193 | 87,535 | 44,177 | 146,186 | **494,710** | 870,025 |
    | rogue | **230,489** | 57,200 | 0 | 24,563 | 93,981 | 406,634 |
    | mage | 24,523 | 26,722 | 2,984 | 15,920 | 89,099 | 159,248 |
    | shaman | 10,306 | 48,943 | 31,423 | 37,591 | 95,258 | 223,521 |
    | heal | 21,537 | 4,605 | 0 | 41,829 | 46,973 | 114,944 |

    单一大头确实是 29829 打坦克 494,710（占坦克承伤 57%），**但它不是杠杆**：
    - 29829 最大生命 **105,894**，其余四只 65,165（29874 只 15,750）——打得多首先是因为活得久；
      总伤害/最大HP 反而最低（29829 = 8，29822 与 Lancer 各 4）。
    - run639–667 按 kill/fail 分组逐来源 **Mann-Whitney U**：**没有一项显著**
      （29829 **p=0.53** / 反伤 p=0.66 / Lancer 普攻 p=0.06 / 29822 p=0.40 / 29874 p=0.52）；
      **连队伍总承伤都不可区分**（kill 中位 90,788 / fail 104,022，**p=0.85**）。

    ⇒ **前置打输不是「某只怪打太多」**，「挑一个最大的数字去针对」这条思路已被数据否掉。
    **新排序**：① **接控制链**（它改的是「同时接敌数量与焦点」，不是针对某只怪，设计已就绪）；
    ② 若仍要单变量，先量**过程**指标（同时接敌数 / 换目标频率 / 焦点集中度）与 kill/fail 的关联，
    **不要再从承伤排行挑靶子**；③ 「40546 期间停手」不推荐。

    反伤不推荐的三条依据（可复现）：
    - 对 Lancer 的 1,395 次命中里落在 5 秒 aura 窗内 **415 次 = 30%**，而反伤总伤害 356,048
      只占队伍前置总承伤（8.6M）的 **4.1%**；停手换来的是 200 秒超时风险。
    - 每次 aura 只落地 **2–8 次**反伤，窗口内 proc 率实测 **31.6%**（核心只对
      `DONE_MELEE_AUTO_ATTACK` 且命中判定通过的那次挥击 proc）——**反伤只是 Lancer 那
      234,525 普攻伤害的另一种结算形态**，不是独立大头。
    - 死因里反伤只占一小块：run639–667 前置窗口内玩家死亡 **14 次**（不是 39，39 是
      不限制在前置窗口内的口径）：`29822×4 / Lancer反伤×4 / Lancer普攻×3 / 29829×3`。
      run664–667 只有 2 次前置死亡，两次都是盗贼 100% 死于反伤。

    复现：`bosses/heroic-gd-moorabi/evidence/lancer_retaliation_rate.py`（A–E 段）与
    `bosses/heroic-gd-moorabi/evidence/run_result_source_split.py`（kill/fail 逐来源检验）。
    新增两条口径陷阱（写进台账）：**damage 行 `spell_id` 恒为 0**（不能靠它区分反伤/普攻）；
    **aura 窗口必须 `min(下一次施法, 施法+5000)` 封顶**（否则最后一段会把输出占比从 30% 夸大成 80%）。

2. **接控制链**（**本轮之后的首选**，需编译授权）：mod-playerbots 把 `WotlkDungeonGDStrategy` 改成继承
   `TrashCcPullStrategy` 并调 `TrashCcPullStrategy::InitTriggers`（参照 `NexStrategy` / `ANStrategy`）；
   场景 conf 加 `PrerequisiteCcWaitSeconds = 25`。注意会拉长清怪时长（魔枢测床 33s→69–81s），
   莫拉比前置超时 200s、当前 53–75s，余量约 2–3 倍。
3. **boss 阶段 `CanNotReachTarget`（run640 seq4）仍未归因**，本轮未复现，与前两项是不同的事。
   只有复现该异常时才重接临时日志：启动后、**排队前**执行 `server set loglevel 1 movement.chase 3`，
   在 `TargetedMovementGenerator` 的 accessibility 与 path-failure 分支分别记录源/目标状态与 path type；
   结束立即撤回并重编译。
4. 不要改装备、难度、cheat、怪物属性或把未死亡 spawn 记为击杀。

## 仓库状态

- 管理库：`main` `e47537c`，**累计 14 个提交未推 `origin/main`**（`d462bbe` 起到 `e47537c`，全部 2026-09-18）。
- core：`main` `c747f55ca`，未推送 0；仅有本地运行日志/快照未跟踪（`.gitignore` 含 `*.log`，
  但 core 仓库的忽略规则不覆盖它们，属既有状态，非本轮新增）。
- mod-playerbots：`codex/gd-takeover` `f0e08d97`，未推送 0，本轮无源码改动。
- mod-raidtest：`codex/gd-takeover` `aa01349`，本轮 2 个提交（`3189b9a` 前置拉怪 + `aa01349` 总线换绑），
  **相对本地 `main` 未推送 3 个**（含上一轮的 `8ec1420`）。
- 二进制：`azerothcore-wotlk/var/build/obj/.../worldserver` 2026-09-18 16:57 构建，
  **与 mod-raidtest 工作区一致**（源码 16:55）。worldserver 当前 IDLE。

## 接手核对清单（新会话第一轮照这个走）

1. 逐库 `git status/branch/HEAD`（四库：管理库 / core / mod-playerbots / mod-raidtest）。
2. `pgrep -x worldserver` 应只有 1 个。relay 的**正确形态是 2 行**
   （`sh -c python3 ... fifo_relay.py | ./var/build/obj/.../worldserver` 一条
   + 它 fork 出的 python 一条），核对命令：

   ```bash
   ps -eo pid,ppid,command | grep "[f]ifo_relay" | grep -v grep   # 期望恰好 2 行，且 ppid 对得上
   ```

   ⚠ **不要**用 `pgrep -f fifo_relay.py` 数：它会把执行这条命令的 shell 自己也算进去
   （本轮实测误数成 2 而实际也是 2，数值巧合，容易误判）。这条和 START-HERE
   「等待循环的两个坑」是同一个 `pgrep -f` 自匹配问题。
3. 发一条 `raidtest status` 回读（**必须回读**，不能只发）；应为 `state=IDLE`。
4. 跑测试前清库：
   `DELETE FROM acore_characters.account_instance_times; DELETE FROM acore_characters.instance WHERE map=604;`
5. 核对配置三项：`LogInGroupOnly=1`、`AutoEquipUpgradeLoot=0`、`BotCheats=""`。
6. 二进制 = `azerothcore-wotlk/var/build/obj/src/server/apps/worldserver`（16:57），
   与 mod-raidtest 工作区一致；**若本轮要改源码，需先获得编译授权**。

## 环境坑（本轮新踩，影响每次跑测试）

`scripts/restart_world.sh` 用 `tail -n 0 -f /tmp/ac_world_fifo | worldserver` 作 FIFO 读端。
**`tail` 写管道时是块缓冲（16KB）**，`raidtest run` 这类短命令会永远停在缓冲区里——本会话三次发命令
都没进控制台（日志无 `Orchestrator` 行、数据库无新 run），一度误判为「启动期吞命令」。
改用 `scripts/fifo_relay.py`（`O_RDWR` 自持写端 + 逐行 flush）后一次即通。
**该修复已提交进 `restart_world.sh`（`8396a02`）并实机验证**，下一个会话不必手工起 relay。
⚠ 不能用 `perl -e '$|=1; while(<STDIN>){print}'`：写端关闭时它会收到 EOF 并退出。
