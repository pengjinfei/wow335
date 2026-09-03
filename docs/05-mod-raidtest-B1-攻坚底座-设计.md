# mod-raidtest B1：攻坚底座（设计文档）

> 日期: 2026-09-04
> 前置: A 阶段完成（模块骨架/建号装配/RosterLogin/CombatTrigger/事件总线/场景注册/编排器/命令层，全部已审查并合并 main）
> 目标 boss: Patchwerk（NAXX map 533, entry 16028，已实测坐标）

## 1. 目标

打通"补全 AI 战斗 → 真实装备 → 实例重置 → Patchwerk 可复现跑到 kill/wipe/timeout 判定"的攻坚链，**拿到第一个真实胜负判定**。

## 2. 验收标准（B1 完成判据）

```
.raidtest run naxx-patchwerk --attempts 3
```

- [ ] bot 能放技能（日志/事件流出现 bot 施法事件，不再只有 melee 近战）
- [ ] 角色装上有 NAXX 10 人 T7 档装备（ilvl ≤ 213 史诗）
- [ ] 多次尝试间副本真重置（第二次尝试能重新开打，不再 "boss already dead"）
- [ ] 最终跑出**真实 kill/wipe/timeout 之一**（不要求 kill——只要判定是真实战斗结果，B1 即完成）

## 3. 背景事实（已核实）

- **AI tick 根因线索**：`RandomPlayerbotMgr::UpdateAI`（`modules/mod-playerbots/src/Bot/RandomPlayerbotMgr.cpp:286`）`if (!randomBotAutologin || !enabled) return;` 直接早退。我们以 `masterAccountId=0` 拉入的 bot 走随机 bot 管理路径，`RandomBotAutologin=0` 使整个 AI tick 空转 → 只剩 melee 自动攻击、无施法。`Playerbots::OnPlayerAfterUpdate`（`src/Script/Playerbots.cpp:162-167`）对所有在线玩家调 `botAI->UpdateAI(diff)`，但那已是空转后的残余路径。
- **装备数据源**：`acore_playerbots.playerbots_bis_gear`（6647 行，字段 class/spec/slot/faction/phase/item_id 等）联 `item_template`（有 ItemLevel/Quality）可按 **class/spec/slot + ilvl ≤ 213** 提取 NAXX 10 人 T7 档。已验证 `Valorous Dreadnaught Helmet (40528)` = ItemLevel 213 / Quality 4（史诗）。
- **实例重置**：`InstanceSaveMgr` / `InstanceSave`（`src/server/game/Instances/InstanceSaveMgr.h`）提供重置能力；Task 7 已确认无重置时死 boss 会 abort。

## 4. B1 任务分解（三个攻坚任务 + 一个记录项）

### B1-1 bot 战斗 AI 激活

**动作**：置 `playerbots.conf` 的 `AiPlayerbot.RandomBotAutologin = 1`，实测无 master bot 是否恢复完整 AI（施法/循环）。

**副作用（已接受，记录 TODO）**：该开关会连带开启世界随机 bot 的自动登录与游荡（原 A 阶段为省开发机资源关掉它）。用户明确:先接受副作用跑通流程，**TODO 记录：跑通后研究如何禁用随机 bot 世界游荡**。

- TODO 登记位置：B1 完成后（拿到第一个真实判定时）评估。可能的禁用方向：
  1. 若 `MinRandomBots=0` 足以压制随机 bot 生成，则副作用有限——把 `RandomBotAutologin=1` + `MinRandomBots=0` 组合固化进配置模板；
  2. 若随机 bot 仍会大量生成/游荡，研究 mod-playerbots 是否有独立于 `Autologin` 的"仅激活战斗 AI、不游荡"开关；
  3. 若均无，评估在 mod-playerbots 加一个细粒度配置（B2 边界内的小源码改动）。

### B1-2 真实装备（BIS 自动提取）

**动作**：RosterBuilder 增加"装备来源 = BIS 表"路径。对蓝图**未显式指定**的槽位，按 `playerbots_bis_gear` 联 `item_template` 查询对应 (class, spec, slot, faction) 且 `ItemLevel ≤ 213` 的史诗装备填充；蓝图显式指定的槽位仍优先。

**数据流**：`RosterBuilder::ApplyGear` → 对缺省槽位调 BIS 提取器 → `Player::AddItem` → 按蓝图 gem/enchant 逻辑（无则 BIS 对应附魔或工厂兜底）。

**约束**：不改 mod-playerbots 的 BiS 机制本身；只从既有表读取数据。装备验证=查角色 inventory（如 `item_instance` 关联 `characters.guid`）确认装上了 T7。

**风险**：`playerbots_bis_gear.phase` 字段含义需确认（可能按阶段分档，ilvl 过滤可能与 phase 冲突）——若 phase 已有"NAXX 档"则直接用它，否则用 ilvl 过滤。B1 实现第一步先核对 phase 取值分布。

### B1-3 跨 attempt 实例重置

**动作**：`AttemptRunner` 在每次 attempt 结束（SERIALIZE_RESULT 后、进入下次尝试前）调用实例重置逻辑：按 `mapId 533 + 当前 instanceId` 找到 `InstanceSave` 并重置（清 boss 死亡状态、复活区域、副本进度），使下次尝试可重新开打。

**约束**：重置只影响 raidtest 使用的实例，不影响正式内容；bot 回城/重置后需重新组队传送（已有管线）。

**风险**：重叠尝试的传送时序；重置后 `Creature` 引用失效要重新解析。

## 5. 完成后的记录项（给 B2 的清单）

- [TODO] 研究禁用随机 bot 世界游荡（用户指定）
- [记录] Patchwerk 首次真实判定的结果（以便 B2 对比是否有进展）
- [记录] bot 施法事件是否进入 `raidtest_events`（验证 B1-1 后事件流仍正常）

## 6. 风险汇总

| 风险 | 缓解 |
|---|---|
| `RandomBotAutologin=1` 副作用（随机 bot 游荡） | 用户明确接受；TODO 记录禁用研究方向 |
| BIS 的 `phase` 字段语义未知 | B1-2 第一步核对 phase 分布；冲突则退回 ilvl 过滤 |
| 实例重置后引用失效/时序 | 复用 RosterLogin 的传送管线；boss 引用在开战前重新 FindBoss |
| Patchwerk 超 300s → timeout 误判伤害不足 | 首次 run 观察实际耗时，据此调超时/判断伤害档位 |