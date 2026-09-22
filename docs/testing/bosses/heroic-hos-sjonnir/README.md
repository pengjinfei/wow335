# 英雄岩石大厅 / 斯约尼尔·塑铁者（Sjonnir the Ironshaper）

状态：**跳过（框架阻断）**。Tribunal 后转入本 boss 的路由已经完成可复核审计；这不是 Sjonnir 策略或战斗失败，因为没有有效战斗样本。

## 接手摘要

- 当前未建立 Sjonnir scenario，未运行样本，未提出策略或代码改动。
- 计划基线沿用 campaign 的 Heroic / normal5-v1 / 5 人 / `BotCheats=""` / `GearProfile=none` / 无 fixture；实际运行前须重新核对 binary、配置、roster、前置和场景边界。
- 本轮只读审计已确认常驻 boss 为 spawn `126792` / normal entry `27978`（heroic `difficulty_entry_1=31386`），map 599 坐标 `(1295.21,667.16,189.69)`、`ScriptName=boss_sjonnir`。85 码内只有两个 World Trigger；最近非 trigger 常驻敌人距 112 码，故没有证据把邻近常驻怪预填为 boss 前置。
- Tribunal 维持 **基线未通过 / 暂缓**：r32 run745 为真实 DONE，run746/748/750/751 为有效动态 wipe；r34 样本仍为排除 lifecycle 的诊断，不能混入。

## 机制与路径审计（只读）

- core `boss_sjonnir.cpp` 的正常战斗包含 Chain Lightning (50830)、Lightning Shield (50831)、Static Charge (50834)、每 40 秒 Lightning Ring (50840)，并在 75%/50%/25%/20% 血量进入 trogg、ooze、dwarf 和 frenzy/ring 阶段。运行样本尚未覆盖任一机制。
- 现有 `wotlk-hos` 已注册 `lightning ring -> avoid lightning ring`（`ACTION_RAID+5`）；动作仅在 boss 施放 50840 时离开 boss 至 12 码，`SjonnirMultiplier` 同期抑制其他移动动作。源码注释明确 add 处理/站位仍未设计，不能把“已注册”称为已验证。
- 存在正常规则前置门：`instance_halls_of_stone.cpp` 仅在 `BOSS_TRIBUNAL_OF_AGES == DONE` 时对 Sjonnir 执行 `RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE)`；Brann 的完整路径另把 `BRANN_DOOR` 置 DONE 以开门。不得以 fixture/直接 boss state 绕过此门，也不能把此前独立 Tribunal 的跨实例 DONE 当作本次 Sjonnir scenario 前置完成。

## 框架可承载性结论

现有 `mod-raidtest` **不能表达**这一正常规则链，故当前为 **框架阻断**，不是 Sjonnir 的 bot 策略失败，也没有有效战斗样本：

- 一个 `Scenario` 只有一个 `BossEntry`。带 `EventStarterEntry` 时，`AttemptRunner::BossPosition` 对 starter 做真实 gossip 后直接进入 `Observing`；`AttemptObserver` 一见 `EventCompletionBossState == DONE` 就返回本 attempt 的 `Kill`。它没有“事件完成后保留实例、跟随 Brann、重定位并拉第二个 BossEntry”的 stage 或配置。
- 因而将 `BossEntry=28070`/Tribunal event 写入场景会在 Tribunal DONE 结束，绝不会进入 Sjonnir；将 `BossEntry=27978` 写入新实例则没有同实例 Tribunal DONE，不能正常解锁。`FixtureBossStates` 虽可直写状态，但文档和代码都定义为隔离 fixture，禁止用于本 normal-rule cohort。
- 续链不能只把“DONE 后再 gossip”硬接：core 在事件结束约 17 秒首次置 `BOSS_TRIBUNAL_OF_AGES=DONE`，但 Brann 的 lore 至约 256 秒才自然到达可前往 Sjonnir 的 gossip 点。因此框架必须把“事件完成”和“后续真实 gossip 可用”分为两个可观察 state/delay gate；不得在 DONE 时调用 action 或伪造 menu。
- 本轮 FIFO 再次确认运行 r32 的 `raidtest status --json` 为 `idle=true`，未启动 run；所有上述是可复核源码/配置结论，未以 DB 直接改状态或创建伪场景。

## 最小多阶段设计（未实现）

静态接口/状态机审计已经把变量收敛为一个向后兼容的 `EventFollowup` 配置组，而不是为 HoS 写 C++ 特例：

- `EventFollowupBossEntry`（0=关闭）是 event 完成后唯一的真实死亡结算目标；`EventFollowupReadyState=<instance-state>:<value>` 是第二次 gossip 后必须由**核心**自然写入的门/路径确认。Sjonnir 应为 `27978` 与 `5:3`（`BRANN_DOOR=DONE`）。没有这两个字段的所有旧场景保持原先 event DONE 即 kill。
- runner：`Observing(event)` 只在 `EventFollowupBossEntry==0` 时沿用 observer 的 event-DONE kill；有 followup 时，首次 DONE 记 `event_complete`，保留同一 `InstanceScript`/roster/Brann GUID，转 `post_event_wait`。此阶段只等 starter 再有真实 `UNIT_NPC_FLAG_GOSSIP`，超时为 `post_event_failed: followup gossip unavailable`；成功后复用既有 `StartScriptedEventGossip()`，所以仍走 core 的当前 menu `sGossipSelect`，而非 `DoAction`。
- `post_event_ready` 只等 `EventFollowupReadyState`；超时为 `post_event_failed: ready state not reached`。到达后应重新解析 followup entry、`CombatEventBus::RebindBoss`，再走既有 `StartBossPull` / 真死亡判定。不得传送、强制移动、设目标或仇恨；任何 boss 不存在、不可攻击、starter/roster 死亡均明确 abort/wipe，不能误记为 kill。
- **可复核 blocker**：现有 `EventFollowStarter` 每秒直接对每个非战斗 bot 调 `MotionMaster::MoveFollow`，因此它是框架强制移动，不能作为本 campaign 的 normal-rule followup 方案。`WotlkDungeonHoSStrategy` 只注册战斗内的 Lightning Ring/Tribunal 节点，未注册 post-event 路线；通用 `TravelAction::isUseful()` 更硬编码 `return false && ...`，不会启动 travel。故没有 raidtest 代移的前提下，事件后队伍无可用 playerbot 自主路线到 Sjonnir；不得实现会在同一实例强制跟随/导航/传送的 EventFollowup，也不能声称 final pull 可执行。
- 若未来先有 playerbot 自主、可观测的 post-event route，执行验收才做一场**不入 Sjonnir lifecycle**的 chain smoke：事件 DONE、真实第二 gossip、核心写 `BRANN_DOOR=DONE`、followup boss 重新绑定、五人自行到达且 strategy gate/正常 pull 均须有事件记录。该 cohort 不能与旧 Tribunal 1/5 或 fixture/独立 boss 样本混算。

## 结论与路由

正常规则 Sjonnir cohort 被可复核的**跨区移动框架缺口**阻断：同实例前置必须完成，而任何可用续链都会要求 raidtest 强制移动，playerbots 也不存在自主路线。按 campaign 队列，Sjonnir 后没有未审计的下一 boss；将工作面回到仍未完成的 Tribunal，且不得把 Sjonnir 标为策略失败、完成或 fixture 隔离击杀。

## 交接

- running server：r32，已由 FIFO `raidtest status --json` 确认为 IDLE；本 encounter 尚无活动 run。
- 证据边界与仓库状态以 [`../../BOSS-LEDGER.md`](../../BOSS-LEDGER.md)、[`../heroic-hos-tribunal/README.md`](../heroic-hos-tribunal/README.md) 和当前会话检查为准。
