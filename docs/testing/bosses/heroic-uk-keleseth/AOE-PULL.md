# 清怪停滞 / 误伤 boss 调查（2026-09-06）

基线：框架 mod-raidtest/dev `3b9203b` + 未提交改动；mod-playerbots `2f7d9f77`；角色 heroic5-v1，cheat=0。

## 结论

run87/88/90 清怪卡死在 2/4 并 180s 超时，根因是 **mod-raidtest 框架再拉怪门槛误用 unit 战斗标志**，不是几何、不是清怪误伤、也不是 attempt-1 清理。修复门槛判定后 run91/a1、run92/a1、run92/a2 连续三场零死亡击杀，其中 attempt2 走跨场清理路径同样通过。

## 已确认的源码事实（误伤候选）

- MageAoeStrategy 会选择烈焰风暴、暴风雪等；FindMaxDensity/AoeCountValue 统计 possible targets，可包含尚未参战敌人。
- PlayerbotAI::CastSpell 地面法术落点用当前目标位置；aoe position 调用已注释。仅修 AoePositionValue 不能解决实际落点。
- run86/a2 在 481/503ms 有指向上一场 boss139 的施法取消记录；状态残留存在，但不是清怪卡死的原因。

## 停滞根因（run87/88/90）

- 症状：只杀准备点西侧的铁盔战士（126046）与一只符文法师（126042）；战略家 23956（126032，拉怪顺序第一）与另一只符文法师（126041）从未被攻击；bot 全员 target=none、AI 转非战斗态，但坦克/治疗/法师 unit combat 标志残留 true；框架不再发下一次拉怪，180s `clearing timeout`。
- 排除 1（attempt-1 清理）：run89 对 attempt1 跳过清理（`ctx.attemptSeq > 1` 门控）仍卡 2/4 → 推翻。
- 排除 2（几何不可达）：preclear_target 诊断显示战略家 145 对每只 bot 均 los=true、valid=true，距离 19–25 码，在施法/近战范围内 → 推翻。
- 真根因：框架拉怪目标被 `BeginPullForAll` 里的 `SetInCombatWith` 强制入战，但 bots 的 combat AI 先把实际攻击它们的怪（铁盔战士/符文法师）当目标；杀掉后 AI 转非战斗态，残留战斗关系让 `bot->IsInCombat()` 永久为 true，`_prerequisitePullSent` 永不重置 → 不再拉 `next` → 死锁。

## 修复（AttemptRunner.cpp）

再拉怪门槛：`bot->IsInCombat()`（unit 标志）改为 `ai->GetState() == BOT_STATE_COMBAT`（AI 战斗引擎态）。bots 的 AI 退出战斗即允许再拉 `next`。

## 验证

| run / attempt | 结果 | 时长 | deaths | boss 最低 HP |
|---|---|---|---|---|
| 91 / 1 | kill | 154.7s | 0 | 0% |
| 92 / 1 | kill | 142.9s | 0 | 0% |
| 92 / 2 | kill | 154.4s | 0 | 0% |

连续三场零死亡击杀；attempt2 走跨场清理路径（清理只在 attempt2+ 执行）同样通过。对比 run86（此前唯一成功，212.8s）更快。

## 附带改动（均未提交）

- attempt-1 跳过清理：语义正确（首场无上一场残留），但已被证明不是根因，作为加固保留。
- 诊断日志：preclear_status（bot 战斗态/目标/位置）、preclear_target（下一个拉怪目标位置 + 每 bot 的 LOS/距离/有效性）、preclear_boss_invalid 事件、地面法术 dst 记录。
- 代码：`src/Orchestrator/AttemptRunner.cpp`、`src/Observer/CombatEventBus.cpp`。

## 待办

- 误伤候选（法师 AoE 打 boss）在修复后未复现；仍建议按需审计 AoeCountValue 是否把未参战单位计入 possible targets。
- 连续稳定通关（更多场次）与冰墓机制验收仍未完成。
