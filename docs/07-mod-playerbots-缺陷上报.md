# mod-playerbots 缺陷整改/上报文档（2026-09-04）

> 项目: `mod-playerbots`（AzerothCore 3.3.5a WotLK Playerbot fork）
> 提交基线: `2f7d9f77` (master)
> 上报方: mod-raidtest 自动化团测框架（框架仅观察记录，不代写 bot 行为逻辑）
> 状态: 供评审/向上游提交 PR 或 issue

## 摘要

mod-raidtest 在 Naxxramas（地图 533）真实战斗的事件流与位置采样归因中，发现 mod-playerbots 两处**独立**缺陷，均导致机器人无法按真实团队副本策略正常战斗。第一处为 NAXX Patchwerk BOSS 站位动作整段被注释（未启用）；第二处为通用"近战接近目标"判定对大型 BOSS 失真的核心逻辑问题。二者共同造成:近战/坦克不贴近 BOSS、坦克零仇恨、团灭。

---

## 缺陷 ①：Patchwerk 站位动作整段被注释（未启用）

### 现象

10 人团队传送到 Patchwerk 房间任一安全点后，所有 bot 停留在原地不推进;坦克不走向主坦位、远程不拉开距离。BOSS 仇恨打击（Hateful Strike）随即非目标地命中 DPS/治疗，秒杀团灭。

### 证据链（file:line）

| 位置 | 内容 |
|---|---|
| `src/Ai/Raid/Naxx/Action/NaxxActions_Patchwerk.cpp:11-40` | `PatchwerkRangedPositionAction::Execute()` 实现**整段被 `//` 注释**，内含关键逻辑: 判定远程距 boss 12-15 码、`MoveTo` 到正确距离 |
| `src/Ai/Raid/Naxx/NaxxActionContext.h:51` | 动作注册被注释: `//creators["patchwerk ranged position"] = ...` |
| `src/Ai/Raid/Naxx/NaxxActionContext.h:88` | 工厂方法被注释: `//static Action* patchwerk_ranged_position(...)` |
| `src/Ai/Raid/Naxx/NaxxStrategy.cpp:67-76` | 三个触发器被注释: `//"patchwerk tank" (tank face)`, `//"patchwerk ranged" (ranged position)`, `//"patchwerk non-tank" (rear flank)` |
| `src/Ai/Raid/Naxx/Action/NaxxActions.h:325-328` | 动作类声明被注释: `//class PatchwerkRangedPositionAction` |

### 对照（其他 BOSS 站位是激活的）

同目录下其他 NAXX BOSS 站位动作均正常注册与使用:
- `NaxxStrategy.cpp:42` `"kel'thuzad" → kel'thuzad position`
- `NaxxStrategy.cpp:49` `"anub'rekhan" → anub'rekhan position`
- `NaxxStrategy.cpp:89` `"thaddius phase transition" → thaddius move to platform`
- `NaxxStrategy.cpp:102` `"sapphiron ground" → sapphiron ground position`

### Git 历史

`git blame` 确认: 该注释自 2026-03-06 (`18bd6558`) 引入 Naxxramas 策略时就处于注释状态——**作者已写好但从未启用**。

### 建议修法

取消三处主要注释（实现、注册、触发器），保留 `ActionContext.h` 与 `Actions.h` 中的类声明:
```
NaxxActions_Patchwerk.cpp: 恢复 PatchwerkRangedPositionAction::Execute
NaxxActionContext.h:88:     恢复 patchwerk_ranged_position 工厂
NaxxStrategy.cpp:71-73:    恢复 "patchwerk ranged" → patchwerk ranged position
```
也可附加恢复"patchwerk tank"(tank face) 触发器以强化坦克面向。若该动作因历史原因被刻意禁用（如移动死锁），请给出替代方案而非留悬念。

---

## 缺陷 ②：近战接近目标的距离判定对大型 BOSS 失真

### 现象

位置采样显示: 巨型 BOSS（Patchwerk，站距 5 码）与其 10 人团队相距约 5 码时，所有 bot **一毫米不再移动**——`enemy out of melee` 触发器不激活、`reach melee` 动作不执行，近战（尤其坦克）永远不会贴脸。坦克全程只施放无目标 buff、零近战攻击，导致仇恨清零。

### 链路

```
OutOfRangeTrigger::IsActive()      (RangeTriggers.cpp:155-164)
ReachTargetAction::isUseful()      (ReachTargetActions.cpp:31)
    └─ 都调用 → Unit::IsWithinCombatRange(target, distance)
```

核心判定（`src/server/game/Entities/Unit/Unit.cpp:766-779`）:
```cpp
float sizefactor = GetCombatReach() + obj->GetCombatReach();  // 双方体型半径合计
float maxdist   = distance + sizefactor;
return distsq < maxdist * maxdist;
```

### 根因

`IsWithinCombatRange` 将 **BOSS 的体型半径**（`GetCombatReach`）并入"可打击距离"，用于触发玩家的移动。对大型 BOSS（Patchwerk CombatReach 数十码）:
```
distance=0.75 + bot reach(1.5) + boss reach(≈8-10)  → 判定阈值 ≈ 10+ 码
实际站距 5 码 < 10 码  → 判定"已在近战内" → reach melee 不触发 → 不移动
```

该函数语义是"是否在合击中（体型边缘接触即可）"，用于玩家跟怪合理；但被 mod-playerbots 复用为"近战该不该更靠近"的移动判据，对大型 BOSS 造成误判——真实战斗里 bot 需要站到**实际攻击距离**（远程拉满、近战贴平），而非体型边缘。

### 证据（运行时位置采样）

```
boss(entry16028) 位置: 逐步从3256逼近到 3281
所有bot位置:      恒 3286（一毫米不动）
间隔 ≈ 5 码 ≈ 触发阈值内 → 永远判定"已够近"
```

### 建议修法（二选一，倾向 2）

1. **移动判定用实际距离**: `ReachTargetAction::isUseful`/`OutOfRangeTrigger` 对"近战接近目标"改用纯距离判定（`GetDistance` 比较，不含体型合计），或新写 `IsWithinMeleeAttackRange` 语义。
2. **判定阈值按目标** 在大型 BOSS 上收紧: 对 `GetObjectSize() > N` 的 BOSS 目标使 `maxdist` 收敛到"bot reach + 目标 attack reach"，而非两者体型合计。**注意**: 有两个策略同时依赖此判定（RangedCombatStrategy 的移动作业、MeleeCombatStrategy 的 `enemy out of melee`），修法应一并验证。

### 风险提示

改动将影响:
- `EnemyOutOfMeleeTrigger`（近战走近）
- `EnemyOutOfSpellRangeTrigger`（远程射程逼近）
- `ReachSpellAction` / `ReachMeleeAction` cent大使用同一判定
建议改动后用 Kael'Thas、Anub'Rekhan 等不同体型 BOSS 回归验证远近战都能正确走位。

---

## 复现步骤（mod-raidtest 实测环境）

前置: 已编译 mod-raidtest 场景 `naxx-patchwerk`，10 个 80 级 bot（装备 ilvl 264-284 史诗、职业 1坦2治疗7DPS），`playerbots.conf` 关键项: `RandomBotAutologin=1`, `MinRandomBots=0`, `MaxRandomBots=0`。

```
1. .raidtest run naxx-patchwerk --attempts 3
2. 观察 attempt 判定: 3/3 aborted, notes='boss lost combat state (stuck/reset)'
3. 查询 raidtest_events 位置采样:
   SELECT e.rel_ms, e.detail FROM raidtest_events e
   WHERE e.attempt_id=? AND e.detail LIKE 'pos:%' AND e.actor_entry=0;  -- 复数 bot
   → 所有 bot 位置恒定约 5 码外
4. 查询坦克动作: 仅 0~15 次无目标 buff, 无 boss 目标技能
```

## 影响范围

- 通道: 所有 NAXX Patchwerk（架设只 read `naxx-patchwerk` 场景）；缺陷② 影响所有大型/巨型 BOSS 的近战 AI 效率。
- 观察到的最小表现: bot 场均 DPS 施法 ~10 次、BOSS 血量仅降 3-5% 即团灭，攻坚 WotLK 团本（尤其 ICC 大型 BOSS）受阻。

## 关联

- 本项目 context: `docs/06-mod-raidtest-B2-激活输出循环-设计.md`
- 完整数据: `.superpowers/sdd/progress.md` 中 "B2 深挖" 段