# 英雄魔枢 / 凯利丝塔萨（Keristrasza, 26723）/ `heroic-nexus-keristrasza-n5`

## 接手摘要

- 更新日期 2026-09-10。状态：**框架阻断（无法开怪）**，与装备档位和 bot 策略都无关。
- 已完成：定位到阻断是**真机制进度门禁**并读到代码级证据；场景与坐标已就位可复用。
- 唯一下一步：需要用户决定框架方向（见「阻塞」）。在框架支持之前，本 boss 无法取样。
- 阻塞/需用户决定：她要求**同一副本实例内先杀掉另外三个 boss 且点击三个球体**。
  现有 `Scenario` 是「一个 `BossEntry` + 可选一个 `KillGateSpawn`」，做不到多 boss 链式，
  且每个 attempt 都会清实例绑定。两条可选路线写在文末。

## 可复现基线

- 装备档位 `normal5-v1`、boss 英雄难度（等级 82、`HealthModifier = 38`）、`BotCheats = ""`。
- 场景：map 576 / boss 26723 / 英雄 / 5 人 / 无前置怪 / 拉怪点 (309.0,-5.5,-15.48,3.14)
  （boss 实测生成点 (301.45,-5.46,-15.48) 正东 7.6 码）。
- 角色 guid 796–800（与本副本另外三个 boss 共用）。

## 阻断的代码级证据

run 337（1 场）：`aborted`，`notes = pull failed (boss not engaged)`，boss HP 100%，0 死亡。
拉怪动作发出了，boss 没有进战斗。原因不在坐标：

1. `src/server/scripts/Northrend/Nexus/Nexus/boss_keristrasza.cpp:100-120`

   ```
   bool CanRemovePrison() {
       for (uint8 i = DATA_TELESTRA_ORB; i <= DATA_ORMOROK_ORB; ++i)
           if (instance->GetBossState(i) != DONE) return false;
       return true;
   }
   void RemovePrison(bool remove) {
       if (remove) { me->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
                     me->RemoveAurasDueToSpell(SPELL_FROZEN_PRISON); }
       else       { me->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
                     me->CastSpell(me, SPELL_FROZEN_PRISON, true); }
   }
   ```

   她在 `Reset()` 里按 `CanRemovePrison()` 决定是否上 `UNIT_FLAG_NON_ATTACKABLE` +
   冰冻牢笼（47854）。默认状态就是**不可攻击**。

2. `nexus.h`：`DATA_TELESTRA_ORB = 5`、`DATA_ANOMALUS_ORB = 6`、`DATA_ORMOROK_ORB = 7`。

3. `instance_nexus.cpp:140-158`：这三个状态**只由** `SetData(GO_TELESTRA_SPHERE /
   GO_ANOMALUS_SPHERE / GO_ORMOROK_SPHERE)` 置为 `DONE`，即点击球体
   gameobject 188526 / 188527 / 188528。

4. `instance_nexus.cpp:106-125`：球体本身带 `GO_FLAG_NOT_SELECTABLE`，只有在对应 boss
   `GetBossState(...) == DONE` 之后才可选中。

所以链路是：杀 boss → 球体可点 → 点球体 → ORB 状态 DONE → 三个都 DONE → 她解除牢笼。
**这是正常游戏规则的一部分**（真人也必须这么走），不是 bug，也不能靠调坐标绕开。

## 机制与代码审计

| 机制 | trigger → action | 正常规则 | 运行证据 | 结论 |
|---|---|---|---|---|
| 刺骨寒冷（Intense Cold 48094/48095） | `intense cold` → `intense cold jump`（`NexStrategy.cpp:44`） | 是 | 无（未能开怪） | **未覆盖** |
| 龙侧位站位 | `keristrasza positioning` → `rear flank`（`ACTION_MOVE + 4`） | 是 | 无 | **未覆盖** |
| 水晶枷锁 / 水晶火吐息 / 尾扫 | 无专门 trigger | — | 无 | **未覆盖** |

## 两条可选框架路线（需用户决定，本轮未动手）

1. **完整链路（贴近「打通副本」的原意，工作量大）**：`Scenario` 支持有序多遭遇战
   （每个遭遇战各自的拉怪点与前置），在**同一实例内**依次进行，并在每个 boss 死后
   让 bot 使用对应球体 gameobject。需要 attempt 状态机改造 + gameobject 使用步骤。
2. **隔离形态（便宜，但结论口径要降级）**：新增场景键（例如
   `InstanceEncountersDone = 5,6,7`），夹具阶段直接把三个 ORB 状态置 `DONE` 并触发她
   `Reset()`/`SetData(entry)` 解除牢笼，只测她本人的机制。
   **口径**：这只能记「隔离 boss 战」，**不等于正常规则通关**——参照 UK 的
   `heroic-uk-ingvar-disc`（隔离 9/9）与 `heroic-uk-ingvar`（官方档 1/5）分开记账的先例。

两条路线都改 mod-raidtest（编排层），不改 boss 属性、不削弱机制。

## 交接

- 场景与坐标已就位，框架支持后可直接跑。
- 证据：run 337（`raidtest_attempts`/`raidtest_events`）+ 上面四处源码位置。
- 新会话下一条安全操作：先读 [夹具勘测](../heroic-nexus/FIXTURE-SURVEY.md) 的「进度门禁」一节。
