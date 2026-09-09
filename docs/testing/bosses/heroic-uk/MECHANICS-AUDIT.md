# 乌特加德城堡 boss 机制完整性审计（2026-09-06）

目标：核对 map 574 三个 boss 的机制脚本是否完整、未被删减或削弱，与官方 WotLK 3.3.5 一致。背景：用户要求确认"boss 机制没删减、和官方服务器相同"。

## 结论

三个 boss 的 C++ 脚本均为 AzerothCore 上游标准实现，**本地 git 无改动**（`src/server/scripts/Northrend/UtgardeKeep/UtgardeKeep/` git status 干净；最近提交 `a8d75f59c`、`7b26de4e5` 均为上游官方修复）。boss/召唤物 creature 模板齐全，实例脚本三 encounter 状态完整。机制等同官方（假定 AzerothCore 忠实还原官方机制；本项目不在底层删减/削弱 boss）。

## 逐 boss 机制

| boss | entry | 机制 | 技能/实现 | 完整性 |
|---|---|---|---|---|
| 凯雷塞斯王子 | 23953 | 冰墓(随机玩家禁锢，英雄版周期伤害，需打破)、暗影箭、召唤 5 骷髅(装死+复活/Decrepify/英雄版骨甲) | Frost Tomb 42672/48400、Shadow Bolt 43667、Vrykul Skeleton 23970 | ✅ 完整 |
| 斯卡瓦德 & 达尔隆 | 24200/24201 | 双 boss 同战：冲锋、石击、英雄版狂暴；暗影箭、衰弱、英雄版召唤骷髅；**一方死亡→另一侧召唤幽灵(27390/27389)继续战，双杀才过关** | Charge 43651、Stone Strike 48583、Enrage 48193、Shadow Bolt 43649、Debilitate 43650、Summon Skeletons 52611、Ghost 27389/27390 | ✅ 完整 |
| 因格瓦尔 | 23954 | **双阶段**：P1 震慑咆哮/顺劈/猛击/狂暴 → 死亡后安希尔德(24068)降临复活 → 变形亡灵(23980) → P2 恐惧咆哮/痛苦打击/黑暗猛击/暗影斧(投掷回收) | Staggering Roar 42708、Cleave 42724、Smash 42669、Enrage 42705、Summon Valkyr 42912、Resurrection 42857/42862/42704、Transform 42796、Dreadful Roar 42729、Woe Strike 42730、Dark Smash 42723、Shadow Axe 42749 | ✅ 完整 |

## 验证方式

- 核心 git：`git status --short src/server/scripts/Northrend/UtgardeKeep/` 干净；最近提交为上游官方修复。
- creature_template 核验：boss/幽灵(27389/27390)/亡灵(23980)/安希尔德(24068)/冰墓(23965)/骷髅(23970) 全部存在且等级/血量正确。
- 实例脚本 `instance_utgarde_keep.cpp`：DATA_KELESETH / DATA_DALRONN_AND_SKARVALD / DATA_INGVAR 三 encounter 状态齐全。

## 运行时机制触发证据

隔离 boss 战实际触发（DB raidtest_events 核验）：

- **斯卡瓦德&达尔隆**（run94/96）：双 boss 均被击杀（达尔隆先死→幽灵参战→斯卡瓦德后死），冲锋/石击/暗影箭/衰弱/召唤骷髅均有事件。
- **因格瓦尔**（run95/97）：安希尔德复活序列完整运行——召唤瓦格里(42912) → 复活光束(42857) → 复活球(42862) → 复活治疗(42704) → 变形亡灵(42796) → P2 暗影斧(42749)。**机制未被删减，且正是它们在击杀 bots**（见 [因格瓦尔记录](heroic-uk-ingvar/README.md)）。

审计完成：机制完整，与官方一致。未做任何削弱。

## 2026-09-09 英雄 UK 三 boss 回归（attempt 1788426608–1788426615）

固定源码与二进制（管理库 `6f08b06`、core `516b14df1`、playerbots `c668995a`、raidtest `0069a0d`）、同一 roster `heroic5-disc-v1`、heroic、ilvl 200 上限、零 cheat。每个样本一次独立冷启动、单 attempt。

| Boss | 场景 | 样本 | 结果 | 对照基线 |
|---|---|---|---|---|
| 凯雷塞斯王子 | `heroic-uk-keleseth`（含 4 只前置怪清理） | run273 / run274 | **击杀 99.3s / 116.1s，均 0 死亡** | run86/91/92 零死亡击杀 |
| 斯卡瓦尔德 & 达隆 | `heroic-uk-skarvald-dalronn`（前置链无法启动，见下；以 run127 形态隔离 boss 战） | run279 / run280 | **击杀 51.5s / 49.0s，均 0 死亡** | run127 48.6s 零死亡 |
| 因格瓦尔 | `heroic-uk-ingvar-disc` | run265–run272 | **8/8 击杀，93.9–112.3s，4 场 0 死亡** | 改动前正式 2/3 |

三个 boss 均无回归。另外直接核对了策略隔离：凯雷塞斯与斯卡瓦尔德/达隆四个样本的 playerbots 日志中 `Ingvar diagnostic` 条目数均为 **0**——UK 策略虽整本注册了新增的 Ingvar 触发器，但它们都以 `find target "ingvar the plunderer"` 为门槛，不会在其它 boss 上误触发。

### 斯卡瓦尔德 & 达隆的前置清怪链从未启动过（既有缺口，非本轮回归）

`heroic-uk-skarvald-dalronn` 的前置清怪在第一个 tick 就被拒。逐层排除：

- run275：按配置顺序的首个目标 `125971`（24084 Tunneling Ghoul，`23.87,1.17,115.11`）距准备点 `(75,0,117)` **47.67 码、`los=false`** → `prerequisite_failed: initial pull rejected`。
- run276（探针，按世界库实测距离把最近的排到最前）：首个目标 `125967` 距离降到 **19.26 码**（reach 校正），`los` **仍为 false**。**所以顺序不是原因，准备点对整片小怪区没有视线。**
- run277/278（探针，仅停用前置链、保留准备点）：改为 `pull failed (boss not engaged)`——同一个准备点距 boss `(112,-33,118.9)` 也是约 51 码且无可用视线，**boss 拉怪同样失败**。
- run279/280（探针，前置链与准备点一并停用 = run127 形态）：2/2 零死亡击杀。

10 只前置怪的实测坐标范围为 x∈[23.87, 64.41]、y∈[-34.59, 35.59]、z≈115–119，全部位于准备点西侧。

来源已定位到具体提交：`c460d05`（mod-raidtest，2026-09-07 17:50）**同时**加入了 `PrerequisiteSpawns` 与 `PreparationX/Y/Z`，并把场景注释从「首次验证隔离 boss 战（无房间小怪清理）」改为「清理首领房的 4 名吞噬者与 2 组三名狂怒幽灵后开战」。而 run127 的零死亡击杀发生在同日 16:15，**早于该提交**。因此这个准备点自加入起就没有可用视线，该场景在 `c460d05` 之后没有产生过任何成功 run。

下一步（不要猜坐标）：该场景需要一个**实测**的集结点——`heroic-uk-ingvar` 已有 `PrerequisiteX/Y/Z` 这组键可以复用；或者由编排层在目标超出视线/射程时先带队走过去，而不是在第一个 tick 直接 abort（`AttemptRunner.cpp` 的 `preclear_target` 诊断每 15 秒记录距离与 LoS，说明原本就预期队伍会先接近）。

本轮三个探针均已还原：`env/dist/etc/modules/mod-raidtest-scenario-heroic-uk-skarvald-dalronn.conf` 与模板 `conf/*.dist` 逐行一致（已 diff 核对）。探针 attempt `1788426610`–`1788426613` 只用于定位，不计入任何通过率。

### 2026-09-09 斯卡瓦尔德&达隆前置链修复（attempt 1788426616–1788426625）

上节把该场景的前置链定位为「准备点无视线」。本节把根因测到具体数值并修好，全程用核心自己的诊断，不填猜测坐标。

#### 根因一：准备点不在可走地面上

用场景自带的 `NavigationWaypoints` + `NavigationOnly` 做零位移探针（终点 = 准备点本身）：

- run281（终点取真实物件 Cobalt Deposit `57.5,-10.3,118.8`）：`type=68` = `PATHFIND_FARFROMPOLY_START | PATHFIND_INCOMPLETE`，`tiles=true/true`、两端投影均非零、`find_path=0x40000000`（`DT_SUCCESS`，无 detail 位）、`component=connected`。**起点离可走多边形太远**，同时给出终点的真实地面 `actual_end=57.33,-10.67,119.88`。
- run282（零位移，终点 = `75,0,117`）：`type=10` = `PATHFIND_NOPATH | PATHFIND_SHORTCUT`，`actual_end=81.50,-5.13,118.90`。

即 **准备点 `(75,0,117)` 距最近可走多边形 8.3 码**，bot 被传送进几何体内部。这一条同时解释了：对最近前置怪（19.26 码）`los=false`、对 boss（约 51 码）`los=false`、前置拉怪与 boss 拉怪都被拒。

准备点改为核心 `findNearestPoly` 给出的实测投影 **`(81.50, -5.13, 118.90)`**。

#### 根因二：房间是 L 形的，没有任何单一坐标能看到全部前置目标

逐个探针（均为可回滚的运行配置探针，已全部还原）：

- run283（仅修准备点，前置顺序保持配置原样）：首个目标变成 54.59 码、`los=false`，仍被拒。
- run284（再按实测距离把最近的排到最前）：最近目标 24.90 码（reach 校正）、`los` **仍为 false**。
- run285（准备点改为小怪房内的实测 on-mesh 点 `57.33,-10.67,119.88`，距最近前置怪 6.4 码）：**前置链真正启动**，8.286 秒内清掉 4 只（55 条伤害、52 次施法、4 个死亡事件），随后下一个目标在 48.13 码外、`y≈39` 的北侧且无视线，再次被拒。

因此「配一个能看到所有目标的准备点」这个前提本身不成立。同时核对了场景注释的错误：那 10 只怪分布在 `x∈[23.9,64.4]`、`y∈[-34.6,35.6]` 的西侧房间，而双 boss 在 `x≈110`；**首领房 45 码内没有任何小怪**（只有 41 码外一只 Black Rat）。注释已订正。

#### 修复：编排层在目标超出视线时带队接近，而不是第一个 tick 直接 abort

`AttemptRunner::ApproachPrerequisiteTarget`：拉怪被拒时下达一次普通接近移动，并在后续 tick 重试；上限仍由既有的 `PrerequisiteTimeoutSeconds`（180 秒）兜住。它沿用导航段同样的**整队全或无路线预检**，区别是目标是活动生物而不是固定节点，所以只拒绝真正的直线穿墙（`NOPATH | NOT_USING_PATH | SHORTCUT | FARFROMPOLY`），并以「终点落在目标 5 码内」代替严格的节点到达判据。只在无人还在移动且距上次下达超过 1 秒时重新发令，避免每 tick 清运动状态造成抖动。战斗目标选择仍归 bot 自己，框架只给靶标和一次普通 `MovePoint`。

`AttemptRunner.cpp` 里原有的 `preclear_target` 每 15 秒记录距离与 LoS，说明作者本来就预期队伍会先接近；缺的只是这一步。

#### 结果

| attempt | run | 结果 | 时长 | deaths | 前置清理 |
|---|---|---|---:|---:|---|
| 1788426621 | 286 | 击杀 | 86.1s | 0 | `prerequisites_complete elapsed=35168ms`，10/10 |
| 1788426622 | 287 | 击杀 | 80.6s | 0 | 10/10 |
| 1788426623 | 288 | 击杀 | 90.1s | 0 | 10/10 |

run286 的日志可见接近步骤两次生效：`elapsed=4ms` 时对 54.59 码外的首个目标下达接近，21,776ms 时对下一个目标（17.79 码）再下达一次；12 个死亡事件 = 10 小怪 + 2 boss。配置里「最远优先」的顺序不再需要改动，因为队伍会走过去。

同一二进制上的回归：凯雷塞斯 run289 击杀 107.6s / 0 死亡，因格瓦尔 run290 击杀 117.0s / 0 死亡。共享编排改动无回归。

探针 attempt `1788426616`–`1788426620` 只用于定位，不计入通过率；运行配置已与模板逐行一致（含新准备点）。
