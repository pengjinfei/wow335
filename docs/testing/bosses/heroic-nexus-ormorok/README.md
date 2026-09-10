# 英雄魔枢 / 奥莫洛克（Ormorok the Tree-Shaper, 26794）/ `heroic-nexus-ormorok-n5`

## 接手摘要

- 更新日期 2026-09-10。状态：**策略失败（0/5）**，且**无法分离小怪**——遭遇战的真实形态是
  「boss + 4 只精英守卫一次开怪」。
- 已完成：拉怪点实测定位、5 场基线、以及「为什么不能先清守卫」的证据链。
- 唯一下一步：要么按「boss + 4 精英」这个形态去修 bot 策略，要么先给 mod-raidtest 加
  「等前置目标巡逻到距 boss ≥N 码再开怪」的能力，才能测到干净的单 boss 段。
- 阻塞/需用户决定：上面那个框架能力要不要做。

## 可复现基线

- 装备档位 `normal5-v1`（ilvl 上限 187），boss 英雄难度（等级 82、`HealthModifier = 32`），
  `BotCheats = ""`、`AutoEquipUpgradeLoot = 0`。
- mod-raidtest `dev` @ `dfc7372` + 未提交的 `CombatTrigger` 策略名映射；
  mod-playerbots @ `67ac953c`（本轮一行未改）；core @ `516b14df1`。
- 场景：map 576 / boss 26794 / 英雄 / 5 人 / 无前置怪声明 /
  拉怪点 **(275.0, -215.0, -9.00)**（boss 东北 14.5 码，位移导航探针验证在网格上且连通）。
- 角色 guid 796–800（本副本四个 boss 共用）。

## 为什么守卫组分不开（三条实测证据）

守卫组 = `126445`/`126444`(Crystalline Tender 28231) + `126606`/`126605`(Crystalline Keeper 26782)，
等级 80 精英，构成一个 `creature_formation`（leader 126445，groupAI = 514 =
`IDLE_IN_FORMATION | LEADER_ASSISTS_MEMBER`）。

1. **它们是巡逻怪。** DB 生成点 x∈[247.9,253.4]，但运行时 `preclear_target` 采样到同一只
   `28231` 出现在 **(303.55,-240.54,-14.09)** 与 **(285.51,-233.67,-8.41)**——沿平台到花园
   的斜坡游走 50 余码。冷启动瞬间它们总在生成点附近，**距 boss 仅 17.1 码**。
2. **守卫挨打，boss 90 毫秒内参战。** run355 把清怪点放到花园侧、距 boss 41.5 码，
   守卫在 (254.45,-238.90) 被打到第一下（rel_ms 3086，Crystalline Keeper 反击）后，
   **rel_ms 3145 就记录到 `preclear_boss_invalid: alive=true combat=true`**，boss 仍停在生成点。
   运行配置 `CreatureFamilyAssistanceRadius = 10`，17.1 码仍触发；
   **推测**是 `Creature::CallAssistance` 按包围半径计距、而奥莫洛克模型很大
   （`creature_template_model.DisplayScale = 1.15`）——**此推测未验证**，但「守卫被打 →
   boss 立刻协助」这个事实已实测两次（run349 在 27 码、run355 在 41.5 码，均触发）。
3. **拉远也没用。** run343 把拉怪点放在距守卫 31.9 码、距 boss 14.5 码处只打 boss，
   5/5 场守卫全部参战，承伤 Crystalline Keeper **288,315** + Tender **160,307**，
   比 boss 本人的 150,258 还多。boss 与守卫之间**没有** `creature_formations` 联动
   （`linked_respawn` 只把 44 只 Crystalline Frayer 挂在 boss 上，是重生联动不是仇恨联动）。

另外，花园里的 `Crystalline Frayer`(26793) **在奥莫洛克死前打不死**
（`instance_nexus.cpp:249` 的 `_allowDeath`，血空则进种子壳复活），且 `MoveRandom(10.0f)` 游走，
所以花园侧的清怪点还会白拉两只不可击杀的普通怪。

## 机制与代码审计

| 机制 | trigger → action | 正常规则 | 运行证据 | 结论 |
|---|---|---|---|---|
| 水晶尖刺 | `ormorok spikes` → `dodge spikes`（`ACTION_MOVE + 5`，`NexStrategy.cpp:33`） | 是 | run343 出现 `Crystal Spike`(27099) 伤害 6,705（2 次命中） | **已触发**，命中率未量化 |
| 非坦克集合 | `ormorok stack` → `dodge spikes` | 是 | 未单独采样 | 未验收 |
| 法术反射 | 无（`NexStrategy.cpp:37` 注释为 TODO） | — | — | **未覆盖**（上游未实现） |
| 狂乱 | 无 | — | — | 未覆盖 |

## 尝试记录

| run / attempt | 结果 | 时长 | 死亡 | boss HP | 备注 |
|---|---|---|---|---|---|
| 336 / 1 | wipe | 25.7s | 5 | 92% | 拉怪点距守卫 8 码，等于同时开 boss + 4 精英 |
| 343 / 1 | wipe | 17.7s | 5 | 96% | 拉怪点距守卫 31.9 码，守卫仍全部参战 |
| 343 / 2 | wipe | 25.6s | 5 | 94% | |
| 343 / 3 | wipe | 21.6s | 5 | 90% | 五场最好 |
| 343 / 4 | wipe | 38.1s | 5 | 94% | |
| 343 / 5 | wipe | 22.6s | 5 | 94% | |
| 349 / 1–5 | aborted ×5 | 0.75–1.05s | 0 | 100% | 清怪点 27 码，清怪期间 boss 参战 |
| 352 / 1–2 | aborted ×2 | 180s | 0 | 100% | 清怪点 (239.2,-249.0) 是孤立网格，`component=disconnected`、清怪超时 |
| 355 / 1–2 | aborted ×2 | 3.1/3.9s | 0 | 100% | 清怪点花园侧 41.5 码，守卫挨打后 90ms boss 参战 |

**run 343（当前形态基线）**：0 击杀 / 5 团灭，boss 最低 90%，17.7–38.1 秒全灭。
五场合计 bot 输出 456,293，承伤 Keeper 288,315 + Tender 160,307 + boss 150,258 + Crystal Spike 6,705。

结论：normal5-v1 装备下「boss + 4 只等级 80 精英」这个形态**差距很大**（boss 最低只到 90%），
不是窄边界。要判断 boss 本人的机制处理得如何，必须先能把守卫分离出去。

## 交接

- `raidtest run heroic-nexus-ormorok-n5 --attempts 5` 可直接复现当前形态。
- 证据在本地 MySQL（run 336/343/349/352/355）。
- 新会话下一条安全操作：先读 [夹具勘测](../heroic-nexus/FIXTURE-SURVEY.md)，
  再决定是否给 mod-raidtest 加「按巡逻距离择时开怪」的能力。
