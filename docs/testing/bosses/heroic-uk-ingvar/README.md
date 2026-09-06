# 英雄乌特加德城堡：因格瓦尔

更新：2026-09-06；当前状态：双阶段机制完整运行，但 bots 在 P2 团灭——根因是 mod-playerbots 的 UK 绕背躲避策略有缺陷，非框架/机制问题。未改策略代码。

## 基线

- 场景 `heroic-uk-ingvar`；map=574，BossEntry=23954，@ (242.7,-333.6,180.56)。
- 五人普通小队，DungeonDifficulty=heroic(1)，PartySize=5，配置 heroic5-v1。
- 首次验证**隔离 boss 战**（无 PrerequisiteSpawns）。房间 3 只骑手(24849，生成点 125935/125934/125940)留作后续。
- 机制审计见 [UK 机制审计](../heroic-uk/MECHANICS-AUDIT.md)。

## 验证

| run | 结果 | 时长 | deaths | 机制运行 |
|---|---|---|---|---|
| 95 | wipe | 112.7s | 5 | 完整 |
| 97 | wipe | 130.5s | 5 | 完整 |

机制完整触发：P1 顺劈(42724) → 死亡 → 召唤安希尔德(42912) → 复活光束(42857) → 复活球(42862) → 复活治疗(42704) → 变形亡灵(42796) → P2 暗影斧(42749)。**机制未被删减，且正是它们在击杀 bots。**

## wipe 根因：mod-playerbots UK 绕背躲避策略缺陷

`WotlkDungeonUKStrategy`（`mod-playerbots/src/Ai/Dungeon/UK/UKStrategy.cpp`）注册了因格瓦尔躲避：`ingvar smash tank→dodge smash`（坦克猛击绕背）、`not behind ingvar→set behind`（非坦克绕背）、`not behind ingvar`（注释自认 buggy，容易卡在跑来跑去）。但实测 3 个具体缺陷导致绕背基本不生效：

1. **`NotBehindIngvarTrigger` 条件写反**（`UKTriggers.cpp:87`）：返回 `AI_VALUE2("behind",...)`——在 boss 背后时才触发；通用 `IsNotBehindTargetTrigger`（`GenericTriggers.cpp:564`）是 `!behind`（不在背后触发）。缺 `!`。→ **DPS/治疗站在 boss 正面时从不被命令绕背**，站着吃前方锥形猛击。

2. **`SetBehindTargetAction` 要求近战范围**（`MovementActions.cpp:2676`）：`if (!bot->IsWithinMeleeRange(target)) return false`。→ **远程（法师/萨满/治疗）即使触发也绕不了**，只能站正面。

3. **投掷暗影斧无躲避处理**：治疗(737)被斧子 NPC(23997) 击杀，UK 策略没有对应规避。

## 实测死亡序列（run97，guid→职业）

| 时间 | 死者 | 被什么击杀 |
|---|---|---|
| 83.6s | 盗贼(738)、萨满(740) | 因格瓦尔 **36.5K / 26K 单发**（猛击类前锥） |
| 106.5s | 治疗(737) | 暗影斧(23997) |
| 120.6s | 坦克(736) | 因格瓦尔 **26.4K 单发** |
| 130.5s | 法师(739) | 因格瓦尔 **29.3K 单发** |

因格瓦尔周期性全团 ~6K AoE + 26-36K 大额单发（猛击类）。DPS/治疗站在正面吃前锥伤害：ilvl200 血 18-22K，一发即死，治疗来不及。坦克有 dodge 动作但也在 26K 下倒地（代码注释自认该区域 buggy）。

bots 共造成 ~467K 伤害，因格瓦尔回敬 ~353K + 斧子 49K。

## 修复方向（未实施）

- ① 触发器补 `!`（一行，让非坦克在正面时收到绕背命令）。
- ② 远程绕背：去掉 SetBehindTargetAction 的近战范围限制，或为远程加侧移/后退动作。
- ③ 暗影斧躲避：投掷时离开飞行路径。

属于 mod-playerbots 上游策略修复（本项目惯例：不通过削弱 boss 或删机制来过关）。

## 遗留

- 房间 3 只骑手小怪清理未纳入。
- 策略修复（①②③）后复测。
