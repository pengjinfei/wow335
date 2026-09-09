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

### 2026-09-09 全本行走路线实测 + 目标与范围修正

#### 路线：三段全部是完整地面路线

新建了一个只用于采集的探针场景（`NavigationOnly=true`，在夹具、前置怪和 boss 战之前结束），把队伍传送到段起点后对段终点做 mmap 路线预检。预检会把队长的完整路径打进日志，因此航点来自实测而非猜测。副本入口取自 `areatrigger_teleport` 4745：`(153.79,-86.55,12.55)`。

| 段 | 起点 → 终点 | 路线类型 | 首几个实测点 |
|---|---|---|---|
| 1 | 入口 `(153.79,-86.55,12.55)` → 凯雷塞斯准备点 `(221.0,225.0,40.9)` | **`type=1`** 完整 | 153.79,-86.55,12.55 → … → 195.13,-62.15,20.31 → 211.10,-62.89,24.68 → … |
| 2 | 凯雷塞斯开怪点 `(188.0,197.5,40.815)` → 斯卡瓦尔德准备点 `(81.50,-5.13,118.90)` | **`type=1`** 完整 | 188,197.5,40.81 → … → 172.78,230.13,42.86 → 153.04,254.85,42.87 → … |
| 3 | 斯卡瓦尔德准备点 `(81.50,-5.13,118.90)` → Ingvar 平台 `(245.60,-339.73,180.50)` | **`type=1`** 完整 | 81.5,-5.13,118.78 → … → **114.24,-28.11,119.03** → … → 153.44,-20.20,135.01 → … |

三段都是**单次查询**取得的完整路线，说明不需要中间航点即可行走；这也确认了此前提高 Detour 节点池（1,024→4,096）与 playerbots 路径容量（148→512）之后长路线容量足够。**「双向搜索」当年针对的正是被这两项容量修复关掉的 `DT_OUT_OF_NODES`/`DT_BUFFER_TOO_SMALL` 症状**（run166/run167），它仍是更长路线的可选优化，但不是当前阻塞。

第 3 段的第 11 个实测点 `114.24,-28.11,119.03` 就在斯卡瓦尔德房内，因此后段路线只能在前面 boss 清掉之后才能实走验证（run175 已记录过起点位于双 boss 近战范围）。三次探针中都有成员在行走途中被沿途小怪打死（第 1 段死在 `204.46,-62.77,23.55`），这属于「没有清怪就穿房」的预期结果，不是路线问题。

注：`NavigationOnly` 的探针在夹具阶段之前结束，因此不会复活/恢复角色，上一次探针留下的死亡会影响下一次的组队门禁；预检日志仍会正常产出。探针场景与其临时角色已删除。

#### 范围修正：推进与小怪机制属于 playerbots，不属于 raidtest

用户明确了目标优先级：**首要目标是真人 + 机器人打通 boss，次要目标是机器人带着真人打通整个副本**；raidtest 只是测试副本策略的工具。因此原先计划在 raidtest 里实现「全本 run 编排」的方向已停止——那只会服务测试台，不服务实际游戏。

核对上游现状：

- **每个 boss 的机制处理已有**：`src/Ai/Dungeon/` 下 20+ 个 WLK 副本各有策略，且 UK 的策略不引用 `GetMaster()`，所以 masterless 也能生效（这是本项目能验证的前提）。
- **进副本已有**：`LfgJoinAction` / `LfgAcceptAction` / `LfgRoleCheckAction` / `LfgTeleportAction`。
- **副本内推进没有**：`UnknownDungeonTrigger` 要求 `IsRealPlayer(botAI->GetMaster())`，上游设计是**跟着真人走**；`TravelMgr` 只有大世界目标且明确回避副本。所以「机器人带路」需要在 playerbots 里新做。
- **机制的实现位置**：一律按遭遇放在 `src/Ai/Dungeon/<副本>/`。通用层只有打断（且只针对敌方治疗），**没有通用解诅咒、没有通用 AoE 规避**；fixate 与炸弹类机制已有 `AN`、`TK`、`Mech` 的先例可参照。

#### UK 小怪机制清单（SmartAI 实测）

| 小怪 | entry | 需要机器人处理的机制 |
|---|---:|---|
| Dragonflayer Strategist | 23956 | **`54962`/`60227` Ticking Bomb / Ticking Time Bomb**（定时炸弹，需散开）、`42972` Blind、`59685` Hurl Dagger |
| Dragonflayer Runecaster | 23960 | **`42740`/`59616` Njord's Rune of Protection**（护盾，应打断）、**`54965`/`59617` Bolthorn's Rune of Flame**（地面火焰，需走出） |
| Dragonflayer Ironhelm | 23961 | `57846`/`59607` Heroic Strike、`42780`/`59606` Ringing Slap |
| Tunneling Ghoul | 24084 | `42702` Decrepify（诅咒，可解） |
| Proto-Drake Rider | 24849 | `59603` Throw、`59605` Piercing Jab、`59604` Wing Clip |
| Frenzied Geist | 28419 | **`40414` Fixate**（锁定单人追击） |

`Dragonflayer Strategist`/`Runecaster`/`Ironhelm` 位于 `x≈101–112, y≈38–59, z≈87.4`，**不在任何现有场景的前置列表里**——UK 还有未覆盖的小怪房间。

下一步按序：为 UK 小怪机制补 playerbots 触发器/动作，按致命度排序（Ticking Bomb 散开 → Rune of Flame 规避 → Runecaster 打断 → Fixate 处理 → Decrepify 解诅咒），每项用 raidtest 单独验证，与 boss 机制同一套流程。

### 2026-09-09 坦克改为联盟并重建四套 roster（attempt 1788426636–1788426642）

目标是让真人（盗贼 DPS）与 bot 同队验证首要目标。原 roster 的坦克是**血精灵圣骑士（部落）**，其余四人是联盟。

#### 为什么不改 AllowTwoSide

核心代码给出精确边界：

- `GroupHandler.cpp:119` / `Group.cpp:2178`：跨阵营**邀请与成员**需要 `AllowTwoSide.Interaction.Group`。
- `ChatHandler.cpp:231`：开 `Group` 后队伍/团队频道变 `LANG_UNIVERSAL`，指令能通且可读。
- `ChatHandler.cpp:428`：跨阵营**私聊**另需 `AllowTwoSide.Interaction.Chat`，否则 `SendWrongFactionNotice()`——而私聊正是指挥单个 bot 的方式。
- `IsTwoFactionInstance()` 只覆盖 540/576/631/632/649/650/658/668，**map 574 不在其中**，无副本侧特殊分支。

同时有一条已有证据说明**跨阵营治疗本就在工作**：所有 run 里矮人戒律牧都在给血精灵坦克治疗（run263 为 76 次、180,553 点），而当时 `Group = 0`。也就是说那两个开关只影响"玩家主动邀请"和"玩家聊天"。

即便如此，开两个开关等于把服务器改成跨阵营互通，是一处基线改动。**改坦克种族更小且不碰基线**，故采用后者。

#### 实施：force-recreate 是现成路径

`RosterManager.cpp:105` 的角色复用靠持久映射表 `raidtest_accounts`（scenario_key, slot）→ character_guid，**不按名字查**；`DeleteSlotMapping` 在 force-recreate 时删映射行**与角色本身**（账号保留、拒绝删在线角色），因此旧名字会被释放，此前"每槽位仅 6 个候选名已耗尽"的限制自动消失。命令为 `.raidtest run <scenario> --attempts 1 --force-recreate`（`RaidTestCommandScript.cpp:263`）。

改动仅两处：`mod-raidtest-roster-heroic5-disc-v1.conf` 的坦克 `Race = "bloodelf"` → `"dwarf"`（运行配置与模板同步），然后四套 UK 场景各 force-recreate 一次。注意该开关会重建**全部 5 个槽位**，所以四套的五人都按同一蓝图重建；只有坦克种族变化，其余同职业同天赋同装备。

重建结果（全部为矮人圣骑 + 矮人牧师 + 人类盗贼 + 人类法师 + 德莱尼萨满，**皆联盟**，各 18–19 件装备）：

| 场景 | 槽位 0–4 的 guid |
|---|---|
| heroic-uk-ingvar-disc | 751 / 752 / 753 / 754 / 755 |
| heroic-uk-keleseth | 756 / 757 / 758 / 759 / 760 |
| heroic-uk-skarvald-dalronn | 761 / 762 / 763 / 764 / 765 |
| heroic-uk-ingvar | 766 / 767 / 768 / 769 / 770 |

#### 换坦克后的验证

| attempt | 场景 | 结果 | 猛击次数 | effect-0 命中 | 坦克承伤 | 治疗输出 |
|---|---|---|---:|---:|---:|---:|
| 1788426636 | ingvar-disc | 击杀 113.9s / 1 死 | 8 | 0 | 62,031 | 142,557 |
| 1788426640 | ingvar-disc | 击杀 108.9s / 1 死 | 8 | 0 | 82,757 | 171,926 |
| 1788426641 | ingvar-disc | 击杀 96.9s / 2 死 | 7 | 2 | 44,742 | 110,732 |
| 1788426642 | ingvar-disc | 击杀 116.4s / 1 死 | 8 | 1 | 65,503 | 152,006 |

**4/4 击杀，且坦克在 31 次猛击中一次都没被 effect-0 选中**——闪避修复与种族无关，成立。三次 effect-0 命中全在非坦克身上，且都是已记录的残余项：盗贼在接触距离两次（`dist=0.00`，boundary 旁路）、法师一次（`dist=3.48`，即中心距约 3.87 码，远程脱离偶尔失守）。

必须如实标注差异：血精灵那套是 8/8、93.9–112.3 秒、4 场零死亡、56 次猛击仅 1 次 effect-0；矮人这套 4 场每场 1–2 死、坦克承伤 44.7k–82.8k（原 40.2k–59.0k）、治疗输出 110.7k–171.9k（原 68.2k–120.1k）。样本量 n=4 下不能断言两者等价，但"能稳定击杀"与"坦克闪避有效"两条都成立。

其余三套的附带结果：斯卡瓦尔德完整链路**击杀 108.6s / 0 死**；官方 ingvar 仍在骑手阶段失败（骑手平台无导航网格，既有阻塞）；凯雷塞斯出现一个**既有门禁的时间余量问题**——`prerequisite_failed: natural recovery timeout`，`recovery_wait` 显示法师血已满而法力仅 10,166/16,503 且仍以约 990/次恢复，120 秒预算刚好不够（新角色打完前置怪时法力更低）。这不是机制失败，后续可单独复测或调整该预算。
