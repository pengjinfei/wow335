# playerbots 载具支持调研（无 master 的全 bot 队伍）

> 2026-09-26，只读代码调研。没有向 worldserver 发命令，没有编译。数据来源：mod-playerbots 源码、核心脚本、`acore_world`（mysql）、客户端 DBC（`data/world/dbc/Spell.dbc`、`SpellRange.dbc`、`Vehicle.dbc`、`VehicleSeat.dbc`，用 python 按 3.3.5 布局直接解析）。
> 路径缩写：`PB/` = `azerothcore-wotlk/modules/mod-playerbots/src/`，`CORE/` = `azerothcore-wotlk/src/server/`，`RT/` = `azerothcore-wotlk/modules/mod-raidtest/src/`。行号以当前工作树为准。
> 背景：raidtest 登录 5 个 bot，都没有 master（`RT/Bot/RosterLogin.cpp:153-172`），所以 `botAI->GetMaster()` 恒为 nullptr。

## 结论先行

- **通用层有「上车 / 下车 / 施载具技能 / 开地面载具」，没有「开飞行载具」**。所有飞行（龙）逻辑都写在各副本里，而且全部以 master 的龙为锚点。
- **不依赖 master、已经能用的**：ToC5 拿枪 + 上马 + 四技能循环；Ulduar 烈焰巨兽（**只限已在车上的情况**）；ICC 炮艇炮台；ICC 普崔塞德憎恶；Razorscale 鱼叉（不是载具）；战场载具；EoE 与 Oculus 的「龙技能循环」本身。
- **依赖 master、全 bot 队伍下失效的**：Oculus 上龙 / 跟龙 / 下龙；EoE 龙的编队飞行；烈焰巨兽**上车**。
- **核心风险**：`CORE/scripts/Northrend/Nexus/Oculus/oculus.cpp:400-412`：龙的单体技能打中一个**不会飞的敌对**目标，就直接杀掉骑手。按 DB 数据，Varos、Centrifuge Construct、Urom 及其幻象怪都「不会飞」，Eregos 和他的小怪都会飞。所以**骑龙打 Eregos 不受影响，骑龙打 Varos 或构造体会被秒**（源码推断，待真人验证）。
- **推荐的第一站：Ley-Guardian Eregos**。只能骑龙打，目标全会飞（没有秒骑手的风险），龙的属性和装备无关（结果只反映 bot 行为），技能循环和“飞到 Eregos 55 码内”的代码已经有了。只需去掉 `OC/` 里 4 处 master 依赖，再补一个开怪兜底；框架只需建一个场景，用现有的键。详见 §7。

---

## 1. 通用载具代码（PB/）

### 1.1 上车 / 下车

| 位置 | 内容 | master 依赖 |
|---|---|---|
| `PB/Ai/Base/Actions/VehicleActions.h:15-31` | `EnterVehicleAction`（"enter vehicle"）、`LeaveVehicleAction`（"leave vehicle"），都继承 `MovementAction` | — |
| `PB/Ai/Base/Actions/VehicleActions.cpp:21-73` | `EnterVehicleAction::Execute`：已在车上就返回（`:24`）。**聊天命令分支**（`:27-40`）：`event.getOwner() && master && master->GetTarget()` 时，上 master 选中的那辆车。否则遍历 `"nearest vehicles"`（`:42`），跳过不可选中的（`:49`）、IoC 的炮台和投石车（`:54`）、非友方的（`:57`）、没空座的（`:60`）、**已有人的**（`:65`，`IsVehicleInUse`） | 聊天分支要 master；自动分支不要 |
| `VehicleActions.cpp:75-96` | `EnterVehicle`：40 码外放弃（`:78`）；超出交互距离就 `MoveTo(vehicleBase)`（`:85`）；**用 `vehicleBase->HandleSpellClick(bot)` 上车**（`:87`，注释说这是为了走 Ulduar 的特殊载具脚本，也就是走 `npc_spellclick_spells`，不直接调 `Unit::EnterVehicle`）；然后用 `HandleCancelMountAuraOpcode` 取消坐骑光环（`:94`） | 无 |
| `VehicleActions.cpp:98-112` | `LeaveVehicleAction`：座位必须 `CanEnterOrExit()`（`:105`），然后走 `HandleRequestVehicleExit`（`:109`），和客户端下车包是同一条路径 | 无 |
| `PB/Ai/Base/ActionContext.h:237-239, 449-451` | 注册 "enter vehicle" / "leave vehicle" | — |
| `PB/Ai/Base/ChatTriggerContext.h:93-94, 201-202`、`PB/Ai/Base/Strategy/ChatCommandHandlerStrategy.cpp:60-61` | 聊天命令触发 | 要真人发命令 |
| `PB/Ai/Base/TriggerContext.h:215-216, 439-440`、`PB/Ai/Base/Trigger/PvpTriggers.cpp:305-311`、`PvpTriggers.h:128-139` | `"vehicle near"`（附近有可用载具）、`"in vehicle"`（`botAI->IsInVehicle()`） | 无 |
| `PB/Ai/Base/Value/NearestNpcsValue.cpp:41-58`、`NearestNpcsValue.h:41-45`、`PB/Ai/Base/ValueContext.h:117-118, 429-430` | `"nearest vehicles"`（视距内）/ `"nearest vehicles far"`（200 码）：`IsVehicle()`、活着、有空座 | 无 |
| `PB/Ai/Base/Strategy/BattlegroundStrategy.cpp:67-80` | 唯一一个把通用上车挂成定时触发的策略：战场里 `timer`→enter、`random`→leave、`in vehicle`→各种战场载具技能 | 无 |

**上车机制（核心侧）**：`HandleSpellClick` 读 `npc_spellclick_spells`。ToC5 的两种马都是 `67830 Ride Vehicle`，`cast_flags=1`，**没有** `conditions`（SourceType 18）行；lance 的要求在马的脚本里（`CORE/scripts/Northrend/CrusadersColiseum/TrialOfTheChampion/boss_grand_champions.cpp:190-197`，要有 `62853 Lance Equipped` 光环）。**Oculus 三条龙没有 spellclick 行**：龙是精华物品召出来的，召唤时龙对召唤者施 `RIDE_*_DRAKE_QUE`，召唤者自动被装上龙（`oculus.cpp:340-370`）。所以 Oculus 上龙靠「用物品」，不靠点击。

### 1.2 施载具技能

| 位置 | 内容 |
|---|---|
| `PB/Ai/Base/Value/SpellIdValue.cpp:166-215`（`SpellIdValue.h:23-26`、`ValueContext.h:197, 385`） | `"vehicle spell id"::<name>`：座位要有 `VEHICLE_SEAT_FLAG_CAN_CAST`（`:174`），在 **`creature->m_spells[0..MAX_CREATURE_SPELLS)`** 里按法术名匹配（`:199-215`） |
| `PB/Bot/PlayerbotAI.cpp:4019-4102` | `CanCastVehicleSpell`：座位 CAN_CAST（`:4033`），载具技能冷却（`:4045`），有施法时间且载具在移动时返回 false（`:4059-4061`），120 码上限（`:4063`），`new Spell(vehicleBase, …)` 后跑 `CheckCast(true)`（`:4072-4086`）；`NOT_INFRONT` / `MOVING` / `TRY_AGAIN` 也算可施（`:4088-4098`） |
| `PB/Bot/PlayerbotAI.cpp:4104-4236` | `CastVehicleSpell`：需要时先把载具转向目标，本 tick 返回 false 并延迟一个 react delay（`:4158-4176`）。**由 `vehicleBase` 直接 `spell->prepare`**（`:4180-4212`），不走客户端的 `CMSG_PET_CAST_SPELL`；如果载具在移动、技能有施法时间，就停车并取消本次施法（`:4214-4220`） |
| `PB/Bot/PlayerbotAI.cpp:4238-4275`、`PlayerbotAI.h:536-540` | `IsInVehicle(canControl, canCast, canAttack, canTurn, fixed)`：按座位 / 载具标志判断 |
| `PB/Ai/Base/Actions/GenericSpellActions.h:405-480`、`GenericSpellActions.cpp:484-495` | `CastVehicleSpellAction`（按名字查 `vehicle spell id`）+ 战场子类（hurl boulder / ram / napalm / fire cannon …） |

**两个通用缺陷**：
1. `CanCastVehicleSpell` 和 `CastVehicleSpell` 开头都有 `if (!IsValidUnit(target)) return false;`（`PlayerbotAI.cpp:4024`、`:4109`），**传 nullptr 直接失败**，后面的 `if (!spellTarget) spellTarget = vehicleBase;` 永远走不到。影响：`ToCMountedAction` 在没有敌人时放 Defend 会失败（`PB/Ai/Dungeon/TOC/TOCActions.cpp:131-140`）。要对自己施法，只能显式传 `vehicleBase`，Oculus 和 EoE 就是这样写的。
2. 施法绕过了 `m_spells` 和动作条的校验：只要 `CheckCast` 通过，**还没解锁的技能也能放**。例如 Urom 没 DONE 时 `m_spells[5]` 还没填（`oculus.cpp:427-440`），`OccDrakeAttackAction` 仍然会按硬编码 ID 去放 Temporal Rift、Dream Funnel、Martyr。这是规则风险：真人做不到。Eregos 场景有 `2:3` 夹具，所以不受影响，但通用修法是检查 `spellId ∈ vehicleBase->m_spells`（S）。

**class 技能在车上被屏蔽**：`CastSpellAction::isUseful/isPossible`（`PB/Ai/Base/Actions/GenericSpellActions.cpp:186, 212`）、`AttackAction`（`PB/Ai/Base/Actions/AttackAction.cpp:137`）、`MeleeAction`（`:227`）、猎人（`PB/Ai/Class/Hunter/HunterActions.cpp:64`）、战士（`PB/Ai/Class/Warrior/WarriorActions.cpp:23`）、自定义施法（`PB/Ai/Base/Actions/CastCustomSpellAction.cpp:36`），都要求座位有 `CAN_ATTACK`。DBC 实测：Oculus 龙 VehicleId 70 → 座位 1323，flags `0x62110817`（有 CAN_CONTROL 0x800、CAN_CAST 0x20000000、CAN_ENTER_OR_EXIT 0x02000000，**没有 CAN_ATTACK 0x4000**）。ToC5 马 VehicleId 486 → 座位 5406，flags `0xe210880b`（同样没有 CAN_ATTACK）。所以在这两类车上，bot 的全部职业输出和治疗都停掉，只剩载具技能。**`AttackAction` 返回 false 还意味着 raidtest 的 `pull`（`RT/Orchestrator/AttemptRunner.cpp:380` 注释：用真实 `AttackAction` 拉怪）在车上拉不了怪。**

### 1.3 开车（移动）

| 位置 | 内容 |
|---|---|
| `PB/Ai/Base/Actions/MovementActions.cpp:241-264` | **`MoveTo` 的载具分支**：`generatePath = !vehicleBase->CanFly()`（`:245`，会飞的载具走直线、不寻路）；乘客座位直接返回（`:246`）；距离按载具计算（`:249`）；`DoMovePoint(vehicleBase, …)`（`:252`）；等待时间用 **`MOVE_RUN`** 速度（`:253`，飞行载具应该用 `MOVE_FLIGHT`，只影响延迟估算） |
| `MovementActions.cpp:75-89, 234` | **同层守卫 `IsSameFloorDestination` 在载具分支之前**，只用 `bot->IsFlying()` 豁免（`:77`）。骑龙的乘客本身不一定带 FLYING 标志，所以 30 码内、高度差超过 `max(6, 0.8·水平距离)` 的龙移动会被拒绝。**飞行载具要加豁免**（S） |
| `MovementActions.cpp:1328-1337` | `ChaseTo` 的载具分支：`vehicleBase->GetMotionMaster()->MoveChase(obj, 30.0f)`，固定追到 30 码。近战载具（ToC 马 Thrust 0–6 码）永远够不着 |
| `MovementActions.cpp:1832-1866` | `DoMovePoint`：`mm->Clear(); mm->MovePoint(0, x, y, z, generatePath)` |
| `MovementActions.cpp:2782-2783` | 在车上不做碰撞规避 |
| `PB/Bot/PlayerbotAI.cpp:6125-6161` | `CanMove()`：在车上时豁免 rooted/charmed（`:6143`），**但要求 `IsInVehicle(true)`（控制座）**（`:6158`） |
| `PB/Bot/PlayerbotAI.cpp:4341` | 施法让位判断（`JudgeMovementForCast`）对载具直接跳过 |
| `PB/Ai/Base/Actions/CheckMountStateAction.cpp:153` | 在车上不上下坐骑 |
| `CORE/game/Movement/MotionMaster.cpp:399-423` | `MoveForwards(target, dist)`：目标位置 + `dist`·(目标→自己方向)，经 `CanReachPositionAndGetValidCoords` 后发样条。Oculus/EoE 用它逼近 boss |

**飞行载具**：通用层没有「飞」的概念，只有 `MoveTo` 靠 `CanFly()` 关掉寻路。凡是真正让龙飞起来的代码（`vehicleBase->SetCanFly(true)` + `MoveFollow(masterVehicle)` / `MoveForwards(boss)`），都写在 `PB/Ai/Dungeon/OC/OCActions.cpp:128-167` 和 `PB/Ai/Raid/EoE/EoEActions.cpp:238-280`，而且都以 master 的龙为锚点。

---

## 2. 已经用到载具的副本 / 团本策略

| 内容 | 位置 | 上车 | 驾驶 | 技能 | 无 master 能否工作 |
|---|---|---|---|---|---|
| **Ulduar 烈焰巨兽**（Demolisher / Siege Engine / Chopper 及炮塔座） | 策略 `PB/Ai/Raid/Uld/UldStrategy.cpp:14-20` | `FlameLeviathanVehicleNearTrigger`（`PB/Ai/Raid/Uld/UldTriggers.cpp:62-75`）：**要求 `master` 存在且 `master->GetVehicle()`**；动作 `FlameLeviathanEnterVehicleAction`（`PB/Ai/Raid/Uld/UldActions.cpp:272-325`，`nearest vehicles far`，`HandleSpellClick` `:316`），加上分两阶段的座位分配 `ShouldEnter` / `AllMainVehiclesOnUse`（`:327-415`） | `FlameLeviathanVehicleAction`（`UldActions.cpp:52-101`）：被巨兽追时 `MoveAvoidChasing` 按四个角轮流跑（`:103-127`，走 `MoveTo` 的载具分支，**地面载具驾驶的现成样例**） | 各车技能（`:129-270`），按能量或 Pyrite 判断 | **上车不行**（trigger 要 master）；**已在车上的部分可以**（`FlameLeviathanOnVehicleTrigger` `UldTriggers.cpp:46-60` 不看 master） |
| **Razorscale 鱼叉**（GO，不是载具） | `UldStrategy.cpp:46-47`、`UldTriggers.cpp:197-237`、`UldActions.cpp:930-1010` | — | 离鱼叉最近的远程 DPS 走过去 | 发 `CMSG_GAMEOBJ_USE` | **可以**（只看 `group members`）。Skadi 鱼叉可以照这个写 |
| **EoE Malygos 三阶段**（Wyrmrest Skytalon） | `PB/Ai/Raid/EoE/EoEStrategy.cpp:13-21` | 由核心 boss 脚本把玩家装上龙，bot 不负责 | `EoEFlyDrakeAction`（`EoEActions.cpp:238-280`）：**`master` 为空直接 return**（`:240-241`）；逼近 boss 的分支被 `if (boss && false)` 关掉了（`:250`）；其余情况 `SetCanFly(true)` + `MoveFollow(masterVehicle, 3, angle)`（`:267-277`） | `EoEDrakeAttackAction`（`:282-354`，按 GUID 排序取前 N 个当治疗）+ Flame Spike / Engulf / Revivify / Life Burst（`:360-408`；Revivify 绕开 `CanCast` 直接施，`:403-406`） | **技能可以，飞行不行**。注意 EoE 的 `"group flying"` 和 `"drake combat"` **不是 EoE 自己的 trigger**：共享 trigger 上下文（`PB/Bot/Engine/BuildSharedTriggerContexts.cpp:52, 73`）里只有 Oculus 注册了这两个名字（`PB/Ai/Dungeon/OC/OCTriggerContext.h:21-22`），所以 EoE 用的是 Oculus 那个依赖 master 的 `GroupFlyingTrigger`。**不能当「无 master 骑龙」的样例** |
| **ICC 炮艇炮台** | `PB/Ai/Raid/ICC/ICCTriggers.cpp:60-95`（只有 DPS 上）、`PB/Ai/Raid/ICC/Action/ICCActions_GSB.cpp:18-40, 79-86`（炮击）、`:92-176`（上炮，`HandleSpellClick` `:168`）、`:824-836`（下炮） | 自动 | 固定位置 | 按能量阈值放 Incinerating Blast / Cannon Blast | **可以** |
| ICC 炮艇火箭背包 | `ICCActions_GSB.cpp:990-1017` | — | — | **bot 对 NPC 发 `CMSG_GOSSIP_HELLO` + `CMSG_GOSSIP_SELECT_OPTION` 的现成样例**（Zafod Boombox），Oculus 给龙 NPC 可以照抄 | 可以 |
| **ICC 普崔塞德的变异憎恶** | `ICCTriggers.cpp:418-458`、`ICCActions_PP.cpp:1489-1512`（用桌上的 GO 变身）、`:1590-1665`（`MoveTo` 驾驶 + 放 Regurgitated Ooze / Eat Ooze / Mutated Slash） | 自动（副坦） | 地面驾驶 | 载具技能 | **可以** |
| **战场**（IoC / SotA 等） | `BattlegroundStrategy.cpp:67-80`、`PB/Ai/Base/Actions/BattleGroundTactics.cpp:1680-1681, 2848-3075`（有无控制座分工、开车打门） | 通用 `EnterVehicleAction` 自动分支 | 地面 | 通用 `CastVehicleSpellAction` | **可以** |
| **ToC5 骑枪**（§4） | `PB/Ai/Dungeon/TOC/` | 自动 | **不主动开车**（只靠 Charge 位移） | Defend / Charge / Shield-Breaker / Thrust | **可以**（有局限） |
| **Oculus 龙**（§3） | `PB/Ai/Dungeon/OC/` | **要 master** | **要 master** | 不要 master | 上龙和飞行都不行 |
| Utgarde Pinnacle Skadi 鱼叉 | `PB/Ai/Dungeon/UP/UPStrategy.cpp:17-18`：`// TODO: Harpoons launchable via GameObject. For now players should do them` | — | — | — | **未实现**（不是载具，属于捡 GO→拿物品→用 GO 的链，见 `docs/testing/bosses/heroic-up/SURVEY.md`） |
| Naxx | 没有载具代码（grep 无结果） | | | | |

`PB/Ai/Raid/Uld/` 里其余的 `GetMaster()`（`UldTriggers.cpp:537, 938, 1639, 1645`，`UldActions.cpp:1404, 1838, 2010, 2164, 2707`）与载具无关，没有逐一展开。`HasGameClientMaster()` 在载具相关代码里只用来控制 debug 日志（例如 `GenericSpellActions.cpp:214`）。

---

## 3. Oculus（`PB/Ai/Dungeon/OC/`）

### 3.1 trigger / action 清单（`OCStrategy.cpp:10-47`，context key `wotlk-occ`）

| trigger（`OCTriggers.cpp`） | action（`OCActions.cpp`） | 优先级 | master 依赖 |
|---|---|---|---|
| `drake mount` → `DrakeMountTrigger`（`:32-38`）：`master && master->GetVehicleBase() && !bot->GetVehicleBase()` | `mount drake` → `MountDrakeAction`（`:42-116`）：按 {琥珀, 翡翠, 红玉} = {2,2,1} 分配（`:48`），**先扣掉 master 骑的那种**（`:52-69`），遍历组内 bot 按组位分配（`:71-94`）。有对的精华就 `UseItemAuto`（`:105`），拿着错的就销毁（`:109`），没有就 **`bot->AddItem(...)` 凭空发一个**（`:114`，绕过了给龙 NPC 的 gossip） | RAID+5 | **trigger 和 action 都要 master**（`:52-55` 取 `master->GetVehicleBase()`） |
| `drake dismount` → `DrakeDismountTrigger`（`:40-46`）：master 下龙、自己还在龙上 | `dismount drake` → `DismountDrakeAction`（`:118-126`）：`bot->ExitVehicle()`，**不看高度**（在空中下龙会摔死） | RAID+5 | 要 master |
| `group flying` → `GroupFlyingTrigger`（`:48-54`）：master 和自己都在龙上 | `occ fly drake` → `OccFlyDrakeAction`（`:128-167`）：Eregos 在场且没有 Planar Shift 时，`MoveForwards` 到 55 码内并面向他（`:137-155`）；否则 `SetCanFly(true)` + `MoveFollow(masterVehicle, 15, angle)`，3/4 圆编队（`:157-165`） | NORMAL+1 | **要 master**（`:130-134`，Eregos 分支也被这个前置条件挡住） |
| `drake combat` → `DrakeCombatTrigger`（`:56-60`）：`possible targets` 非空 | `occ drake attack` → `OccDrakeAttackAction`（`:169-326`）：用 `current target`，没有就取 `possible targets` 里**第一个已在战斗中的**（`:174-189`）；按龙种放技能（下表） | NORMAL+5 | **不要 master** |
| `unstable sphere` / `arcane explosion` / `time bomb` | Drakos 躲球、Urom 爆炸安全点、Time Bomb 散开 | — | 不要（与载具无关） |

Multiplier（`OCMultipliers.cpp`）：
- `MountingDrakeMultiplier`（`:17-34`）：**没有 master 直接返回 1.0**（`:24-26`）。有 master 时，在 master 骑着龙而自己还没上的这段时间里，除上龙以外的动作都置 0。作者注释（`:19-23`）：不压住的话，0.5 秒的物品施法会被打断，精华进入 15 秒冷却，龙也不来。**这一条去掉 master 后必须保留。**
- `OccFlyingMultiplier`（`:36-45`）：只要在龙上，**除 `OccFlyDrakeAction` 外所有 `MovementAction` 置 0**，不看 master。无 master 时 `OccFlyDrakeAction` 又直接 return，结果龙原地悬停，什么都不做。
- `EregosMultiplier`（`:97-106`）：Planar Shift 期间停止龙攻击。

龙技能（`OCActions.cpp`）与 DBC（`Spell.dbc` / `SpellRange.dbc`）：

| 龙 | DB 技能（`creature_template_spell` 第 0/1 格） | 第 6 格（Urom DONE 后由脚本填，`oculus.cpp:427-440`） | bot 逻辑 |
|---|---|---|---|
| 琥珀 27755 | Shock Lance 49840（单体伤害，60 码）、Stop Time 49838（区域） | Temporal Rift 49592（单体，60 码） | `:216-240`：Shock Charge 超过 8 层就引爆；目标激怒就放 Stop Time；否则引导 Rift |
| 翡翠 27692 | Leeching Poison 50328（单体 DoT）、Touch the Nightmare 50341（单体） | Dream Funnel 50344（`TARGET_UNIT_TARGET_ALLY`） | `:242-301`：毒不足 3 层或剩余不到 4 秒就补；Touch 冷却 10 秒；对血最少的队友龙引导 Funnel，太远就 `MoveForwards` 过去（`:283-289`） |
| 红玉 27756 | Searing Wrath 50232（单体）、Evasive Maneuvers 50240（自身） | Martyr 50253（区域，友方） | `:303-326`：Evasive Charges 满 10 层放 Maneuvers；5 层以上且 Maneuvers 剩 10 秒以上放 Martyr；其余时间放 Searing Wrath |

### 3.2 让无 master 的 bot 能用龙的最小改动

**(a) 拿精华**。现状是 `MountDrakeAction` 直接 `AddItem`（`OCActions.cpp:114`），这是上游 playerbots 已有的做法，本身不需要 master。两条路：
- 最小（S）：保留 `AddItem`，但加上与 gossip 相同的前提：`instance->GetData(0 /*DATA_DRAKOS*/) == DONE`。给龙 NPC 只在 Drakos DONE 后才出 gossip（`oculus.cpp:166-171`），且给多少次都行（`StoreEssence` `:219-229`）。这样与真人能拿到的东西等价，但跳过了「走到 NPC 面前」。
- 合规（M）：照 `ICCActions_GSB.cpp:990-1017` 写：走到 Verdisa 27657 / Belgaristrasz 27658 / Eternos 27659，`HandleGossipHelloOpcode`，再在 `PlayerTalkClass` 的菜单里找 action 为 `GOSSIP_ACTION_INFO_DEF+3`（「给我一条龙」，`oculus.cpp:190, 207`）的那一项，把它的 list id 发给 `HandleGossipSelectOptionOpcode`。三位 NPC 在底层大厅（z≈360），离 Eregos（z≈655）很远，这条路要求 bot 骑龙从大厅飞上去，所以隔离场景先用最小方案。

**(b) 召龙 / 上龙**（S）：
- `DrakeMountTrigger` 改成：无 master 时 `bot->GetMapId()==578 && !bot->GetVehicle() && <需要龙的阶段>`。「需要龙的阶段」最小可以写成：视距内能找到 Eregos（`AI_VALUE2(Unit*, "find target", "ley-guardian eregos")`）且 Urom DONE；或者组里已经有人在龙上（组员有人骑着 27692/27755/27756）。
- `MountDrakeAction`：`master` 为空时不扣 master 的份（`:52-69` 跳过），5 个 bot 按 {2,2,1} 分配。
- `MountingDrakeMultiplier`：无 master 时改用同一个「该上龙了且还没上」谓词，而不是直接返回 1.0（否则就是作者说的，施法被打断）。
- 召出后龙会自己对召唤者放骑乘法术（`oculus.cpp:353-366`）；5 秒内没人上就飞走（`:459-472`）。因为本副本 `IsEncounterInProgress()` 恒 false，龙首帧不会被遣散（`:420-455`）。

**(c) 飞到目标并用技能**（S–M）：
- `GroupFlyingTrigger` 改成：无 master 时只要在龙上就触发。
- `OccFlyDrakeAction`：把 `masterVehicle` 的前置检查（`:130-134`）移到编队分支里，这样 Eregos 分支（`:137-155`）无 master 也能跑。编队锚点在无 master 时换成组长 / 主坦的龙；锚点就是自己时，不跟随。
- **顺带修 `MoveForwards` 的参数**：`mm->MoveForwards(boss, range - distance)`（`:146`）在 `distance > range` 时传的是负数，终点会落在 boss 的**另一侧**、离 boss `distance - range` 码处。应该传 `range`（终点在 boss 朝向自己的一侧、离 boss 55 码处）。翡翠龙追治疗目标的 `:287` 同理，要复核。
- 开怪兜底：`OccDrakeAttackAction` 只挑已在战斗中的目标（`:182`），而 raidtest 的 `pull` 走 `AttackAction`，在车上直接返回 false（§1.2）。所以无 master 时要补一条：没有战斗目标时，把 Eregos 这类「可攻击的 boss」当目标（S）。也可以在框架侧加一个「载具开怪」键，只设置 bot 的目标值、不代替 bot 放技能（S），但前者更符合「行为归 playerbots」。
- 通用层：`IsSameFloorDestination` 对「控制着会飞的载具」要豁免（§1.3，S）。

**(d) 下龙**（M）：`DrakeDismountTrigger` 无 master 时的条件可以是：没有需要龙的目标、脱战、龙离地面 ≤ 3 码。在这之前，先让龙 `MoveTo` 到地面点（`GetMapHeight`）。`DismountDrakeAction` 自己也要加高度检查。**隔离的 Eregos 场景不需要下龙**（打完就结束），可以放到最后做。

### 3.3 其它 Oculus 要注意的

- `OccFlyingMultiplier` 会把 `MasterlessAvoidAoe` 等所有移动压成 0。Eregos 的 Planar Anomaly（30879，15 秒后 Planar Blast）没有躲避逻辑，龙只能硬吃。
- 龙死了骑手会从高处掉下来，observer 里的「bot 死亡」实际上多是龙死或摔死，口径要注明。
- 龙的属性与 bot 装备无关，ilvl 档位对龙战没有意义，结果只反映 bot 行为。

---

## 4. ToC5 骑枪（`PB/Ai/Dungeon/TOC/`）

| trigger（`TOCTriggers.cpp`） | action（`TOCActions.cpp`） | 优先级 | master |
|---|---|---|---|
| `toc lance`（`:12-37`）：不在车上，100 码内 **Warhorse 35644 和 Battleworg 36558 都在**，没装备 Argent Lance 46106 | `ToCLanceAction`（`:14-89`）：包里有枪就换上（`:61-71`），没有就走到枪架 GO 196398 并 `Use`（`:76-86`） | RAID+5 | 无 |
| `toc ue lance`（`:39-53`）：马都没了，还拿着枪 | `ToCUELanceAction`（`:91-102`）：`EquipUpgradeAction` 换回原武器 | RAID+2 | 无 |
| `toc mount near`（`:66-80`） | `ToCMountAction`（`:178-241`）：`nearest vehicles` 里找最近的、友方、有空座的 35644/36558（`:185-207`），`HandleSpellClick`（`:232`），再取消坐骑光环 | RAID+4 | 无 |
| `toc mounted`（`:55-64`） | `ToCMountedAction`（`:104-176`）：从 `possible targets no los` 取**第一个**属于冠军或小怪 entry 的目标（`:111-129`）；Defend 不足 3 层就补（`:131-140`）；目标超过 5 码放 Charge（`:145-153`）；目标有 Defend 就放 Shield-Breaker（`:155-166`）；最后放 Thrust（`:168-173`） | RAID+6 | 无 |

- **不依赖 master**。`docs/testing/bosses/heroic-toc5/README.md` 记录：竞技场的 24 匹马不清掉，`wotlk-toc` 就会让 bot 去拿枪骑马。这说明在全 bot 队伍里「拿枪 + 上马」这段是会自己跑起来的。
- DBC 射程：Charge 68282 **5–25 码**，Shield-Breaker 62575 5–25 码，Thrust 68505 **0–6 码**，Defend 66482 作用于自身。马的 `m_spells` 是 68505 / 62575 / 68282 / 66482（`creature_template_spell`）。
- 缺口：
  1. **没有驾驶**。`ToCMountedAction` 不 `MoveTo`，目标在 25 码外时四个技能全部失败。其它通用移动要么被 `AttackAction` 屏蔽，要么走 `ChaseTo` 的载具分支固定追到 30 码（`MovementActions.cpp:1335`），所以马会停在射程外（S：目标在 25 码外时 `MoveTo` 到 15 码处；Charge 冷却中时贴到 5 码内打 Thrust）。
  2. 目标选择是「第一个」，不看距离和 Defend 层数（S）。
  3. Defend 在没有敌人时传 `target=nullptr`，被 §1.2 的通用缺陷挡掉（S，传 `vehicleBase`）。
  4. **践踏（trample）在 playerbots 里完全没有**（`grep -ri trample PB/` 无结果）。核心判据（`boss_grand_champions.cpp:668-701`，作者自己标了 hackfix）：冠军下马、步行去找新马时（`EVENT_FIND_NEW_MOUNT`，每 200 ms 检查一次），**5 码内有玩家骑着本阵营的马**（部落队伍是 Battleworg，联盟队伍是 Warhorse，`:684`），冠军就被晕 15 秒（67867）。马被骑上时还会自挂 Trample 光环 67865（`:153-158`）。步行的冠军带 `NON_ATTACKABLE` + 全免疫（`:560-563`），不会出现在 `possible targets` 里，bot 不会靠过去。要补的 action（M）：找 `UNIT_FIELD_MOUNTDISPLAYID==0`、活着、带 NON_ATTACKABLE 的冠军（entry 在 `availableTargets` 里），把马 `MoveTo` 到它身上（< 5 码），分工上每只步行冠军派一个 bot。另外三只冠军要**同时**处于下马状态才进入地面阶段（`instance_trial_of_the_champion.cpp`，见 `heroic-toc5/SURVEY.md §1.1`），所以还要让「先下马的」被持续压住。
- 框架侧缺口见 `heroic-toc5/SURVEY.md §1.4`（任一 entry 当 boss、progress `>=` 判开战、以实例数据判完成、播报员 gossip 走 `sScriptMgr`），每项都是 S。

---

## 5. 核心风险：Oculus 龙秒骑手（`oculus.cpp:400-412`）

```cpp
void SpellHitTarget(Unit* target, SpellInfo const* spell) override
{
    for( uint8 i = 0; i < 8; ++i )
        if (me->m_spells[i] == spell->Id)
        {
            if (target && target->IsAlive() && !target->CanFly() && target->IsHostileTo(me) && !spell->IsTargetingArea())
            {
                if (Unit* charmer = me->GetCharmer())
                    Unit::Kill(charmer, charmer, false);
            }
            break;
        }
}
```

**触发条件（全部同时成立）**：
1. 施法者是这条龙本身（`SpellHitTarget` 是施法者 AI 的回调）。bot 的 `CastVehicleSpell` 就是 `new Spell(vehicleBase, …)`（`PlayerbotAI.cpp:4180`），真人通过动作条施放也一样；
2. 法术 ID 在龙的 `m_spells[0..7]` 里（DB 的第 0/1 格，加上 Urom DONE 后填的第 5 格）；
3. 命中的目标活着、**`!CanFly()`**、对龙敌对；
4. 法术**没有任何效果是区域目标**（`SpellInfo::IsTargetingArea`，`CORE/game/Spells/SpellInfo.cpp:1070-1076`）。

满足时杀死 `me->GetCharmer()`。龙被控制座上的乘客 charm（`CORE/game/Entities/Vehicle/Vehicle.cpp:430` `SetCharmedBy(unit, CHARM_TYPE_VEHICLE)`），所以 charmer 就是骑手。

`Creature::CanFly()` = `GetMovementTemplate().IsFlightAllowed() || IsFlying()`（`CORE/game/Entities/Creature/Creature.h:87`）。其中 `IsFlying()` = 带 `MOVEMENTFLAG_FLYING | MOVEMENTFLAG_DISABLE_GRAVITY`（`Unit.h:1720`），移动模板先查 `creature_movement_override`（本副本 0 行），再查 `creature_template_movement`（`Creature.cpp:3146-3152`）。英雄模式用的是 difficulty entry 的模板。

**单体（会触发）**：Shock Lance 49840、Temporal Rift 49592、Leeching Poison 50328、Searing Wrath 50232、Touch the Nightmare 50341（效果 3 以施法者自己为目标，不是区域）。
**不会触发**：Stop Time 49838（区域）、Martyr 50253（区域，且目标是友方）、Evasive Maneuvers 50240（自身）、Dream Funnel 50344（友方）。

**`creature_template_movement` 实测**（`mysql -uacore -pacore acore_world`）：

| entry | 名字 | Flight | 有没有模板行 | 运行时飞行 | 骑龙用单体技能打它 |
|---|---|---|---|---|---|
| 27447 / 31559 | Varos Cloudstrider | — | 两个 entry 都没有 | `boss_varos.cpp` 里没有 `SetCanFly` / `SetDisableGravity`；`creature_template_addon.bytes1=0` | **秒骑手** |
| 27641 / 30905 | Centrifuge Construct | — | 两个 entry 都没有 | 光环 50088 Energy Link（aura 23，周期触发），不是飞行 | **秒骑手** |
| 27655 / 31560 | Mage-Lord Urom | — | 两个 entry 都没有 | 传到中心读条爆炸时 `SetCanFly(true)` + `SetDisableGravity(true)`（`boss_urom.cpp:287-288`），期间 `CanFly()` 为真，但他此时不可攻击 | 平时**秒骑手** |
| 27642–27653 | Urom 的幻象怪 | — | 都没有 | — | **秒骑手** |
| 27654 / 31558 | Drakos | — | 都没有 | — | 秒骑手 |
| 27656 / 31561 | **Ley-Guardian Eregos** | **1** | 两个 entry 都有 | bytes1=50331648（悬停） | **不受影响** |
| 28276 / 30991 | Greater Ley-Whelp（Eregos 召的） | **1** | 有 | — | 不受影响 |
| 30879 | Planar Anomaly（Eregos 召的） | **1** | 有 | 脚本再设一次飞行（`boss_eregos.cpp:225-226`） | 不受影响 |
| 27638 / 30903 | Azure Ring Guardian | **1** | 有 | — | 不受影响 |
| 28236 | Azure Ring Captain（Varos 召的） | **1** | 有 | — | 不受影响 |

**结论**：
- **Eregos 战不受影响**：boss 和他召出的两种小怪都 `Flight=1`。
- **Varos 龙背战在当前核心上打不了**：原设计要骑龙打构造体和 Varos，但他们都「不会飞」，任何单体龙技能命中都会秒骑手，只剩琥珀的 Stop Time 和红玉的 Martyr 这类区域技能不触发。这段代码从 `d4a58700d` 之前就在（git log 只看到 clang-tidy 和格式整理的提交），看起来是防止「骑龙打地面怪」的防刷设计，但把 Varos 这一关按设计要打的目标也罩进去了。**要先由真人 GM 骑龙用 Searing Wrath 打一只构造体，确认是否属实**；属实的话，按 memory「服务端缺陷在核心 fork 修」在核心 fork 里放行 Varos 和构造体（例如 entry 白名单，或改成只对 `Drakos` / 大厅地面怪生效）。
- Urom 本体战原设计就是下龙打的，不受影响；骑龙在外环台之间转场时，对幻象怪用单体技能也会秒骑手。

---

## 6. Skadi 鱼叉（非载具，附带）

`PB/Ai/Dungeon/UP/UPStrategy.cpp:17-18` 是 TODO。链路（`docs/testing/bosses/heroic-up/SURVEY.md:165-188`）：打死 Harpooner → 点尸体旁的 GO 192539 拿到物品 37372 → 到东端发射器 192175/6/7 → 在 Grauf 悬停的 10 秒窗口内使用。可以照 Razorscale 的写法（`UldActions.cpp:930-1010`）加 ToC 枪架的 `GameObject::Use`（`TOCActions.cpp:76-86`）来写，全程不依赖 master，规模 M，和载具支持无关。

---

## 7. 推荐实施顺序

「第一站」选 **Eregos**：信号最干净（只能骑龙打、目标全会飞、结果不受装备影响），改动最小（只动 `OC/` 的 4 个函数，外加两处通用小修），框架只需一个用现有键的场景。

| # | 步骤 | 位置 | 规模 |
|---|---|---|---|
| 0 | **真人 GM 核实**（不写代码）：① 在 Oculus 用精华召龙、上龙；② 骑龙用 Searing Wrath 打一只 Centrifuge Construct，看骑手死不死（§5）；③ 在 Eregos 高台附近召龙，确认不会被遣散 | 真人会话（`docs/testing/HUMAN-SESSION.md`） | S |
| 1 | 通用小修：`CanCast/CastVehicleSpell` 的 null target 回退到 `vehicleBase`（`PlayerbotAI.cpp:4024, 4109`）；`IsSameFloorDestination` 对控制飞行载具豁免（`MovementActions.cpp:77`）；载具分支用 `MOVE_FLIGHT` 估算延迟（`:253`）；（可选）施载具技能前校验 `spellId ∈ m_spells` | `PB/Bot/`、`PB/Ai/Base/Actions/` | S |
| 2 | Oculus 无 master 上龙：`DrakeMountTrigger` 与 `MountingDrakeMultiplier` 改用谓词「map 578、Drakos DONE、没在车上、需要龙（视距内有 Eregos 或组里已有人骑龙）」；`MountDrakeAction` 无 master 时跳过扣减；`AddItem` 加上 Drakos DONE 前提 | `OCTriggers.cpp:32-38`、`OCMultipliers.cpp:17-34`、`OCActions.cpp:42-116` | S |
| 3 | 无 master 飞行：`GroupFlyingTrigger` 在龙上即触发；`OccFlyDrakeAction` 的 Eregos 分支不再依赖 `masterVehicle`，修正 `MoveForwards` 参数（`:146`，复核 `:287`）；编队锚点换成组长或主坦 | `OCTriggers.cpp:48-54`、`OCActions.cpp:128-167` | S–M |
| 4 | 龙背开怪：`OccDrakeAttackAction` 没有战斗目标时选可攻击的 Eregos | `OCActions.cpp:174-189` | S |
| 5 | 建场景 `heroic-oc-eregos-h5g`：`FixtureInstanceData=0:3,1:3,2:3`，准备点放在 Cache 高台 (1015.06, 1051.09, 605.62)（待 los 与地面高度实测），`EngageConfirmInstanceData=3:1`，`BossEntry=27656`。首轮先量中间量：上龙人数和耗时、龙到 Eregos 的距离分布、各龙技能施放次数、龙死亡和摔死次数，然后才看击杀 | `env/dist/etc/modules/`，`RT/` 不改代码 | S |
| 6 | 安全下龙：先把龙降到地面，离地 ≤ 3 码再 `ExitVehicle`；`DismountDrakeAction` 加高度检查。链式场景才需要 | `OCActions.cpp:118-126` | M |
| 7 | EoE Malygos 三阶段：把步骤 3 的「无 master 锚点 / 逼近 boss」抽成两副本共用的函数，启用 `EoEFlyDrakeAction` 的 boss 分支（`EoEActions.cpp:250` 的 `&& false`）。EoE 借用的是 OC 的 trigger，步骤 3 改完后它会一起受影响，要回归 | `PB/Ai/Raid/EoE/` | S |
| 8 | ToC5 骑枪：驾驶（25 码外 `MoveTo`，Thrust 贴到 6 码内）、按距离选目标、践踏步行冠军（新 action）、三只同时下马的分工；框架四个 S 键（见 `heroic-toc5/SURVEY.md §1.4`）。可以先不改 bot，建一个冒烟场景只打第一组小怪，量 Defend / Charge / Thrust 的施放次数 | `PB/Ai/Dungeon/TOC/`、`RT/` | M（践踏）+ 4×S（框架） |
| 9 | 烈焰巨兽无 master 上车：`FlameLeviathanVehicleNearTrigger` 去掉 master 依赖，改成「巨兽在场、附近有空车」 | `UldTriggers.cpp:62-75` | S（团本，当前不在 5 人范围） |
| 10 | Varos 龙背形态：取决于步骤 0 的结论。确认后在核心 fork 修 §5 的判据；bot 还要会三维躲 Energize Cores 的 100 码扇形（M），外加打构造体的分工 | `CORE/scripts/.../oculus.cpp:400-412`、`OC/` | M–L |
| 11 | Urom 链式（骑龙在 3 个外环台之间转场、下龙打幻象怪）、Oculus 全程；Skadi 鱼叉（§6） | `OC/`、`UP/` | L；鱼叉 M |

**边界说明**：步骤 1–4、6–10 都是 bot 行为，放在 playerbots 开发分支。步骤 5 只是编排，不给 bot 发物品、不代替 bot 上龙，也不代替 bot 放技能（memory「mod-raidtest 框架边界」）。步骤 2 里保留上游的 `AddItem` 属于「与 gossip 等价」的简化，结论里要注明；想完全合规就做 §3.2(a) 的 gossip 方案。
