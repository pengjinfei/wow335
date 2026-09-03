# mod-raidtest 设计文档

> 版本: v0.1（草案）
> 日期: 2026-09-03
> 目标仓库: `modules/mod-raidtest`（本项目管理库的子模块，独立 git 仓库）

## 1. 目标与非目标

### 1.1 目标

为 AzerothCore **Playerbot fork**（`mod-playerbots/azerothcore-wotlk` 的 Playerbot 分支 + `mod-playerbots`）提供一个**无客户端、全服务端可自动化**的团队副本验证模块：

1. 一键创建/复用测试账号与角色（10 人团，坦克/治疗/DPS 阵容可配置）；
2. 按副本/boss 场景批量执行（组队 → 传送 → 开战 → 判定胜负 → 采集结果）；
3. 结果落 DB，可跨运行聚合统计（胜率、耗时、死亡清单、伤害归因）；
4. 场景由数据/配置驱动，后续覆盖 WLK 全团本只需"加场景"，不改框架；
5. **战斗日志驱动的策略优化闭环**：每次尝试沉淀结构化战斗事件流，可回放、可对比、可归因，用于验证 mod-playerbots 的 raid 策略是否合理，并支撑"改策略 → 重跑 → 对比 → 收敛"的迭代循环。

### 1.2 非目标（明确不做）

- ❌ 修改核心/模块的伤害倍率、装备属性、boss 机制（本项目的硬性约束）；
- ❌ 自动"修好" bot 策略——模块只采集、展示、对比，判定和改策略仍是人的工作（这保持模块边界干净）；
- ❌ 模拟真实玩家客户端行为（bot 走 mod-playerbots 既有 AI，测试模块只做编排）；
- ❌ 代替 mod-playerbots 的 raid 策略开发——测试模块**消费**它们，不重写它们；
- ❌ 改 mod-playerbots 源码来输出策略切换事件（只读其既有输出/状态，见 §4.4；改动其源码会抬高同步成本）；
- ❌ 首个里程碑不做成型前的细粒度调试面板（见 §7 阶段规划）。

### 1.3 成功判据（验收标准）

对首个场景 `naxx-patchwerk`：

```
.raidtest run naxx-patchwerk --attempts 3
```

必须从零完成：创建账号 → 创建 10 个角色 → 按职责配装 → 组队 → 传送进 NAXX → 触发 boss 战 → 在合理超时内给出明确 `kill/wipe/timeout` 判定 → 结果写入 `characters.raidtest_attempts`。
重启服务器后重复运行应能复用角色（或按参数强制重建）。

## 2. 术语

| 术语 | 含义 |
|---|---|
| Scenario（场景） | 一次可复现的战斗验证单元：`{副本, boss, 团队模板, 配装档位, 开战方式, 超时}` |
| Run（运行） | 某个场景的一次执行（可含多次尝试） |
| Attempt（尝试） | Run 内的一次拉怪，从进入战斗到胜负判定或本次重置 |
| Roster（阵容） | 一组位子：`{槽位, 职业, 职责}`，如 `{0, warrior, tank}` |
| Roster Blueprint（角色蓝图） | 阵容的完整配置声明：槽位/名称/种族/职业/职责/天赋/专业/装备/宝石/附魔（§5.1） |
| Test Account（测试账号） | `raidtest` 前缀的专用账号，由模块创建，不与真实/随机 bot 混用 |

## 3. 架构总览

```
┌────────────────────────────────────────────────────────────┐
│                      worldserver 进程                        │
│                                                            │
│  ┌──────────────┐   ┌──────────────────────────────────┐   │
│  │ Command Layer │   │         Orchestrator             │   │
│  │ .raidtest     │──▶│  RaidTestOrchestrator (状态机)   │   │
│  │ (Console/RA)  │   │   Run ──▶ Attempt ──▶ 判定       │   │
│  └──────────────┘   └───────┬──────────────────┬────────┘   │
│                            │ 调用              │ 写结果     │
│         ┌──────────────────▼────┐   ┌──────────▼────────┐   │
│         │     RosterManager     │   │    ResultStore    │   │
│         │ 建号/建角/登录/配装    │   │  characters 库表   │   │
│         │ 组队/传送/开战         │   └──────────┬────────┘   │
│         └──────────────────┬────┘              │           │
│   ┌────────────────────────▼───────────────────▼─────────┐ │
│   │              CombatEventBus（战斗事件总线）            │ │
│   │  AllSpellScript/UnitScript/AllCreatureScript hooks    │ │
│   │  + 策略状态快照 → 结构化事件流 → raidtest_events 表     │ │
│   └────────────────────────▲─────────────────────────────┘ │
│   ┌────────────────────────┘─────────────────────────────┐ │
│   │           mod-playerbots 既有能力（只调用，不改）       │ │
│   │  PlayerbotMgr::AddPlayerBot  无 session 头less 登录   │ │
│   │  PlayerbotFactory            建角色/天赋/装备/宝石附魔 │ │
│   │  GroupMgr / Teleport        组队/传送                │ │
│   │  PullAction / AttackAction  bot AI 开战              │ │
│   │  mapId→raid策略  (PlayerbotAI.cpp)  副本内自动激活     │ │
│   └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

**关键设计原则**：
1. 测试模块只做**编排**，一切"bot 如何表现"交给 mod-playerbots 的既有 AI；
2. 对上游的侵入**仅限模块目录内**（新增场景源文件），不碰核心源码（同步友好）；
3. 每个组件单一职责、接口明确、可独立测试（见 §5 文件布局）。

## 4. 技术基础（已核实的事实）

以下机制已在上游源码中验证，设计直接依赖它们：

| 能力 | 位置/原理 | 用途 |
|---|---|---|
| 无客户端登录 | `PlayerbotMgr.cpp:203` `new WorldSession(botAccountId, "", ...)` → `HandlePlayerLoginFromDB` → `OnPlayerLogin` | bot 角色头less 上线 |
| 无 master 自治 | 随机 bot 以 `masterAccountId=0` 登录；AI `FindNewMaster()` 自动选组长 | 全队可为 bot，无需真人 |
| Raid 策略自动激活 | `PlayerbotAI.cpp`：`mapId → strategyName`（naxx/ulduar/icc/onyxia/rs 全覆盖） | 进副本即获得战斗行为 |
| 组队 | `InviteToGroupAction` / `GroupMgr` | 服务端成组 |
| 开战 | `PullAction` / `AttackAction::Attack(Unit*, bool)`；或引擎级 `Unit::AddThreat`/`AttackStart`（禁止：不绕过 AI 直接改 boss 血） | 触发 boss 战 |
| 配装 | `PlayerbotFactory` 构造 + `InitSkills/InitTalentsTrees/InitEquipment/ApplyEnchantAndGemsNew`；`AutoGear(bot, itemQuality, ilvl, ...)`；`init=epic/auto` 命令语义 | 合法配装（克隆自工厂随机化逻辑） |

### 4.1 建号与角色创建（配置驱动）

- **角色蓝图（Roster Blueprint）**：阵容中的每个槽位由**配置文件声明**，包括：
  `槽位 / 名称 / 种族 / 职业 / 职责 / 天赋 / 专业技能 / 装备（逐槽位 item_id）/ 宝石 / 附魔`
  代码与数据分离——建号逻辑读蓝图执行，改角色方案只改配置，不动代码（格式见 §5.1）。
- **账号**：在 `auth.account` 建记录（复用 `AccountMgr::CreateAccount` 的 SRP6 建号逻辑），密码随机生成即可——bot 登录走 DB 加载，不走网络验证；
- **角色**：写入 `characters.characters` 及关联表（`Player::Create` 流程 / `CharacterCreateGameData`）。初始化管线：
  1. 按蓝图建角色（80 级）
  2. `PlayerbotFactory` 初始化天赋/技能/法术（复用其成熟逻辑，按蓝图的职业/天赋声明）
  3. **装备/宝石/附魔按蓝图逐槽位落实**：`Player::AddItem` → 插宝石（`Item::AddSocketGem`）→ 附魔（`Player::ApplyEnchantment`）；未指定的槽位可落回工厂自动配装（档位驱动），实现"精确与省事兼顾"
- **蓝图的持久化**：建好的账号/角色映射仍写 `raidtest_accounts` 表；蓝图文本随配置进 git，天然版本化，可快速对比"同一角色、不同装备配置"的测试结果

### 4.2 数据库取舍（重要）

**不新增核心数据库连接**。优先复用 `characters` 库存放运行时结果（账号映射、run/attempt/事件），场景定义放配置+代码（场景包含 C++ hook，纯数据不够描述）。理由：

- 新增独立库需改 `DatabaseEnv.h` / `DatabaseWorkerPool` / `DatabaseUpdater`（core 侧），上游同步会冲突；
- `characters` 库已承载 mod-playerbots 的扩展表，风险最小、schema 可版本化（`data/sql/characters/updates/` 机制沿用）。

### 4.3 副本重置

复用现有实例机制：`InstanceSaveMgr` / `.instance unbind` 语义对应的 C++ 接口（`InstanceSave::Delete` / `InstanceHandler::ResetInstance`）。每次 Attempt 结束按场景配置决定是否重置副本。

### 4.4 战斗事件与策略数据来源（已验证）

| 数据 | 来源 | 现状 |
|---|---|---|
| **施法事件** | `AllSpellScript::OnSpellCast` | ✅ core 提供，无需绑定具体 boss |
| **伤害事件** | `UnitScript::OnDamage(attacker, victim, damage)` | ✅ core 提供，hook 全部伤害 |
| **生物死亡** | `AllCreatureScript` | ✅ core 提供 |
| **策略切换** | mod-playerbots `ChangeStrategy()` / `SelectiveResetStrategies()` | ⚠️ 只读其既有输出/AI 状态；不改其源码。A 阶段先验证这些调用是否附带日志输出，无则回退到"AI 状态快照 + 施法序列反推" |
| **boss 血量** | `EncounterObserver` 轮询 `boss->GetHealthPct()` | 设计内 |
| **bot 位置** | `boss/Player::GetPosition` 轮询快照 | 设计内（可选粒度） |

> **决策**：A 阶段战斗事件总线只采集"施法/伤害/死亡/血量/胜负"，策略合理性靠战斗结果反推（死在哪 → 看死前施法序列与状态快照）。策略切换事件的关键性在 B 阶段验证，若 mod-playerbots 现有输出可复用则直接并入事件流，否则采取状态快照方案。避免为采集策略而修改模块源码（同步成本高）。

## 5. 模块文件布局

```
modules/mod-raidtest/
├── include.sh                      # 模块 shell 入口（加载 conf）
├── conf/
│   └── mod-raidtest.conf.dist      # 配置模板
├── data/sql/
│   └── characters/
│       └── updates/
│           └── 2026_09_03_00_mod_raidtest.sql   # schema 版本化（沿用核心更新机制）
├── README.md                       # 使用说明（本模块自述）
└── src/
    ├── Module/RaidTestModule.h/.cpp      # ScriptMgr 挂载、命令注册、World loop tick
    ├── Command/RaidTestCommandScript.h/.cpp  # .raidtest 命令解析（Console::Yes）
    ├── Config/
    │   ├── RaidTestConfig.h/.cpp         # 模块配置读取（前缀、默认尝试数、超时…）
    │   └── RosterBlueprint.h/.cpp        # ★ 角色蓝图：解析配置文件 → 槽位声明列表
    ├── Scenario/
    │   ├── Scenario.h/.cpp               # 场景定义基类 + 注册表（mapId→scenario）
    │   ├── Encounter.h/.cpp              # 单 boss 战斗：开战 hook / 判定 hook / 超时
    │   └── scenarios/
    │       └── NaxxScenario.cpp          # NAXX 场景（首个：Patchwerk）
    ├── Orchestrator/
    │   ├── RaidTestOrchestrator.h/.cpp   # Run/Attempt 状态机
    │   ├── RunContext.h                  # 单次 run 的上下文（阵容、账号、uuid）
    │   └── AttemptRunner.h/.cpp          # 单次尝试：传送→开战→轮询判定→记录
    ├── Bot/
    │   ├── RosterManager.h/.cpp          # 账号/角色生命周期（按蓝图 建/查/重置）
    │   ├── RosterBuilder.h/.cpp          # ★ 按蓝图造角：天赋/专业/装备/宝石/附魔落实
    │   ├── RosterLogin.h/.cpp            # 登录（调 PlayerbotMgr）、组队、传送
    │   └── CombatTrigger.h/.cpp          # 开战触发 + "已进入 raid 策略"检查
    ├── Observer/
    │   ├── AttemptObserver.h/.cpp        # 每 tick 轮询 boss 存活/全团存活/超时；判定
    │   └── CombatEventBus.h/.cpp         # ★ 战斗事件总线：挂 core hooks，聚合事件流
    │       └── CombatEvent.h             #   事件结构（ts/source/type/spellId/damage/...）
    └── Storage/
        ├── ResultStore.h/.cpp            # characters 库 DAO（写入 run/attempt）
        └── EventStore.h/.cpp             # 战斗事件批量落库（raidtest_events）
```

**组件依赖方向（严格单向）**：
`Command → Orchestrator → {RosterManager, AttemptRunner} → {RaidTestConfig, ResultStore}`
`Scenario → Encounter`；`RosterManager → RosterBlueprint → RosterBuilder`（被 Orchestrator 依赖）

### 5.1 角色蓝图配置格式（★ 建号数据驱动核心）

蓝图声明一个场景的完整阵容，配置文件名 `mod-raidtest-roster-<scenario>.conf`（随模块 git 版本化）。按槽位描述"这个角色的全部构成"：

```ini
# mod-raidtest-roster-naxx-patchwerk.conf
# 槽位索引从 0 开始；职责直接影响 bot 的 AI 行为（tank/heal/dps）

[Roster.0]                    # 副坦（可换人的位置）
Name            = "Patch-Tank"   # 角色名（自动加前缀，避免与真实玩家冲突）
Race            = "human"        # 种族（决定初始技能）
Class           = "warrior"      # 职业
Role            = "tank"         # 职责：tank/heal/dps
TalentSpec      = "warrior_tank" # 天赋模板（对应 PlayerbotFactory 天赋骨架）
Professions     = "mining,jewelcrafting"   # 双专业（逗号分隔）
MainHand        = 40491          # 逐槽位 item_id；缺省槽位交给工厂按档位自动配装
OffHand         = 40491
Head            = 40492
Shoulder        = 40493
Neck            = 40494
Chest           = 40495
Back            = 40496
Wrist           = 40497
Hands           = 40498
Waist           = 40499
Legs            = 40500
Feet            = 40501
Ring1           = 40502
Ring2           = 40503
Trinket1        = 40504
Trinket2        = 40505
# 宝石与附魔按槽位（gem=item_id 进 socket, enchant=附魔 id）
Head.Gem1       = 40111
Head.Gem2       = 40112
Head.Enchant    = 3856
Chest.Gem1      = 40113
Chest.Enchant   = 3858
```

关键设计：
- **不在蓝图里的槽位** → `RosterBuilder` 落回 `PlayerbotFactory` 的档位自动配装（`init=epic` 等价语义），保证"精确到逐件"和"省事到全自动"都成立；
- **装配顺序**：建角色 → 天赋/专业 → 装备 item → 插宝石（`Item::AddSocketGem`）→ 附魔（`Player::ApplyEnchantment`）→ 校验（`CanEquipItem`）；任一步失败该槽位标记并继续，不中断整队；
- **蓝图关联场景**：场景元数据里声明自己用的蓝图文件（`Scenario::GetRosterFile()`），`run` 时加载；
- **蓝图版本对比**：配置即 git 历史，改一套装备 → 重跑 → `compare`，天然支持"装备变量对照实验"。

## 6. 数据模型（characters 库）

```sql
-- %(raidtest_accounts) 账号映射：测试账号 ↔ 槽位角色
CREATE TABLE raidtest_accounts (
    scenario_key  VARCHAR(64)  NOT NULL,      -- 场景名（归属场景）
    slot          TINYINT      NOT NULL,      -- 0..9
    account_id    INT UNSIGNED NOT NULL,      -- auth.account.id
    character_guid INT UNSIGNED NOT NULL,
    class         TINYINT      NOT NULL,
    role          VARCHAR(16)  NOT NULL,      -- tank|heal|dps
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (scenario_key, slot)
) ENGINE=InnoDB;

-- %(raidtest_runs) 运行记录
CREATE TABLE raidtest_runs (
    id             INT UNSIGNED AUTO_INCREMENT,
    scenario_key   VARCHAR(64)  NOT NULL,
    map_id         INT UNSIGNED NOT NULL,
    boss_entry     INT UNSIGNED NOT NULL,
    attempts_total INT NOT NULL,
    kills          INT DEFAULT 0,
    wipes          INT DEFAULT 0,
    timeouts       INT DEFAULT 0,
    started_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at    DATETIME NULL,
    PRIMARY KEY (id),
    KEY idx_scenario (scenario_key)
) ENGINE=InnoDB;

-- %(raidtest_attempts) 单次尝试结果
CREATE TABLE raidtest_attempts (
    id              INT UNSIGNED AUTO_INCREMENT,
    run_id          INT UNSIGNED NOT NULL,
    seq             INT NOT NULL,            -- 第几次尝试
    result          ENUM('kill','wipe','timeout','aborted') NOT NULL,
    duration_ms     INT NOT NULL,
    boss_hp_min     TINYINT NULL,            -- 战斗中最深血量%（辅助评估）
    deaths          INT NOT NULL,            -- 团灭人数
    death_names     TEXT NULL,               -- 死亡角色名列表（逗号分隔）
    notes           VARCHAR(255) NULL,       -- 留给判定摘要
    PRIMARY KEY (id),
    KEY idx_run (run_id, seq)
) ENGINE=InnoDB;

-- %(raidtest_events) 战斗事件流（★ 策略验证的数据基础）
CREATE TABLE raidtest_events (
    id             BIGINT UNSIGNED AUTO_INCREMENT,
    attempt_id     INT UNSIGNED NOT NULL,
    rel_ms         INT NOT NULL,             -- 相对本次尝试开始（毫秒）
    event_type     ENUM('spell','damage','death','boss_hp','combat_start','combat_end','strategy','state') NOT NULL,
    source_guid    BIGINT UNSIGNED NOT NULL, -- 发生者
    target_guid    BIGINT UNSIGNED NULL,     -- 目标
    spell_id       INT UNSIGNED NULL,        -- 法术 id（spell/damage 事件）
    actor_entry    INT UNSIGNED NULL,        -- 生物 entry（非玩家的事件源）
    value          INT NULL,                 -- 伤害量/tick 值
    detail         VARCHAR(255) NULL,        -- 附加文本（如策略名/状态快照）
    PRIMARY KEY (id),
    KEY idx_attempt (attempt_id, rel_ms),
    KEY idx_attempt_type (attempt_id, event_type)
) ENGINE=InnoDB;
```

> 事件表（§6 的 `raidtest_events`）在 A 阶段即启用（spell/damage/death/boss_hp 等），它是策略迭代的数据基础，不是事后补丁。

## 7. 场景定义（Naxx Patchwerk 最小示例）

```cpp
// NaxxScenario.cpp（注册表由 Scenario::Register 汇总）
class NaxxPatchwerkScenario : public Scenario
{
public:
    std::string GetName() const override { return "naxx-patchwerk"; }
    uint32 GetMapId() const override      { return 533; }          // Naxxramas
    uint32 GetBossEntry() const override  { return 16028; }        // Patchwerk

    // 阵容由蓝图配置驱动（§5.1），运行时按文件加载
    std::string GetRosterFile() const override
    {
        return "mod-raidtest-roster-naxx-patchwerk.conf";
    }

    GearProfile GetGearProfile() const override
    {
        // 蓝图未指定槽位的兜底档位（init=epic 等价语义），符合"不修改装备"约束
        return GearProfile::Epic();
    }

    void ConfigureEncounter(Encounter& e) override
    {
        e.SetTimeoutSeconds(300);
        // 默认判定：boss 死亡 = kill；全团死亡 = wipe；超时 = timeout
        e.SetEngageTrigger(EncounterTrigger::Pull);   // PullAction 开战
    }
};
REGISTER_SCENARIO(NaxxPatchwerkScenario);
```

- **职责判定 hook**（`Encounter::OnBossDeath / OnAllDead`）在阶段 B 提供给需要特殊判定的 boss（如 Loatheb 之类靠机制不是靠血量的），MVP 一律用"血量为 0=kill"这个通用判据，后续 boss 按需覆写。

## 8. 配置项（mod-raidtest.conf.dist）

```ini
# 开关
RaidTest.Enabled = 1

# 测试账号前缀（模块专用，不与 rndbot 冲突）
RaidTest.AccountPrefix = "raidtest"

# 团队规模（10 / 25）
RaidTest.PartySize = 10

# 默认每次运行的尝试数
RaidTest.DefaultAttempts = 5

# 单次尝试超时（秒）
RaidTest.AttemptTimeout = 300

# 是否在 run 前强制重建阵容（角色重建/重置天赋装备）
RaidTest.ForceRecreateOnRun = 0

# 数据目录日志级别（0 关 1 摘要 2 详细）
RaidTest.LogLevel = 1
```

## 9. 命令接口（worldserver 控制台 / RA，`Console::Yes`）

```
.raidtest scenario list                      # 列出已注册场景
.raidtest scenario show naxx-patchwerk       # 显示场景元数据（阵容/配装/地图/boss）
.raidtest run <scenario> [--attempts N]      # 运行：建阵容(如缺)→登录→组队→进本→开战→判定
            [--force-recreate] [--party 10]
.raidtest status                             # 当前 run 实时状态（进行中/上次结果）
.raidtest stop                               # 中止当前 run
.raidtest report <scenario> [--last N]       # 聚合最近 N 次结果（胜率/平均耗时/死亡归因）
.raidtest compare runA runB                  # ★ 同场景两次 run 对比（胜率/时间线/总伤害）
.raidtest dump <attempt_id> [--json]         # ★ 导出单次尝试的事件流，供外部分析
```

> 游戏内 GM 命令（可选）首期不做，但注册表结构已预留（`Command::SetConsoleOnly(false)` 一条线）。

## 10. Run 生命周期（状态机）

```
IDLE ──run──▶ ROSTER_ENSURE ──▶ LOGIN_AND_GROUP ──▶ TELEPORT_AND_POSITION
                                                  │
                                                  ▼
                         ◀──(reset prop)── ATTEMPT_RUNNING
                                                  │  每 tick: AttemptObserver
                                              kill │ wipe│ timeout
                                                  ▼
                                              SERIALIZE_RESULT
                                                  │  attempts_left>0  → ATTEMPT_RUNNING (重置后)
                                                  │  跑完             → 聚合 → IDLE
```

- **ROSTER_ENSURE**：按 `RaidTestAccountRepository` 查 `raidtest_accounts`；缺则创建（查 `auth.account` → 建角色 → `PlayerbotFactory` 初始化 → 写映射）。
- **LOGIN_AND_GROUP**：对每个 guid 调 `PlayerbotMgr::AddPlayerBot`（master 取首个 bot 或空），等 `IsInWorld`，再服务端组队。
- **ATTEMPT_RUNNING**：传送至 boss 房安全点 → `CombatTrigger::Pull()` → 轮询判定。
- 粘滞状态防护：`AttemptRunner` 在传送/开战后若 `N` tick 无进展（boss 未进战斗），判定为 `aborted` 并记 notes，避免死循环。

## 11. 错误处理

| 场景 | 处理 |
|---|---|
| 账号/角色创建失败 | 终止 run，输出原因，不改动已有 raidtest 账号 |
| bot 登录超时（AddPlayerBot 后不在世界） | 等待上限 → 标记 aborted，记录缺失 guid |
| 传送失败/不在副本 | 重试一次 → aborted |
| 开战后 boss 无战斗状态 | 视为 aborted（不是 wipe），避免把流程 bug 记成战斗失败 |
| 服务器重启 | run 状态不持久化；重启后 `/raidtest status` 显示 last abort，下次 run 从 ROSTER_ENSURE 重查（账号/角色已存在则跳过） |
| 数据库写失败 | 逻辑照常跑完，结果异步重试写（尽量多采集一次） |

## 12. 测试策略

- **单元/轻量**：`RosterTemplate::Parse`、`Command` 参数解析、`Scenario` 元数据、`CombatEvent` 序列化——纯逻辑无世界依赖，可配套简单 gtest 或命令行自检（`--analyze-only` 校验场景定义不依赖 live 世界）。
- **集成（核心）**：一台本地服务器跑 `naxx-patchwerk --attempts 1`，验收清单：
  - [ ] 从零建出 10 角色（账号 `raidtest*` 存在）
  - [ ] 全员上线、组队 10 人
  - [ ] 进入 NAXX 副本地图
  - [ ] 触发 Patchwerk 战，日志出现 naxx 策略切换
  - [ ] 达成 kill/wipe/timeout 之一并落 DB
  - [ ] `raidtest_events` 有该 attempt 的 spell/damage/death 事件行（验证事件总线通）
  - [ ] 二跑复用角色、`--force-recreate` 重建生效
  - [ ] `dump <attempt_id>` 能导出事件流
- **回归**：阶段 C 的定时全量场景（§7 阶段 B/C 的自动化统计）。

## 13. 阶段规划

**阶段 A（本次）——框架 + 首场景 + 战斗事件流**
- §5 全部文件骨架；`Scenario` 注册表；`RosterManager`（建号/建角/配装/组队/传送）；`AttemptRunner` + 通用判定（血量为 0/全团死亡/超时）；`ResultStore`（run/attempt 表）+ `EventStore`（events 表）。
- **CombatEventBus 基础版**：采集 `spell/damage/death/boss_hp/combat_start/combat_end`，落 `raidtest_events`。策略事件先尝试读 mod-playerbots 既有输出，无则 A 阶段不采（留 B 验证）。
- 命令：`list/show/run/status/stop/report/dump`（dump 走 JSON）。
- 场景仅 `naxx-patchwerk`。

**阶段 B —— 策略验证深化（优化闭环的主战场）**
- **策略事件源确定**：验证 mod-playerbots `ChangeStrategy` 输出可否采集；可则并入 `raidtest_events`（`strategy` 类型），否则用 **AI 状态快照**（每 tick 记录 `GetCurrentStrategyName` 等）做反推。
- **compare 命令深化**：死亡时间线对齐、施法序列对比、boss 血量曲线、策略切换序列对比——直接回答"这次改动到底改好了什么"。≥2 次 run 对比。
- **归因报表**：死亡归因（死前最后 N 秒受到的伤害源/打断缺失/走位判断）、DPS/HPS 聚合。
- 每场景多 boss：`naxx-anub`、补全 NAXX → `ulduar-fl`、`icc-marrowgar`（逐个加场景文件）。

**阶段 C —— 自动化运维**
- 定时全场景回归（复用服务管理器模式：隔日批量跑，结果报表）；
- 胜率/死因看板（`report`/`compare` 增强）；
- 优化闭环固化：改策略 → 批量重跑 → `compare` 上一版 → 胜率/时耗收敛线。

**优化闭环工作流（贯穿 B/C）**：
```
1. .raidtest run naxx-pw --attempts 20        # 跑出基线
2. .raidtest report naxx-pw --last 20          # 死亡归因 → 找出头号死因
3. （人工）改 mod-playerbots RAID 策略
4. .raidtest run naxx-pw --attempts 20        # 重跑
5. .raidtest compare runX runY                 # 对比胜率/时间线 → 是否收敛
6. 收敛 → 提交策略改动；未收敛 → 回到 3
```

## 14. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 模块改动与上游 Playerbot 分支同步冲突 | 只新增文件、不修改既有文件；不碰 core；同步用 `sync-upstream.sh` 的 merge 模式 |
| bot AI 对无 master 团队副本表现不佳 | 这是本项目的"研究对象"而非本模块的缺陷：模块如实记录失败（wipe 也是有效结果） |
| `AddPlayerBot` 头less 登录在某些场景被 master 逻辑限制 | 复用随机 bot 的 `masterAccountId=0` 路径（已验证），并把首个角色的账号设为 `PlayerbotsAccountType::AddClass` 以走成熟路径 |
| 长 run 影响世界服务器性能 | 每 tick 只轮询少数目标；`RaidTest.Enabled` 可关；实验时世界服务器空闲即无干扰 |
| 测试账号污染正式内容 | 后缀 `raidtest*` 专用，注册表可整组重建（`--force-recreate`） |

## 15. 完成定义（Definition of Done）

1. §13 A 阶段所有文件提交、编译通过、无编译告警新增；
2. 在环境上跑通 `naxx-patchwerk` 验收清单（§12 集成项全 ✅）；
3. 结果表/命令/配置与本文档一致，README 有使用示例；
4. 管理库 docs/README 更新模块索引。