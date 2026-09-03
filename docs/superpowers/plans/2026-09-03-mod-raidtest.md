# mod-raidtest 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 AzerothCore Playerbot fork 上实现 `modules/mod-raidtest`——无客户端、全服务端可自动化的团本验证模块，首个场景 `naxx-patchwerk` 跑通"建角→配装→组队→进本→开战→判定→记战斗事件"闭环。

**Architecture:** 场景驱动框架。模块是独立静态模块（有 `src/` 即被 fork 的 `modules/CMakeLists.txt` 自动收集编译），只做编排、复用 mod-playerbots 的既有 AI 能力（`AddPlayerBot` 头less登录 / `PlayerbotFactory` 配装 / mapId→raid 策略自动激活 / `PullAction` 开战）。关键组件：`RosterBlueprint`(配置解析)、`RosterBuilder`(按图造角装配)、`CombatEventBus`(战斗事件采集)、`Orchestrator`(Run/Attempt 状态机)、`ResultStore`/`EventStore`(characters 库持久化)。

**Tech Stack:** C++20（AC 已启用）、AzerothCore Playerbot fork 静态模块机制、characters MySQL 库、worldserver Console 命令。

## Global Constraints

- 零核心修改：只新增 `modules/mod-raidtest/**` 文件，不碰 `src/server/` 与 `modules/mod-playerbots/` 既有文件。
- 不改 bot 行为：模块只消费 mod-playerbots 能力，不调整伤害/装备/boss 机制。
- 设计文档定稿：`docs/04-mod-raidtest-设计.md`（§5.1 蓝图格式、§6 schema、§10 状态机、§13 阶段划分是唯一权威）。
- 数据驱动：建号只允许由蓝图配置驱动（`mod-raidtest-roster-<scenario>.conf`），代码不硬编码角色构成。
- 结果写 characters 库，不新增数据库连接（沿用 `data/sql/characters/updates/` 版本化机制）。
- 本机约定（见 docs/02）：编译需先征得用户同意；用 `AC_CCACHE=true + CCUSTOMOPTIONS` 的构建链；`MTHREADS=4`。
- 命名：`raidtest_` 表前缀；`.raidtest` 命令前缀；`mod-raidtest` 模块名。
- **测试策略**：模块无单测设施，测试 = 编译通过 + worldserver 加载无 crash + FIFO 控制台跑 `.raidtest` 命令的服务端内联验证。每任务末尾给出明确的验证命令与预期输出。

---
## 文件结构总览

| 文件 | 职责 |
|---|---|
| `conf/mod-raidtest.conf.dist` | 模块配置模板 |
| `data/sql/characters/updates/2026_09_03_00_mod_raidtest.sql` | raidtest_runs/attempts/events 表 |
| `src/Module/RaidTestModule.cpp/.h` | ScriptMgr 挂载、AddRaidTestScripts 导出 |
| `src/Config/RaidTestConfig.cpp/.h` | 模块配置读取单例 |
| `src/Config/RosterBlueprint.cpp/.h` | 蓝图文配置解析 → 槽位声明 |
| `src/Bot/RosterBuilder.cpp/.h` | 按蓝图建号/建角/天赋/专业/装备/宝石/附魔 |
| `src/Bot/RosterManager.cpp/.h` | 账号角色生命周期（查/建/重置） |
| `src/Bot/RosterLogin.cpp/.h` | 登录/组队/传送（调 AddPlayerBot 等） |
| `src/Bot/CombatTrigger.cpp/.h` | 开战触发 + raid 策略激活检查 |
| `src/Scenario/Scenario.cpp/.h` | 场景基类 + 注册表 |
| `src/Scenario/Encounter.cpp/.h` | 单 boss 战斗配置（超时/判定） |
| `src/Scenario/scenarios/NaxxScenario.cpp` | `naxx-patchwerk` 场景（map 533, boss 16028） |
| `src/Observer/AttemptObserver.cpp/.h` | 每 tick 判定（kill/wipe/timeout） |
| `src/Observer/CombatEventBus.cpp/.h` | ★ core hooks → 事件流 |
| `src/Observer/CombatEvent.h` | 事件结构定义 |
| `src/Orchestrator/RaidTestOrchestrator.cpp/.h` | Run/Attempt 状态机 |
| `src/Storage/ResultStore.cpp/.h` | run/attempt DAO |
| `src/Storage/EventStore.cpp/.h` | events DAO（批量落库） |
| `src/Command/RaidTestCommandScript.cpp/.h` | `.raidtest` Console 命令 |

依赖方向（严格单向）：`Command → Orchestrator → {RosterManager, AttemptRunner, ResultStore}`；`RosterManager → RosterBlueprint → RosterBuilder`；`AttemptObserver → CombatEventBus → EventStore`；`Scenario` 被 Orchestrator 依赖。

---
### Task 1: 模块骨架 + 配置读取

**Files:**
- Create: `modules/mod-raidtest/conf/mod-raidtest.conf.dist`
- Create: `modules/mod-raidtest/src/Module/RaidTestModule.cpp`
- Create: `modules/mod-raidtest/src/Module/RaidTestModule.h`
- Create: `modules/mod-raidtest/src/Config/RaidTestConfig.cpp`
- Create: `modules/mod-raidtest/src/Config/RaidTestConfig.h`
- Create: `modules/mod-raidtest/include.sh`
- Create: `modules/mod-raidtest/README.md`（骨架）

**Interfaces:**
- Produces: `RaidTestModule::AddRaidTestScripts()`（被 worldserver 的模块静态加载调用，见 ModulesScriptLoader 生成的 `AddModulesScripts()`）；`RaidTestConfig::instance()` 单例，方法 `Enabled()`, `AccountPrefix()`, `PartySize()`, `DefaultAttempts()`, `AttemptTimeoutSeconds()`

**背景事实**（已验证）：fork 的 `modules/CMakeLists.txt` 用 `CollectSourceFiles` 自动收集 `modules/*/src` 下所有 `.cpp`；`CollectIncludeDirectories` 把各模块 src 透传为公共 include。所以模块不需要 CMakeLists.txt，且可直接 `#include "PlayerbotMgr.h"`。**PCH 对模块是注释关闭的**，无头文件预处理负担。

- [ ] **Step 1: 写配置模板**

`modules/mod-raidtest/conf/mod-raidtest.conf.dist`:
```ini
# mod-raidtest 自动化团测模块
RaidTest.Enabled = 1
RaidTest.AccountPrefix = "raidtest"
RaidTest.PartySize = 10
RaidTest.DefaultAttempts = 5
RaidTest.AttemptTimeout = 300
RaidTest.ForceRecreateOnRun = 0
RaidTest.LogLevel = 1
```

- [ ] **Step 2: 写 include.sh**

`modules/mod-raidtest/include.sh`（AC 模块约定，让 dashboard 识别模块存在）:
```bash
#!/usr/bin/env bash
## GETS THE CURRENT MODULE ROOT DIRECTORY
MOD_RAIDTEST_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/" && pwd )"
```

- [ ] **Step 3: 写配置单例**

`src/Config/RaidTestConfig.h`:
```cpp
#ifndef PLAYERBOTS_RAIDTEST_CONFIG_H
#define PLAYERBOTS_RAIDTEST_CONFIG_H
#include <string>
class RaidTestConfig
{
public:
    static RaidTestConfig& instance();
    void Initialize();
    bool Enabled() const { return _enabled; }
    std::string const& AccountPrefix() const { return _accountPrefix; }
    uint8 PartySize() const { return _partySize; }
    uint32 DefaultAttempts() const { return _defaultAttempts; }
    uint32 AttemptTimeoutSeconds() const { return _attemptTimeoutSeconds; }
    bool ForceRecreateOnRun() const { return _forceRecreateOnRun; }
    uint8 LogLevel() const { return _logLevel; }
private:
    bool _enabled{true};
    std::string _accountPrefix{"raidtest"};
    uint8 _partySize{10};
    uint32 _defaultAttempts{5};
    uint32 _attemptTimeoutSeconds{300};
    bool _forceRecreateOnRun{false};
    uint8 _logLevel{1};
};
#endif
```

`src/Config/RaidTestConfig.cpp`（用 AC 的 `ConfigMgr` 读配置，键名与 conf.dist 一致）:
```cpp
#include "RaidTestConfig.h"
#include "Config.h"
RaidTestConfig& RaidTestConfig::instance()
{
    static RaidTestConfig instance;
    return instance;
}
void RaidTestConfig::Initialize()
{
    _enabled = sConfigMgr->GetOption<bool>("RaidTest.Enabled", true);
    _accountPrefix = sConfigMgr->GetOption<std::string>("RaidTest.AccountPrefix", "raidtest");
    _partySize = sConfigMgr->GetOption<uint8>("RaidTest.PartySize", 10);
    _defaultAttempts = sConfigMgr->GetOption<uint32>("RaidTest.DefaultAttempts", 5);
    _attemptTimeoutSeconds = sConfigMgr->GetOption<uint32>("RaidTest.AttemptTimeout", 300);
    _forceRecreateOnRun = sConfigMgr->GetOption<bool>("RaidTest.ForceRecreateOnRun", false);
    _logLevel = sConfigMgr->GetOption<uint8>("RaidTest.LogLevel", 1);
}
```

- [ ] **Step 4: 写模块入口（最小：加载时在日志确认本模块存在）**

`src/Module/RaidTestModule.cpp`:
```cpp
#include "RaidTestModule.h"
#include "Playerbots.h"          // 仅验证 include 通道；后续任务再扩展
#include "RaidTestConfig.h"
#include "Config.h"
#include "Log.h"
#include "PlayerbotMgr.h"        // 验证跨模块 include 已通

void AddRaidTestScripts()
{
    RaidTestConfig::instance().Initialize();
    LOG_INFO("raidtest", ">> mod-raidtest loaded (prefix={}, party={})",
        RaidTestConfig::instance().AccountPrefix(),
        uint32(RaidTestConfig::instance().PartySize()));
}
```
`src/Module/RaidTestModule.h`:
```cpp
#ifndef PLAYERBOTS_RAIDTEST_MODULE_H
#define PLAYERBOTS_RAIDTEST_MODULE_H
void AddRaidTestScripts();
#endif
```

- [ ] **Step 5: 写 README 骨架**

`modules/mod-raidtest/README.md`：简介 + 设计文档链接 + 阶段状态一行。

- [ ] **Step 6: 编译验证（需征得用户同意后执行）**

Run: `./acore.sh compiler build`
Expected: modules 库编译通过，无 `AddRaidTestScripts` 未定义/重复定义错误；`worldserver` 链接成功。

- [ ] **Step 7: 运行期加载验证**

依次：世界服务器正常启动 → 日志出现 `>> mod-raidtest loaded (prefix=raidtest, party=10)`（先临时在 worldserver.conf 或默认配置确认读取）。
Expected: 该行出现在启动日志，无 crash。

- [ ] **Step 8: Commit**

```bash
cd modules/mod-raidtest
git init
git add .
git commit -m "feat: mod-raidtest module skeleton + config singleton"
```

---
### Task 2: SQL schema + RosterBlueprint 解析

**Files:**
- Create: `modules/mod-raidtest/data/sql/characters/updates/2026_09_03_00_mod_raidtest.sql`
- Create: `modules/mod-raidtest/src/Config/RosterBlueprint.h`
- Create: `modules/mod-raidtest/src/Config/RosterBlueprint.cpp`
- Test: `var/build/obj` 编译 + 世界启动自动应用 SQL

**Interfaces:**
- Produces:
  - `struct RosterSlot { uint8 slot; std::string name; std::string race; std::string charClass; std::string role; std::string talentSpec; std::vector<std::string> professions; std::map<std::string,uint32> gear{}; std::map<std::string,std::vector<uint32>> gems{}; std::map<std::string,uint32> enchants{}; }`
  - `class RosterBlueprint { bool Load(std::string const& filePath); std::vector<RosterSlot> const& Slots() const; uint8 Size() const; }`
  - 槽位 key 约定：装备 `MainHand/OffHand/Head/Shoulder/Neck/Chest/Back/Wrist/Hands/Waist/Legs/Feet/Ring1/Ring2/Trinket1/Trinket2`；宝石 `Head.Gem1/Head.Gem2/...`；附魔 `Head.Enchant/...`

- [ ] **Step 1: 写 SQL 迁移（三段式：attempts + runs + events，严格按设计 §6）**

`data/sql/characters/updates/2026_09_03_00_mod_raidtest.sql`:
```sql
-- mod-raidtest: 自动化团测结果表
-- 设计文档: docs/04-mod-raidtest-设计.md §6
CREATE TABLE IF NOT EXISTS `raidtest_accounts` (
    `scenario_key` VARCHAR(64) NOT NULL,
    `slot` TINYINT NOT NULL,
    `account_id` INT UNSIGNED NOT NULL,
    `character_guid` INT UNSIGNED NOT NULL,
    `class` TINYINT NOT NULL,
    `role` VARCHAR(16) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`scenario_key`, `slot`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `raidtest_runs` (
    `id` INT UNSIGNED AUTO_INCREMENT,
    `scenario_key` VARCHAR(64) NOT NULL,
    `map_id` INT UNSIGNED NOT NULL,
    `boss_entry` INT UNSIGNED NOT NULL,
    `attempts_total` INT NOT NULL,
    `kills` INT DEFAULT 0,
    `wipes` INT DEFAULT 0,
    `timeouts` INT DEFAULT 0,
    `started_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `finished_at` DATETIME NULL,
    PRIMARY KEY (`id`),
    KEY `idx_scenario` (`scenario_key`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `raidtest_attempts` (
    `id` INT UNSIGNED AUTO_INCREMENT,
    `run_id` INT UNSIGNED NOT NULL,
    `seq` INT NOT NULL,
    `result` ENUM('kill','wipe','timeout','aborted') NOT NULL,
    `duration_ms` INT NOT NULL,
    `boss_hp_min` TINYINT NULL,
    `deaths` INT NOT NULL,
    `death_names` TEXT NULL,
    `notes` VARCHAR(255) NULL,
    PRIMARY KEY (`id`),
    KEY `idx_run` (`run_id`, `seq`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `raidtest_events` (
    `id` BIGINT UNSIGNED AUTO_INCREMENT,
    `attempt_id` INT UNSIGNED NOT NULL,
    `rel_ms` INT NOT NULL,
    `event_type` ENUM('spell','damage','death','boss_hp','combat_start','combat_end','strategy','state') NOT NULL,
    `source_guid` BIGINT UNSIGNED NOT NULL,
    `target_guid` BIGINT UNSIGNED NULL,
    `spell_id` INT UNSIGNED NULL,
    `actor_entry` INT UNSIGNED NULL,
    `value` INT NULL,
    `detail` VARCHAR(255) NULL,
    PRIMARY KEY (`id`),
    KEY `idx_attempt` (`attempt_id`, `rel_ms`),
    KEY `idx_attempt_type` (`attempt_id`, `event_type`)
) ENGINE=InnoDB;
```

- [ ] **Step 2: 写蓝图数据结构头**

`src/Config/RosterBlueprint.h`（接口见上，含 `RosterSlot` 与字段，注释对照 §5.1 格式）。

- [ ] **Step 3: 写蓝图解析实现**

`src/Config/RosterBlueprint.cpp`：用 AC `ConfigMgr` 以 section 方式读（`sConfigMgr->GetSectionKeyList()` 即可拿到 `[Roster.N]` 各段），对每段 `[Roster.i]` 建 `RosterSlot`，读 `Name/Race/Class/Role/TalentSpec/Professions` 与装备/宝石/附魔键。要点：
- 槽位号为段名里的数字；
- `Professions` 按逗号 split；
- 装备匹配 `MainHand|OffHand|Head|...` 精确键；宝石匹配 `^.*\.Gem\d+$`；附魔匹配 `^.*\.Enchant$`；
- 缺省槽位（未出现的装备键）不放入 `gear`——语义=留给工厂兜底；
- `Load()` 失败返回 false 并 LOG_ERROR（路径拼 `modules/mod-raidtest/conf/`）。

- [ ] **Step 4: 编译验证**

Run: `./acore.sh compiler build`（需用户同意）
Expected: 编译通过。

- [ ] **Step 5: 验证 SQL 自动应用**

重启 worldserver，查 `SHOW TABLES LIKE 'raidtest%'` 在 characters 库出现 4 张表。
Expected: 4 张表存在；`raidtest_runs/attempts/events/accounts` 字段与 SQL 内一致。

- [ ] **Step 6: 蓝图解析冒烟**（用临时配置文件手工构造路径，配合 Orchestrator 未就绪前由 Task 3 的 RosterManager 断言 file 存在）

在 Task 3 完成前，此处只验证：蓝图文件存在 `conf/mod-raidtest-roster-naxx-patchwerk.conf`（随 Task 3 落盘）。本步只需确保模块在启动时若 `ForceRecreateOnRun` 或账号缺失才解析蓝图，避免失控。

- [ ] **Step 7: Commit**

```bash
git add . && git commit -m "feat: raidtest SQL schema + RosterBlueprint parser"
```

---
### Task 3: roster 蓝图文件 + RosterManager/RosterBuilder（建号与配装核心）

**Files:**
- Create: `modules/mod-raidtest/conf/mod-raidtest-roster-naxx-patchwerk.conf`
- Create: `modules/mod-raidtest/src/Bot/RosterManager.h/.cpp`
- Create: `modules/mod-raidtest/src/Bot/RosterBuilder.h/.cpp`

**Interfaces:**
- Produces:
  - `bool RosterManager::EnsureRoster(std::string const& scenarioKey, RosterBlueprint const& blueprint, uint8 partySize)` — 查 `raidtest_accounts`（scenario_key+slot），缺则建号建角装配后写表；返回成败。幂等。
  - `struct CreatedChar { uint32 accountId; ObjectGuid guid; }`
  - `RosterBuilder::CreateCharacter(RosterSlot const& slot, std::string const& prefix)` → `CreatedChar`
  - `RosterBuilder::ApplyGear(Player* bot, RosterSlot const& slot)` — 逐槽位 `AddItem` + 宝石 + 附魔，缺省槽位交给 `PlayerbotFactory` 兜底。

**关键依赖（已验证 API）**：`AccountMgr::CreateAccount(username, password, email)`；`Player::AddItem(uint32 itemId, uint32 count)`；`Item::SetEnchantment(EnchantmentSlot, uint32 id, ...)`；宝石与天赋/专业复用 `PlayerbotFactory::ApplyEnchantAndGemsNew / InitTalentsTree / InitSkills`（mod-playerbots 现成实现，见其 `PlayerbotFactory.h` 声明）。建角：`Player` 用 `CharacterCreateInfo` 走 `Player::Create` 或复用 addclass 路径（`RandomPlayerbotMgr::PrepareAddclassCache` 只查既有角色——所以必须自己创建）。**实现提示**：最稳路径是先 `AccountMgr::CreateAccount` 建账号，再调 `Player::Create(accountId, name, race, class, gender, hair...)` 创建角色（对照 `WorldSession::HandleCharCreateOpcode` 的 `CharacterCreateInfo` 初始化序列），随后 `PlayerbotFactory` 完成天赋/技能/专业，本模块只补装备/宝石/附魔。若 `Player::Create` 签名与 AC 版本有出入，参考 `CharacterHandler.cpp:267` 的建角流程与其调用的 `Player::Create`。

- [ ] **Step 1: 写 naxx-patchwerk 蓝图文件**

`conf/mod-raidtest-roster-naxx-patchwerk.conf`（10 人：1 战士坦 + 2 治疗 + 7 DPS，装备 id 先用设计 §5.1 的 40491-40505 示例，后续按 NAXX 掉落替换；`Head/...` 逐个给出，宝石附魔各给 1-2 个有效 id 示例，剩余槽位留空触发工厂兜底）:
```ini
[Roster.0]
Name = "Patch-Tank"
Race = "human"
Class = "warrior"
Role = "tank"
TalentSpec = "warrior_tank"
Professions = "mining,jewelcrafting"
Head = 40492
Head.Enchant = 3856
MainHand = 40491
OffHand = 40491
... (按 §5.1 完整 10 槽位; ring/trinket 等)
[Roster.1] ... (healer: priest, holy)
[Roster.2] ... (healer: druid, resto)
[Roster.3..9] ... (dps: mage/warlock/hunter/rogue/... 职业多样性)
```
> 注意：蓝图文件落地后，`RosterBlueprint::Load` 在解析时对未提供键保持 `gear` 为空（工厂兜底）。本任务需保证文件可解析。

- [ ] **Step 2: 写 RosterManager**

`src/Bot/RosterManager.h/.cpp`：
- `EnsureRoster`：对每个 slot，查 `SELECT character_guid FROM raidtest_accounts WHERE scenario_key=? AND slot=?`；命中则跳过；未命中则 `RosterBuilder::CreateCharacter` + `INSERT INTO raidtest_accounts ...`。
- 提供 `GetSlotGuids(scenarioKey)` → `std::vector<ObjectGuid>`。
- 异常：账号建失败/角色建失败 → 返回 false 并在世界日志输出原因，不动已成功槽位（部分成功语义）。

- [ ] **Step 3: 写 RosterBuilder（建角+装配）**

`src/Bot/RosterBuilder.h/.cpp`：
- `CreateCharacter`：建账号（随机密码）→ 建角色（参考 CharacterHandler 流程）→ `PlayerbotFactory(bot, 80, itemQuality自动).InitSkills()`/`InitTalentsTree()`/`InitClassSpells()` → 返回。
- `ApplyGear`：遍历 `slot.gear` → `bot->AddItem(itemId, 1)`；对每件物品：按 `slot.gems[slotName]` 的 gem item 调用 `ApplyEnchantAndGemsNew` 或节点式插到 socket（依 mod-playerbots 的实际宝石实现为准——**这块直接调 `PlayerbotFactory` 现成的宝石逻辑，避免另写**）；附魔用 `Item::SetEnchantment(SOCK_ENCHANTMENT_SLOT.., enchantId, 0, 0)`。缺省槽位标记给工厂 `AutoGear` 补齐。
- `InitTalentsBySpecNo` / `InitTalentsByParsedSpecLink` 按 TalentSpec 用（mod-playerbots 已暴露静态方法，见 `PlayerbotFactory.h:67-68`）。

- [ ] **Step 4: 编译验证 + 首次建号冒烟（需用户同意编译）**

Run: `.raidtest run naxx-patchwerk --attempts 1`（命令骨架在 Task 8 前用临时调试入口，或本任务先把 Orchestrator 的最小 run 引擎一起写完再验——见 Step 5 选择）。
Expected: 10 个 `raidtest*` 前缀账号在 auth.account；10 角色对应 guid 写入 raidtest_accounts；日志显示每角色初始化完成。

- [ ] **Step 5: Commit**

```bash
git add . && git commit -m "feat: roster blueprint file + builder/manager (create+gear)"
```

---
### Task 4: RosterLogin（登录/组队/传送） + CombatTrigger（开战）

**Files:**
- Create: `modules/mod-raidtest/src/Bot/RosterLogin.h/.cpp`
- Create: `modules/mod-raidtest/src/Bot/CombatTrigger.h/.cpp`

**Interfaces:**
- Produces:
  - `bool RosterLogin::LoginAll(std::vector<ObjectGuid> const& guids, uint32 waitTicks)` — 对每个 guid 调 `sRandomPlayerbotMgr.AddPlayerBot(guid, 0)` 或 `PlayerbotMgr::AddPlayerBot(guid, 0)`（masterAccountId=0 → 无 master 自治，已验证），轮询 `ObjectAccessor::FindPlayer(guid)` 直到 `IsInWorld`。
  - `bool RosterLogin::FormGroup(std::vector<Player*> const& bots)` — 用 `GroupMgr`/邀请 AP 组队，首个 bot 为 leader。
  - `bool RosterLogin::TeleportToRaid(std::vector<Player*> const& bots, uint32 mapId, Position const& pos)` — 服务端 `TeleportTo`。
  - `bool CombatTrigger::PullBoss(Player* leader, Creature* boss)` — `PullAction`/`AttackAction::Attack(boss)` 发起，然后校验 boss 进入 `boss->GetAI()->IsInCombat()`。
  - `bool CombatTrigger::IsRaidStrategyActive(Player* bot, std::string const& strategyName)` — 校验 `botAI->GetAiObjectContext()->GetRunner()->GetCurrentStrategy()` 含该策略（A 阶段先用日志观察，不做强校验）。

- [ ] **Step 1: 实现 LoginAll/FormGroup**

用 `AddPlayerBot(guid, 0)`（headless 登录，已验证 `PlayerbotMgr.cpp:203`），等待 `IsInWorld()` 超时上限（配置 `DefaultAttempts` 无关，这里用固定 60 tick / 5s）。组队参考 `InviteToGroupAction` 语义，直接用服务端 `Group`。

- [ ] **Step 2: 实现 TeleportToRaid + PullBoss**

- 坐标：NAXX(533) Patchwerk 房安全点（写常量；后续场景配置化）。
- `PullBoss`：让 leader bot 执行 `AttackAction::Attack(Creature*)`（真实 bot 行为），若 2 秒未进战斗则视为 aborted 信号（由 Orchestrator 处理）。

- [ ] **Step 3: 编译 + 服务级冒烟**

通过 `.raidtest run`（Task 8 命令就绪后）或临时调试入口：确认 10 bot 全部上线、形成 10 人团、传送到位、PullBoss 后世界日志出现 naxx 策略激活线。

- [ ] **Step 4: Commit**

---
### Task 5: CombatEventBus + EventStore（战斗事件流）

**Files:**
- Create: `modules/mod-raidtest/src/Observer/CombatEvent.h`
- Create: `modules/mod-raidtest/src/Observer/CombatEventBus.h/.cpp`
- Create: `modules/mod-raidtest/src/Storage/EventStore.h/.cpp`

**Interfaces:**
- Produces:
  - `enum class CombatEventType { Spell, Damage, Death, BossHp, CombatStart, CombatEnd, Strategy, State };`
  - `struct CombatEvent { CombatEventType type; uint32 relMs; ObjectGuid source, target; uint32 spellId=0, actorEntry=0; int32 value=0; std::string detail; };`
  - `class CombatEventBus { void StartAttempt(uint32 attemptId); void EndAttempt(); void Push(CombatEvent e); std::vector<CombatEvent>& Pending(); }` — 单例，节流批量 flush。
  - `class EventStore { bool InsertBatch(uint32 attemptId, std::vector<CombatEvent> const& events); }`

**背景事实（已验证）**：`AllSpellScript` 提供 `ALLSPELLHOOK_ON_CAST`（`OnSpellCast(Spell*, Unit*, SpellInfo const*, bool)`）；`UnitScript::OnDamage(Unit* attacker, Unit* victim, uint32& damage)`；`AllCreatureScript` 可捕获生物死亡。三者均不需绑定具体 entry（`IsDatabaseBound()` 为 false），直接实现为模块脚本子类即可。

- [ ] **Step 1: 定义事件结构 + 数据集队列**

- [ ] **Step 2: 实现 Bus 与 core hooks**

`CombatEventBus` 继承 `AllSpellScript`/`UnitScript`（AC 一个脚本类可同时继承多个 ScriptObject 家族的系统）——**按 AC 惯例：一个模块可注册多个脚本对象**，即分别定义 `class RaidTestSpellScript : public AllSpellScript`、`class RaidTestUnitScript : public UnitScript`、`class RaidTestCreatureScript : public AllCreatureScript`，各自在 hook 里 `CombatEventBus::instance().Push(...)`，并把 `source/target` 限定为 raidtest 阵营成员（guid ∈ 当前 attempt bot 集合）避免脏数据。

- [ ] **Step 3: EventStore 批量落库**

`attempt_id + rel_ms + event_type + source_guid + ...` 一次 `PreparedStatement` 批插（`CharacterDatabase.Execute` 支持 `InsertTask` 链）。每 500 事件或 attempt 结束 flush。

- [ ] **Step 4: 编译 + 事件冒烟**

世界启动无 crash；`run naxx` 过程中查 `raidtest_events` 有 spell/damage 行（先临时 LOG 验证 hook 命中数）。

- [ ] **Step 5: Commit**

---
### Task 6: Scenario + Encounter + NaxxScenario

**Files:**
- Create: `modules/mod-raidtest/src/Scenario/Scenario.h/.cpp`
- Create: `modules/mod-raidtest/src/Scenario/Encounter.h/.cpp`
- Create: `modules/mod-raidtest/src/Scenario/scenarios/NaxxScenario.cpp`

**Interfaces:**
- Produces:
  - `class Scenario { virtual std::string GetName() const; virtual uint32 GetMapId() const; virtual uint32 GetBossEntry() const; virtual std::string GetRosterFile() const; virtual GearProfile GetGearProfile() const; virtual void ConfigureEncounter(Encounter&); virtual Position GetEngagePoint() const; }`
  - `class ScenarioRegistry { static ScenarioRegistry& instance(); Scenario* Get(std::string const& name); std::vector<std::string> Names(); void Register(Scenario*); }`
  - `class Encounter { void SetTimeoutSeconds(uint32); uint32 TimeoutSeconds() const; void SetEngageTrigger(EncounterTrigger t); }`
  - 注册宏 `REGISTER_SCENARIO(ClassName)`

- [ ] **Step 1: 实现 Scenario/Encounter 基类与注册表**

`GetEngagePoint()` 为 Patchwerk 房安全点（`{x,y,z,o}` 常量，来自 NAXX 地形的常规安全坐标，具体数值在集成测试时校准）。

- [ ] **Step 2: 写 NaxxPatchwerkScenario**

map=533, boss=16028（已验证 Patchwerk=16028），roster 文件 `mod-raidtest-roster-naxx-patchwerk.conf`，`ConfigureEncounter` 超时 300s、`Pull` 开战、通用判定（boss 死亡=kill/全团死=wipe/超时=timeout）。注册走 `REGISTER_SCENARIO`。

- [ ] **Step 3: 编译 + `scenario list/show` 命令骨架（先手工建最小命令）**

验证 `.raidtest scenario list` 输出含 `naxx-patchwerk`。

- [ ] **Step 4: Commit**

---
### Task 7: Orchestrator + AttemptObserver（Run/Attempt 状态机）

**Files:**
- Create: `modules/mod-raidtest/src/Orchestrator/RaidTestOrchestrator.h/.cpp`
- Create: `modules/mod-raidtest/src/Orchestrator/RunContext.h`
- Create: `modules/mod-raidtest/src/Orchestrator/AttemptRunner.h/.cpp`（可并入 Orchestrator 文件保持小而独立——按依赖拆分）
- Create: `modules/mod-raidtest/src/Observer/AttemptObserver.h/.cpp`

**Interfaces:**
- Produces:
  - `struct RunContext { std::string scenarioKey; Scenario* scenario; std::vector<ObjectGuid> botGuids; std::vector<Player*> bots; uint32 runId; uint32 attemptsTotal; uint32 attemptsDone; uint32 kills, wipes, timeouts; }`
  - `class RaidTestOrchestrator { bool StartRun(std::string const& scenarioKey, uint32 attempts); void StopRun(); bool IsRunning() const; std::string Status() const; void Update(uint32 diff); }` — 单例，worldserver 每 tick 调用 `Update`。
  - `enum class AttemptResult { Kill, Wipe, Timeout, Aborted };`
  - `AttemptObserver::Tick(RunContext&, uint32 diff)` → 判定（boss 血 0=kill / 全员死亡=wipe / 超时=timeout / 战前卡壳=aborted）

**背景事实**：worldserver 每帧调 `WorldScript::OnUpdate(diff)`（模块可注册 `WorldScript` 子类驱动 Orchestrator）。

- [ ] **Step 1: RunContext + Orchestrator 状态机**

按设计 §10 实现 `IDLE→ROSTER_ENSURE→LOGIN_AND_GROUP→TELEPORT_AND_POSITION→ATTEMPT_RUNNING→SERIALIZE_RESULT→(loop)→IDLE`。每 tick 由 `WorldScript::OnUpdate` 驱动，粘滞防护（传送/开战后 N tick 无进展 → aborted，记 notes）。

- [ ] **Step 2: AttemptObserver 判定**

`boss->GetHealthPct()<=0` → Kill；遍历队内 `IsDead()` 计数=全部 → Wipe；`elapsed>=Timeout` → Timeout。三次采样确认不死循环。

- [ ] **Step 3: ResultStore 写库接入**

`run 开始` 插 `raidtest_runs`；每次 attempt 结束插 `raidtest_attempts`（含 death_names = 死亡角色名 join）；run 结束回写 kills/wipes/timeouts/finished_at。

- [ ] **Step 4: 编译 + `status/stop` 冒烟**

`.raidtest status` 显示进行中/最新结果；`.raidtest stop` 能中止。

- [ ] **Step 5: Commit**

---
### Task 8: Command 完整接通 + 端到端验收

**Files:**
- Create: `modules/mod-raidtest/src/Command/RaidTestCommandScript.h/.cpp`

**Interfaces:**
- Produces: `.raidtest scenario list|show <name>|run <scenario> [--attempts N]|status|stop|report <scenario> [--last N]|compare runA runB|dump <attempt_id> [--json]`（`Console::Yes`，参考 `PlayerbotCommandScript` 的 `ChatCommandTable` 注册）

- [ ] **Step 1: 命令解析实现**（支持 `--attempts N` 选项；`compare` 初步输出差异项；`dump` 查 `raidtest_events` 逐行打印 JSON 数组）

- [ ] **Step 2: 端到端验收清单**

在服务器上对 `naxx-patchwerk --attempts 1` 走完整验收（§12 集成项 + 事件表有数据 + `dump` 可导出 + 二跑复用角色 + `--force-recreate` 重建生效）。

- [ ] **Step 3: 修复暴露的集成问题**（坐标校准、pull 未进战斗的 aborted 判定、事件量过大节流等），确保清单全绿。

- [ ] **Step 4: docs/README 更新 + Commit**

`README.md` 使用示例（run/report/dump/compare 一行一个）；设计文档已含这部分，README 指向之。

---
### Self-Review（实施中每任务回查）

1. **Spec 覆盖**：比对 `docs/04-mod-raidtest-设计.md` §1.3（naxx-patchwerk 全链路）、§5.1（蓝图格式）、§6（schema）、§9（命令清单）、§10（状态机）、§12（验收清单）——每条都有对应 Task 落地。（§4.4 的策略事件 B 阶段做，A 阶段不阻塞。）
2. **占位符**：本计划无 TBD；`...` 仅出现在蓝图文件示例的槽位填充处，由 Task 3 Step 1 展开完整 10 槽位。
3. **类型一致性**：`RosterSlot`/`CombatEvent`/`RunContext`/`AttemptResult` 在 Task 2/5/6/7 定义的签名被 Task 3/4/7/8 一致引用；`EncounterTrigger::Pull` 与 `Encounter` 在 Task 6 定义、Task 7 消费。

---
## 执行移交

计划保存到 `docs/superpowers/plans/2026-09-03-mod-raidtest.md`（本文件）。执行方式二选一：

**1. Subagent-Driven（推荐）** - 每任务派发独立 subagent，任务间审查，快速迭代

**2. Inline Execution** - 本会话用 executing-plans 批量执行，带检查点

> 注：每次 `./acore.sh compiler build` 前必须先征得用户同意（记忆约束 consent-before-compile）。