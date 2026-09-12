# 英雄艾卓-尼鲁布（Azjol-Nerub，map 601）夹具勘测

更新：2026-09-12。用户 2026-09-12 指定为第三个副本（原话「英雄安卡赫特（Azjol-Nerub）」，
中文名与英文名指向两个不同副本，已确认取 **Azjol-Nerub / map 601**，不是安卡赫特古代王国 map 619）。

装备档位仍是 [normal5-v1](../../fixtures/normal5-v1/README.md)，难度英雄，`BotCheats` 为空。
本轮按用户要求把**盗贼由战斗改刺杀**，见下面「本轮基线改动」。

## 副本与 boss

| boss | entry | 英雄 entry | 等级 | spawn guid | 坐标 | bot 策略 |
|---|---|---|---|---|---|---|
| 门卫克里克希尔 | 28684 | 31612 | 82 | 127214 | (529.6, 646.2, 777.4) | `wotlk-an` |
| 哈多诺克斯 | 28921 | 31611 | 82 | 127401 | (522.5, 544.9, 674.7) | 同上 |
| 阿努巴拉克 | 29120 | 31610 | 82 | 132273 | (551.0, 248.3, 224.0) | 同上 |

mod-playerbots 侧 `wotlk-an` 已有的东西（`Ai/Dungeon/AN/ANStrategy.cpp`）：克里克希尔的
「攻击蛛网茧」「守望者优先级」+ `KrikthirMultiplier`；阿努巴拉克的「躲践踏」。
哈多诺克斯没有任何针对性触发器（源码注释：核心那几个 trigger 对这个 boss 很不稳，默认策略看起来能打）。
阿努巴拉克的**穿刺**在源码里标了 TODO：没有 gameobject/触发器可追踪、瞬发无读条，现阶段只能靠治疗硬吃。

## 战斗区间（核心 `instance_azjol_nerub.cpp` 的 BossBoundaryData）

| boss | 区间 | 影响 |
|---|---|---|
| 克里克希尔 | `RectangleBoundary(400, 580, 623.5, 810)` | 整条走廊都算 |
| 哈多诺克斯 | `ZRangeBoundary(666, 776)` | **低于 z=666 她就 evade**，坑底还有更低的一层 |
| 阿努巴拉克 | `CircleBoundary((550.6, 253.6), 32)` | 半径 32 码的竞技场 |

## 仇恨半径（`Creature::GetAggroRange`，本机 `Rate.Creature.Aggro = 1`）

全部 boss/小怪 `creature_template.detection_range = 20`。80 级玩家：

- 对 82 级 boss（三个 boss 都是）：20 − (80 − 82) = **22 码**
- 对 81 级守望者/蛛网术士：**21 码**
- 对 80–81 级小怪：20–21 码

## 勘测结果（`raidtest los` 实测，非估算）

`raidtest los <map> <x1> <y1> <z1> <x2> <y2> <z2>` 是只读控制台命令，回 2D 距离、视线、
以及两端 `getHeight` 的 vmap 地面高度。**它只证明有地面，不证明在导航网格上**（见 START-HERE 1b）。

### 克里克希尔的门厅

沿 x=528 中线取地面：y 655→705 全在 **z 775.5–777.3** 的平地上，对 boss 视线全通；
y 715–730 在 x=528 处**没有地面**（`vmap_floor = -200000`），y≥735 是升起的入口坡道（788→797）。
y=680 横扫：x 505–545 地面 775.4–775.7，x=495/550 开始是墙或另一层 → 门厅宽度约 x∈[503, 548]。

- **准备点 (528, 690, 775.5)**：距 boss 43.8 码 ✓；距 9 只守望者组小怪 26.4–35.4 码，**全部 > 21 码**
  （传送进场不会立刻拉怪）；对 9 只**逐只探过，视线全为 true**。
- **开怪点 (529.6, 656, 776.8)**：boss 正北 9.8 码，地面 776.79，视线通。

### 哈多诺克斯的坑

坑是一个连续斜面：固定 x 时地面随 y 增大而降低，固定 y 时随 x 增大而升高。

- **准备点 (525, 520, 688.0)**：距 boss 2D 25.0 码、z 差 13.5 → 3D 28.4 码 > 22 ✓。
  相邻点 (515,520)=686.5 / (535,520)=690.3 / (525,515)=691.6 / (525,525)=684.6，平滑无洞。
- **开怪点 (525, 535, 678.1)**：2D 10.2 码，视线通。
- ⚠️ **别往 (505,550) / (515,560) 方向放**：地面骤降到 655.6 / 660.2，是通往下层
  （32593 Skittering Swarmer 所在，z 646–657）的落差。与魔枢萨满掉坑是同一类陷阱。

### 阿努巴拉克的竞技场

- **准备点 (551, 280, 224.33)**：距 boss 31.7 码 ✓，视线通；距区间圆心 26.4 码 < 32，仍在区间内。
  四周 (541..561, 275..285) 地面 223.4–226.0 全平；**x=535 那一列 y=275 已经没有地面**，别往西放。
- **开怪点 (551, 260, 224.31)**：11.7 码，视线通。
- 三扇房间门 192396/192397/192398 在 (550.4, 254.7, z≈211) 一带，`DOOR_TYPE_ROOM`，
  开怪后 5 秒（`EVENT_CLOSE_DOORS`）才关，准备点→开怪点不会被挡。

## 场景范围与口径

| 场景 | 前置 | 口径 |
|---|---|---|
| `heroic-an-krikthir-n5` | 守望者三组共 9 只（guid 12758–12766） | **完整遭遇战**。这 9 只是 boss 脚本的一部分，不是路怪：实例脚本把它们的 evade 与死亡都接到 boss（`OnCreatureEvade` → `krikthir->EnterEvadeMode`；`OnUnitDeath` → `ACTION_MINION_DIED` 触发补招），boss 又在第一只随从进战斗后 60s/120s 各派一批、英雄 **200 秒**时 `SetInCombatWithZone` 亲自下场。走廊更上方两组（127229/127235/127338 中段、127230/127339 巡逻）不在脚本里，按路怪处理、不纳入（与魔枢/UK 各场景同规）。 |
| `heroic-an-anubarak-n5` | 无 | **完整遭遇战**。他本来就没有前置小怪，战斗中的守卫/毒疗者/刺客/掷矛者全是他 75/50/25% 下潜时自己召的。走廊里两只 Anub'ar Prime Guard（132274/132275，y≈341）在 92 码外、不在 32 码区间内。 |
| `heroic-an-hadronox-n5` | 无 | **隔离形态，不能记正常规则通关**（同 `heroic-uk-ingvar-disc` 先例）。完整遭遇战的开场是打上层平台的粉碎者包（`npc_anub_ar_crusher::DoEngagedWith` → `ACTION_CRUSHER_ENGAGED` → `SetBossState(IN_PROGRESS)` → 召 2/3 号包 → 她按 45s/70s 分三段爬上平台织门）。这三个包是她 `Reset()` 时 `SummonCreatureGroup` 出来的**召唤物，spawnId = 0**，而 `PrerequisiteSpawns` 只接受数据库 spawn 的 guid（`AttemptRunner` 用 `map->GetCreatureBySpawnIdStore()` 查），**当前框架表达不了**。要做完整形态得先给框架加「按召唤 entry 的前置门禁」。 |

## 本轮基线改动：盗贼 战斗 → 刺杀（用户 2026-09-12 指定）

`mod-raidtest-roster-normal5-v1.conf` 的 `Roster.2`：

- `TalentSpec`：`rogue_combat` → `rogue_assassination`
- 雕文：`399,468,469,715,467,406` → `399,468,469,733,467,791`。换掉的两个大雕文对刺杀是死的——
  715 击杀之刃属战斗系 51 点天赋，406 割裂对应的 `rupture` 在 `AssassinationRogueStrategy` 里
  只注册了节点、没有触发器（实际不放）。换成 733 残忍、791 毒伤，三个大雕文都对应策略真正会放的技能；
  保留 399 破甲（刺杀策略有 `expose armor` 触发器）与三个通用小雕文。
  槽位大小写顺序必须是 major,minor,minor,major,minor,major（`PrepareCharacter` 逐槽比对 `TypeFlags`）。
- `RequiredSpells`：`48638` → `48638,1329`。1329 残忍由刺杀 31 点天赋授予，作为「天赋真的切过去了」的入场证据。
- 武器无需改动：主副手 41825 / 44028 都是匕首（`item_template.subclass = 15`），残忍可用；
  补给 43231 迅捷毒药 + 43233 致命毒药本来就是刺杀的毒药组合。

**实机验证**：run426（对照组 `heroic-nexus-keristrasza-disc-n5`）角色快照 slot-2 为
`spec rogue_assassination` / `talent_points 71` / `free_talent_points 0` /
雕文 `399,468,469,733,467,791`，夹具零报错，该场 **125.7 秒零死亡击杀**。

## 本轮定位到的三个缺陷

见 [台账](../../BOSS-LEDGER.md) 顶部与各 boss 记录。摘要：

1. **核心崩溃（上游 AC bug）**：`CreatureGroup::DespawnFormation` 边遍历 `m_members` 边让成员
   同步 `RemoveFromWorld`，释放迭代器脚下的红黑树节点（最后一个成员还会 `delete this`）。
   克里克希尔 evade 必经此路（`OnCreatureEvade` → 三组守望者 `DespawnFormation(0s, 20s)`）。
2. **mod-raidtest `RuntimeStrategyName` 硬编码表只有 UK 和魔枢两行**，换新副本必撞
   `raid_invalid: instance combat strategy inactive before pull`。
3. **哈多诺克斯 `ResetInstance` 返回 false**，原因待归因日志确认。
