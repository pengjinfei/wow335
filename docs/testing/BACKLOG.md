# 后续优化项（跨 boss 待办索引）

更新：2026-09-25。这里只登记**已识别、尚未排期**的后续工作：每项一句问题、证据入口和建议方向。
实验叙事与样本仍写在对应 encounter README；项目被排期后，把设计写成独立设计文档或写进 encounter README 的“下一步”，并在此标为「已排期」或删除。

## 条目格式

| 字段 | 内容 |
|---|---|
| 层 | `bot`（mod-playerbots 行为）/ `框架`（mod-raidtest 编排）/ `场景`（conf、准备点） |
| 状态 | 待设计 / 已排期 / 已完成（完成后保留一行结论与提交） |
| 证据 | 触发它的 run 与 encounter README 链接 |

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

### 12. 前置阵亡改为等队友复活（框架已实现；bot 侧阻断，2026-09-26）

- **改动**：raidtest `3c26d3d`：恢复阶段遇到本场有死亡记录的成员时记 `recovery_wait:dead` 并等最多 180 秒让 bot 自己复活；超时记 `casualty not revived during recovery`。无死亡记录的死者直接判 `scene_invalid`（`73cc994`）。框架不代为复活。
- **首次触发（Tribunal run1084）**：盗贼 74.5 秒前置阵亡后**立即释放灵魂**，以鬼魂回到副本外墓地（map 571），牧师全程未施放复活——等满 180 秒中止。原因在 playerbots：无真人 master 时 `DeadStrategy` 的 "auto release" 立即释放，真人会躺着等复活。
- **方向（bot，待设计）**：无 master 的队伍里，若有存活且带复活技能的队友，延后释放灵魂（例如脱战后仍等一段时间或直到队友施放复活）；否则保持现状。改后此条框架路径才有意义；在此之前每次前置阵亡多耗 180 秒。
- **动机**：Tribunal cohort3 7 次启动中 2 次因盗贼前置阵亡作废（run1033/1035）。

### 13. 环境致死不产生死亡事件（观测，已补 2026-09-26）

- **结论**：raidtest `6569786` 加 `PlayerScript::OnPlayerJustDied` 兜底（所有玩家死亡最终都经 `Player::KillPlayer`）：同一玩家 2 秒内已由 `OnUnitDeath` 记过则跳过，否则补一条死亡事件，detail 带 `via=player_just_died`、位置与出界标志。正常死亡不重复（run1084 盗贼只记 1 条）。
- **未复现的部分**：旧沃尔坎下层准备点诊断 run1078–1080 三场均无人死亡，环境致死本身没能复现，兜底对它的效果待自然出现时核对。

### 14. 乌特加德之巅 Skadi：鱼叉链（bot，跳过待确认 2026-09-26）

- **问题**：打下 Grauf 需要玩家捡 Harpoon GO 192539（Harpooner 26692 死亡召出）→ 得物品 37372 → 在 Grauf 飞到东端悬停的 10 秒窗口内使用发射器 192175–192177，三发打下后 Skadi 才可攻击。playerbots UP 策略里是 TODO；通用拾取只处理有 loot 表的 GO。另 Skadi HARD_RESET、框架坦克仇恨校验需调整。
- **方向**：参考 Ulduar `RazorscaleHarpoonAction`（`UldActions.cpp:930`）实现“捡鱼叉 → 窗口内用发射器”。
- **证据**：[乌特加德之巅 SURVEY](bosses/heroic-up/SURVEY.md)「Skadi」。

### 15. 乌特加德之巅 Svala：献祭期间优先打 Ritual Channeler（bot，待设计）

- **问题**：Ritual of the Sword 把一名队员传送到祭坛，3 只 Channeler 25 秒内不打掉就献祭致死；bot 无优先打 Channeler 的逻辑（run1095/1106 各 1 死）。
- **方向**：UP 策略加 trigger（Channeler 存在）→ DPS 切目标。

### 16. 灵魂洪炉 Bronjahm：碎片回血与二阶段（bot，跳过待确认 2026-09-26）

- **问题**：ilvl 200 档 3 场 0 击杀（run1114 小怪卷入超时、run1120 47%、run1125 25%）。run1125 二阶段开始时（171 秒，boss 34%）一只 Corrupted Soul Fragment（36535）没被打死，172.97 秒走到 boss 身上，boss 回到 61%；随后二阶段牧师被 Magic's Bane（69050）与 Shadow Bolt（69049）点杀。run1120 另有牧师 147.5–188.6 秒完全不施法的空窗，run1125 未复现。
- **方向**：Corrupt Soul 目标应远离 boss 再让碎片出生（现 `MoveFromBronjahmAction` 只在 boss 读条时逃 15 码）；碎片存在时 DPS 强制切目标（现只挂骷髅标记）；二阶段治疗站位。
- **证据**：[灵魂洪炉 README](bosses/heroic-fos/README.md)。

### 17. 灵魂洪炉 Devourer：哀嚎之魂站位（bot，跳过待确认 2026-09-26）

- **问题**：run1115 38%、run1121 22% 两场团灭。开 `MasterlessAvoidAoe` 后灵魂之井（36536）伤害从集中在一人（10.6 万）变为分散，但哀嚎之魂（70324）一场仍约 13 万，幽灵冲击（70322）压坦克。现有策略只处理 Mirrored Soul（非坦克背对 boss）。
- **方向**：Wailing Souls（68899 读条 / 68912 选目标）期间非坦克站到 boss 背后；幽灵冲击可打断的职业打断。

### 18. 萨隆矿坑 Ick：载具 boss 开怪（框架/bot，跳过待确认 2026-09-26）

- **问题**：Ick（36476）是载具，Krick 坐在上面。去掉前置怪后 3 场全部 `pull failed (tank did not establish aggro)`：坦克引擎日志每 tick `reach melee`/`reach spell` 为 USELESS、`melee` FAILED，实际距离 42 码，8 秒无一次伤害。前置怪 202156 距 Ick 8 码，会连带拉起 boss（run1123/1124）。
- **方向**：查 bot 对载具目标的 `current target` 与距离判定（是否取到了 Krick 或载具座位位置）；框架可考虑把坦克先带到 Ick 身边再拉。
- **证据**：[萨隆矿坑 README](bosses/heroic-pos/README.md)。

### 19. 萨隆矿坑 Garfrost：近战/坦克的永冻叠层（bot，跳过待确认 2026-09-26）

- **现状**：playerbots `eb2aadb5`：永冻不再驱散（牧师曾前 47 秒只放驱散魔法）；远程 DPS 6 层起躲到萨隆岩石背面直到光环消失，治疗不躲（岩石会挡住到坦克的视线，run1131 牧师整场只放 14 个法术）。ilvl 200 档改前 0/6、改后 1/3（run1137 击杀，4 死）。
- **剩余问题**：脚本对近战距离内的目标永远施加永冻，run1138 盗贼 53 跳 13.2 万、坦克 63 跳 11.7 万，两场团灭都是近战先死。
- **方向**：近战 DPS 高层数时退到岩石后清层再回来；坦克需要带 boss 绕岩石或交替。需要先确认真人打法再设计。
