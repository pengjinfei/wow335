# run59 双坦战斗日志分析（2026-09-06）

> 最新验收：[LIFECYCLE-FIX.md](LIFECYCLE-FIX.md)。run67重启后原角色、原实例连续两次零死亡击杀；DK显式主坦、首次传送、击杀后恢复三项通过。下文历史状态保留供审计。

> 接手新进展：见 [TAKEOVER-VALIDATION.md](TAKEOVER-VALIDATION.md)。已定位建团漏注册并修复；run63/65血DK均恢复全场持续攻击并击杀；run65防骑死亡后由DK承伤完成击杀。原run59分析保留历史口径。

数据源：本目录 events-run56-run59.tsv；技能名从本机 data/world/dbc/Spell.dbc 读取（DBCStructure.h 的136–151字段）。本次只分析，没有新增战斗或修改行为代码。

## 核心结论

run59 实际由防骑694承伤并建立持续输出，蓝图主坦血DK686基本缺席boss攻击。血DK不是持续施法后被抵抗：全场对boss106的spell事件为0，只有开局3次damage共846；也没有自己的cast_cancel事件。它仍能移动，159秒后可对非boss目标施放职业技能，因此不能概括为整个AI完全停止。

## 定量比较

| run59指标 | 血DK686 | 防骑694 |
|---|---:|---:|
| 对boss伤害 | 846 | 773649 |
| 对boss damage事件数 | 3 | 741 |
| 对boss显式目标spell事件 | 0 | 持续存在 |
| boss战斗victim采样 | 0 | 194/197 |
| 来自boss的damage合计 | 25440 | 199781 |
| 自身cast_cancel | 0 | 0 |
| 在固定坦克站位的采样数 | 182/197 | 189/197 |

boss其余3个victim采样指向猎人691。伤害为事件hook值，含机制伤害，不等于普攻次数或精确净血损。事件没有damage的真实spell_id，不能将全部boss伤害当普攻。

全队对boss伤害事件合计6693699，防骑约11.56%，血DK约0.013%。防骑按198.304秒折算约3901伤害/秒，血DK约4.27。

## 时间线

- 0.743 / 1.502 / 2.244秒：血DK分别造成378/270/198；此后再无对boss伤害。
- 2.509秒：防骑施放25780 Righteous Fury（正义之怒）。
- 3.104秒：防骑对boss施放62124/67485 Hand of Reckoning（清算之手相关事件）。两条spell不应当成两次独立按键。
- 4.011秒：首个victim=694采样；此后全部战斗victim采样保持694。4.463秒防骑承受3733伤害，5.718秒6988。
- 约9–10秒：防骑/血DK到达同一坦克点(2877.57,-3967.00,273.63)。boss随后稳定在(2881.26,-3969.82,273.63)，2D中心距约4.644码。
- 10–158秒：血DK几乎固定站位，没有可见主动职业攻击；防骑稳定输出。
- 159.068秒：血DK首次记录到48263/61261 Frost Presence。
- 159.655秒：对非boss目标917施放56222 Dark Command；160.240秒对917施放49909 Icy Touch、55095 Frost Fever，并有1393伤害。
- 192.398秒：Horn of Winter；192.980秒对非boss922 Dark Command；197.657秒对922 Death Coil。
- 198.293秒：Loatheb死亡；队员无死亡事件。

917/922很可能是孢子，与选目标策略相符，但当前导出没有它们的actor_entry映射，故本记录只确认为“非boss目标”，不将孢子身份写成事实。

## 纠正“血DK全程刷buff”的说法

159秒前，source=686的spell事件实际只有以下几类：

- 57723 Exhaustion：英勇/嗜血后的疲惫类效果。
- 55594 Deathbloom：死亡之花，boss机制相关；不是智力、命令怒吼或主动buff。
- 41637 / 48111 / 33110 Prayer of Mending：愈合祷言触发/弹跳相关。

这些事件由该单位作为caster触发，并不说明bot AI主动选择了相应技能。记录中“有spell”不能推出“职业输出循环在运行”。

## 防骑确实在正常执行职业循环

全场可见：正义盾击61411共26次、正义之锤53595共22次、智慧审判53408共16次、奉献48819共21次、神圣之盾48952共15次，另有圣印/装备触发。0–15秒造成20574伤害；之后每15秒段持续约4.1万–7.8万，没有长输出中断。

血DK只受到周期性小额机制伤害和后期团伤，不能因总承伤25440说它在主坦。位置相同且防骑能持续攻击，削弱了“此位置让所有坦克都打不到boss”的解释，但没有朝向、实际武器范围和cast check失败日志，尚不能完全排除血DK自身的范围/朝向条件。

## 与run56–58对照

| run | 主坦对boss次数/伤害 | 防骑对boss伤害 | 防骑死亡时间 | 结果 |
|---|---|---:|---|---|
| 56 | 5 / 1384 | 267585 | 83.426秒 | timeout、47% |
| 57 | 3 / 744 | 216925 | 78.696秒 | timeout、54% |
| 58 | 5 / 1531 | 540365 | 161.003秒 | kill、6死亡 |
| 59 | 3 / 846 | 773649 | 未死亡 | kill、0死亡 |

成功与防骑存活更久、稳定承伤相吻合；这只是相关性，日志未采集治疗量、实时血量、完整装备快照，尚不能解释防骑生存差异的因果。血DK的缺失跨四场持续存在，没有随着DPS恢复或击杀而消失。

## 源码支持的调查方向（均未被日志定案）

1. **主坦身份与共享仇恨语义**：RosterLogin::FormGroup只建团、指定leader、加成员，没有设置MEMBER_FLAG_MAINTANK。PlayerbotAI::IsExplicitMainTank只认该旗标；GetMainTankGuid无旗标则按成员遍历找第一个存活坦克。HasAggroValue对非显式主坦允许“另一个坦克被攻击”也返回true。因此站到mainTankPos不代表自身拿到boss仇恨。需运行时核对flag、IsMainTank、IsExplicitMainTank，不能只看蓝图注释。
2. **current target与真实攻击状态可能脱节**：LoathebChooseTargetAction.cpp:56只要current target已经等于目标就早退，不检查Unit::GetVictim或MELEE_ATTACKING；通用AttackAction::Attack则会同时检查目标、combat引擎和攻击模式。若曾停止攻击而缓存目标未清，专项选目标动作可能不负责修复。但当前日志没有上述内部状态，未证实发生。
3. **选目标与策略交互**：Loatheb选择1码内孢子不分角色；LoathebGenericMultiplier将TankAssist/DpsAssist等动作权重归零；站位和选目标同为高优先级。必须观测具体动作，不能只凭优先级断言站位动作饿死输出，MoveTo有重复移动等早退。
4. **leader特有开怪上下文**：框架仅给leader设置pull target，确认开战即清除leader的pull target与prioritized targets；其他bot没有同样的设置/清理过程。血DK同时是leader，这条差异需要检查，但目前没有证据证明清理直接导致停攻。

最有价值的后续观测是开局0–15秒和159秒附近：血DK的currentEngine、current target GUID、Unit::GetVictim GUID、MELEE_ATTACKING、实际策略集、主坦旗标、正在执行动作及失败原因。优先找“2.244秒最后一次boss伤害之后状态发生了什么”。现有日志足以定位行为缺失阶段，不足以唯一定位引擎代码根因。
