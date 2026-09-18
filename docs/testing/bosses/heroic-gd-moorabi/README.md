# 英雄古达克 · 莫拉比 Moorabi（29305）

## 接手摘要

- 更新：2026-09-17。状态：北侧准备点已在 **10 个 boss 样本**中都到达 boss 且未触发 boss proximity aggro；
  但 boss 终态是 **8 击杀 / 1 aborted / 1 timeout**，尚不能判为稳定通关。
- 已完成：地形勘测、场景、只读进战探针、原站位 3 刀作废（run632–634）、北侧无控清怪两刀
  （run635、run639）及控制链接入的门禁时序两刀（run636–637，均已回退）。
- 当前前置基线：`(1772,875,124.44)`，不启用额外控场策略。run639–644 与 run646 的十刀都越过前置与恢复；
  八刀击杀（七刀零死亡），但两刀在 boss 阶段异常，不能宣称稳定。
- run646 已在排队前启用临时 `movement.chase` 分类，结果为 150.589 秒零死亡击杀；既未触发
  `moorabi_unreachable_probe`，也没有两条 core 分支日志。临时日志已经移除并重编译，故这只是验证接线，
  不是 seq 4 的归因。下一步只应在复现异常的样本上重新接入该日志；不要改装备、难度、cheat 或通用控场策略。

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

## 尝试记录

### 2026-09-17：探针定位、北侧清怪与复验（run632–640）

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

所以原先的零威胁首项不是“谁对 boss 造成仇恨”的答案，而是 boss 已经被普通 proximity aggro 触发后，
`BossAI::DoZoneInCombat()` 的后果。唯一满足原生 `CanStartAttack` 条件的首个成员是萨满；问题是队伍在
小怪与 boss 之间清怪，常规施法走位向 boss 侧越过了 22 码边界。

北侧 `(1772,858)` 已证明方向正确（清怪时成员在 y≈857–877，boss 未进战），但它仍在首怪仇恨圈内。
`(1772,875)` 距首怪约 26 码、距 boss 约 65 码；run639–644 与 run646 证明它无额外控场能稳定走通前置与恢复，
并已取得八刀 boss 击杀（七刀零死亡）。
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

1. 只有开始下一轮复现时才重新补临时日志；启动后、**排队前**执行 `server set loglevel 1 movement.chase 3`，在 `TargetedMovementGenerator` 的 accessibility 与 path-failure 分支分别记录源/目标状态与 path type。每次结束立即撤回并重编译。
2. 单独复现 seq 4 的 boss 阶段异常；只有拿到 `CanNotReachTarget` / 超时样本中的置标分支，才能判断是 core 路径、地形、还是 bot 拉位。run646 的成功无事件样本不改变这一结论。
3. 暂不改装备、难度、cheat 或通用控场策略；北侧已经稳定解决前置 proximity aggro，这些不是当前异常的候选解。

## 交接

场景已注册，当前基线是北侧 `(1772,875,124.44)`；复跑：`raidtest run heroic-gd-moorabi-n5 --attempts 1`。
现有证据为 **8 击杀 / 1 aborted / 1 timeout**（10 个 boss 样本，run645 前置作废不计）；北侧前置可靠，但 boss 战仍需先定位 `CanNotReachTarget` 的置标分支。
