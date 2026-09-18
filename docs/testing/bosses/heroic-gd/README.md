# 英雄古达克（Gundrak，map 604）——副本级勘测与场景设计

更新：2026-09-17。第五个副本，接在达克萨隆要塞之后。装备档 normal5-v1（ilvl 上限 187），
难度英雄，`BotCheats = ""`，无作弊。当前 core / mod-playerbots **没有保留未合并的改动**；
mod-raidtest 的场景 conf 只在运行目录（gitignored）。

## 一、四个 boss 的现状

| boss | entry | 场景 | 本轮结果 |
|---|---|---|---|
| 毒蛇领主斯拉德兰 Slad'ran | 29304 | `heroic-gd-sladran-n5`（完整）/ `heroic-gd-sladran-disc-n5`（隔离） | 合并后 **3/5**；随后「平台下坦克 / 平台上远程」独立样本 **0/5**，已回退。见 [记录](../heroic-gd-sladran/README.md) |
| 莫拉比 Moorabi | 29305 | `heroic-gd-moorabi-n5` | **8 击杀 / 1 aborted / 1 timeout**（10 个 boss 样本）；仍未稳定。见 [记录](../heroic-gd-moorabi/README.md) |
| 德拉克瑞巨像 Drakkari Colossus | 29307 | `heroic-gd-colossus-n5` | **5/5 零死亡**，64.374–68.137 秒（run651–652）；隔离 boss 战基线通过，不混作连续副本通关。见 [记录](../heroic-gd-colossus/README.md) |
| 迦尔达拉 Gal'darah | 29306 | `heroic-gd-galdarah-n5` | **2/5 击杀**（68.4 / 71.9 秒，均零死亡）。见 [记录](../heroic-gd-galdarah/README.md) |

## 二、地形勘测（`raidtest los` 静态探针，约 1300 个点）

**这一轮最值钱的一条方法教训又是探针的 z 用法**（LESSONS 里已有条目，本轮再踩）：
第一遍我用统一 `z1=129.3` 扫斯拉德兰/莫拉比两个房间，得出「南走廊/北走廊对 boss 全部 los=true」。
`raidtest los` 是从 `z1+2` 量的，而那两条走廊的地面是 **124.5 / 123.4**——等于站在半空看。
用**逐点实测地面高度**重扫之后，结论**整个翻转**：两条走廊对 boss 全部 `los=false`。

三个房间的可用站位结构（第二遍、正确 z 的结果）：

| boss | boss 平台 | 可见区 | 22–30 码带内有无候选 | 结论 |
|---|---|---|---|---|
| 斯拉德兰 (1775.1,675.0,129.30) | x 1765–1790 / y 665–685，z=129.22 | 平台 + 南走廊（z≈124.5） | **无**（平台上任何点 ≤18 码；走廊里 >22 码的点全部 los=false） | 必须走「前置清怪 → 传送到开怪点」 |
| 莫拉比 (1772.5,809.5,129.30) | x 1755–1785 / y 800–825，z=129.22 | **恰好只有平台本身** | **无**（22–30 码带内零候选，逐点实测） | 同上，结构上必须有前置怪 |
| 迦尔达拉 (1914.8,743.6,136.58) | 一整块平地 x 1865–1955 / y 705–785 | 全 true | 有 | 无需前置怪，队伍在准备点直接开怪 |

斯拉德兰平台北面 y≥690 地面掉到 95–105（中央深坑）、西面 x 1735–1755 是断崖（z 96–107）；
**唯一进出口是南面那条下沉走廊**。莫拉比平台南面 y≤795 掉到 96。

### 为什么「没有前置怪就开不了怪」

`AttemptRunner` 只有走完 `Prerequisites → Recovery → BossPosition` 才会把队伍传送到 `EngagePoint`
（`AttemptRunner.cpp:866`）；隔离型场景**跳过 BossPosition**，队伍停在 `PreparationPoint` 开怪。
所以准备点必须同时满足「距 boss >22 码（英雄 82 级 boss 的仇恨半径）」「<30 码（制裁之手射程）」
「对 boss los=true」。斯拉德兰和莫拉比都不存在这样的点，因此**至少要留一只前置怪**。
这条与德雷德 conf 里那段结论一致，但那里是「准备点太远」，这里是「不存在可见点」。

## 三、小怪与编队（建夹具必查的两类）

- 巡逻（`MovementType=2`）：斯拉德兰南走廊两条巡逻线 `1270140`（x1780–1790, y605–650）与
  `1270170`（x1767–1776, y610–642）**把整条走廊扫满**，走廊里不存在「巡逻够不到」的驻点。
- 编队（`creature_formations`）：斯拉德兰走廊三组（队长 127014 / 127017 / 127026），
  莫拉比北走廊一组（队长 127113），**巨像 127046 本人是队长**、两只 Drakkari Golem
  127080/127081 是成员且 `groupAI=1`（MEMBER_ASSIST_LEADER）——拉巨像会把 47 码外的两只石魔带进来。
- 三个 boss 房都没有门；Gal'darah Door(192568) 是 `DOOR_TYPE_ROOM`，战斗中才关，
  队伍是传送进去的，三祭坛的桥（`GO_GUNDRAK_COLLISION` 192633）不影响。

## 四、德拉克瑞巨像：原生 Mojo 开战已建模，隔离口径仍需清房间路怪

`boss_drakkari_colossus.cpp` 的 `Reset()` 里巨像挂 `UNIT_FLAG_NON_ATTACKABLE` + `SPELL_FREEZE_ANIM`，
并在自身周围召五只临时 Living Mojo（29830；x 1663–1681 / y 733–754）。旧记录的「先打死五只」是错误口径：
任意一只被玩家真实拉到后，`npc_living_mojoAI::JustEngagedWith()` 会通知巨像 `ACTION_INFORM`；巨像随即
`SetInCombatWithZone()`、命令五只合并，并在 3.5 秒后解除不可攻击。

新能力 `EngageTrigger=summon` / `SummonTriggerEntry=29830` 只匹配 `GetSummonerGUID()==bossGuid` 的临时单位，
不会把同 entry 的世界刷怪混作触发目标。run647–648 发现旧的 20-tick 确认窗口在空载服只过数十毫秒；改为最多
等待 6 秒的真实时间后，run649 观测到 Mojo 合并、巨像 3.5 秒后解除不可攻击、全队进入其威胁表，原生开战链完整。

run649 的 23.018 秒全灭（boss 73%）有至少 3 只常驻 Living Mojo 参战；查询显示这类房间怪共有
127076–127079 四只，且与临时 Mojo 同为 entry 29830。用户确认后，run650 的隔离夹具逐只移除了这 4 只，
原生链保持完整并取得 89.722 秒零死亡击杀。

run650 仍不是隔离 boss 结论：巨像是两只 Drakkari Golem（127080/127081）的 formation leader，`groupAI=1`，
两只均参战。经确认后，run651 的夹具在 0ms 移除了 4 只常驻 Mojo 和这 2 只编队石魔；原生临时 Mojo
仍完成触发、合并与解锁。run651–652 的五场同口径样本均零死亡击杀（64.374–68.137 秒；Wilson 95% CI 57–100%），
故巨像的隔离 boss 战基线通过。它不等于连续清本；若继续应另建完整房间口径，不能与此样本混算或改装备、难度、cheat、boss 仇恨。

## 五、上游 mod-playerbots 的 GD 策略覆盖度

`modules/mod-playerbots/src/Ai/Dungeon/GD/`（`WotlkDungeonGDStrategy`，运行名 `gundrak`，
`wotlk-gd` 已在 mod-raidtest 的 `RuntimeStrategyName` 表里，本轮无需补表）：

| boss | 触发器/乘子 | 覆盖 |
|---|---|---|
| 斯拉德兰 | `poison nova` → `avoid poison nova`；`snake wrap` → `attack snake wrap`；`SladranMultiplier` | 部分，且乘子有反效果，见 boss 记录 |
| 迦尔达拉 | `whirling slash` → `avoid whirling slash`；`GaldarahMultiplier` | 只有旋刃；冲锋/践踏/穿刺叠加无触发器 |
| 莫拉比 | **一条没有**（`GDStrategy.cpp` 里是空注释） | 未覆盖 |
| 巨像 | **一条没有** | 未覆盖 |
| 凶残的艾克（英雄限定） | **一条没有** | 未覆盖 |

`GDStrategy.cpp` 上游自己写着 `// TODO: Might need to add target priority for heroic on the snakes
or to burn down boss. Will re-test in heroic.`——**英雄难度上游从没测过**。

## 收尾时补记：凶残的艾克（29932，英雄限定）**这一轮完全没碰**

上面的「上游 GD 策略覆盖表」里这一行写的是「一条没有 / 未覆盖」——那说的是
**上游 mod-playerbots 没有针对它的策略代码**。收尾时才意识到更严重的是：
**我这一轮连场景都没建、连准备点勘测都没做。**

这不是「测出来打不过」，是**遗漏**。古达克是 5 个 boss（艾克是英雄限定、在侧厅、
可跳过但属于本副本），所以「5 个里通了 1 个」这个口径里，艾克算**未覆盖**而不是**失败**。

下一轮接手时，艾克应该排在斯拉德兰之前——它是全新样本，成本只有建场景；
而斯拉德兰的瓶颈已经量成硬天花板（治疗 1,237 HPS 对 DTPS 1,819），继续投入的边际收益低。
