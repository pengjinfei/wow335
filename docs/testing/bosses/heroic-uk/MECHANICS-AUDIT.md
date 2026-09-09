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
