# run55 分析 Prompt（给无上下文 AI，一页版）

> 最新验收：[LIFECYCLE-FIX.md](LIFECYCLE-FIX.md)。run67重启后原角色、原实例连续两次零死亡击杀；DK显式主坦、首次传送、击杀后恢复三项通过。下文历史状态保留供审计。

> 接手新进展：见 [TAKEOVER-VALIDATION.md](TAKEOVER-VALIDATION.md)。已定位建团漏注册并修复；run63/65血DK均恢复全场持续攻击并击杀；run65防骑死亡后由DK承伤完成击杀。原run59分析保留历史口径。

> **最新状态：编译及热身+3次正式验证已完成，不要重复执行下文历史任务步骤。** run56/57 timeout，run58/59真实kill（run59零死亡）；四次均无长空窗、无unreachable采样、无boss目标miss=6。主坦持续攻击问题仍存在。下一步以 [VALIDATION.md](VALIDATION.md) 的遗留项为准，run55不可达假设仍未证实。

**角色**：你是 AzerothCore 3.3.5a + mod-playerbots 的战斗分析 AI。目标：定位 run55 Loatheb 战斗"正伤害空窗 + boss 回血"根因。

## 问题

mod-raidtest 场景 `naxx-loatheb`（10 bot，地图 533）run55（attempt 1788426357，result=timeout，boss_hp_min=86%）：
- 开局 **7.244–65.260s 对 boss(entry 16011, guid=106) 正伤害空窗 ~58s**
- **boss 血量 13.607s 从 99% 回满到 100%**（run54 无此回血）
- 防骑(654) 死于 64856ms，正伤害 65260ms 恢复
- run54（attempt 1788426356）为正常基线（无空窗无回血，hp_min 59%）

## 已核实（勿推翻）

- 前 60s 全团对 boss 伤害合计 **31866**（非零）；主坦血DK 开局 0-3000ms **5 次共 1488**
- mage 前 60s 施法**恒定 1.092s** = GCD 节奏，**不是"读条被打断"证据**
- OnSpellCast 在 `Spell::_cast` 执行后段，**≠读条开始、不保证命中**（旧"读条自打断"归因已撤回）

## 优先假设（未证实）

boss 追逐防骑至坦克站位(2881,-3969) → 目标不可达 `SetCannotReachTarget` → `IsEvadingAttacks()=IsInEvadeMode()||CanNotReachTarget()` → 法术/普攻 `SPELL_MISS_EVADE` → evade timer + `IsNotReachableAndNeedRegen` 回血 → 防骑死后解除。
源码落点：`TargetedMovementGenerator.cpp` / `Creature.h` / `Unit.cpp` / `Creature.cpp` / `UnitAI.cpp`(EvadeTimerExpired) / `boss_loatheb.cpp`(IsInRoom>50码)。

## 证据

- DB：`export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"; mysql -uacore -pacore acore_characters` → 表 `raidtest_events`（按 attempt_id 查，detail 含 `pos:`/`boss_state:` 采样；事件 enum：spell/damage/death/boss_hp/combat/strategy/state）
- 复算脚本：`python3 docs/investigations/run55/analyze.py`
- 详细核验：`docs/investigations/run55/README.md`

## 代码（已提交 829b220，已授权编译安装，run56–59 验证完成）

mod-raidtest dev 分支观测补丁（只观察不改 bot 行为）：
- `CombatEventBus.cpp`：spell detail 带 `cast_ms` + `miss/reflect`；新增 `cast_cancel` 状态事件（`by_self/cast_ms/remaining_ms`）
- `AttemptObserver.cpp`：每秒采样 `boss_state`（combat/evade/unreachable/evading_attacks/regen/unreachable_guid/victim）

## 你的任务

1. **编译须用户明确授权**（`MTHREADS=4` + ccache；CLAUDE.md 规则）。编译后先确认 `cast_cancel` / `boss_state` / spell `miss` 新字段确实落库
2. 服务器重启后**先热身跑一次**（已知 teleport 超时回归），再连跑 3 次 `naxx-loatheb`
3. 核对空窗是否与 `boss_state.unreachable/evading_attacks` 及 spell `miss` 时间一致
   - 一致 → 验证假设链，继续定位寻路失败点（boss 为何不可达、站位）
   - 不一致 → 按 `cast_cancel`（by_self？谁取消？剩余读条）或命中结果转查其他路径
4. 对照 run54 基线（无空窗无回血）
5. 独立遗留项（不能跳过）：① 主坦未形成持续攻击 ② 角色死亡后离开副本，最终仍为 timeout（完整事件流到 299998ms，时钟两倍差异已排除）

## 约束

- 编译必须征得用户同意（本机编译会卡死）
- mod-raidtest 只**编排与观察**，不代写 bot 行为逻辑绕过；底层缺陷记录为 mod-playerbots 的发现
- 数据库只读查询；文档/交流用中文
