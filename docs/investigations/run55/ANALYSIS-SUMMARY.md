# run55 分析任务书（给接手 AI）

> 用途：其他 AI 会话接手分析 run55 Loatheb 正伤害空窗根因的自包含任务书。
> 关联：本目录 `README.md`（接手核验详情）、`analyze.py`（复算脚本）、`events-run54-run55.tsv`（本地导出，gitignore）。
> 更新时间：2026-09-06。

## 1. 背景

`mod-raidtest`（AzerothCore 3.3.5a + mod-playerbots 自动团测框架）用 10 个 80 级 bot 打 Naxxramas 各 boss，验证 mod-playerbots 底层机制。框架只**编排与观察**（建号/组队/传送/开怪/记录），**不代写 bot 行为逻辑**——发现底层缺陷如实记录为 mod-playerbots 的发现。

场景 `naxx-loatheb`：10 bot（主坦血DK 646 + 防骑 654 + 牧师 647 + 德鲁伊 648 + 法师 649 + 术士 650 + 猎人 651 + 盗贼 652 + 萨满 653 + 冰DK 655）。Loatheb entry=16011，实例 guid=106，home=出生点(2909,-3997.41)。

## 2. 待解问题（run55，attempt 1788426357）

run55 结果为 timeout（300s），boss_hp_min=86%，但**开局 7.244–65.260s 对 boss 正伤害空窗约 58s**，且 **boss 血量 13.607s 从 99% 回满到 100%**（run54 对照无此回血）。防骑(654) 死于 64856ms，正伤害于 65260ms 恢复。

## 3. 已核实事实（数据库事件，勿再推翻）

| 项目 | 值 |
|---|---|
| run54 vs run55 | 均 timeout；hp_min 59% vs 86% |
| 开局 13.6s 对 boss 伤害 | run55 ~33k / run54 ~178k（约 1/5，低效但**非零**） |
| 前 60s 对 boss 伤害合计 | **31866**（防骑 3818 只是其中一部分） |
| 主坦对 boss | 开局 0-3000ms **5 次共 1488**（非 1488×5、非零） |
| 正伤害空窗 | 7244ms → 65260ms（~58s）；空窗中冰DK 还有 5 条 damage=0 记录 |
| boss HP 转折 | 0ms=99% → **13.607s=100%** → 65.260s=99% → 一路降到 86% |
| 防骑死亡 | 64856ms；距恢复正伤害 65260ms 约 404ms（**非同帧**） |
| 施法 | mage 前 60s spell 事件**恒定 1.092s**（= GCD 节奏，非"读条被打断"证据） |
| boss 位置 | ~8s 到坦克站位(2881,-3969) 固定；防骑死后向远程位移动 |

**时钟注意**：事件 rel_ms 是 steady_clock，Observer 的 duration_ms 是 diff 累加（300008），两者不是同一时钟，不能直接混用。

## 4. 当前假设（优先级，**未证实**）

**假设链**：boss 追逐防骑至坦克站位 → 寻路失败/目标不可达 → `SetCannotReachTarget` → `IsEvadingAttacks()=IsInEvadeMode()||CanNotReachTarget()` → 法术返回 `SPELL_MISS_EVADE`、普攻同类检查 → `SetCannotReachTarget` 启动 evade timer + `IsNotReachableAndNeedRegen` 关联回血 → `EvadeTimerExpired` raid 分支继续 regen（不一定正式脱战归位）。**该链可同时解释"持续施法 + 伤害空窗 + 回血 + 防骑死后恢复"，但历史事件未记录 miss/evade 标记，仍非已证实根因。**

**已撤回的旧假设**：DPS 引擎"读条持续自打断 / 初始化随机性"——OnSpellCast 是 `Spell::_cast` 执行后段（≠读条开始、不保证命中），恒定施法间隔只是 GCD 节奏，不能证明自打断；`PlayerbotAI::UpdateAI` PREPARING 分支正常路径等待施法。

## 5. 证据与复算

- **数据库**（`mysql -uacore -pacore acore_characters`）：表 `raidtest_runs / raidtest_attempts / raidtest_events`（attempt 1788426354=run54 / 1788426356=run54 / 1788426357=run55；事件类型 enum：spell/damage/death/boss_hp/combat_start/combat_end/strategy/state）
- **复算脚本**：`python3 docs/investigations/run55/analyze.py`（读本地 `events-run54-run55.tsv`，输出伤害窗口/死亡/空窗/HP 转折）
- **run55 日志快照**：本目录 `worldserver-run55.log`（gitignore，本地保留）
- **服务器当前日志**：`env/dist/bin/Playerbots.log`（只到 06:41，**不覆盖 run55 09:40**）

## 6. 代码状态（已提交 829b220，未编译）

观测补丁在 `mod-raidtest` dev 分支（只观察、不改 bot 行为/仇恨/boss 机制）：
- `src/Observer/CombatEventBus.cpp`：spell 事件 detail 加 `cast_ms` + 显式目标 `miss={} reflect={}`；新增 `OnSpellCastCancel` → `cast_cancel` 状态事件（`by_self/cast_ms/remaining_ms`）
- `src/Observer/AttemptObserver.cpp`：每秒随位置采样 `boss_state:combat evade unreachable evading_attacks regen unreachable_guid victim`
- `src/Bot/RosterLogin.cpp/.h` + `src/Orchestrator/RaidTestOrchestrator.cpp`：`LogoutAll` run 收尾强制登出（全灭残留污染下一 run）
- 不改 SQL schema（复用 detail/state 字段）

**关键源码参考**（假设链落点）：
- `azerothcore-wotlk/src/server/game/Movement/TargetedMovementGenerator.cpp`（SetCannotReachTarget）
- `src/server/game/Entities/Creature/Creature.h`（IsEvadingAttacks/CanNotReachTarget）
- `src/server/game/Entities/Unit/Unit.cpp`（SPELL_MISS_EVADE 判定）
- `src/server/game/Entities/Creature/Creature.cpp`（SetCannotReachTarget/IsNotReachableAndNeedRegen）
- `src/server/game/AI/CoreAI/UnitAI.cpp`（EvadeTimerExpired raid 分支）
- `src/server/scripts/Northrend/Naxxramas/boss_loatheb.cpp`（IsInRoom>50 码 EnterEvadeMode）

## 7. 给分析 AI 的任务

1. **编译授权后**（用户必须明确同意；`MTHREADS=4` + ccache）：编译 mod-raidtest 补丁，确认 `cast_cancel` / `boss_state` / spell `miss` 新字段落库
2. **重跑**：服务器重启后先热身跑一次（已知 teleport 超时回归），再连跑 3 次 `naxx-loatheb`
3. **核对**：正伤害空窗是否与 `boss_state.unreachable / evading_attacks` 及 spell `miss` 时间一致
   - 一致 → 验证假设链，进一步定位寻路失败点（boss 为何不可达、站位如何）
   - 不一致 → 按 `cast_cancel`（by_self？谁取消？剩余读条）或命中结果转查其他路径
4. **对照**：run54 无回血无空窗，作为正常基线
5. **独立遗留项**（不能跳过）：主坦未形成持续攻击；事件时钟 vs duration_ms 差约 2 倍；全灭后判定仍为 timeout（B2-6 竞态家族）

## 8. 约束

- 编译必须征得用户同意（本机编译会卡死）
- mod-raidtest 只编排观察，发现缺陷记录为 mod-playerbots 的发现，不代写 bot 逻辑绕过
- 数据库只读查询；改数据需走工单/确认
- 文档/沟通用中文；提交用仓库现有风格
