# mod-raidtest B2：激活无 master bot 的输出循环（设计文档）

> 日期: 2026-09-04
> 前置: B1 攻坚底座完成（AI 激活/顶装/实例重置/可信判定，真实 wipe 收官，已合并 main）
> 目标: 让无 master bot 的 DPS 输出循环真正转起来 → 首次打掉 boss 血量 → 向"打通首个 boss"迈进

## 1. 背景修正（重要）

B2 初始规划时曾假设"角色初始化缺技能学习"（`LearnDefaultSkills`），**该假设已证伪**：
- `Player::Create`（Player.cpp:622）本身调用 `LearnDefaultSkills()`——core 建角流程已含
- `character_spell` 只存额外学的技能，默认职业技能登录时自动加载；random bot 的 `character_spell` 为 0 行但完全正常
- run 事件里 bot 确实在放职业技能（48438 狂暴等）

**真实问题**：bot 有完整技能、能施法，但对 boss 的 DPS 施法每场仅 ~4 次（~1.8 casts/s 主要是辅助/自 buff）——输出循环没对主目标形成。

## 2. 根因（已核实，精确到 file:line）

`AttackersValue::IsPossibleTarget`（`src/Ai/Base/Value/AttackersValue.cpp:223-233`）对 loot-tagged 生物的判断：

```
botAI->GetMaster() 为 null（无 master）→ leaderHasThreat=false
isMemberBotGroup=false
boss 有 loot recipient（Pull 时设置）→ !hasLootRecipient()=false
isTappedBy(bot)=false（仅 leader 被 tapped）
→ canAttack=false → boss 对 non-leader 无 master bot 不是合法目标
```

**抑制链**（每 tick 执行）：
1. `CombatStrategy.cpp:21-28` 注册 `"invalid target" → NextAction("drop target", 99)`（优先级 99，压过输出循环的 ~5）
2. `InvalidTargetTrigger::IsActive`（GenericTriggers.cpp:201）→ `InvalidTargetValue`（InvalidTargetValue.cpp:25）对 loot-tagged boss 返回 true
3. `DropTargetAction`（ChooseTargetActions.cpp:59-70）清 `current target`、弹回 NON_COMBAT
4. `CastSpellAction::isUseful`（GenericSpellActions.cpp:183-207）目标 null → 输出循环动作全部 useless

**为何 BeginPullForAll 没治本**：`AttackAction::Attack` 设了 current target 并切 COMBAT 引擎（目标**获取**成功），但下一个 tick 的 "invalid target" 触发器重新校验 → 又清掉。方案 b 修了"获取"，没修"每 tick 再校验"。

## 3. 修复设计（方案 b：模块侧启用 attack tagged 策略）

**核心**：`AttackersValue.cpp:223` 有现成豁免——`HasStrategy("attack tagged", BOT_STATE_NON_COMBAT)` 为真时 boss 成为合法目标。mod-raidtest 在每个 bot 登录后调 `PlayerbotAI::ChangeStrategy("+attack tagged", BOT_STATE_NON_COMBAT)`（`PlayerbotAI.cpp:1584`，`AttackTaggedStrategy` 存在于 `NonCombatStrategy.h:43-50`）。

**为什么选模块侧而非配置/源码**：
- 方案 (a) 全局配置 `AiPlayerbot.NonCombatStrategies=+attack tagged`——会污染所有随机 bot 的世界行为
- 方案 (c) 改 `AttackersValue.cpp` 共享逻辑——同步成本高，可能被视为改被测环境
- 方案 (b) 只作用于 raidtest 拉入的 bot，作用域干净、不碰 mod-playerbots 源码

**接入点**：`RaidTestOrchestrator::TickLoginAndGroup`（`RaidTestOrchestrator.cpp:293`，登录完成、bot 全部 `IsInWorld` 后）遍历 bot 调 `GET_PLAYERBOT_AI(bot)->ChangeStrategy("+attack tagged", BOT_STATE_NON_COMBAT)`。或封装进 `RosterLogin` 提供 `ApplyMasterlessCombatStrategy(bots)` 供 Orchestrator 调用。

**效果**：`canAttack=true` → boss 成为合法目标 → "invalid target" 不再触发 → 输出循环（frost/arms/fury 等 class 策略）对 current target 正常施法。**施法选择仍是 bot 自身策略决定，不注入任何脚本化轮换。**

## 4. 验收标准（B2-1 完成判据）

- [ ] 编译通过、世界线程非阻塞纪律保持
- [ ] 重建/重新登录后，`.raidtest run naxx-patchwerk --attempts 3` 的 DPS 施法量显著回升（>>4 次/场，出现稳定输出法术重复施放）
- [ ] boss 血量开始明显下降（不再钉死在 98-99%）
- [ ] 无脚本化轮换注入——施法序列由 class 策略产生（可用 `raidtest_events` 的 spell 序列验证是策略驱动而非硬编码）

## 5. 风险与说明

| 风险 | 缓解 |
|---|---|
| `ChangeStrategy` 在错误引擎上调用无效 | 确认传 `BOT_STATE_NON_COMBAT`（AttackersValue 检查的就是 NON_COMBAT 的 HasStrategy） |
| 策略启用后仍不施法 | 下一步调查 class 策略的触发条件/动作优先级（B2 深化） |
| 影响真实场景 | 仅对 raidtest 拉入的 bot 生效，随机 bot 不受影响 |
| 与 Pull 的交互 | Pull 时 attack tagged 已生效，不需额外处理 |

## 6. 完成后记录

- [记录] 启用后 DPS 施法量实测值（对比 B1 的 ~4 次/场）
- [记录] boss 血量实际下降程度
- [TODO] 首次 run 传送超时根修（B1 遗留）
- [TODO] 随机 bot 游荡禁用（MaxRandomBots=0 已压制）
