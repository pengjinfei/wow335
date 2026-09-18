# 英雄古达克 · 莫拉比 Moorabi（29305）

## 接手摘要

- 更新：2026-09-18（晚）。状态：**前置拉怪缺陷已定位并修复**，run664 在完整遭遇战口径下
  **5/5 零死亡击杀**（160.7–242.5 秒）；仍需一轮独立复现。
- 本轮修的是**框架自己的缺陷**，不是 boss 策略：`mod-raidtest` 的 `AttemptRunner` 在普通前置接近时
  只让坦克探路、其余人留在准备点并压制其 `attack tagged`，把清怪变成了坦克单挑（run659/661 的 3 死与 200 秒超时）。
  boss 阶段那个 `CanNotReachTarget`（run640 seq4）本轮未复现，**仍未归因**，与本修复是两件事。
- 已完成：地形勘测、场景、只读进战探针、原站位 3 刀作废（run632–634）、北侧无控清怪两刀
  （run635、run639）及控制链接入的门禁时序两刀（run636–637，均已回退）。
- 当前前置基线：`(1772,875,124.44)`，不启用额外控场策略。
- ⚠ 环境坑：`scripts/restart_world.sh` 用 `tail` 当 FIFO 读端，**块缓冲会把命令永远吞掉**；
  本轮三次 `raidtest run` 因此没进控制台。改用 `python3 -u /tmp/fifo_relay.py`（`O_RDWR` 自持写端 + 逐行 flush）后正常。
  重启用 `scripts/restart_world.sh <logname>`；开跑前清 `account_instance_times`。

## 结构性约束（先看这个，别急着换坐标）

`raidtest los` 第二遍（**每个点用自己实测的地面高度当 z1**）扫莫拉比房间 140 个点：

- 对 boss `los=true` 的点**恰好只有他那块平台本身**（x 1755–1785 / y 800–825，z=129.22）；
- 平台上任何点距 boss **≤16 码**，进不了「>22 码仇恨半径」这一关（英雄莫拉比 30530，82 级 → 22 码）；
- **22–30 码带内可见点：零个**（30 码是制裁之手的射程上限）。
- 北面走廊（y 830–845，地面 z≈123.2–124.5）距 boss 22–36 码，但**全部 `los=false`**——下坡的坎挡住。

⚠ 第一遍我用统一 `z1=129.3` 扫，得出「北走廊对 boss 全部可见」，**是错的**：探针从 `z1+2` 量，
而走廊地面是 123.4，等于站在 8 码高空看。这条是 LESSONS 里已有的坑，本轮又踩一次。

结论：**莫拉比结构上必须走「前置清怪 → 恢复 → 传送到开怪点」这条路**
（`AttemptRunner` 只有走完这条路才会把队伍送到 `EngagePoint`），没有「隔离档直接开怪」这个退路。

## 场景与已证实的进战原因

原准备点是 `(1772,838,123.40)`，在前置怪与 boss 之间；开怪点 `(1772.5,818,129.22)` 距 boss 8.5 码、
`los=true`。前置五只如下：

| guid | 名称 | 坐标 | 距准备点 | 距 boss |
|---|---|---|---|---|
| 127067 | Drakkari Earthshaker | (1772.8,848.7) | 10.7 | 39.6 |
| 127113 | Drakkari Inciter（编队队长） | (1777.8,850.6) | 13.9 | 41.8 |
| 127068 | Drakkari Earthshaker | (1772.7,852.8) | 14.8 | 43.7 |
| 127062 | Drakkari Fire Weaver | (1797.7,847.0) | 27.2 | 45.1 |
| 127051 | Drakkari Lancer | (1797.6,856.0) | 31.3 | 52.8 |

（带上 127062/127051 是因为 127062 距编队队长 127113 只有 20.2 码 < 英雄小怪 21 码仇恨半径，必然被卷进来。）

## 2026-09-18：前置拉怪缺陷定位与修复（run659/661 → run662–664）

交接文档留下的开放问题（「spawn 从未重载」还是「已重载但队伍无法再拉怪」）**两个选项都不成立**。
run661 的 25 秒 spawnId 重绑等待根本没被触发（没有 spawn 消失）；真正原因是上一轮那两处未提交改动
**自身的暴露面**。

### 根因（run661 日志逐行）

`AttemptRunner::ApproachPrerequisiteTarget` 在普通（无 CC 门禁）前置接近时：

- 只让 `ctx.bots.front()`（leader = 坦克）沿路径探路，其余 4 人留在准备点；
- 同时调 `CombatTrigger::HoldFollowerAttackTagged` 压制他们的 `attack tagged`。

run661 实测：

| 时刻 | 事件 |
|---|---|
| 33.5–39.6s | 三次 `prerequisite approach`，目标都是东侧**上层平台**的 127062 Fire Weaver（z=129.29）；坦克被单放到下层走廊 `(1787,841,124.4)`→`(1793,857,124.4)`，全部 `los=false` |
| 同时 | `HoldFollowerAttackTagged: held 4 follower bot(s)`；4 人全程 `combat=false target=none` 钉在 `(1772,877)` |
| 39.6s | `BeginPullForAll` 只有 leader 成功，4 个跟随者 `could not initiate attack ... continuing`——**框架仍把这次拉怪记为已发出** |
| 81.7s | 坦克单人在 `(1803.96,856.80,129.20)` 被 29819 Lancer 打死 |
| 200.003s | `prerequisite_failed: clearing timeout`（坦克 1 死，`boss_hp_min=100`） |

run659 的 3 死同一路径。也就是说：**跟随者既没被拉怪指令带上，又因被压制而不能自行接战**，
坦克一死清怪就永久停摆。

### 修复（mod-raidtest `AttemptRunner`，未提交）

1. 落点改由 leader 的可走路径决定、**全队共用**；删掉 `HoldFollowerAttackTagged` 压制。
2. `BeginPullForAll` 之后**校验每个活着的 bot 都真的拿到这次拉怪目标**（`current target` 或 `victim`），
   不足就按接近流程重试。这正是 run661 里缺的那道门。
3. 共同落点用路径上**第一个**可见点（能开怪的最短走法）。用最后一个可见点（≈怪脚下）会把全队
   多拖一段路：run663 seq3 就是这样被拖到平台西侧、把**不在前置表里**的西侧那组
   （127047/127059/127065，编队队长 127059）卷进来，3 死超时。

### 实测

| run | 形态 | 结果 |
|---|---|---|
| 662 | 共同落点 = 最后一个可见点 | 1/1 kill，261.516s 零死亡 |
| 663 | 同上 | 2/5：seq1 kill 166.732s、seq2 kill 149.097s（均零死亡）；seq3 被卷入西侧那组 3 死超时；seq4 `prerequisite spawn 127062 stayed absent for 25003ms`；seq5 前置减员 |
| 664 | 共同落点 = **第一个**可见点 | **5/5 kill 零死亡**：160.700 / 201.156 / 213.071 / 242.489 / 216.814 秒 |

run664 细节：每场前置清怪 53.160–74.637 秒（run661 是 200 秒超时）；`prerequisite pull engaged only`
只出现 1 次（3/5），下一 tick 就补齐并正常推进；五场的 boss 击杀均为零死亡。

⚠ 口径：完整遭遇战（五个前置 spawn 一个不删）、Heroic / normal5-v1 / `BotCheats=""` / `gear_profile=none`。
run664 的 Wilson 95% CI = 56.6–100%，**单轮 5/5 还不能宣称稳定**，下一步是独立复现一轮 5 场。

## 尝试记录

### 2026-09-17–18：探针定位、北侧清怪与复验（run632–640、641–646、653）

`AttemptRunner` 加了只读记录：boss 刚进战时的 threat table、每个成员的距离/LOS，以及**首次**同时满足
`distance <= GetAggroRange` 和 LOS 的成员。它不改变移动、目标或仇恨。

| run | 站位 / 形态 | 结果 | 关键证据 |
|---|---|---|---|
| 632–634 | 原点 `(1772,838)` | 作废，2.8–7.0s boss 进战 | run634：萨满在打 Earthshaker 时 `dist=20.09`、`aggro=22`、有 LOS；随后 BossAI 的 `DoZoneInCombat` 把全队以 0 threat 加入表。|
| 635 | 小怪北侧 `(1772,858)`，无控 | 五只前置 66.1s 全清，boss 未进战；恢复前盗贼死亡，作废 | 38.8s 盗贼同时受到 Fire Weaver 4,290 与 Lancer 4,817 伤害，说明无控的多怪分散仇恨。|
| 636 | 同站位，接入既有 CC 门禁 | 无效，手动停止 | 起点距 Earthshaker 仅 9.4 码，0.376s 自然进战，`cc_pull_gate: reason=pack_engaged icons=0`；控制窗口尚未来得及工作。|
| 637 | `(1772,875)`，既有 CC 门禁 | 无效，手动停止 | 5s 已有 2 个控制图标、尚未自然进战；7.9s 仍 `landed=0` 后首组进战。第二组从当前点对 Fire Weaver 无 LOS，反复 `no_plan`，未形成可复现流程。接入已回退。|
| 639 | `(1772,875)`，**无额外 CC** | **有效：击杀、零死亡** | 五只前置 61.745s 完成，未触发 boss 提前进战；恢复后 6.028s、在 67.773s 开 boss；attempt 145.195s 结束，`kill / deaths=0 / boss_hp_min=0`。|
| 640 seq 1 | 同上 | **击杀、零死亡** | 五只前置 60.019s 完成；attempt 112.156s，`kill / deaths=0 / boss_hp_min=0`。|
| 640 seq 2 | 同上 | **aborted，不能计击杀** | 五只前置完成；46.192s 萨满被 Lancer（77）两次伤害 2,858 + 2,866 击杀。boss 最低 0%，但 180.047s 时脱战/复位，`boss lost combat state (stuck/reset)`。|
| 640 seq 3 | 同上 | **击杀、零死亡** | 五只前置 58.647s 完成；attempt 134.704s，`kill / deaths=0 / boss_hp_min=0`。|
| 640 seq 4 | 同上 | **timeout，不能计击杀** | 五只前置 54.719s 完成且无死亡；战至 30% 后，116.054s `unreachable=true, evading_attacks=true`，坦克仍与 boss 距离 0；121.054s 开始回血，最终 1,237.141s 超时。|
| 641 | 同上，新增只读 probe | **击杀、零死亡** | 189.170s。129.525s 捕获 `CanNotReachTarget`；同 tick 可达性=true、无 transport/液体/跌落、fresh mmap route 为 `PATHFIND_NORMAL`。|
| 642 | 同上，新增只读 probe | **击杀，1 死亡** | 237.655s；前置阶段萨满短暂阵亡后复活。175.109s 捕获同样的短暂 `CanNotReachTarget`，probe 仍显示可达且路径正常。|
| 643 | 同上，新增只读 probe | **击杀、零死亡** | 152.312s。122.760s 捕获同样的短暂 `CanNotReachTarget`，probe 仍显示可达且路径正常。|
| 644 | 同上，新增只读 probe | **击杀、零死亡** | 156.377s。143.828s 第四次捕获同样的短暂 `CanNotReachTarget`，probe 仍显示可达且路径正常。|
| 645 | 同上，临时 core 分支日志 | **前置 abort，不计 boss 样本** | 56.618s；Fire Weaver 实体未记录死亡即消失，`prerequisite_invalid`，从未进入 boss。临时日志因启动后才调级而未输出；源码已移除。|
| 646 | 同上，临时 core 分支日志 | **击杀、零死亡** | 150.589s。启动后、排队前已执行 `server set loglevel 1 movement.chase 3`；未见 `chase_path_failed` / `chase_target_inaccessible`，数据库也无 `moorabi_unreachable_probe`。日志接线正常但没有复现目标现象；源码随即移除并重编译。|
| 653 | 同上，临时 core 分支日志 | **击杀、零死亡** | 221.834s；启动后、排队前已启用 `movement.chase`。无 `Moorabi chase path failed` / `Moorabi chase target inaccessible`，未复现 `CanNotReachTarget`。日志随即移除并重编译。|
| 654 seq 1 | 同上，四连验证 | **击杀、零死亡** | 245.629s。|
| 654 seq 2 | 同上，四连验证 | **击杀，1 死亡** | 205.824s；前置阶段 `Raidteenfivc` 阵亡，恢复后击杀。|
| 654 seq 3 | 同上，四连验证 | **前置 wipe，不计 boss 样本** | 65.519s；五人清怪阶段全部阵亡，`prerequisite_failed: roster wiped during clearing`。|
| 654 seq 4 | 同上，四连验证 | **前置 abort，不计 boss 样本** | 69.927s；一名跟随者未进战，`pull failed (not all followers entered combat)`，未进入 boss。|
| 656 | 同上，修复回归 | **击杀、零死亡** | 175.944s。前置接近改为各 bot 路径中最后一个有 LOS 的地面点；boss assist 改为每秒重试、最多 8 秒。此前的前置团灭与拉起 abort 均未重现。|

所以原先的零威胁首项不是“谁对 boss 造成仇恨”的答案，而是 boss 已经被普通 proximity aggro 触发后，
`BossAI::DoZoneInCombat()` 的后果。唯一满足原生 `CanStartAttack` 条件的首个成员是萨满；问题是队伍在
小怪与 boss 之间清怪，常规施法走位向 boss 侧越过了 22 码边界。

北侧 `(1772,858)` 已证明方向正确（清怪时成员在 y≈857–877，boss 未进战），但它仍在首怪仇恨圈内。
`(1772,875)` 距首怪约 26 码、距 boss 约 65 码；run639–644、646 与 653 曾连续通过前置并取得九刀 boss 击杀（八刀零死亡），
但 run654 的四连验证出现一次前置五人团灭和一次拉起门禁 abort，故完整链路不能再称为稳定。
直接复用单包控制链仍因两组怪的视线切换失败，且已回退；不应在目前的成功基线上重新引入它。

但这不是稳定 boss 基线：5 刀中的另两刀都在 boss 阶段失去可验证终态。seq 2 的前置减员后出现 0% 脱战复位；
seq 4 则明确记录到 boss 对主坦 `unreachable=true` 与 `evading_attacks=true`，随后回满/回血。后者发生时
坦克 `boss_dist=0`、仍在 melee range，故不是简单的队伍离开战斗范围或输出不足。先追可达性/寻路状态，再谈策略。

源码核对已把 seq 4 的字段落到核心的 `TargetedMovementGenerator`：它会因目标不可访问**或**路径构建失败调用
`SetCannotReachTarget(tank)`，而该调用立即启动 evade 计时。莫拉比没有覆盖 `OnTeleportUnreacheablePlayer`，所以
计时到期只能走通用 boss 处理，继而出现回血/重置。run641–644 的 harness probe 证明这个标志本身也可能短暂出现：
四次触发时，boss/坦克相距约 1.72–1.75 码、`accessible=true`、无 transport/液体/跌落、fresh 路径均为
`PATHFIND_NORMAL`，并且都正常击杀。因此 seq 4 不能再直接归因为 navmesh。run645 的临时 core 分支日志未在启动前启用
分类且该刀前置 abort；run646 则在排队前正确启用、完成零死亡击杀，但未出现不可达 probe 或任一分支日志。
所以日志接线已经核验、分支归因仍缺失：只有复现 `CanNotReachTarget` / 超时的样本才有证据价值；临时源码已移除。

**run 579**（5 场，全部作废）：

| seq | 结果 | 作废时刻 | 证据 |
|---|---|---|---|
| 1 | aborted | 3.0s | `preclear_boss_invalid:alive=true combat=true pos=1772.47,809.54,129.30` |
| 2 | aborted | 7.9s | 同上 |
| 3 | aborted | 9.8s | 同上 |
| 4 | aborted | 10.0s | 同上 |
| 5 | aborted | 7.4s | 同上 |

五场**一模一样**：莫拉比**停在出生点没动**，但 `IsInCombat()` 为真，并且同一毫秒放了
`55163 Mojo Frenzy`——那条只在 `JustEngagedWith` 里放，所以他是**真的被拉进了战斗**，不是状态残留。

### 已排除

- **不是位置漂移**：五场里 bot 的施法落点（萨满图腾、骑士奉献、盗贼刀扇、法师暴风雪）
  全部在 y 835–847，没有任何人往南走到 boss 的 22 码内。
- **不是击退**：地震者的 `Slam Ground 55563` 命中后队伍落点没有南移。
- **不是呼救半径**：`CreatureFamilyAssistanceRadius = 10`、`CreatureFamilyFleeAssistanceRadius = 30`，
  最近的前置怪离 boss 39.6 码，够不着。
- **不是编队**：`creature_formations` 里莫拉比不在任何队里（队长是 127113）。
- **不是 SmartAI**：29829/29874 及其英雄模板 30926/30931 的 `smart_scripts` 只有 Strike/Head Crack/
  Powerful Blow/Slam Ground，没有任何 zone-combat 动作。

### 只解释了一场

**seq 2**：法师(799) 在 7590ms 放 `1953 闪现`，落点 **(1770.55, 818.65, 129.22)**——
直接跳到莫拉比平台上、离 boss **9.2 码**；299 毫秒后 boss 进战斗。
其余四场**没有任何位移技能**（全 run 只有这一次 1953），**原因未定位**。

### 下一步（按序）

1. **独立复现一轮 5 场**（`raidtest run heroic-gd-moorabi-n5 --attempts 5`，先清
   `account_instance_times`）。run664 的 5/5 需要第二个独立样本才能写进台账结论。
2. **boss 阶段 `CanNotReachTarget`（run640 seq4）仍未归因**，与本轮的前置缺陷是两件事。
   只在复现该异常的样本上重新接临时日志：启动后、**排队前**执行
   `server set loglevel 1 movement.chase 3`，在 `TargetedMovementGenerator` 的 accessibility 与
   path-failure 分支分别记录源/目标状态与 path type。每次结束立即撤回并重编译。
3. 暂不改装备、难度、cheat 或通用控场策略。

## 交接

场景已注册，当前基线是北侧 `(1772,875,124.44)`；复跑：`raidtest run heroic-gd-moorabi-n5 --attempts 1`。
当前 boss 证据为 **run639–654 的 12 击杀 / 1 aborted / 1 timeout（14 个 boss 样本）**
加上 **run662–664 的 8 场击杀 / 0 aborted / 0 timeout**（run663 seq3–5 与 run659/661/645 前置作废不计）。
run664 在「共同落点 = 第一个可见点」修复后完整链路 5/5 零死亡，但单轮回归不足以声称稳定。

### 环境坑（本轮新踩）

`scripts/restart_world.sh` 用 `tail -n 0 -f /tmp/ac_world_fifo | worldserver` 作 FIFO 读端，
**`tail` 写管道时是块缓冲（16KB）**，`raidtest run` 这类短命令会永远停在缓冲区里——本会话三次
发命令都没进控制台（日志无任何 `Orchestrator` 行，数据库也无新 run），一度误判为「启动期吞命令」。
改用 `python3 -u /tmp/fifo_relay.py`（`O_RDWR` 自持写端 + 逐行 flush）后一次即通。
注意：不能用 `perl -e '$|=1; while(<STDIN>){print}'`——它在写端关闭时收到 EOF 就退出。

2026-09-18 run659：队长单独探路、跟随者待命的修复已编译并加载；首轮在前置阶段 86.901 秒出现 3 死，随后一个未记录死亡的前置 spawn 消失，按完整遭遇战不变量作废（`boss_hp_min=100`）。停止余下轮次；它不是 boss 样本，也尚不能宣称前置稳定。

2026-09-18 run661（修复已重启加载）：旧 GUID 消失后不再立刻以“spawn disappeared without a recorded death”作废，证明 25 秒的 spawnId 重绑等待实际生效；但前置战斗未恢复，200.003 秒后以 `prerequisite_failed: clearing timeout` 结束（坦克 1 死、`boss_hp_min=100`）。因此该修复只消除了错误终态，**没有证明前置清怪稳定**。
