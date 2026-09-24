# 后续优化项（跨 boss 待办索引）

更新：2026-09-24。这里只登记**已识别、尚未排期**的后续工作：每项一句问题、证据入口和建议方向。
实验叙事与样本仍写在对应 encounter README；项目被排期后，把设计写成独立设计文档或写进 encounter README 的“下一步”，并在此标为「已排期」或删除。

## 条目格式

| 字段 | 内容 |
|---|---|
| 层 | `bot`（mod-playerbots 行为）/ `框架`（mod-raidtest 编排）/ `场景`（conf、准备点） |
| 状态 | 待设计 / 已排期 / 已完成（完成后保留一行结论与提交） |
| 证据 | 触发它的 run 与 encounter README 链接 |

## 待办

### 1. 克里克希尔：坦克按组把守望者拉回门口再接（bot，待设计）

- **问题**：三组守望者刷在 boss 12–27 码内（Gashra 17.6、Silthik 23.6、Narjil 27.0），坦克/近战原地接怪会站到 boss 22 码仇恨边缘，带上 boss 或引发 evade → 三组整体 `DespawnFormation`。ilvl 200 档 boss 战 10/10 kill，但前置阶段约一半启动中止。
- **已否定**：框架层“接近净空”（0 次触发，进圈的不是编排层移动）；全员“离 boss 24.5 码就退离”（与近战追击抖动，1/5，已回退）。
- **方向**：只针对坦克的“拉离再接”——开怪后坦克先退到门口安全点（距 boss ≥30 码、同层有地面），怪跟随后再原地坦；近战与远程跟随坦克/目标，不加通用退离。执行门槛：前置阶段 `preclear_boss_proximity` 与 boss 提前参战次数下降；效果看前置中止率。
- **证据**：[克里克希尔 README](bosses/heroic-an-krikthir/README.md) 末尾「h5g 前置中止调查」「站位修正两次尝试」。

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

### 7. 哈多诺克斯：离开酸液云 / 被蛛网猛拉后拉开（进行中）

- **问题**：完整形态 ilvl 200 档 0/5（boss 最低 20–95%），隔离形态 normal5 0/5；每场酸液云 59419 与蛛网猛拉 59420 各 6–13 次，阵亡者多死在原地。AN 策略对她没有任何节点。
- **方向**：先量化每次酸液云落点与受伤 bot 的停留时间、蛛网猛拉后远程被拉入近身的比例，再分别加「离开酸液云」「猛拉后回到远程距离」两个单变量。
- **进展 2026-09-24**：根因是全 bot 队伍没有启用标准 `avoid aoe`（见第 8 条）；`MasterlessAvoidAoe=1` 后 1/5，时限 900 秒 1/5，再加粉碎者阶段法师群攻归零（playerbots `e955cc80`）2/5。剩余失败都在 300 秒后的 boss 阶段；蛛网猛拉伤害仅 2.4%，不再是优先项。
- **证据**：[哈多诺克斯 README](bosses/heroic-an-hadronox/README.md)。

### 8. 全部场景是否启用 MasterlessAvoidAoe（框架/基线，待决策）

- **问题**：mod-playerbots 只给有真人 master 的 bot 默认加 `avoid aoe`；raidtest 所有历史样本都在没有通用躲 AoE 的条件下测得。哈多诺克斯开启后酸液云承伤明显下降并拿到首杀。
- **方向**：真人带队时这是默认策略，按“正常规则、真人同等配置”应逐场景开启，但会改变每个场景的基线。建议先在仍不稳定、且有地面持续 AoE 的 boss 上开启并重跑，再决定是否作为全局默认；已稳定的 boss 抽查确认无回归。
- **证据**：raidtest `MasterlessAvoidAoe`（见哈多诺克斯 README「第 7 条：酸液云」）。

### 9. 伤害事件缺技能 id（观测，待设计）

- **问题**：`CombatEventBus` 的伤害来自 `UnitScript::OnDamage`，不带 SpellInfo，`raidtest_events.spell_id` 恒为 0；哈多诺克斯只能按伤害数值分桶区分酸液云/吸血毒/猛拉，被护盾部分吸收的跳数会被分错。
- **方向**：补接带 SpellInfo 的 hook（如 `ModifyPeriodicDamageAurasTick`、`ModifySpellDamageTaken`）记录周期/法术伤害的 spell id，纯观测。
