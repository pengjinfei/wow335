# run56–59 观测验证结果（2026-09-06）

## 结论

观测补丁已编译、安装、实机验证。热身一次后完成三个独立正式 run：run57 timeout，run58/59 真实 kill；run59 无队员死亡。四次均未复现 run55 的长伤害空窗，不能将未复现称为已修复。

主坦血 DK 的持续攻击缺失在四次中都存在。run59 实际由防骑稳定承伤，证明“所有坦克都无法建仇、必须先修引擎才能击杀”的旧判断过强。

## 实验条件

- 用户已授权编译及验证；构建维持 MTHREADS=4、ccache。
- `./acore.sh compiler build` 重新配置触发大范围构建。发现本地 conf/config.sh 的 MySQL 路径指向 9.3，停止首次构建后改为 mysql@8.4，重新构建安装成功。otool 确认 worldserver 链接 mysql@8.4 的 libmysqlclient.24。
- Core `47960183bb03`，playerbots `2f7d9f774987`，raidtest 当前 `829b220`，包含本次两个 Observer 的采样。测试期间没有修改行为、仇恨、伤害倍率或 boss 脚本。
- 重启后 run56 热身，随后 run57–59 各自执行 `naxx-loatheb --attempts 1 --force-recreate`。每次 run 结束 LogoutAll。
- 蓝图与 engage 坐标不变，但 force-recreate 涉及工厂补装等初始化差异，不能把本轮当成所有装备/运行状态完全固定的严格因果实验。

## 结果

| run | attempt | 用途 | 结果 | 时长 ms | 最低 HP% | 队员死亡事件 | 前60秒伤害 | 最长相邻正伤害间隔 ms | 主坦次数/伤害 |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| 56 | 1788426358 | 热身 | timeout | 300008 | 47 | 10 | 1831609 | 3004 | 5 / 1384 |
| 57 | 1788426359 | 正式1 | timeout | 300006 | 54 | 10 | 1745472 | 3004 | 3 / 744 |
| 58 | 1788426360 | 正式2 | kill | 215264 | 0 | 6 | 1798180 | 1161 | 5 / 1531 |
| 59 | 1788426361 | 正式3 | kill | 198304 | 0 | 0 | 1839253 | 825 | 3 / 846 |

伤害按所有来源 target=boss 的 damage 事件计；间隔只计算首尾正伤害之间，不包含战斗收尾后的无输出时间。

真实击杀证据：

- run58：215261ms，death source=106，actor_entry=16011，killer=682；日志确认 hp=0 + boss death event 连续3采样。提前出现的 0% HP 是整数百分比，不能独立证明死亡。
- run59：198293ms，death source=106，actor_entry=16011，killer=931；attempt=kill，队员死亡事件为0。

## 新观测验收

- 四场 boss_state 均有数据，`unreachable=true` 数量全部0。
- 显式 boss 目标 spell 的 `miss=6`（SPELL_MISS_EVADE）全部0。`miss=7/8` 为免疫，不能当作 evade。
- cast_cancel 事件依次18、17、19、17条；有取消事件本身不等于持续自打断，需按角色和法术定位。没有复现58秒空窗。
- run56/57 出现战斗后正式 evade，与开局的不可达假设分开看。
- 状态每秒采样，不能排除亚秒级瞬态；cast hook 的 miss 是该时点快照，不覆盖所有延迟命中阶段。

## 两条独立遗留问题

### 主坦持续攻击

主坦 GUID 656/666/676/686 的伤害都只在开局几秒，成功击杀也未恢复。run59 boss 战斗 victim 采样共197个，其中194个指向防骑694，3个指向猎人691；不能再称“坦克从未建仇”。

下一步优先核对主坦 current target、实际策略、动作执行及主坦角色识别。源码 `LoathebGenericMultiplier` 会屏蔽 TankAssist/DpsAssist 等动作；Loatheb 站位/选目标优先级高，且选孢子不分角色。它们是需要观测的交互，不是已证实根因。MovementAction::MoveTo 有重复移动等早退，不能仅凭优先级断言动作饥饿。

### 死亡、离场与 timeout

run56/57 末尾角色均在地图571，已经离开NAXX533，仍记录为timeout。run58也可见死者离场、幸存者留在533直至击杀。

Observer 仅按当前 isDead 判断 allDead，ResolveBoss 使用 bots[0] 当前地图。必须核对复活/释放/离场过程如何影响判定；不能简单以“每人死过一次”判wipe，因为实际可能复活。run55完整事件流到299998ms，duration_ms=300008；时钟两倍差异已排除。

## 证据文件与复算

本地大文件由 .gitignore 排除：`events-run56-run59.tsv`、`worldserver-run56-run59.log`、`build-run56.log`。查询数据库仅用SELECT，实验通过服务器控制台运行。

运行 `python3 docs/investigations/run55/audit_observers.py` 复算伤害、间隔、状态、取消与死亡证据。一次性顺序运行脚本 `validate_runs.py` 已完成；它带 run56 前置检查，不应直接重跑。

run55 不可达假设保留为未证实。若后续再次出现空窗，应优先保全同时间段新字段；当前不应为尚未复现的路径盲改核心逻辑。
