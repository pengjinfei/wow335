# 纳克萨玛斯 10 人 / 天启四骑士 / `naxx10-horsemen-r10g`

## 接手摘要

- 2026-09-28：**0/6（全部开怪中止），跳过待用户决定**。
- raidtest 新增 `KillOnBossState = 12`（实例 boss 状态 DONE 判击杀，不按单个 BossEntry 死亡）。

## 开怪失败（run 1606–1611）

- 准备点 (2494,-2962,241.3)，距四人 30 码、在 BOSS_HORSEMAN 边界内。框架对科尔塔兹开怪后 boss 进战但无目标、**不移动**；主坦走到 12.7 码后触发 bot 的 `invalid target`（`AttackersValue::IsValidTarget` 过滤）并丢掉目标。
- 脚本：`JustEngagedWith` 里四人切 `REACT_PASSIVE` 沿路点走向各自角落，到终点才 `SetInCombatWithZone` 并选目标。这里四人没走动，推测框架的远程开怪只让 boss 挂上战斗、未触发真正的 engage；未证实。
- 试过让拿仇恨窗口忽略「boss 无目标且在移动」——boss 没动，无效，已撤回。

## 即使开怪解决，还需要

playerbots 四骑士策略只处理远程侧（第一远程 + 第一治疗在两个点之间轮换吸女士/泽里克），近战侧印记（科尔塔兹、里文戴尔）叠层需要坦克跨角落换位，10 人双坦要重新设计。属较大改动。
