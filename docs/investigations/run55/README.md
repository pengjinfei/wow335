# run55 接手核验（2026-09-06）

## 范围与状态

本记录基于本机 MySQL 原始事件、保留的 worldserver 日志和当前源码；替代旧报告中未经验证的具体归因。没有编译、重启或新跑实验。旧工作区改动全部保留。

- Core HEAD: `47960183bb03b83e8943eb2f0f39c16df9710c9d`（Playerbot，干净）。
- mod-playerbots HEAD: `2f7d9f774987d0157c6a0d0cc08c40bec3db3945`（master，干净）。
- mod-raidtest HEAD: `83d1a10`（dev）。接手前已有 roster、RosterLogin.cpp/.h、Orchestrator 修改，以及未跟踪的 Anub 场景。
- 日志证实 run55 使用 force-recreate，GUID 646–655；收尾实际执行了 LogoutAll。不能仅凭当前 HEAD 重现二进制，原有未提交修改也是现场的一部分。
- 原始导出 `events-run54-run55.tsv` 和日志快照仅本地保留，由本目录 .gitignore 排除；运行 `python3 docs/investigations/run55/analyze.py` 可复算。

## 经原始数据核实的事实

| 项目 | run54 | run55 |
|---|---|---|
| attempt_id | 1788426356 | 1788426357 |
| 数据库结果 | timeout | timeout |
| duration_ms | 300006 | 300008 |
| boss_hp_min | 59 | 86 |
| 死亡事件数 | 11（含重复角色） | 10 |

run55 的时间线使用事件 rel_ms（steady_clock）；结果 duration_ms 由 Observer 累加 diff。两者不是同一时钟：run55 最后 boss_hp 事件约 150504ms，但 duration_ms 为 300008。需另查 diff 的调用/计时，不能把它们直接混为同一时间轴，也不能仅凭每名角色死过一次断言同时全灭。

- boss low GUID=106。主坦血 DK=646，防骑=654，法师=649，术士=650，猎人=651，盗贼=652，萨满=653，冰 DK=655；647/648 是治疗牧师/德鲁伊，没有“暗牧 DPS”槽位。
- 主坦开局 0–3000ms 对 boss **5 次共 1488**，不是 1488×5，更不是零伤害。
- 全部来源对 boss 前 60 秒伤害记录合计 **31866**；防骑贡献 4 次共 3818。damage hook 是结算路径内采样，数值不能无条件等同净血量损失。
- 最后一次空窗前正伤害在 **7244ms**；下一次在 **65260ms**（来源 898）；法师第一次恢复伤害在 65446ms。正伤害空窗约 **58.016 秒**。
- 空窗中冰 DK 有 5 条 damage=0 记录（9767–21773ms），所以“无 damage 事件”也不准确。
- boss HP 首个样本为 99%，**13607ms 回到 100%**，65260ms 回到 99%。原描述“开局 100% 钉死 60 秒”遗漏了回血。
- 防骑死亡 64856ms，距首笔恢复正伤害 **404ms**，不是同帧。
- 10–60 秒内 boss 对防骑仍有伤害记录，共 42876；不能延用“boss 不攻击任何坦克”的表述。
- boss 在约 8 秒到达坦克站位附近，60–64 秒位置为 (2881.26,-3969.82,273.63)；防骑死后开始向远程位置移动。

## 源码解释与假设分级

已核实：CombatEventBus 用 AllSpellScript::OnSpellCast 采集 spell。该 hook 在 Spell::_cast 的执行后段；不是读条开始事件，也不保证命中。固定施法间隔不能证明持续自打断。PlayerbotAI::UpdateAI 的 PREPARING 分支正常路径会等待施法，不支持“每 tick 都重评估并取消一切读条”的概括。

优先待验证：boss 追逐防骑到达坦克站位时触发无法到达目标状态，导致攻击被 evade，然后开始回血；防骑死亡换目标后解除。

对应源码链：

1. `TargetedMovementGenerator.cpp`：寻路失败或目标不可达调用 `SetCannotReachTarget(target GUID)`。
2. `Creature.h`：`IsEvadingAttacks() = IsInEvadeMode() || CanNotReachTarget()`。
3. `Unit.cpp`：该状态可令法术返回 `SPELL_MISS_EVADE`，普攻也有对应检查。
4. `Creature.cpp`：SetCannotReachTarget 启动 evade timer；`IsNotReachableAndNeedRegen` 关联回血。
5. `UnitAI::EvadeTimerExpired`：raid 分支继续 evade regen，不一定正式脱战归位。

这条链可以同时解释持续施法、伤害空窗、回血、目标死亡后恢复，但历史事件未记录相关标记或 miss，**仍不是已证实根因**。已请用户转问开发 AI 是否留有相应日志。

## 已准备的观测补丁（尚未编译）

仅 mod-raidtest 两个 Observer 文件，未改 bot 行为、仇恨或 boss 机制：

- `AttemptObserver.cpp`：每秒随位置额外采样 boss combat、evade、unreachable、evading_attacks、regen、不可达目标 GUID 和当前 victim。
- `CombatEventBus.cpp`：spell.detail 增加实际 cast_ms 和显式目标 miss/reflect（有匹配才记录）；新增 cast_cancel 状态事件，记录 bySelf 和剩余施法时间。bySelf 是 core 参数，不等于已定位 AI 中断来源；miss 是该 hook 时点快照，不保证覆盖所有延迟命中后的结果。
- 不改 SQL schema；复用 detail/state。取消事件显式限制在本 attempt 成员范围。
- 已检查本地 API 声明及 git diff --check；**编译和实机验证待授权**。

## 下一轮验证

保持 run55 阵容和 engage 配置，获准编译后以低并发构建。先核对新字段确实落库，再查看伤害空窗是否与 boss_state.unreachable/evading_attacks 及 spell miss 一致。若一致，再定位路径失败点及站位；若不一致，根据取消记录/命中结果转查其他路径。

另列两项独立问题：主坦未形成持续攻击；事件时钟与 duration_ms 差约两倍且全员死亡记录最终为 timeout。两项都不能由“DPS 引擎随机性”代替调查。
