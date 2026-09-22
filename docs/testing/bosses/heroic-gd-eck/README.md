# 英雄古达克 · 凶残的艾克 Eck the Ferocious（29932，英雄限定）

## 接手摘要

- 更新日期：2026-09-20。当前状态：**勘测完成 + 阻塞已实测确认（run686）；无击杀样本。**
- 已完成：原生机制与代码审计；`creature`/`creature_formations`/GO/`instance_encounters` 数据核对；
  准备点与开怪点地形勘测（`raidtest los` 静态探针，实读地面高度）；
  **场景脚手架建好并实测跑了一场（run686，attempts=1），确认了阻塞。**
- 唯一阻塞：**艾克没有数据库 spawn（只由副本脚本运行时召唤）**，而 mod-raidtest 的
  `ResetInstance` / `FindBossNear` / `summon` 触发器三条路径都假定 boss 是一个数据库 spawn。
  run686 实测：每场都在 fixture 阶段 `scene_invalid: reset scope could not be restored` 作废，
  `duration=0ms`，**永远走不到拉怪**。
- 唯一下一步：**决定是否要改 mod-raidtest 以支持「召唤型 boss」**（需编译授权）。
- 口径：本 boss 属于古达克 5 个 boss 之一（英雄限定、侧厅、可跳过），
  台账里此前一直记 **未覆盖（遗漏）**，本轮把「为什么不能直接建场景」查清楚了，仍未取得击杀样本。

## 一、原生机制（core 审计）

`src/server/scripts/Northrend/Gundrak/instance_gundrak.cpp`：

```cpp
void OnUnitDeath(Unit* unit) override
{
    if (!instance->IsHeroic() || !unit->EntryEquals(NPC_RUINS_DWELLER) || IsBossDone(DATA_ECK_THE_FEROCIOUS))
        return;
    if (Creature* dweller = unit->ToCreature())
        if (CreatureGroup* formation = dweller->GetFormation())
        {
            scheduler.CancelAll();
            scheduler.Schedule(1s, [this, dweller, formation](TaskContext) {
                if (!formation->IsAnyMemberAlive())
                {
                    dweller->AI()->Talk(EMOTE_SUMMON_ECK);
                    instance->SummonCreature(NPC_ECK_THE_FEROCIOUS, { 1624.70f, 891.43f, 95.08f, 1.2f });
                }
            });
        }
}
```

要点：

| 项 | 值 | 依据 |
|---|---|---|
| 触发条件 | 英雄难度 + `NPC_RUINS_DWELLER`(29920) 死亡 + 艾克未 DONE | 源码 `EntryEquals(NPC_RUINS_DWELLER)` |
| 额外条件 | 该 Dweller **必须属于一个编队**（`GetFormation()!=nullptr`） | 源码 `if (CreatureGroup* formation = ...)` |
| 再额外条件 | 整组 `IsAnyMemberAlive()==false`，即三只**全死** | 源码 |
| 延迟 | 1 秒（`scheduler.Schedule(1s, ...)`），`CancelAll()` 先清 | 源码 |
| 召唤点 | **(1624.70, 891.43, 95.08, O=1.2)** | 源码字面量 |
| 召唤类型 | `instance->SummonCreature` → `WorldObject::SummonCreature(..., TEMPSUMMON_MANUAL_DESPAWN)` → `TempSummon`，**`m_spawnId == 0`** | `Object.cpp:2448/2383`；`Creature::Create` 不设 `m_spawnId`（只有 `LoadCreatureFromDB` 设） |

`boss_eck.cpp`：

| 项 | 值 |
|---|---|
| `InitializeAI` | `MovePoint(POINT_START, EckCombatStartPosition)`；`SetHomePosition(EckHomePosition)`；`SetReactState(REACT_PASSIVE)` |
| `EckHomePosition` | **(1642.712, 934.646, 107.205, 0.767)** |
| `EckCombatStartPosition` | **(1638.55, 919.76, 104.95, 0.00)** |
| `MovementInform` | 到达 `POINT_START` 后自施 `55837`（SPRING_INIT）、转 `REACT_AGGRESSIVE` |
| 技能 | `55813` Bite（victim，5s 起，8–12s 间隔）、`55814` Spit（victim，10–37s 起，8–12s）、`55815` Spring（随机目标，30 码，10–24s）、`55816` Berserk（90s 硬狂暴） |
| `SpellHitTarget` | 命中 `55815` 时 `ResetAllThreat()` 并把该目标威胁置 **1.0**（= 强制换目标，不是加仇恨） |
| 死亡 emote | 77s `Talk(EMOTE_CRAZED)` |

**Spring(55815) 是唯一的「机制」，也是本 boss 的核心难点**：它把艾克的威胁表清零并把被打中的人设为唯一威胁 1.0，
所以每一次 Spring 都会让艾克换目标。它不是「拉不拉得住」的问题，是设计上就换。

## 二、数据核对（`acore_world`，2026-09-20）

```sql
SELECT COUNT(*) FROM creature WHERE id=29932;   -- 0
SELECT COUNT(*) FROM creature WHERE id=30939;   -- 0  （Ruins Dweller 英雄 entry）
```

| 项 | 值 |
|---|---|
| `creature` 中 29932 的 spawn | **0 行**（30939 也是 0 行） |
| `creature_template` 29932 | lvl 81–82，rank 1，faction 16，`unit_flags=32768 (0x8000 = UNIT_FLAG_SWIMMING)`，`unit_flags2=2048`，`speed_walk=1.6`，`type_flags=72`，`BaseAttackTime=2000`，`flags_extra=1 (INSTANCE_BIND)` |
| `instance_encounters` | `entry=389, creditType=0, creditEntry=29932, lastEncounterDungeon=0, comment='Eck the Ferocious'` → 启动时给 29932 打上 `CREATURE_FLAG_EXTRA_DUNGEON_BOSS`（`ObjectMgr.cpp:6661`），所以 `IsDungeonBoss()==true` |
| `spell_dbc` 覆盖 | 55813/55814/55815/55816/55837 **均无行**（纯客户端 DBC，无服务端覆盖） |
| `smart_scripts` | 29932/30939 均无行（AI 全在 `boss_eck.cpp`） |

### Dweller 编队（决定「清哪几只才会召唤」）

| spawn | entry | 坐标 | 是否触发 |
|---|---|---|---|
| **127203** | 29920 | (1644.73, 936.472, 107.288) | **编队 leader** |
| **127201** | 29920 | (1651.26, 936.455, 107.277) | 编队成员 |
| **127202** | 29920 | (1643.2, 943.617, 107.276) | 编队成员 |
| 127204 | 29920 | (1708.48, 926.962, 116.094) | 单体，**不触发** |
| 127205 | 29920 | (1701.66, 951.026, 116.536) | 单体，**不触发** |
| 127206 | 29920 | (1717.3, 935.615, 117.105) | 单体，**不触发** |

```sql
SELECT * FROM creature_formations WHERE leaderGUID=127203;
-- 127203 -> 127201 (groupAI=3), 127203 -> 127202 (groupAI=3), 127203 -> 127203 (groupAI=3)
```

`groupAI=3` = `MEMBER_ASSIST_LEADER(1) | LEADER_ASSIST_MEMBER(2)`，即互相协助。
**只有这三只的编队全灭才会召唤艾克**；另三只单体 Dweller 死不死无关。

Dweller 的 SAI：`55652 Spring`（10–15s 循环，`On Target Spellhit` 把全威胁设为 0–100）、
`55643 Regurgitate`（2–7s 循环）。

GO：`192569 Eck Underwater Grate` 在 **(1622.89, 857.706, 108.755)**，
`192632 Eck Doors` 在 (1772.7, 878.415, 124.118)。两者都是 `DOOR_TYPE_PASSAGE`，
英雄难度下才 `AddDoor`（`instance_gundrak.cpp` 的 `OnGameObjectCreate`）。

## 三、地形勘测（`raidtest los` 静态探针，**实读地面高度**）

**方法**：先对每个候选点做自探针（`from == to`，取 `vmap_floor_from`）拿到真实地面 z，
再用该 z 去量对目标的 LOS。直接拿一个想当然的 z 去量会得到假结果——
本轮第一次用 z=130 扫整个房间，得出「到处都是 void」，改用自探针后才发现
真正的地面在 90–117 之间分层。这条与 START-HERE 里「探针的 z 用法」是同一个坑。

### 房间地形（实测地面高度，5 码网格）

```
        y=890  895  900  905  910  915  920  925  930  935  940  945  950  955  960
x=1615       84.9 85.9 88.2 90.1 91.5 void 111.2 106.7 106.0 101.8 100.8 104.9 void void void
x=1620  84.4 84.7 87.3 88.6 90.2 91.3 94.3 96.1 98.4 121.9 101.3 void void void void void
x=1630  84.7 87.1 88.7 90.3 void void 97.7 100.5 103.0 104.6 105.1 void void void void void
x=1640  void void void 99.7 93.9 96.6 99.1 102.0 105.0 106.2 107.4 107.2 107.3 109.4 112.7 115.9
x=1650  void void void void 104.5 97.5 98.8 101.9 105.9 107.4 107.2 107.2 107.2 108.9 112.0 void
x=1660  void void void void void void void void void void 110.2 110.7 void void void 115.9
x=1670  void void void void void void void void void 116.0 void 115.9 void 115.9 void 116.0
```

- **西侧低台/坡道**：x 1615–1635，y 890–915，z **84–92**（缓坡，可通行）。
- **中央高台（Dweller 编队所在）**：x 1640–1665，y 930–950，z **107.2**。
- 高台西北缘 (1615–1635, 915–925) z 100–111，是连接低台与高台的过渡。
- **下方水潭**：z≈84–91（西侧），x<1615 或 y<890 处大量 void（几何外）。

### 关键几何结论

| 判据 | 结果 |
|---|---|
| Dweller 编队质心 | **(1646.40, 938.85, 107.28)** |
| 对三只 Dweller 全部 `los=true` 的实测点 | **22 个**（x 1630–1655，y 925–945，z 104.3–107.7） |
| 其中距艾克开怪点 **(1638.55, 919.76, 104.95)** > 22 码的 | **(1655,935) d=22.4**、**(1650,940) d=23.3** 等 |
| **准备点选定** | **(1650.0, 940.0, 107.20)** — 对三只 Dweller 全 `los=true`；距艾克开怪点 **23.3 码**（>22 码仇恨半径） |
| 艾克开怪点对准备点 LOS | `true`（实测） |
| 艾克召唤点 (1624.70, 891.43, 95.08) 实测地面 | **88.70**（该点 z 比地面高 6.4 码，即脚本给的召唤 z 悬空；艾克会自己落到地面） |

⚠ 与斯拉德兰/莫拉比不同：**本 boss 不需要「隔离 boss 战」夹具**。原生链本身就是
「清完 Dweller 编队 → 1 秒后召唤艾克 → 艾克走到开怪点 → 转主动」，这是**完整遭遇战**。
所以本 boss 的正确口径是**正常规则**，不是隔离档。

## 四、阻塞：框架当前无法承载「召唤型 boss」（**第 2 条已实测确认**）

这是本轮真正的发现。**四条独立路径都假定 boss 是一个数据库 spawn**：

1. **`creature` 表里 29932 的 spawn 数为 0**（第一节已列），艾克只由副本脚本运行时召唤。
2. ✅ **已实测确认（run686）**：`AttemptRunner::ResetInstance()` 每场都会作废本场景。
   `found` 只在「某个重置目标 spawn 的 `data->id == BossEntry`」时置真
   （`AttemptRunner.cpp:1444`），而重置目标集合来自 `sObjectMgr->GetAllCreatureData()`
   （`AttemptRunner.cpp:1364`，只含数据库 spawn）。
   无 DB spawn 的 boss ⇒ `found` 恒 false ⇒ `ok=false` ⇒
   `Abort("scene_invalid: reset scope could not be restored")`。
   实测日志（run686）：
   ```
   AttemptRunner: ResetInstance failed for scenario boss 29932 on map 604 -
     boss_found=false spawns_clean=true prerequisites_restored=0/0 snapshot_ok=true
   AttemptRunner: attempt aborted by request (scene_invalid: reset scope could not be restored)
   Orchestrator: attempt 1788427894 complete - result=aborted seq=1 elapsed=0ms
     boss_hp_min=100% deaths=0 notes='scene_invalid: reset scope could not be restored'
   ```
   注意 `spawns_clean=true`、`snapshot_ok=true`、`prerequisites_restored=0/0`——
   除 `boss_found` 外全部通过，**孤立地坐实了「只有 boss 没有 DB spawn 这一件事不成立」**。
3. ⚠ **静态推断（未实测）**：`FindBossNear()` 解析不到临时召唤物——它只扫
   `map->GetCreatureBySpawnIdStore()`（`AttemptRunner.cpp:1236`）；而
   `Creature::AddToWorld()` 对 `m_spawnId==0` 的单位**不入该索引**
   （`Creature.cpp:311` 的 `if (m_spawnId)`）。要验证它必须先跨过第 2 条。
4. ⚠ **静态推断（未实测）**：`EngageTrigger=summon` 解决不了这个问题——
   `StartSummonTriggerPull()`（`AttemptRunner.cpp:1909`）第一行就是 `if (!entry || !ctx.boss)`，
   要求 `ctx.boss` 已存在。现有 `summon` 触发器是为**巨像**设计的：boss 有 DB spawn、
   一直在场，只是「不可攻击」，需要打它召出的 Living Mojo 来解锁。
   艾克是**相反**的情形：boss 一开始不存在，要靠清怪把他召出来。两者的语义不同，不能复用。

**已建脚手架**：`mod-raidtest-scenario-heroic-gd-eck-n5.conf.dist`（准备点/开怪点/触发方式已按勘测填好，
文件头写死了上面的阻塞原因）。运行副本已放到 `env/dist/etc/modules/`，
所以它会出现在 `raidtest scenario list` 里——**不要拿它记击杀率，它永远作废**。

**本轮没有编译任何改动**（不需要：阻塞在配置面就已复现）。

## 五、尝试记录

| run / attempt | 结果 | 时长 | 死亡 | boss HP | 有效基线 | 机制覆盖 | 证据 |
|---|---|---:|---:|---:|---|---|---|
| 686 seq1 | **aborted**（`scene_invalid: reset scope could not be restored`） | 0ms | 0 | 100% | ❌ 夹具前置不成立 | 无（未到拉怪） | 日志 `ResetInstance failed ... boss_found=false spawns_clean=true prerequisites_restored=0/0 snapshot_ok=true`；`raidtest_runs` id=686 |

这一场**不是 boss 战失败**，是**框架前置条件失败**，所以不能计入任何击杀率。
它的价值是把第三节的静态推断（第 2 条）变成实测证据。

## 六、若要继续，需要的最小框架改动（三条，待用户决定）

| # | 位置 | 改动 | 风险 |
|---|---|---|---|
| ① | `ResetInstance` | `found` 判据不能只看 DB spawn：boss 无 DB spawn 时按「前置怪齐备 + instance 状态」放行，或新增场景键声明「本场景 boss 由脚本召唤」 | 中：改的是所有场景共用的 fixture 前置，必须回归全部旧场景 |
| ② | `FindBossNear` / `ResolveBoss` | 增加按 entry 扫 `map->GetObjectsStore()`（含临时召唤物）的解析路径，或按 `GetSummonerGUID()`/副本脚本记录 GUID | 中：`FindBossNear` 被 boss 重寻址与观察会话共用 |
| ③ | 拉怪阶段 | 新增「等 boss 被召唤出来」的阶段：清完前置 → 轮询 entry 29932 出现 → 再走 `StartBossPull` | 低：新增阶段，不动既有路径 |

三者都属于**框架能力**，不是策略改动，也不涉及装备/难度/cheat。
若只做 ①，会推进到 `FindBossNear` 失败；只做 ①+②，会推进到「boss 不存在时无法拉怪」。
**三条要一起做才有意义。**

## 七、与台账的关系

- 古达克 5 个 boss 里，艾克是**唯一未覆盖**的一个；此前台账记「完全未覆盖，连勘测都没做」。
  本轮把**勘测做了、阻塞查清了**，但**仍未取得击杀样本**，所以台账状态从
  「未覆盖（遗漏）」更新为「**已勘测，被框架能力阻塞**」——这仍然不是「测出来打不过」。
- 不得把本 boss 与斯拉德兰/莫拉比/巨像/迦尔达拉的任何样本混算。

## 八、复现命令

```bash
# 数据核对
/opt/homebrew/opt/mysql@8.4/bin/mysql -h127.0.0.1 -P3306 -uacore -pacore acore_world \
  -e "SELECT COUNT(*) FROM creature WHERE id=29932;"        # -> 0（关键）
/opt/homebrew/opt/mysql@8.4/bin/mysql -h127.0.0.1 -P3306 -uacore -pacore acore_world \
  -e "SELECT * FROM creature_formations WHERE leaderGUID=127203;"

# 阻塞复现（run686 的做法；每场都作废，不要重复跑）
#   cp modules/mod-raidtest/conf/mod-raidtest-scenario-heroic-gd-eck-n5.conf.dist \
#      env/dist/etc/modules/mod-raidtest-scenario-heroic-gd-eck-n5.conf
#   bash scripts/restart_world.sh eck-r1        # 场景表只在启动时扫描
#   .raidtest run heroic-gd-eck-n5 --attempts 1
#   预期：result=aborted, duration_ms=0,
#         notes='scene_invalid: reset scope could not be restored'

# 地形（先自探针读地面，再用该 z 量 LOS；z1 必须用实测地面，不要想当然）
#   .raidtest los 604 1650.0 940.0 107.20 1650.0 940.0 107.20   -> floor=107.20
#   .raidtest los 604 1650.0 940.0 107.20 1651.26 936.455 107.277 -> los=true
#   .raidtest los 604 1650.0 940.0 107.20 1638.55 919.76 104.95  -> dist2d=23.3 los=true
```

## 2026-09-20：通用召唤型 boss 支持落地；首个有效样本

`mod-raidtest` 新增默认关闭的 `BossSpawnMode=script`：以 DB 前置怪作为 reset 合约，允许 boss
开场缺席，按 entry 解析临时 creature，并在出现后绑定事件总线 GUID。艾克还显式使用
`ScriptBossAcceptAutoEngage=1`：其原生 AI 走到开怪点后会进入当前高台队伍的仇恨范围；这是
原生自动进战，不伪装成坦克手动 pull，事件流记录 `script_boss_auto_engage:accepted`。

| run / attempt | 结果 | 时长 | 死亡 | 机制证据 | 口径 |
|---|---|---:|---:|---|---|
| 686 seq1 | aborted 0ms | 0ms | 0 | 旧框架 `boss_found=false` | 无效（历史阻塞） |
| 690 seq1 | **kill** | **79.901s** | **0** | `prerequisites_complete=25.115s` → `script boss 29932 appeared` → `script_boss_auto_engage:accepted`（4.809s recovery）→ boss HP 0% | **正常规则；首个有效样本，非稳定性结论** |

run687/688/689 是实现过程中的无效诊断：687 仍是旧 recovery 缺席判据；688 未绑定 boss 导致
误报 appearance timeout；689 已绑定且准确报出原生 auto-engage。不得计入胜率。

构建：`MTHREADS=4 ./acore.sh compiler build` 成功。构建时还修正了既有未提交
`CombatTrigger.cpp` 中未声明 `los` 的编译错误（补 `bot->IsWithinLOSInMap(boss)`）。

### 扩样：run691（5 attempts）

| seq | 结果 | 时长 | 死亡 | 有效性 |
|---:|---|---:|---:|---|
| 1 | kill | 76.774s | 0 | 有效；auto-engage 已记录 |
| 2 | kill | 90.714s | 0 | 有效；auto-engage 已记录 |
| 3 | kill | 70.036s | 0 | 有效；29932 有 18,416 条事件 |
| 4 | kill | 68.869s | 0 | 有效；29932 有 19,018 条事件 |
| 5 | aborted | 23.052s | 0 | **无效**：前置完成 19.033s 后无任何 29932 事件，`script_boss_failed: appearance timeout` |

累计有效样本：**5/5 kill、零死亡、68.869–90.714s**（run690 seq1 + run691 seq1–4）。
但 run691 seq5 是**原生召唤链未触发/未被观察到**，不计分，也意味着还不能称稳定；需继续归因。

### 召唤链复验：run692（连续 5 attempts）

**5/5 kill、零死亡**：79.855s、79.135s、74.875s、79.352s、71.692s。
每场都跨过完整原生链（前置 → instance summon → auto-engage → kill）；run691 seq5 的
appearance-timeout **未复现**。累计有效样本为 **10/10 kill、零死**，最近连续五场完整链路全通过。

当前判定提升为：**艾克正常规则稳定候选**。仍保留 run691 seq5 这一个历史无效样本，不把它删除或改记为击杀；
若要正式关闭该 boss，下一步是审查本次临时 core 诊断日志为何未进入 console sink，并决定保留/移除诊断。

### 收尾（2026-09-20）

为归因 run691 seq5 临时加入 core 的只读 Eck summon 日志已**移除**，`instance_gundrak.cpp`
恢复原样；未保留任何 core 机制改动。随后重编译成功，并跑既有 DB-spawn 场景最小烟测：
**run693 `heroic-gd-galdarah-disc-n5` kill，86.991s，零死**。这只证明默认 database 路径可运行，
不替代全旧场景回归（`TODO-8c197583`）。

艾克当前可从“稳定候选”收尾为：**正常规则已验证通过**；历史 run691 seq5 无效仍保留在记录中。
