# 后续优化项（跨 boss 待办索引）

更新：2026-09-26。这里只登记**已识别、尚未排期**的后续工作：每项一句问题、证据入口和建议方向。
实验叙事与样本仍写在对应 encounter README；项目被排期后，把设计写成独立设计文档或写进 encounter README 的“下一步”，并在此标为「已排期」或删除。

## 条目格式

| 字段 | 内容 |
|---|---|
| 层 | `bot`（mod-playerbots 行为）/ `框架`（mod-raidtest 编排）/ `场景`（conf、准备点） |
| 状态 | 待设计 / 已排期 / 已完成（完成后保留一行结论与提交） |
| 证据 | 触发它的 run 与 encounter README 链接 |

## 开放项总览（2026-09-26 收尾，新对话从这里挑）

口径：ilvl 200 档 `-h5g` 场景，每项先跑 5 场基线再改（memory「共享层收益不跨 boss 通用」）。规模：S=改一处、M=新 action/trigger 或框架键、L=多阶段/新行为体系。

| 建议顺序 | # | 项 | 层 | 现状 | 建议第一步 | 规模 |
|---|---|---|---|---|---|---|
| ✓ | 12 | 无 master 队伍阵亡后立即释放灵魂 | bot | **已合入**（playerbots `ce22678c`，2026-09-27） | 自然前置阵亡出现时核对 recovery_wait 走通 | — |
| ⏸ | 14 | Skadi 推进节奏 | bot/框架 | 基线 2/5；“非坦克落后坦克”1/5 未合入 | **待确认**：坦克逐组拉怪 或 框架改走位（见 14） | M |
| ✗ | 15 | Svala 献祭期间打 Ritual Channeler | bot | 基线 5/5 0 死；改后 5/5 2 死，未合入 | **待确认**：只让远程打 / 关闭本条（见 15） | S |
| ⏸ | 19 | Garfrost 近战/坦克永冻叠层 | bot | 基线 0/5 | **待确认**：用户选的“坦克带怪绕岩石”在 AC 脚本下无效（见 19） | M |
| ✓ | 20 | Eregos 龙战 | bot | **已合入**（playerbots `d1181635`）：躲 Planar Anomaly 后 0/5 → 2/5 | 剩余团灭在 20–30%（雏龙+Arcane Barrage，输出/承伤） | M |
| 6 | 23 | Falric / Marwyn / 巫妖王逃亡 | bot+框架 | Falric 3/18，另两个未建 | 逃亡：框架 gossip 走 `sScriptMgr->OnGossipSelect` + 等 gossip 标志（S），再看 bot | L |
| 7 | 21 | 大勇士骑乘阶段 | bot+框架 | 地面阶段 6/6 | 驾驶（25 码外 MoveTo）+ 践踏步行冠军 | L |
| — | 22 | 单 boss 爆发技能不放 | bot（共享层） | 实验分支 `exp/boost-on-boss`：生效但不涨击杀 | 决定是否作为正确打法合入；合入要全量回归 | S+回归 |
| — | 16/17 | Bronjahm 4/5、Devourer 3/5 | bot | 已改善 | 需要时补样本、看剩余团灭 | S |
| — | 8 | 全场景默认 MasterlessAvoidAoe | 基线决策 | 逐 boss 决定 | 待用户决策 | — |
| — | 3/4/6 | Sjonnir 续链、软泥阶段、Tribunal normal5 | 框架/观测/bot | 低优先 | — | M–L |

## 待办

### 1. 克里克希尔前置阶段中止（框架，主因已修 2026-09-25）

- **结论**：主因不是站位，而是框架在 boss 自己派下一组时抢拉另一组，两组同打队伍（击杀场几乎无重叠，中止场 5–21 个 5 秒桶重叠；阵亡都在门口）。raidtest `4790175` 的 `PrerequisiteRepullDelaySeconds=20` 后 10/12 kill（原 15/30）。原“坦克拉回门口”方向作废。
- **剩余**：全员脱战时 boss 自身 evade 带下三组（950/956），原因待 `creature_engage` 复现后定位；Silthik 被派出后不过来时门禁多等至超时（956）；近战（盗贼）冲出去迎击派来的组、路过未清组 18 码内把它拉上（977）。补跑后合计 **17/20 启动 kill**。
- **证据**：[克里克希尔 README](bosses/heroic-an-krikthir/README.md)「前置阶段根因：两组同时打队伍」。

### 2. 召唤物作为前置（框架，已完成 2026-09-24）

- **结论**：德拉克瑞巨像此前已由 `EngageTrigger=summon` 解决（隔离 5/5），本条原写法有误。哈多诺克斯由 raidtest `125ccc2`（`SummonTriggerRadius` + `EngageConfirmBossState`）解除阻断，完整遭遇原生链路全部复现；ilvl 200 档基线 0/5（最好 20%），剩余问题转为第 7 条。
- **证据**：[哈多诺克斯](bosses/heroic-an-hadronox/README.md)「完整遭遇形态」。

### 3. 脚本事件后续阶段 EventFollowup（框架 + bot，待设计）

- **问题**：Tribunal DONE 后同实例续打 Sjonnir 需要多阶段场景（第二次真实 gossip、`BRANN_DOOR=DONE` 门控、重绑 followup boss），且 playerbots 没有事件后自主前往 Sjonnir 的路线；raidtest 不可代移。当前 Sjonnir 只有隔离 5/5。
- **证据**：[Sjonnir README](bosses/heroic-hos-sjonnir/README.md)「最小多阶段设计」。

### 4. Sjonnir 50% 软泥阶段未入库（观测，待查）

- **问题**：隔离基线 5 场均无 Iron Sludge 27981 事件；未确认是高 DPS 跳过阶段还是软泥不造成伤害而未被记录。
- **证据**：[Sjonnir README](bosses/heroic-hos-sjonnir/README.md)「2026-09-24 隔离 boss 战基线」。

### 5. run 行已建但 orchestrator 未启动（框架，已完成 2026-09-24）

- **结论**：run id 读回竞态——`InsertThenSelectId` 异步 INSERT 后「队列排空」即 SELECT 同场景最新行，读到上一 run 的 id；新 run 的 attempt/结果写进上一 run，新行永不收尾（run859、run892）。raidtest `fbd6bd9` 改为 `DirectExecute` 后读回，已验证 run893 id 一致。历史错挂：attempt 1788428082→run859、1788428115→run892。

### 6. Tribunal normal5 档的剩余杠杆（bot，待设计，低优先）

- **问题**：normal5（ilvl≈183）下 Holy Shield、r35 远程补视线均中间量达标但 0/5；约 200 秒叠波崩溃由总输出/生存总量决定。ilvl 200 档已 5/10。
- **方向**：若仍需 normal5 口径，只考虑能明显提高全队总输出或总治疗的组合改动，并单独记 cohort。
- **证据**：[Tribunal README](bosses/heroic-hos-tribunal/README.md)。

### 7. 哈多诺克斯：离开酸液云 / 被蛛网猛拉后拉开（已完成 2026-09-25）

- **问题**：完整形态 ilvl 200 档 0/5（boss 最低 20–95%），隔离形态 normal5 0/5；每场酸液云 59419 与蛛网猛拉 59420 各 6–13 次，阵亡者多死在原地。AN 策略对她没有任何节点。
- **方向**：先量化每次酸液云落点与受伤 bot 的停留时间、蛛网猛拉后远程被拉入近身的比例，再分别加「离开酸液云」「猛拉后回到远程距离」两个单变量。
- **进展 2026-09-24**：根因是全 bot 队伍没有启用标准 `avoid aoe`（见第 8 条）；`MasterlessAvoidAoe=1` 后 1/5，时限 900 秒 1/5，再加粉碎者阶段法师群攻归零（playerbots `e955cc80`）2/5。剩余失败都在 300 秒后的 boss 阶段；蛛网猛拉伤害仅 2.4%，不再是优先项。
- **结论 2026-09-25**：真正根因是克里克希尔节点在哈多诺克斯平台上劫持 DPS（盗贼 30/31 场零输出）；限定作用域后 5/5、0 死（playerbots `b42f27d1`）。
- **证据**：[哈多诺克斯 README](bosses/heroic-an-hadronox/README.md)。

### 8. 全部场景是否启用 MasterlessAvoidAoe（框架/基线，待决策）

- **2026-09-25 数据点**：阿努巴拉克开启后 4/5 有效样本，对基线 5/5，无收益；哈多诺克斯开启后明显改善。结论仍是逐 boss 决定。

- **问题**：mod-playerbots 只给有真人 master 的 bot 默认加 `avoid aoe`；raidtest 所有历史样本都在没有通用躲 AoE 的条件下测得。哈多诺克斯开启后酸液云承伤明显下降并拿到首杀。
- **方向**：真人带队时这是默认策略，按“正常规则、真人同等配置”应逐场景开启，但会改变每个场景的基线。建议先在仍不稳定、且有地面持续 AoE 的 boss 上开启并重跑，再决定是否作为全局默认；已稳定的 boss 抽查确认无回归。
- **证据**：raidtest `MasterlessAvoidAoe`（见哈多诺克斯 README「第 7 条：酸液云」）。

### 9. 伤害事件缺技能 id（观测，已完成 2026-09-24）

- **结论**：raidtest 在 `ModifyPeriodicDamageAurasTick` / `ModifySpellDamageTaken` / `ModifyMeleeDamage` 记 (攻击者, 受害者) 法术提示，`OnDamage` 取用写入 `spell_id`（近战 0，50 ms 过期，表封顶 4096）；哈多诺克斯 59419/59417/59420 已正确入库。

### 10. 副本内相邻 boss 的节点作用域审计（bot，已完成 2026-09-25）

- **结论**：审计 `Ai/Dungeon/*` 中所有按 `possible targets no los`（100 码、无视线/楼层）或大半径 `FindNearestCreature` 判定存在的 trigger/multiplier。仅 AN 克里克希尔两处会跨房间生效（已修 `b42f27d1`）；其余均由 `find target`（只查 bot 自身仇恨列表，即已交战单位）先门控（AK Nadox/Jedoga、HoL Bjarngrim 等）、只影响该 boss 专用动作（FoS Bronjahm）、或半径内不可能有别的 boss（AN 阿努巴拉克 200 码，最近的其他 boss 约 600 码）。克里克希尔自身回归检查无回归（boss 战 3/3，盗贼输出持平）。

### 11. boss 半血复位被记成 aborted（框架口径，已完成 2026-09-25）

- **结论**：raidtest `0abf76b`：无人死亡、boss 脱战的结局里，boss 本 attempt 掉过血且此刻 evade（或已回满血）→ **Wipe**，notes `encounter reset mid-fight (no deaths)`；从未掉血（开怪没落地）仍 aborted；掉过血但未 evade、未满血（如血量读 0 的死亡判定竞态，莫拉比 run640/665）仍 aborted 待人工核对。验证 run1000–1007：run1004 于 17% 复位记为 wipe，其余 7 场 kill。
- **历史回查**（旧口径下 `boss lost combat state` 且 boss 掉过血）：阿努巴拉克 h5g 5 次、h5g-aoe 2 次、n5 4 次（n5 共 286 条记录，击杀率几乎不变）；莫拉比 2 次为血量 0（不属此类）；naxx 早期 run2–36 共 28 次属框架初期开怪问题，不在现行台账。数据库原始行不改，重算只写进文档。
- **证据**：[阿努巴拉克 README](bosses/heroic-an-anubarak/README.md)「“卡住中止”的真相」及其后一节。

### 12. 前置阵亡改为等队友复活（**已完成 2026-09-27**，playerbots `ce22678c`）

- **改动**：`AutoReleaseSpiritAction` 在副本里、无真人 master 时，只要同图还有存活且会复活技能（牧师 Resurrection / 圣骑 Redemption / 萨满 Ancestral Spirit / 德鲁伊 Revive、Rebirth，按技能链查）的队友就不释放；全队无复活者或死满 5 分钟才释放。日志 `holds release` / `releases:`。
- **验证**：Tribunal h5g run1391–1395 共 **3/5**（上一 cohort 3/5，无回退）；4 次阵亡都打出 `holds release`，死者原地躺着。5 场里没有出现前置阵亡，恢复阶段的 `recovery_wait:dead → 牧师复活` 链路**尚未被自然触发**，下次出现时核对。raidtest 没有杀 bot 的控制台命令，确定性 smoke 未做。

#### 原记录

- **改动**：raidtest `3c26d3d`：恢复阶段遇到本场有死亡记录的成员时记 `recovery_wait:dead` 并等最多 180 秒让 bot 自己复活；超时记 `casualty not revived during recovery`。无死亡记录的死者直接判 `scene_invalid`（`73cc994`）。框架不代为复活。
- **首次触发（Tribunal run1084）**：盗贼 74.5 秒前置阵亡后**立即释放灵魂**，以鬼魂回到副本外墓地（map 571），牧师全程未施放复活——等满 180 秒中止。原因在 playerbots：无真人 master 时 `DeadStrategy` 的 "auto release" 立即释放，真人会躺着等复活。
- **方向（bot，待设计）**：无 master 的队伍里，若有存活且带复活技能的队友，延后释放灵魂（例如脱战后仍等一段时间或直到队友施放复活）；否则保持现状。改后此条框架路径才有意义；在此之前每次前置阵亡多耗 180 秒。
- **动机**：Tribunal cohort3 7 次启动中 2 次因盗贼前置阵亡作废（run1033/1035）。

### 13. 环境致死不产生死亡事件（观测，已补 2026-09-26）

- **结论**：raidtest `6569786` 加 `PlayerScript::OnPlayerJustDied` 兜底（所有玩家死亡最终都经 `Player::KillPlayer`）：同一玩家 2 秒内已由 `OnUnitDeath` 记过则跳过，否则补一条死亡事件，detail 带 `via=player_just_died`、位置与出界标志。正常死亡不重复（run1084 盗贼只记 1 条）。
- **未复现的部分**：旧沃尔坎下层准备点诊断 run1078–1080 三场均无人死亡，环境致死本身没能复现，兜底对它的效果待自然出现时核对。

### 14. 乌特加德之巅 Skadi：鱼叉链（bot，已实现；推进节奏待确认 2026-09-27）

- **2026-09-27 基线**（run1401–1405）：**2/5**。原记录“法师先死”不准确：3 场团灭都是**第 10–11 秒一人被 4–5 只 Ymirjar Warrior（26690，英雄 4–5k/下）同一瞬间打死**，首死是牧师（2 场）或盗贼。当时牧师在坦克身后 2–5 码，并没有超前。
- **试验“非坦克落后坦克 2–20 码”**（playerbots `exp/skadi-behind-tank`，未合入）：run1426–1430 **1/5**。非坦克确实落后了 30 码，但第 11 秒照样有一人被 4–5 只战士秒掉（盗贼 x≈387）。
- **真实原因**：坦克是被框架 `MovePoint`（AT 触发后“走到开怪点”）带着走过走廊的，**路过 x≈392–394 的战士点位时不进战斗、不拉怪**；等后面的人走到这些点位，几只战士一起扑上去。
- **待确认（改动面较大）**：a) bot 侧“坦克逐组拉怪”：飞行阶段坦克走到下一个未交战的怪点、先拿仇恨再前进（M）；b) 场景/框架：开怪点改回准备点（不整队穿走廊），由坦克自己推进（需 a 配合）。两者都要改变现有走位方式，先等用户确认。

#### 已完成部分

- **已完成**：playerbots `21fcad00`：DPS 捡 Harpoon GO → 在 Grauf 东端悬停时对发射器用物品（CMSG_USE_ITEM，走锁校验）；持鱼叉者守在发射器旁。raidtest `场景 heroic-up-skadi-h5g`：AT 4991 开战，全队走到三台发射器之间。
- **结果**：完整遭遇 3/6 击杀（run1317/1320/1321，212–399 秒）。
- **剩余**：团灭都是开战后全队一次走到东端时穿过第一波（走廊里 13 只），法师每场第 10 秒左右先死，DPS 不够时鱼叉只能打出 2 发。需要“坦克在前、逐段推进”的节奏：框架分段导航或 bot 跟随坦克推进（中改）。

#### 原记录

- **问题**：打下 Grauf 需要玩家捡 Harpoon GO 192539（Harpooner 26692 死亡召出）→ 得物品 37372 → 在 Grauf 飞到东端悬停的 10 秒窗口内使用发射器 192175–192177，三发打下后 Skadi 才可攻击。playerbots UP 策略里是 TODO；通用拾取只处理有 loot 表的 GO。另 Skadi HARD_RESET、框架坦克仇恨校验需调整。
- **方向**：参考 Ulduar `RazorscaleHarpoonAction`（`UldActions.cpp:930`）实现“捡鱼叉 → 窗口内用发射器”。
- **证据**：[乌特加德之巅 SURVEY](bosses/heroic-up/SURVEY.md)「Skadi」。

### 15. 乌特加德之巅 Svala：献祭期间优先打 Ritual Channeler（**试验为负，未合入** 2026-09-27）

- **基线**（run1396–1400）：**5/5、0 死**。被献祭者在 ilvl 200 档扛得住（Channeler 每场只打出 0.2–1 万），Channeler 从来没被打死，25 秒后被脚本 despawn。原来“每场 1 死”的问题在当前装备下已经不出现。
- **试验**（playerbots `exp/svala-channeler`）：非治疗切 Channeler，run1421–1425 **5/5、2 死**，Channeler 仍然 0 击杀、对全队伤害升到 1.5–2.7 万。死的是盗贼：英雄 Channeler 带 Shadows in the Dark（59407，受击触发 59408），近战打它被反噬约 2.4 万。
- **待确认**：只让远程打 Channeler（收益预计很小）或直接关闭本条。

#### 原记录

- **问题**：Ritual of the Sword 把一名队员传送到祭坛，3 只 Channeler 25 秒内不打掉就献祭致死；bot 无优先打 Channeler 的逻辑（run1095/1106 各 1 死）。
- **方向**：UP 策略加 trigger（Channeler 存在）→ DPS 切目标。

### 16. 灵魂洪炉 Bronjahm：碎片回血与二阶段（**已改善 4/5**，playerbots `fdd4ff99`，2026-09-26）

- **问题**：ilvl 200 档 3 场 0 击杀（run1114 小怪卷入超时、run1120 47%、run1125 25%）。run1125 二阶段开始时（171 秒，boss 34%）一只 Corrupted Soul Fragment（36535）没被打死，172.97 秒走到 boss 身上，boss 回到 61%；随后二阶段牧师被 Magic's Bane（69050）与 Shadow Bolt（69049）点杀。run1120 另有牧师 147.5–188.6 秒完全不施法的空窗，run1125 未复现。
- **方向**：Corrupt Soul 目标应远离 boss 再让碎片出生（现 `MoveFromBronjahmAction` 只在 boss 读条时逃 15 码）；碎片存在时 DPS 强制切目标（现只挂骷髅标记）；二阶段治疗站位。
- **证据**：[灵魂洪炉 README](bosses/heroic-fos/README.md)。

### 17. 灵魂洪炉 Devourer：哀嚎之魂站位（**已改善 3/5**，playerbots `fdd4ff99`，2026-09-26）

- **问题**：run1115 38%、run1121 22% 两场团灭。开 `MasterlessAvoidAoe` 后灵魂之井（36536）伤害从集中在一人（10.6 万）变为分散，但哀嚎之魂（70324）一场仍约 13 万，幽灵冲击（70322）压坦克。现有策略只处理 Mirrored Soul（非坦克背对 boss）。
- **方向**：Wailing Souls（68899 读条 / 68912 选目标）期间非坦克站到 boss 背后；幽灵冲击可打断的职业打断。

### 18. 萨隆矿坑 Ick：载具 boss 开怪（**已解决 5/5**，raidtest `862dc13`：治疗站在追击拴绳外，开怪点移到 20 码，2026-09-26）

- **问题**：Ick（36476）是载具，Krick 坐在上面。去掉前置怪后 3 场全部 `pull failed (tank did not establish aggro)`：坦克引擎日志每 tick `reach melee`/`reach spell` 为 USELESS、`melee` FAILED，实际距离 42 码，8 秒无一次伤害。前置怪 202156 距 Ick 8 码，会连带拉起 boss（run1123/1124）。
- **方向**：查 bot 对载具目标的 `current target` 与距离判定（是否取到了 Krick 或载具座位位置）；框架可考虑把坦克先带到 Ick 身边再拉。
- **证据**：[萨隆矿坑 README](bosses/heroic-pos/README.md)。

### 19. 萨隆矿坑 Garfrost：近战/坦克的永冻叠层（bot，**待确认** 2026-09-27）

- **2026-09-27 基线**（run1406–1410）：**0/5**，boss 最低 10–62%。
- **用户选的打法（坦克带 boss 到岩石后清层）在 AC 脚本下无效**：`spell_garfrost_permafrost::FilterTargets` 对 Garfrost **近战距离内**的目标一律施加永冻，岩石只过滤近战距离外、且被岩石挡在 4 码线内的目标。boss 会一直追到坦克的近战距离，坦克和近战的层数清不掉。零售服务器按视线判定，这里的实现不一样。
- **待确认**：可行方向只剩 a) 近战高层数时离开近战到岩石后清层（09-26 试过 0/4 已撤回）；b) 治疗/输出总量（装备档位问题）；c) 暂按能力边缘记账。

#### 原记录

- **现状**：playerbots `eb2aadb5`：永冻不再驱散（牧师曾前 47 秒只放驱散魔法）；远程 DPS 6 层起躲到萨隆岩石背面直到光环消失，治疗不躲（岩石会挡住到坦克的视线，run1131 牧师整场只放 14 个法术）。ilvl 200 档改前 0/6、改后 1/3（run1137 击杀，4 死）。
- **剩余问题**：脚本对近战距离内的目标永远施加永冻，run1138 盗贼 53 跳 13.2 万、坦克 63 跳 11.7 万，两场团灭都是近战先死。
- **方向**：近战 DPS 高层数时退到岩石后清层再回来；坦克需要带 boss 绕岩石或交替。需要先确认真人打法再设计。

### 20. 魔环 Eregos / 龙战（**躲 Planar Anomaly 已合入** playerbots `d1181635`，2026-09-27）

- **基线**（run1411–1415）：**0/5**，五场都停在 57–59%（第一次 Planar Shift 在 60%）。团灭来源是 Anomaly：Planar Distortion 59380 约 5.6 万、Planar Blast 57976（15.5 秒后 20 码 1.4 万）约 2.9 万。
- **改动**：骑龙时 28 码内有 Planar Anomaly（30879）就按远离方向飞 40 码（离 Eregos 超过 80 码时改为绕他侧飞），期间不放龙技能（引导会让龙停下）。
- **结果**（run1416–1420）：**2/5**（该 boss 首杀，run1416 0 死 87 秒），另外 3 场在 20–30% 团灭；Anomaly 伤害降为 0。剩余团灭是第二次 Planar Shift 之后被 Eregos Arcane Barrage（59382）和雏龙磨死，属输出/承伤问题。

#### 更早记录

- **已完成**（playerbots `0d8ea9d3`、raidtest `bc45826`）：无 master 上龙（Eregos 可攻击时；精华以 Drakos DONE 为前提）、飞到 Eregos 45 码、自行开怪（框架 `EngageTrigger=self`）；龙技能轮换放不出时顺延；翡翠龙优先 Dream Funnel；`CastVehicleSpell` 对友方目标不再转身（之前 Dream Funnel 一次都放不出）；飞行载具豁免同层守卫。无 master 时编队 3 琥珀 / 2 翡翠。
- **结果**：heroic Eregos 隔离 0/9，最好 37%（run1311）；最近几场都在 54–58% 附近团灭（Planar Shift 阶段）。
- **剩余问题**：Planar Shift 期间召出的 Planar Anomaly 15 秒后 Planar Blast，龙不会躲（`OccFlyingMultiplier` 压掉了其它移动）；Eregos 盯着一条翡翠龙打（run1312 一条龙吃 12.9 万）。需要骑龙时的躲避和威胁/承伤分担，属于中到大改。

#### 原记录

- **问题**：Eregos 在 z≈655 飞行，只能骑龙打；Varos、Urom 的设计形态也是龙战。playerbots `wotlk-occ` 里上龙、下龙、骑龙飞行的 trigger 全都依赖 master，全 bot 队伍永远不会上龙；骑上后移动也只跟随 master。另据源码推断，龙的单体技能打到不会飞的敌对目标时脚本会杀死骑手（`oculus.cpp:400-411`），需真人 GM 先验证一次。
- **方向**：playerbots 无 master 时的上龙/飞行/龙技能轮换；框架侧骑乘战的开怪与观察口径。
- **证据**：[魔环 SURVEY](bosses/heroic-oculus/SURVEY.md) §4、§5。

### 21. 冠军的试炼 Grand Champions（bot + 框架，待确认 2026-09-26）

- **进展**：地面阶段隔离场景已建，6/6（raidtest `049620f`，`KillOnInstanceData=4:6`）。剩下骑乘阶段。

- **问题**：骑乘阶段不能按正常规则跳过；bot 没有践踏（骑马压下马的冠军）逻辑，冠军会反复上马。只做地面阶段也需要框架补“三只都投降才算完成”的判据，并清掉上一场投降的旧冠军（否则会被绑定、误判击杀）。
- **证据**：[冠军的试炼 SURVEY](bosses/heroic-toc5/SURVEY.md) §1。

### 22. 共享层：单个 5 人本 boss 上所有爆发技能都不放（bot，待确认 2026-09-26）

- **问题**：`BoostTrigger`（34 个爆发技能共用：英勇/嗜血、急速射击、冰冷血脉、鲁莽等）只在 `balance <= 50` 时触发。`balance` = 存活队员等级和 ÷ 敌方等级和（精英 ×3）。单个 82 级精英 boss（rank 1，5 人本 boss 基本都是）对满员 5 人是 400/246 = 162%，剩 2 人也有 65%，**永远达不到 50%**。所以隔离 boss 战里这些技能从不施放，只有同时来 3 只以上精英时才放（映像大厅 Falric：英勇每场都交在第 1 波小怪上）。
- **现状**：只在映像大厅做了窄修（playerbots `wotlk-hor`：波次期间压住英勇、Falric/Marwyn 可攻击后萨满直接放）。
- **方向**：`BoostTrigger::IsActive` 在当前目标 `IsDungeonBoss() || isWorldBoss()` 时也算触发（`DebuffOnBossTrigger` 已有同样判据）。影响所有职业所有 boss，属共享层行为变化，需要全量回归，**先待确认**。
- **实验（2026-09-26，playerbots 本地分支 `exp/boost-on-boss`，未合并）**：按上面的方向改后，单 boss 阶段的爆发确实放出来了（Falric 阶段真言术：注入每场 0 → 1–2 次，复仇之怒 1/4 → 4/4 场），但击杀率不变：Falric 1/5（改前 1/5）、Garfrost 0/5（改前 1/3）、Skadi 3/5（改前 3/6）、Tribunal 3/5（改前 11/29）。另外修正上面的说法：**带精英小怪的战斗（Garfrost 6 只 Siegesmith、Skadi、Tribunal）改前就会放爆发**，只有纯单 boss 才完全不放。结论：不是这几个卡住 boss 的杠杆；是否作为“打法更正确”的通用修正合入，需要回归后由用户决定。

### 23. 映像大厅 Falric / Marwyn / 巫妖王逃亡（bot + 框架，待确认 2026-09-26）

- **Falric**：ilvl 200 档 3/18。4 波灵魂（英雄伤害 ×13）加 Falric 本体；Defiling Horror（惊骇，驱不掉）每场约 23 万，Hopelessness 把 11% 以下的伤害/治疗砍 60%，多数团灭停在 0–5%，也有死在波次里。英勇改到 boss 上（`0fc1b7ad`）后击杀率不变。像 Tribunal 一样是装备/总量问题（见 memory「装备才是杠杆」），bot 侧没有明确的机制杠杆。
- **Marwyn**：要链式（先过 Falric，`_falricPhaseComplete` 不持久化），受 Falric 通过率限制。
- **巫妖王逃亡**：框架要改 gossip 调用（`sScriptMgr->OnGossipSelect`）并等领袖挂 gossip 标志（S）；bot 要不打不死的巫妖王、跟领袖跑、打冰墙波次，还要躲 LK 身后 20 码的持续伤害（L）。
- **证据**：[映像大厅 README](bosses/heroic-hor/README.md)、[SURVEY](bosses/heroic-hor/SURVEY.md)。
