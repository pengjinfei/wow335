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
