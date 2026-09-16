# 英雄达克萨隆要塞 / 巨魔之喉（Trollgore）

场景：`heroic-dtk-trollgore-n5`（map 600，boss entry 26630，英雄难度取 31362，82 级）

## 接手摘要

- 更新日期：2026-09-16 凌晨。**状态：首轮基线即通关，无需任何改动。**
- 已完成：建场景 → 冒烟 1 场（run 545，57.4 秒击杀）→ 基线 10 场（run 546，**10 击杀 / 0 团灭 / 零死亡**，48.9–58.2 秒）。
- 唯一下一步：换本内第二个 boss（召唤者诺沃斯 26631）。
- 阻塞：无。口径说明见下（10 场，Wilson 95% CI 72–100%；按「≥20 场再写率」的约定，这里记的是
  「首轮 10/10、未见失败模式」，不是收窄过的稳定率）。

## 可复现基线

| 仓库 | 分支 | HEAD | 工作区 |
|---|---|---|---|
| azerothcore-wotlk | codex/an-formation-despawn-crash | `fa702e6a5` | 7 个文件未提交（沿用上一轮，未因本 boss 改动） |
| mod-playerbots | codex/uk-ingvar-los-recovery | `1e285dff` | 干净 |
| mod-raidtest | codex/an-runtime-strategy-names | `d030865` | 1 个文件未提交（`44f5947` 的 `casting=` 探针，**二进制不含**） |

- 二进制：2026-09-15 19:28 那次增量编译（与 mod-playerbots `1e285dff` 一致）。**本 boss 全程没有编译。**
- worldserver：2026-09-16 00:0x 以 `scripts/restart_world.sh r34a` 重启（新场景只在启动时注册），
  日志 `/tmp/wow335-worldserver-r34a.log`。重启后第一条 FIFO 命令照例被吞，重发才生效。
- 装备档 normal5-v1（ilvl 上限 187），roster 复用 796–800（与 AN / 魔枢各场景同一组角色），
  `GearProfile = none`，无 cheat。
- 结果：run 545（冒烟 1 场）、run 546（基线 10 场），实例 id 1/6。

## 场景设计（勘测证据）

boss (-266.2,-660.1,26.5)，房间地板 z≈26.5，`CheckInRoom` 盒子 y∈[-700,-628]。

- **准备点 (-261,-633,26.52)**：`raidtest los` 实测地面 26.52、对 boss los=true；距 boss 27.6 码
  （英雄 82 级仇恨半径 = 20−(80−82) = 22）；距三个小怪落点 26.0–29.3 码。
- **开怪点 (-260,-660,26.55)**：boss 正东 6.2 码，los=true。无前置怪，队伍从准备点直接开怪。
- **不需要清怪**：房间内没有路怪，最近一组（127605/127584/127558，z≈11）在西侧下层 34 码外；
  `SetInCombatWithZone` 只对玩家生效，不会把它们拉进来。所以 `PrerequisiteSpawns` 留空是实情，不是简化。
- 换本三个坑已核：Trollgore `flags_extra=0`（无 HARD_RESET）；`wotlk-dtk → "drak'tharon keep"`
  已在 `CombatTrigger::RuntimeStrategyName` 表里；准备点用位移探针（实跑）验证，不只靠 los。
- **新场景要自己补 roster 映射**：`raidtest_accounts` 按 scenario_key 存槽位，新键没有映射会去**新建角色**，
  而名字 `Raidteanfive`(+a..e) 早被占满 → `failed to create character for slot 0 after 6 candidate name(s)`。
  照抄一份既有映射即可：
  ```sql
  INSERT INTO acore_characters.raidtest_accounts (scenario_key,slot,account_id,character_guid,class,role,created_at)
  SELECT '<新场景键>',slot,account_id,character_guid,class,role,NOW()
  FROM acore_characters.raidtest_accounts WHERE scenario_key='heroic-an-krikthir-n5';
  ```

## 机制与代码审计

| 机制 | 源码 | 基线 10 场实测 | 结论 |
|---|---|---|---|
| 召唤小怪 49456/49457/49458（三只 Drakkari Invader，脱战也每 30 秒一轮） | `boss_trollgore.cpp` events2 | 各 **11 次**；27709/27753/27754 各放 11 次挑衅 49405 | 触发了 |
| 小怪造成的伤害 | — | **0**（十场合计） | 小怪落地即被清/未出手；50 秒的战斗长度下它们没有头寸 |
| Crush 49639 | 3–5 秒起手、10–15 秒循环 | 44 次 | 触发了，坦克扛住 |
| Infected Wound 49637 | 6–10 秒起手 | 20 次 | 触发了 |
| Consume 49380 / 英勇 59803 | 15 秒循环，吞尸体叠 49381 | 59803 共 31 次 | 触发了；未观察到失控叠层（战斗 50 秒） |
| Corpse Explode 49555 / 英勇 59807 | 35 秒起手 | 59807 共 16 次 | 触发了 |
| bot 侧 `corpse explode spread` | 上游 `DTKStrategy.cpp` → `CorpseExplodeSpreadAction`（尸体 5+2 码内走开） | 未单独量执行率（零死亡，没有排查动机） | **未覆盖**：想量要开 `LogInGroupOnly=0` |

队伍承伤 64k–128k/场，零死亡。判别不出瓶颈——本 boss 在这套 bot 上不构成检验。

## 尝试记录

| run / attempt | 结果 | 时长 | 死亡 | boss HP |
|---|---|---|---|---|
| 545 / 1（冒烟） | kill | 57.4s | 0 | 0% |
| 546 / 1–10 | **kill ×10** | 48.9–58.2s | 0 | 0% |

## 判定

**正常规则通关（隔离 boss 战口径）**：不清路怪、不改难度、不改装备、无 cheat，bot 自主处理
召唤小怪与 boss 循环，10/10 零死亡。房间本来就没有路怪，所以这里的「隔离」只少了走廊上的包，
不少任何 boss 机制。

## 交接

- 管理库：本文件 + 台账 + START-HERE 已更新。源码两库**未因本 boss 产生任何改动**。
- 进程：worldserver（r34a 日志）运行中，run 546 已收尾，state=IDLE。
- 下一条安全操作：建 `heroic-dtk-novos-n5` 场景。**注意诺沃斯 `flags_extra=0x80000000`（HARD_RESET）**，
  这是 `ResolveOrRestoreSpawn()` 修过的那条路径，首轮要盯 reset 日志。
