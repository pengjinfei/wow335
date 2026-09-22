# 英雄岩石大厅 / Tribunal of Ages（map 599）

状态：r32 同配置已有 1/5 真实 Brann lifecycle DONE（run745 kill；run746/run748/run750/run751 动态 wipe）；不稳定，不能视为 Tribunal 或 HoS 通关。

- 2026-09-21 diagnostic cycle：隔离 telemetry binary 已以项目 `env/dist` 安装前缀四线程构建完成；受控替换 r32 后已 ready/IDLE，并实际加载 `heroic-hos-tribunal-event-n5`。它只含 tank-assist 诊断。run752/attempt `1788427975` 是一次明确排除 lifecycle 分母的 execution smoke：前置 141.567 秒完成、真实 gossip 0/1 于 163.285/187.472 秒，终态为 436.028 秒动态 wipe、5 deaths、boss_hp_min=100%。诊断二进制日志中 `tribunal-tank-assist` 及 `tribunal-tank-assist-action` 均为 0 行；这场没有复现/覆盖 run751 的空目标接管条件，故既不能在候选集、调度竞争或 LOS 间裁决，也不能把本场 wipe 当策略结果。已受控停掉隔离 server 并确认 r32 恢复为 ready/IDLE。事后源码核查发现 telemetry 使用 `LOG_DEBUG("playerbots", ...)`；默认诊断日志没有该级别输出，因此 0 行反映日志级别不可见而非条件未触发。已仅将隔离 telemetry 的两处实际日志点从 `LOG_DEBUG` 提升为 `LOG_INFO`（头文件无日志点）；`git diff --check` 与隔离 `worldserver -j4` 重建通过。仍无行为变更；已受控替换 r32，隔离 INFO telemetry server ready/IDLE 且已加载 Tribunal scenario。已启动唯一一次、排除 lifecycle 分母的 INFO execution smoke run753/attempt `1788427976`；30 秒时仍 prerequisites/hp_min=100%，但已确认 telemetry 可见且无行为变更：tank-assist 记录 `attackers=3`、`active=true` 后 action 选中 27970/27971、`los=true result=true`。有界 60 秒后，前置 160.191 秒完成、真实 gossip 0/1 于 166.826/191.008 秒到达；telemetry 已累计 247 trigger/12 action 行，并首次出现 4 条 `current=0`，证明可观测空当前目标分支。随后按行号与 phase 定位：动态 gossip 后的 2855–2857 是 `attackers=3,current=0,active=true` 连续两 tick，紧接 `TankAssistAction target=27983,los=true,result=true`，之后 current=27983。该场实际覆盖了空当前目标分支并证明既有 tank-assist 可调度、可选中且 LOS 成功；与 run751 的 23 秒缺口不符，故不支持“恒定的 trigger/action 竞争或 LOS 失败”。`tank_target=0` 是空-current 诊断分支刻意不取该 value 的记录口径，不能读为候选遗漏。run753 已终态为 440.359 秒动态 wipe、5 deaths、boss_hp_min=100%，仍明确排除 lifecycle 分母；共 597 trigger/77 action 行、7 次 positive-attacker empty-current active 记录。该样本的空当前目标 handoff 能立刻选中并 Attack 成功，故完成了诊断目标：run751 的 23.082 秒首伤→接战缺口不是恒定的 `TankAssist` 候选/调度/LOS 管道断路；仍不能从一次成功 handoff 推出为何 run751 偶发长缺口。隔离 server 已停止；r32 已确认 ready/IDLE。原 `mod-playerbots` 工作树仍保留外来 11 文件未提交集合，未将诊断改动带回。只读 DB 关联复核 run751：三 Protector 204/205/206 于 401.045/401.065/402.572 秒死亡；821 在 402.654 秒已 `victim=0` 但 select=206，且 403.660 秒起 engine=1/select=0，吻合既有长缺口起点。为让诊断可同 DB `rel_ms` 对齐，隔离 worktree 增加纯观测锚点：`CombatEventBus` 记录实际 `_attemptStart` 的 `app_ms`，tank-assist 两日志记录同一 `steady_clock - GetApplicationStartTime()` 的 `getMSTime()`；差值可对齐 attempt `rel_ms`（仅毫秒截断）。隔离 `worldserver -j4`/diff-check 通过，run754/attempt `1788427977` 实测输出 anchor `app_ms=44958`，验证 instrumentation 已执行；但它在 300.006 秒前置 clearing timeout 终态（2 roster deaths、hp_min=100%、无 gossip/动态，明确排除 lifecycle），故没有可作 time-aligned handoff 比较的样本。诊断 server 已停，r32 已恢复 ready/IDLE。run754 对 run753 的只读前置对照不产生策略变量：同一 spawn `126746` Lightning Construct (low 8) 在 run753 于 102.124 秒死亡、全员存活并于 160.191 秒完成前置；run754 在该目标先降为 2/5 接敌、随后两名 roster 死亡，重试降为 1/3 接敌并反复 LOS reject，未能清除。该“同 binary”前提随后被审计推翻：run753 在先前诊断 source 上运行；run754–756 的隔离 source 被改指向 clean `mod-raidtest` HEAD，缺少 active r32 module 工作树中 809 行未提交的 script-spawn Tribunal orchestration（Brann 延迟出现、preclear 时 boss absence、follower hold/auto-engage guard 等）。因此 r754–756 的三种前置异常不能归为随机前置暴露、也不能与 run753/r32 作策略或 telemetry 对照。时间观测不改行为；第二次隔离 smoke run755/attempt `1788427978` 也实测输出 anchor `app_ms=33042`，但 204.147 秒以 `pull failed (boss not engaged)` 前置终态（1 roster death、hp_min=100%、无 gossip/动态），明确排除 lifecycle，仍无 handoff 可量。连续两场 time-aligned diagnostics 都被既有前置路径截断（run754 为 300.006 秒 clearing timeout；run755 为末只 low-10 LOS/pull failed），故不得重复相同 smoke 来碰运气，也不得将其归因到 telemetry/Tribunal 行为。诊断 server 已停，r32 已恢复 ready/IDLE。随后对调度层只读排除一个看似可解释的间歇条件：`tank assist` relevance=50，而 `Engine::DoNextAction(minimal=true)` 会跳过 <100 的 trigger/action；但 `PlayerbotAI::AllowActive()` 对 dungeon/raid（以及 in-combat）无条件 true，因此 map-599 的 821 不会因随机 activity throttling 进入 minimal tick。故不能把 run751 23 秒 gap 归因为 low-relevance minimal-mode 饥饿。更关键地，run751 403.660–440.736 秒每秒 state 都是 `in_combat=true, engine=1`：`DoNextAction()` 每次都会先以 `attackers` 非空为唯一条件把 non-combat engine 切回 combat 并 return；没有切换因而可推知这些检查的 `attackers` value 为空。run753 则直接记录正 attackerCount=3 后即时 handoff。静态追踪已将 `AttackersValue` 的可能空化收敛到明确 gate：group member 的 `ThreatenedByMeList` 仅在 member→attacker 小于 `sightDistance` 时加入；随后 `RemoveNonThreating()` 又以 `IsValidTarget(unit, bot)` 过滤，而它强制 **tank→attacker `IsWithinLOSInMap`**。进一步以 core threat-manager 与 run751 event 只读排除前门：`AddThreat` 会把 creature reference 写入 victim 的 `GetThreatenedByMeList`；221 已在425.530 秒伤822，且822在424.957 秒先伤221（因此既有 combat/threat relation，又有组内 tap），821→822约29码、221→822约18码，均低于 sightDistance。故余下合理空化 gate 收敛为**以821为基准的 `CanSeeOrDetect`/`IsWithinLOSInMap`**（后二者均在 `IsValidTarget`）；DB 无该 LOS/visibility 字段，不能判断其时变原因或放宽 LOS。关键修正：LOS 已在 AttackersValue（不是只在 AttackAction）发生，正可解释 engine 不切换。为只观测这个残余 gate，已仅在隔离 `AttackersValue.cpp` 的既有拒绝分支加 map-599/in-combat tank `tribunal-attackers-reject` INFO（同 `app_ms`，entry、`CanSeeOrDetect`、LOS）；它只在 target 已入集合却被 `IsValidTarget` 拒绝时输出，不影响返回/筛选。隔离 diff-check 与 `worldserver -j4` 成功；全树 codestyle 仍只见既有 core 文件告警。该精确观测已作为新变量受控启动一次、明确排除 lifecycle 的 diagnostic：run756/attempt `1788427979`，正常规则/无行为改动，时间 anchor 已实测输出 `app_ms=33493`。run756 未进动态：64.585 秒以 `prerequisite_invalid: boss missing or engaged before clearing completed` 终态（0 roster death、hp_min=100%；Brann low-98 已有 victim/threat），明确排除 lifecycle；因此新 rejection telemetry 无 run751-shaped 输出，也无策略结论。三次新诊断均在不同前置异常处截断，按约定停止 diagnostics、不重试。诊断 server 已停，r32 已恢复 ready/IDLE；保留仅隔离 telemetry。只读 diff 已确认 clean diagnostic harness 漏掉 active r32 的 script-spawn preclear guards，正能解释 run756 的 Brann 过早 engagement；故这三场都不再用作任何 bot 行为判断。只读 provenance 核实 r32 binary 含 active harness 独有的 `script_spawned` reset 与 `could not hold followers before script boss appearance` literals；clean diagnostic binary 不含后者，确认 r32 使用 active module 而非 clean HEAD。为恢复同 harness 且保持 playerbots telemetry 隔离，已只把 isolated core source 的 `modules/mod-raidtest` symlink 改回 active r32 module worktree（不修改其16项外来变更），而 `modules/mod-playerbots` 仍指向 isolated telemetry worktree。首次常规 `worldserver -j4` 未重编译已替换 symlink 后的 raidtest objects（active source时间戳早于旧 objects，binary仍缺 follower-hold literal），故改在**隔离 build artifact**上 `--clean-first -j4` 强制重建；600秒上限时仍在编译且被工具终止，隔离 diagnostic binary 已按 clean-first 移除，未可执行。r32 未受影响且仍ready/IDLE。cycle35续建由19%推进到55%后再到窗口上限；cycle36继续同一隔离 `-j4` build 并在100%成功链接 worldserver（此前仅既有 `PartyMemberValue.h` missing-override warnings）。provenance 已验收：isolated core 的 raidtest symlink=active r32 module、playerbots symlink=isolated telemetry；新 binary 同时含 active harness 的 `script_spawned` reset 与 `could not hold followers before script boss appearance`，及三条 isolated `tribunal-*-` telemetry literals；AttemptRunner/AttackersValue objects和binary时间戳均本次重建，两个 relevant diff-check 通过。随后作了受控 replacement/startup gate：先保存原r32 binary至 `/tmp/wow335-worldserver-r32-before-active-harness-diag-cycle37`，替换诊断binary并由restart脚本停旧server；诊断server未留存进程且启动log为空，故立即复制backup并重启r32。r32 已再次 ready/IDLE。进一步在不替换r32的前提下对diagnostic binary运行 `--dry-run`，它在约12秒、playerbots config加载中以 SIGSEGV(11)/rc=139 终止（末尾仅到 `Playerbots: ListSpellsAct...`）；`--help` 正常(rc=0)，说明不是Mach-O/配置路径无法启动。无 crash report 可供堆栈；诊断binary的startup gate失败，绝不执行Tribunal observation run。cycle38 只读比较发现 isolated playerbots 虽同HEAD，却只带三处base telemetry改动，漏掉 active r32 的8个既有 HoS/ReachTarget paths（51 additions/3 deletions）；这违反“保持r32行为基线”，也可能影响运行一致性，虽无证据称它是config-load SIGSEGV根因。已仅将这8个**既有r32**文件复制到isolated worktree（不触原11 paths），现isolated diff为12 paths=active 11项行为基线加三处observation telemetry，`diff --check`通过。cycle39 以 `-j4` 重编译上述修正，仅重编译8个HoS/ReachTarget关联objects并成功链接。新binary仍含 active follower-hold 与 `tribunal-attackers-reject` literals；受控替换后启动gate通过：PID 87469、playerbots config 14.127秒完成、`ListSpellsAction caches initialized`，world ready，并加载 `heroic-hos-tribunal-event-n5`；FIFO 确认 IDLE。这一次对照表明补齐r32 playerbots行为基线后 SIGSEGV 不再出现；单次修复不能断言精确因果，但已使该binary满足startup gate（仍不将其外推为Tribunal策略结论）。当前server为verified isolated observation binary、正常规则。cycle40已启动唯一一次 active-harness observation-only diagnostic：run757/attempt `1788427980`（`--attempts 1`，明确排除lifecycle分母）。有界60秒后仍在 prerequisites，elapsed=64.383秒、hp_min=100%、无终态；tank-assist INFO已可见（例如attacker=1/current=27971），但也见leader对 Lightning Construct 两条 `could not initiate attack ... no LOS/invalid target`。cycle41 再有界等待60秒后，run757/attempt `1788427980` 仍active，已完成前置179.606秒、recovery3.006秒，真实 script gossip 0/1 于182.612/206.821秒，状态为 observing/elapsed=223.223秒、hp_min=100%。`HoldFollowerAttackTagged` 实际held 4 followers，正验证本次使用active r32 script-spawn harness；但仍不得把active样本当lifecycle。cycle42 又有界60秒后仍 observing（elapsed=383.308秒、hp_min=100%），但本次有效active-harness动态样本再覆盖空-current handoff：app_ms=553608 为 `attackers=3,current=0,active=true`，同毫秒 action 选27983且 `los=true,result=true`；下一tick（521ms后）current=27983。该观测与run753一致、不复现run751长gap，只能再排除**恒定**tank-assist/action/LOS管道故障，不能解释偶发gap。cycle43 有界读到终态：run757/attempt `1788427980` 在479.629秒以动态 wipe结束（5 deaths、boss_hp_min=100%，仍明确排除lifecycle）；已归档完整diagnostic log `/tmp/wow335-worldserver-hos-tribunal-active-harness-diag-cycle39-run757-terminal.log` 并恢复原r32，server ready/IDLE。该场 active-harness telemetry=766 trigger/98 action/55 rejection 行、10次正attacker empty-current active；所有55个已收集且real-threat target的reject都为 `visible=true,los=false`（非visibility），entry包括27972及后期27984/27985。它首次直接实测剩余gate可发生：tank-relative **LOS** 会从 AttackersValue 删除候选；但本binary使用active r32 raidtest而无先前clean-harness的CombatEventBus app_ms anchor，故不能把reject精确对齐run rel_ms、更不能证明它就是run751长gap的实例。与即时handoff并存，结论仅是LOS过滤为已观测的间歇候选空化机制，不能据此放宽LOS。cycle44 的归档行序关联补强但不越界：preclear 的27972 LOS rejects（app_ms274530–281786）均在 `prerequisites_complete` 前；gossip1后出现动态rejections。尤其app_ms=506435 同一world tick先记录三条27983 `visible=true,los=false` reject，随后同tick `attackers=2,current=0,active=true`；action仍可在别的eligible target立即handoff。因active harness未记录attempt-start app_ms，不能将该绝对clock转成精确rel_ms，也不能称该tick为run751的空-Attackers engine gap；但它是直接的时序证据：LOS过滤和tank的空current可在同tick共存，而非纯事后推测。无证据支持绕开/放宽LOS。cycle1静态追踪修正了“不同候选来源”的假设：`TankAssistAction::GetTargetName()` 固定为 `tank target`；`TankTargetValue::Calculate()` 的 smart strategy 调 `TargetValue::FindTarget()`；后者**直接读取 `GuidVector "attackers"`**，再按策略选其一。因此app_ms=506435 action选27984不是绕过AttackersValue，而是27983被LOS剔除、27984仍在同一Attackers vector；这也严格证明该tick `current=0` 不等于空Attackers。`TankAssistTrigger`仅以另一个`attacker count`正值和空current激活，不能替代engine-sync的`attackers`空化证据。run751 403.660–440.736的engine=1推断仍只适用于其独立每秒state证据。cycle2 静态复核缓存时序：`AttackersValue` 构造为 `ObjectGuidListCalculatedValue(..., 1*1000)`；`CalculatedValue::Get()` 最多每1000ms重算、其余读取同一cached vector。`PlayerbotAI::DoNextAction()` 的noncombat→combat engine-sync直接读该vector；`AttackerCountValue::Calculate()`也直接读同一个vector并只作alive/distance计数。因此run757 app_ms=506435 的 `attacker count=2` 与action从attackers选27984是同一非空snapshot，进一步排除“trigger来自另一个候选集”。缓存最多可制造约1秒的陈旧读，不能单独解释run751 403.660–440.736约37秒持续engine=1；要成立只能是每次1000ms刷新持续算空。run751的秒级state采样不足以精确给出每次cache刷新，但与该持续空化解释相容。cycle3 完成 `hasRealThreat`/LOS 静态审计。`RemoveNonThreating`仅会因 map不同、`hasRealThreat`或`IsValidTarget`删候选；前者纯即时四项（in-world、alive、非poly、非friendly），无定时/缓存。run757 rejection telemetry的日志守卫本身要求`hasRealThreat=true`，故那55条绝非该gate。run751的821/822在gap内仍互相造成伤害，至少排除822当时的dead/out-of-world/friendly/poly；但不能由此排除其它候选。`IsValidTarget=IsPossibleTarget && IsWithinLOSInMap`；core LOS每次立即以双方hit-sphere/碰撞高度调用 `Map::isInLineOfSight`，不维护可等待“刷新”的LOS cache。因此持续37秒空化若属LOS，必须是位置/地图几何/phase等持续使即时射线失败，而非旧LOS值滞留。cycle4 只读DB position/spawn复核：run751在403.660、412.687、423.692、427.705、438.735、440.736、441.740秒的821坐标均固定`(929.03,361.04,203.78)`；其余近战小组也近乎固定，只有远端822/824有小幅位移。动态新增spawn原点相对821为Stormcaller210=41.122码、Protector215=42.720码、Custodian221=40.997码（Z差约2.38）；它们随即攻击远端队员，821仍无目标。此确证长gap内tank没有以移动改变LOS几何，但仅记录了敌方spawn位置、没有每秒敌方位置/LOS射线，不能判断其追击后的实际几何或把距离当LOS结论。run757 rejection日志同样只有entry/visible/los而无双方坐标，不能回填。cycle5 已只在 `/tmp/mod-playerbots-tribunal-diag` 的既有 `tribunal-attackers-reject` INFO 行扩展**纯观测**字段：bot/unit XYZ和双方phase mask；仍只在map599、in-combat tank、同map、hasRealThreat且已有target被拒绝时执行，未改变任何筛选/返回/策略。此变量可在未来直接区分几何位置与phase，不再从spawn距离推断；active r32 worktree未触。isolated diff-check通过。cycle6 已以`-j4`增量重建：仅重编译isolated `AttackersValue.cpp`、链接worldserver成功。provenance gate通过：core links仍为active r32 raidtest+isolated playerbots，新binary同时含active follower-hold literal和扩展reject `bot_pos/unit_pos/phase` literal；fresh object/binary时间戳与两relevant diff-check均通过。r32仍IDLE，尚未替换/启动/运行。cycle7 受控startup gate通过：r32 binary已先保存 `/tmp/wow335-worldserver-r32-before-geometry-phase-diag-cycle7`，替换后旧PID9884正常退出，isolated PID19220以RelWithDebInfo ready；playerbots config=13.902秒、`ListSpellsAction caches initialized`，Tribunal scenario已加载且FIFO=IDLE。当前运行的是verified geometry/phase observation binary、无行为变更。cycle8 已启动唯一 geometry/phase observation：run758/attempt `1788427981`（`--attempts 1`，明确排除lifecycle）。有界60秒后仍prerequisites，elapsed=59.343秒、hp_min=100%、无终态；INFO tank-assist正常可见，但尚无rejection geometry记录可分析。cycle9 有界60秒后run758仍active，已进动态：scripted gossip1=211.298秒，observing elapsed=232.814秒、hp_min=100%。前置达到真实gossip，故geometry/phase telemetry具备有效动态采集条件，但本场仍排除lifecycle且不得由active样本预判。cycle10 再有界60秒后仍 observing（elapsed=393.362秒、hp_min=100%）。本窗tank-assist稳定以27983为current/tank target并多次`los=true,result=true`；末一条`result=false`发生在current=target=27983且attacker=1，符合AttackAction已攻击同target的拒绝路径，不能当LOS或候选结论。cycle11 终态：run758/attempt `1788427981`=479.307秒动态wipe、5 deaths、boss_hp_min=100%，明确排除lifecycle；完整log归档 `/tmp/wow335-worldserver-hos-tribunal-geometry-phase-diag-cycle7-run758-terminal.log`，r32 backup已恢复ready/IDLE。新变量得到40条reject：38×27983（app_ms395753–571923）与2×27984；**全数 `visible=true,los=false,phase=1:1`**。27983在reject期间三维距离从82.54降至32.22码仍LOS false（27984=61.12），故直接排除phase mismatch，也证明并非仅超距；实际map碰撞/几何射线可在同phase、近至32码时持续阻止tank候选。这是run758的直接机制证据，但没有run751的同tick坐标，不能声称同一几何实例或据此放宽LOS。诊断预算已用完。cycle12 静态审计现有移动路径：generic `ReachTargetAction`只以`current target`为移动目标；run751的问题恰是Attackers空→current target空，故它不会触发。`possible targets no los`则在100码内收集可见、有效但不要求map LOS的敌人，足以发现被AttackersValue删掉的27983/4/5；但直接复用generic reach会缺少本场景的group安全约束。下一步唯一候选是**map599 tank LOS-reacquire**正常移动：仅当in-combat、Attackers空、current空，且27983/4/5正攻击存活同组成员时，从`possible targets no los`取最近者；再额外要求该敌人距存活治疗≤heal range，才以PathGenerator/`ReachCombatTo`靠至正常combat距离（不Attack、不改target优先级、不放宽LOS）。该条件把run751的“tank离开近战组、敌在治疗侧”变为向队伍回接，避免run489式远点追怪。cycle13 注册/安全审计通过实施门槛：`ApplyInstanceStrategies(599)` 将`wotlk-hos`同时加进combat与non-combat engines，故可覆盖run751 engine=1；HoS action/trigger contexts与`InitTriggers`已有直接接入模式。恢复node将用`ACTION_RAID+5`（65），低于既有Searing Gaze `ACTION_EMERGENCY+10`（100），不抢紧急避险。`ReachCombatTo`已有same-map/`CanMove`/PathGenerator与normal|incomplete|shortcut路径早退；新action仍须显式拒绝`stay`，并在trigger/action双层检查tank、combat、empty attackers/current、存活同组victim、存活healer范围和Tribunal三entry，避免`possible targets no los`把未参战敌带入。cycle14 已实施唯一变量于active r32 HoS集合（7 paths）：`TribunalLosReacquireTrigger/Action`双层复用同一严格target finder；只在tank/in-combat/not-stay/Attackers空/current空、27983/4/5攻击存活同组成员且该敌距存活治疗≤heal range时，从`possible targets no los`选最近者并`ReachCombatTo`，不Attack、不设置target、不改优先级/LOS。contexts注册且strategy以`ACTION_RAID+5`接入。`MTHREADS=4` worldserver build成功（重编HoS contexts/strategy/actions/triggers并链接）；`diff --check`通过。cycle15 r34 los-reacquire binary 已受控restart：旧r32 PID40704正常退出，新PID63841 ready，playerbots config=11.889秒、`ListSpellsAction caches initialized`，Tribunal scenario加载且FIFO=IDLE。当前server为唯一行为变量r34；原r32 rollback binary仍保存 `/tmp/wow335-worldserver-r32-before-geometry-phase-diag-cycle7`。cycle16 已启动唯一r34 execution smoke：run759/attempt `1788427982`（`--attempts 1`，明确排除lifecycle）。有界60秒仍prerequisites，elapsed=59.354秒、hp_min=100%、无终态；仅见既有前置`4/5 engaged`后party approach retry，尚不满足动态LOS-reacquire验收条件，也不能从前置读出变量效果。cycle17 有界60秒后run759仍active且进动态，observing elapsed=224.206秒、hp_min=100%；前置已越过，具备r34 execution验收条件，但当前无逐trigger日志，不从active状态猜测变量是否触发。cycle19终态：r34 run759/attempt`1788427982`=525.633秒 kill、0 deaths；但预声明execution smoke，明确排除lifecycle，不改r32 1/5。log归档`/tmp/wow335-worldserver-hos-tribunal-r34-los-reacquire-cycle15-run759-terminal.log`，r32已恢复ready/IDLE。DB唯一强候选窗：391.766秒821 combat/engine1/current0/victim0/moving=false，392.767变moving=true，393.767已combat engine/melee选214；214/215=392.621生成，215=393.626伤821，tank(948.78,377.88)→(956.38,377.44)。新action是唯一no-current状态调用ReachCombatTo的HoS node且静态不Attack/target/LOS bypass；但DB不记214在392–393的victim或action dispatch，default follow也可移动，故仅称与触发一致、不能验收strict finder实际触发；0死kill不归因。cycle20 已在active r34 action增加唯一INFO dispatch telemetry：仅finder成功时，在既有`ReachCombatTo`之后记录app_ms、target entry、victim low、最近存活治疗距离、调用前双方XYZ及`moved`返回；不影响target finder、动作、返回或LOS。`MTHREADS=4`仅重编HoSActions并成功链接，diff-check通过。cycle21 literal/provenance复核后受控restart通过：旧r32 PID85103正常退出，新r34 telemetry PID96282 ready，`ListSpellsAction caches initialized`、Tribunal scenario加载且FIFO=IDLE。当前server为r34+dispatch INFO，原r32 rollback仍`/tmp/wow335-worldserver-r32-before-geometry-phase-diag-cycle7`。cycle21 已启动唯一排除lifecycle的dispatch smoke：run760/attempt`1788427983`，`--attempts 1`。10秒status为ATTEMPT_RUNNING/prerequisites、9.338秒、hp_min=100%，仍是正常4/5 pull approach retry；不得从此前置状态读telemetry或效果。cycle22 有界60秒后run760仍active：观察阶段169.566秒、hp_min=100%；前置recovery_complete=27.185秒、真实gossip0=167.978秒，且`HoldFollowerAttackTagged`实际held4，验证active harness。刚进动态，尚无dispatch INFO/效果结论；本场仍排除lifecycle。cycle23 再有界60秒后run760仍observing=325.823秒、hp_min=100%；真实gossip1=192.193秒。当前完整server log的`tribunal-los-reacquire`为0行，故截至本动态时点strict finder/action均未实际dispatch（不是日志级别不可见：已验binary literal且INFO）；不能将无行误称变量失败或成功。本场仍排除lifecycle。cycle24终态：run760/attempt`1788427983`=470.622秒动态wipe、5 deaths、boss_hp_min=100%，AttemptObserver与Orchestrator/IDLE相互确认；明确排除lifecycle，不改r32 1/5。完整日志归档`/tmp/wow335-worldserver-hos-tribunal-r34-dispatch-telemetry-cycle21-run760-terminal.log`；全场`tribunal-los-reacquire`仍为**0行**，故严格finder/action未发生，run759的391–394秒移动不能归因r34，run760 wipe也不能评价它。已复制rollback并受控重启r32（PID20931 ready/IDLE）。r34候选保留在source仅供后续有新证据的受控验证；不得计入lifecycle或称已验收。

## 固定口径

- Heroic、normal5-v1、5 人、`AiPlayerbot.BotCheats = ""`、`GearProfile=none`。
- 不改装备、cheat、难度或副本脚本；不用 fixture 删除单位。
- `mod-raidtest` 仅处理前置清怪、真实 gossip、观察与正常团队 skull 标记；不调用 `DoAction`、`SetBossState`、强制攻击、设目标或修改仇恨。
- 场景 `heroic-hos-tribunal-event-n5`：Brann 28070，前置为 126738、126739、126744、126746、126749、126750；事件状态 `4:3,2:3`，Brann 跟随开启，超时 900 秒。动态观察/团队 skull 条目为 27983、27984、27985、28265、30898。
- **新时间预算基线**：`PrerequisiteTimeoutSeconds=300`。这只扩展 harness 对六段正常前置清怪的观察窗口（原默认 180 秒会在最后一只已接敌时截断），不改任何游戏规则；与旧 180 秒前置结果分账。

## 非统计历史

- **run714**：17.395 秒曾被误记为 kill，Brann 实际死亡；护送 NPC 死亡优先判 wipe 后已修，永不计样本。
- **run720**：12 个前置 spawn 一次性清除，180 秒 `prerequisite_failed: clearing timeout`、零死亡；证明这不是可用的单段前置边界。
- **run721**：6-spawn 边界下 382.979 秒、2 death，但 tick 从死亡/换图 bot 临时取 instance script 而报 `missing instance script`；是框架伪中止，不计。
- **run725**：稳定绑定版首次复跑仍在 180.007 秒前置超时、零死亡，未开始事件。126750 已实际参战；原因是框架把治疗 bot 正常以坦克为当前目标误判为“没有拉到该怪”。
- **run727**：改为只验证正常战斗参与后，仍在 180.000 秒前置超时、零死亡，未开始事件。前五个前置死亡，126750 已在 160.741–178.490 秒持续攻击坦克，但没有死亡事件；这不是 instance-script 或 gossip 失败，也不能计入动态波次样本。

## 稳定 instance binding 与前置参与判据

- 事件型场景在 `BossPosition` 确认全员已进入 map 599 后，捕获该 `InstanceMap` 的 `InstanceScript*`；attempt 开始时清空，事件 tick 不再从任一 bot 的当前地图重取。若起始捕获失败，明确中止为 `scripted_event_failed: instance script unavailable at event start`。
- run725 的前置假失败另修为：只验证每个存活成员已正常 `IsInCombat()`，不再要求每人的当前攻击目标都是该前置怪。这样仍能拒绝 run661 型“只有坦克进战”，但不会把正常治疗目标当成未参与；不改变 bot 的目标、技能、移动或仇恨。
- 上述两项均已四线程增量构建，r10 worldserver 运行该二进制。全仓 codestyle 仍因既有 core 文件非零；本次文件未出现在诊断，且 `git diff --check` 通过。

## 首个有效 lifecycle 样本：run726 / attempt 1

- **447.981 秒 wipe、5 deaths、Brann 存活**；这是正常规则的实际战斗失败，不是 gossip、instance script 或完成状态的伪中止，不能计 kill。
- 前置六只全死，最后一只 126750 于 **139.932 秒**死亡；恢复完成于 **162.482 秒**。
- 真实 gossip phase 0 于 **162.483 秒**记录；阶段 `4:3` 已观察到，随后真实 gossip phase 1 于 **186.710 秒**记录。`2:3` / DONE 未到达。
- 动态伤害来源包括 Dark Rune Protector 27983、Stormcaller 27984、Iron Golem Custodian 27985、Searing Gaze 28265、Kaddrak 30898；另有 Dark Matter Target 28237。死亡记录只有 death snapshot，尚不能将每名玩家死亡严格归到单一动态来源。
- 因此当前瓶颈是实际动态波次战斗。skull 标记本身不能证明策略有效。

## 300 秒前置预算复验：run728 / attempts 1–3

- seq1：**441.512 秒 wipe、5 deaths**；六只前置 129.159 秒完成，真实 gossip 0/1 分别为 148.196 / 172.399 秒，Brann 无死亡。动态来源 27983、27984、27985、28237、28265、30898 均有伤害事件。
- seq2：147.509 秒、1 death，`prerequisite_failed: roster casualty before boss pull`；未启动事件，不混入动态样本。
- seq3：**517.172 秒 wipe、5 deaths**；六只前置 176.615 秒完成，真实 gossip 0/1 为 196.067 / 220.267 秒，Brann 无死亡。相同六类动态来源均参战。
- 因而新时间预算下 **2/3** 场通过前置并到达两次真实 gossip；两场有效 lifecycle 都在动态阶段 5 人团灭，且没有 instance-script 伪中止。它支持“当前瓶颈是实际动态战斗”，但 2 个样本仍不足以量化策略效果或完成率。

## playerbot 策略审计（只读）

`WotlkDungeonHoSStrategy` 只给 Krystallus 注册 Ground Slam → Shatter Spread，并给 Sjonnir 注册 Lightning Ring；
Tribunal 段落仅有注释，明确提到英雄难度或许需要 focus targeting、以及 DPS 可能在坦克建立仇恨前冲入，**没有**
Tribunal trigger、action 或 multiplier。故 run726 不能归因到某个现有 Tribunal 动作，也不能以 mod-raidtest 补偿。
下一轮先以现有事件/伤害数据量化动态目标、坦克接手和 Searing Gaze；只有有可复现的 playerbot 决策缺口，才考虑在
mod-playerbots 中提出单变量策略。

## 动态波次只读量化（run726/728 seq1/seq3 三场有效 wipe）

### 死亡窗口

以每条玩家 death snapshot 前 12 秒、同一 target 的动态 damage 为窗口。18 条 snapshot 中 **13 条**有
Searing Gaze 28265 伤害；它是重复出现的高风险来源，但不能单凭窗口把任何死亡归为单一技能。

- run726 的 820 在 423.226 秒死亡前，28265 为 19,332（另有 Kaddrak 2,324）；819 在 435.883 秒死亡前，
  28265 为 11,961、Protector 为 10,984。
- run728/seq1 的 820 首死窗口为 28,184 动态伤害（Gaze 11,640、Dark Matter Target 4,651、Stormcaller
  4,235、Protector 5,334）；坦克 816 死亡窗口为 31,211（Protector 14,241、Gaze 12,848）。
- run728/seq3 的坦克 816 于 498.448 秒死亡前承受 39,945（Stormcaller 10,101、Custodian 16,580、
  Protector 8,808、Gaze 3,323）；不是只由 Gaze 造成。

### 坦克接手

坦克每秒采样中，有目标且目标 entry 为 Protector/Stormcaller/Custodian 的比例分别是：

| attempt | Protector | Stormcaller | Custodian | 无动态目标 |
|---|---:|---:|---:|---:|
| run726/1 | 107/285 | 40/285 | 6/285 | 132/285 |
| run728/1 | 108/293 | 41/293 | 9/293 | 135/293 |
| run728/3 | 110/316 | 46/316 | 12/316 | 148/316 |

坦克确实接手动态单位，且 Protector 是其最常见目标；并非“坦克从不接怪”。按三场总动态承伤，Protector 的
约 53% 与 Stormcaller 的约 64% 落在坦克，Custodian 约 46%。但约 47% 的采样没有动态 target，且非坦克仍吃到
大量 Protector/Custodian 承伤，故现有数据不支持“只加一个强制集火/嘲讽”这种结论。

### Searing Gaze

28265 都是 Brann（28070）召唤的 spawnId=0 单位；三场合计对队伍造成 **231,367** 伤害。仅约 21,011（9%）
落在坦克，主要持续打向非坦克：例如 run726 中 819/820 分别 45,579/39,533；run728/seq3 中 817/820 分别
37,382/30,959。其伤害以约 0.5 秒 tick 连续出现；例如 run728/seq3 的 817 有 30 tick、37,382 伤害。
因此 Gaze 是独立于坦克接手的远程压力，当前尚无数据证明 bot 是否识别/规避它。

### 决策日志诊断：run729（临时 `LogInGroupOnly=0`）

- run729 是 **442.496 秒、5 death 的动态 wipe**；前置 161.059 秒完成、真实 gossip 0/1 为
  164.116 / 189.337 秒。采样结束后已将 `LogInGroupOnly` 恢复为 `1`，并以 r13 重启。
- `Playerbots.log` 中没有 `Searing Gaze` 或 `28265` 的 trigger/action；结合 HoS 策略无 Tribunal
  trigger/action，说明当前没有已登记的 Gaze 专用决策链。此处只是“不存在命名链”的证据，尚未证明何种规避动作可行。
- 动态段从首个 Protector 日志起，远程三人共有 401 次 `combat formation move` 的 PREREQ/FAILED 记录。
  **不能把 FAILED 读成移动失败**：基类 `CombatFormationMoveAction::Execute()` 即使调用 `FleePosition()`，最后也
  固定 `return false`，日志的结果码不能证明是否实际移动。仅有一次普通 `flee` 成功，亦不是 Gaze 专用响应。
- 因此下一轮不能根据这些 FAILED 行修改 multiplier 或宣称“队形移动坏了”。

### 位置与核心机制复核（run729，纯只读）

核心的 `DoAbedneumSearingGaze()` 每 15 秒在随机玩家**当前坐标**召唤存活 10 秒的 28265 trigger；所以这是
可通过离开初始落点减伤的地面威胁，而非应该由坦克接手或可被击杀的目标。run729 在第二次 gossip 后 216.510 秒
首次出现 Gaze（正合 phase 3 开始后 16 秒），全团于事件第 253.155 秒灭团，距离正常的 300 秒结束仅 **46.845 秒**。

- 816 在其 24.503 秒 Gaze 伤害窗口内只有一次 1.7 码位移，随后 433.909 秒死亡；820 在其 6.499 秒窗口内
  零位移，442.492 秒死亡。
- 818 在 24.503 秒窗口内累积移动 20.7 码，却仍承受 34,920 Gaze 伤害；现有每秒位置采样不记录每个
  28265 trigger 的精确落点，不能把它解释为“已逃离仍无效”。

这把优先级从笼统的“Gaze 可能很危险”收窄为：先补**只读**的 trigger 坐标/每 tick 距离关联，再验证一个
Gaze 位置规避动作是否足以让团队撑完最后约 47 秒。

### trigger 坐标诊断：run730（新只读 probe）

授权编译的 `mod-raidtest` probe 仅在 28265 `OnCreatureAddWorld` 写入生成坐标，并在其伤害 tick 写入
trigger—玩家距离、玩家坐标及移动状态；不读取或驱动 playerbot 决策。run730 为 **426.738 秒、5 death 的 wipe**，
前置 147.708 秒完成、gossip 150.870/175.070 秒；首个 Gaze 为事件第 216.027 秒，仍是 phase 3 的预期时点。

| trigger 生成（相对 attempt） | 受击玩家 | tick 时距离 / 移动 | 结论 |
|---|---|---|---|
| 391.097s @ `(926.16,360.46)` | 820、816 | 820 = 0.00 码且未移动；816 = 2.29 码且未移动 | 二人留在伤害半径内 |
| 406.100s @ `(916.55,352.78)` | 819 | 0.00 码且未移动 | 819 于 411.102s 被该 trigger 击杀 |
| 421.093s @ `(940.88,383.35)` | 818 | 0.00 码且未移动 | 818 于 425.388s 死亡 |

820 于 426.733s 在首个 trigger 原坐标死亡；816 于 423.174s、817 于 424.731s 相继死亡。这个样本已证实
至少四名受击者没有执行离开 Gaze 落点的动作，且 28265 的 tick 在距离 0–2.29 码时持续命中。

### 单变量实现与首轮验证状态

经授权，`mod-playerbots` HoS 策略新增 `tribunal searing gaze` trigger：仅在 combat 中、5 码内有 28265
时，以 `ACTION_EMERGENCY + 10` 运行 `tribunal flee searing gaze`，用既有 `MoveAway()` 离开至 12 码。
它不改目标、仇恨或任何游戏规则；已用四线程构建并安装。

r15 的首轮验证未产生有效 Tribunal 样本：run731 在前置阶段出现团队被带离目标、持续 `los=false` 的既有
`pull_rejected`，未落 attempt 终态；随后 run732 是 `aborted`（0ms）。二者均未到 gossip / Gaze，不能用于评价
该策略，也不能记入 Tribunal 战斗统计。

r16 的干净重跑 run733 则为有效样本：**493.296s / 5 deaths wipe**，前置 185.138s、gossip 199.011/223.232s；
事件持续 270.050 秒，距 300 秒正常结束约 **29.950 秒**。四个 Gaze trigger 共只产生 14 个伤害 tick、14,419
伤害（11 个非零）：820 首轮两 tick 后移出；819 第二、三轮分别在 4/3 tick 后开始移动并停止继续受击。
相较无规避 probe 的 run730（49 tick / 54,987 伤害，三轮即团灭），这是动作触发且离点后停止 Gaze tick 的
直接证据；但 816/818 仍于 477.641/478.254s 死亡，最终团队未撑住，**单场不构成完成或稳定性结论**。

### run733 余下 30 秒的只读归因

Gaze 已不再是首死主因：816（坦克）于 477.641s 首死，死前 12 秒为 Protector 8,518、Custodian
2,806、Kaddrak 588，另有 7,944 治疗；818 于 478.254s 紧随死亡，窗口为 Protector 12,225、Custodian
7,308，**零治疗**。末段 820 / 817 / 819 的窗口也以 Custodian / Protector / Kaddrak 为主（820 首次
6,715 Custodian；817 13,300 Custodian；819 15,179 Protector），仅 817 有一笔 1,396 Gaze。

坦克并非完全漏接：全动态段 816 承受 Protector 115,742（总 Protector 198,444 的约 58%）、Stormcaller
40,704（约 69%）、Custodian 11,048（约 21%）。其末段每秒采样仍在 Protector / Stormcaller / Custodian
间切换，故证据不足以支持“强制嘲讽”或第二个 target multiplier。当前最具体的剩余缺口是**坦克首死后的
治疗覆盖与多种动态怪叠压**；818 的零治疗是单场观察，不能直接归因为治疗 AI 缺陷。

追加同基线 run734 也完整进入事件但于 **445.773s / 5 deaths** wipe（gossip 195.290s，事件仅撑
250.483 秒）。Gaze 仍只有 **6 tick / 6,467** 伤害，受击 816/817/819 的首 tick 均 `moving=true`，再次确认
规避在触发；但 817 已在事件第 227.707 秒死亡、早于最终阶段。两场改动后样本都显示 Gaze 压力已显著下降，
但都未跨过 300 秒，故当前只能把 Gaze 修复视为**已验证的必要改善**，不是充分通关条件。

### 两场 Gaze 修复后首死比较（纯只读）

| run | 首死（相对 attempt） | 首个 Gaze 后 | 首死前 12 秒承伤 | 治疗 |
|---|---:|---:|---|---:|
| 733 | 816 tank @ 477.641s | 38.393s | Protector 8,518；Custodian 2,806；Kaddrak 588 | 1 次 / 7,944 |
| 734 | 817 DPS @ 422.997s | 11.694s | Protector 16,959；Stormcaller 4,330；Gaze 2,792；Kaddrak 541 | 3 次 / 3,015 |

两场首死都以 Protector 为最大来源；run734 DPS 的 Protector burst 更高而治疗更低。整体 Protector 承伤中坦克
仍占 58%（run733）/55%（run734），Stormcaller 也占 69%/75%，所以这不是“坦克从不接怪”的证据；同样，两例
不足以归因治疗 AI。已能排除 Gaze 为这两场首死主因，当前阻断收窄为有明显随机性的多 add burst / 治疗吞吐交互。

第三个完整样本 run735 同样为 **434.971s / 5 deaths wipe**（gossip 186.404s；事件 248.567s），Gaze
仍仅 6 tick / 7,743；首死再次是坦克 816（事件第 233.314s），死前 12 秒为 Protector 10,677、Stormcaller
4,944，Gaze 484。至此 Gaze 修复后 3 个完整样本均为 0/3 DONE，事件时长 270.050 / 250.483 / 248.567 秒，
且首死 2/3 为坦克、3/3 的首死最大来源均为 Protector。**Gaze 缺口已稳定改善，剩余阻断已重复指向动态 add
压力；但尚未证明是坦克决策、仇恨、DPS 击杀速度或治疗选择中的哪一项。**

临时全量决策日志诊断 run736 未产生动态样本：前置第 3 个 spawn 时 818 死亡，300 秒以
`prerequisite_failed: clearing timeout` abort，未到 gossip / Gaze。诊断设置已恢复 `LogInGroupOnly=1`；该场
不用于战斗归因，也不能评价坦克 / 治疗动作。r18 首次启动未保持进程，已以 r18b 重启并恢复服务。

run738 取得了有效全量日志（428.960s / 5-death dynamic wipe），并出现关键拒绝：坦克已反复 `tank assist - OK`，
但对 Protector 的 `reach melee` 被 `reach-leash` 拒绝（治疗锚 817 到 Protector 39.3 码，heal leash 38.5，
坦克本身距目标仅 17.7）。静态审计确认这是 `ReachTargetAction` 对全部 combat enemy chase（含坦克）的共享
护栏：坦克锚定最近存活治疗，目标超治疗范围即拒绝；其原始目的正是防止坦克离队去 100 码外刷新点。Tribunal
这一例仅超 0.8 码、目标已在坦克接近范围，故该共享安全规则在动态波次边界可能错误阻断接手；但单例不足以直接
关闭或放宽全局 leash，必须做 Tribunal 特异、保留远距离保护的设计和回归。

## 最新决策：Custodian DPS 优先级回退

run740 lifecycle 证明 Custodian 0/2 击杀；新增 DPS Custodian 动作后，run741 为 0/1、修正为仅 DPS 后 run743 为 0/2，
且 Protector 击杀数从 24/27 降至 22/27。run742 全量日志确认动作虽多次触发/部分 OK，却曾错误包含治疗者；修正后仍无
Custodian 击杀。该单变量未改善，必须回退，不混入 Gaze/窄 leash 的已验证改善。run740 的有界只读导出进一步显示动态 add 玩家伤害为 Protector 740,413（82.1%）、Stormcaller 142,454（15.8%）、Custodian 18,867（2.1%）；三名主 DPS（818/819/820）均以 Protector 为最大目标，故不能把 Custodian 0 击杀简单归为“DPS 碎片化/未集火”。下一变量尚无证据，不自动扩大目标优先级。lifecycle cadence 复核：Protector 每 23.5 秒固定三只、Stormcaller 每 32 秒固定两只、Custodian 每 32 秒一只；run740 的峰值正是最后一波生成时 11 存活（6/3/2）。此前 Protector 平均死亡 15.1 秒、Stormcaller 17.0 秒，均小于下一波同类刷新间隔；因此 11 add 不是长期稳定清怪速度不足造成的渐进积压，而是团灭临界期前一波已无法完成清理的崩溃后果。不能据此再加全局 DPS 集火变量。run740 的崩溃转折发生在 426.813 秒坦克首死：此前 12 秒承伤 Protector 14,302、Stormcaller 11,703、Custodian 7,139、Kaddrak 502（共 33,646）；随后 healer 817 于 433.904 秒死亡、其余 DPS 连锁死亡。该 event schema 没有 `heal` 事件（全 attempt event_type 仅 spell/damage/death/boss_hp/combat/state），不能从该表推断“零治疗”或提出治疗改动；下一步须用已授权的全量 playerbot 决策日志，将 817 的治疗 action 与这 12 秒窗口对齐。r31/run744 以临时 `LogInGroupOnly=0` 启动后卡在前置 Lightning Construct：leader 重复 `could not initiate attack ... invalid target`，未进事件；但随后原始 `pull_rejected` 记录证实目标 27972 `valid=true alive=true`，实际是 63.75 码、`los=false` 的瞬时接近/视线失败，不是 stale GUID。已正常 `raidtest stop` 作废，并在 r32 恢复 `LogInGroupOnly=1`。不得将该场用于治疗归因。

## run745：r32 回退版首个真实完成（单场，不足以验收）

- r32 当前运行配置已恢复 `AiPlayerbot.LogInGroupOnly=1`；run745/seq1 是 `heroic-hos-tribunal-event-n5` 的一次正常规则完成：**491.468 秒、result=kill、5 人零死亡**。日志中的 event-bus `death=6` 是登记事件总数，不能误作玩家死亡；runner 的明确结果为 `deaths=0`。
- 六只前置在 148.515 秒完成，恢复完成于 150.241 秒；真实 Brann gossip phase 0/1 分别在 150.241 / 174.447 秒；`AttemptObserver` 随后确认 `EventCompletionBossState=2` 达到 DONE。run 在 491.468 秒收尾（动态事件约 317 秒），Brann 未触发 escort-failure，非 fixture、Heroic / normal5-v1 / `BotCheats=""` 均未变。
- 这闭合了此前只到 `4:3`、`2:3` 而动态团灭的 lifecycle 缺口，但 n=1 不证明当前 Gaze 离点/窄 leash 策略的充分性，也不与 run733–735 的 0/3 动态 wipe 合并成率。证据日志：`/tmp/wow335-worldserver-hos-tribunal-r32-restore.log`，持久阶段/结果数字已在本记录中保存。

## run746：同 r32 基线复验为真实动态 wipe

- run746/seq1 已终态：**522.820 秒 wipe、5 名玩家死亡**（runner `death_names` = 五名 roster bot），不是运行中 `aborted/0` 占位或前置 abort。六个前置于 200.359 秒完成，真实 gossip 0/1 于 200.360/224.548 秒到达；之后进入 observing，故这是一条有效动态阶段失败样本。
- 前置第 4 至第 6 只 Lightning Construct 曾反复 `los=false`，但最后仍正常清完；它只把前置延长至 200 秒，不能当作本次 wipe 的死因或把此场剔出 lifecycle 分母。动态段约 298.272 秒后以全灭结束，未见 DONE/escort failure。
- 所以 r32 的同口径复验目前为 **1/3 DONE（run745 零死亡完成；run746/run748 全灭）**。run748/seq1 是同一基线的第二个有效动态失败：前置 146.608 秒完成，gossip 0/1 于 146.609/170.909 秒到达，**463.049 秒 wipe、5 名 roster 玩家死亡**；它不受 run747 前置减员的影响。run748 动态玩家承伤以 Protector 27983 的 279,191 为首（Stormcaller 67,192、Custodian 70,193、Gaze 10,082）；首个可见 roster 阵亡状态为 818 @ 433.460 秒，后续 820 @ 442.492、治疗 817 @ 448.511、坦克 816 @ 450.513，符合级联而非 Gaze 主导的形态。
- 818 首死窗口 `[421.460,435.960]`：Custodian 13,592 + Protector 4,494 + Stormcaller 1,397 + Kaddrak 609。818 从 10,689 降至 4,361（431.450 秒）后，于 433.460 秒死亡；治疗 817 曾三次落在 818（2,849 / 2,849 / 2,849，最后一次 430.384 秒），而 430.981–432.642 的后续多次施法全落在同时低血的坦克 816。此处是**有限窗口的目标竞争事实，不是治疗 AI 缺陷归因**：817 在同窗自身满血、法力约 2.5–4.5k/20k，且坦克也在 8.5–14.7k/24.4k。cycle 14 对照成功 run745 最后 15 秒显示该 healer 的低血取舍并非失败场独有：817 只有 154–715/16,708 法力，仍先治疗低血 819、继而治疗坦克 816；818 始终至少 16,089/16,644，且该窗全团仅受 11,351 可计伤害。两窗敌方压力显著不等，故不能由其不同目标顺序归因或改治疗优先级。cycle 15 以 gossip 对齐 250.551–265.051 秒事件年龄后，run745 的 roster 承伤为 Custodian 9,173、Stormcaller 3,748、Kaddrak 2,505；两个 Protector（GUID 230/231）已于 425.050/426.013 秒死亡，下一组三只到 437.953 秒才生成。run748 同年龄承伤为 Custodian 26,426、Protector 12,856、Stormcaller 7,412、Kaddrak 3,519、Gaze 1,396；一个 Protector 已于 421.790 秒死亡，但 GUID 227/228 至少存活至 428.897/431.561 秒。期间坦克 816 连续选中 Stormcaller 232/233，至 431.450 秒才选 Protector 228，发生在 818 已死亡之后。该次序与额外 Protector 压力有关联，是可复核的**目标选择假说**。cycle 16 的 run746 首死前窗口也复现 Protector 逗留与压力：三只 Protector 236–238 于 464.554 秒生成；坦克 816 在 467.871–471.882 秒确实短暂选它们，但 472.882–478.890 秒又连续选 Stormcaller 243，而 Protector 237/238 仍活。其间 Protector 造成 40,904 roster 伤害（另有 Custodian 24,378、Stormcaller 8,166、Kaddrak 5,468、Gaze 4,365），818 于 478.890 秒成为首个可见死亡；236 475.021 秒死，237/238 仍延至 485.848/496.921 秒。两个有效 wipe 都有“Protector 留场并在首死前转打 Stormcaller”的形态，足以进入单一 Protector target-priority 设计调查。cycle 17 已定位实际入口：`TankTargetValue::Calculate()` 在无 RTI 时调用 `FindTankTargetSmartStrategy`；其现有排序只依次看未获得仇恨、近战距离、威胁/距离，完全不看 Tribunal entry，`tank assist` 与死后即时接管均消费该 `tank target`。因此若实施，变量必须只是在该选择器中为 map 599 的存活 27983 加优先级，且不替 raidtest 选目标、不覆盖 RTI，其他地图不变。上线前验收定义为：在有至少一只可攻击 27983 的连续动态窗口，tank-state `entry=27983` 的快照率为 100% 直至该批 Protector 清空；并记录 spawn→death 延迟和 roster 承伤，**不**把单次 DONE 当效果判定。尚未改代码：cycle 18 确认最小接入无需新增 HoS trigger/action（现有 HoS 未提交 diff 仅是已验证的 Gaze 离点）；直接在 `TankTargetValue.cpp` 的 fallback comparator 先比较 `bot->GetMapId()==599 && attacker->GetEntry()==27983` 即可。`CheckAttacker` 接收的是 `FindTarget` 已筛过的有效 attacker，故不会让坦克追不可攻击 spawn；RTI 的早退分支仍在 comparator 之前。实现只需一个局部 predicate 和 comparator 的早退，不增 state、不改 raidtest 或 DPS 选择器。cycle 19 已在读完 C++/build 规范后实施这一个变化：`TankTargetValue.cpp` 只新增 map 599/entry 27983 comparator early return；RTI、raidtest、DPS selector 和其他地图未动。`cmake --build var/build/obj --target worldserver -j4` 成功（重新编译该 `.cpp`、链接 modules/worldserver），随后已用 FIFO relay 受控重启 r33（PID 25327，`raidtest status=IDLE` 后确认）。codestyle 脚本会全树扫描，因既有 core 文件空行/qualifier/tab 告警返回失败；本文件不在报告中，且改前 `git diff --check` 通过，编译成功。执行 smoke run749/attempt `1788427972` 已启动并在 4.398 秒确认 `ATTEMPT_RUNNING/prerequisites`；cycle 20 一次有界 60 秒终态等待后仍 `finished_at=NULL`，`aborted/0` 只是运行中占位。run749 已以 **477.207 秒 wipe、5 deaths** 终态；它是执行 smoke，**不计入完成率**。结果未达预设执行验收：Protector 存活窗口的 166 个 tank-state 快照仅 127 个为 27983（**76.5%**，目标为 100%），33 只生成、28 只死亡，平均 spawn→death 13.497 秒（最大 20.497 秒）；其窗口 roster 承伤 Protector 259,932、Custodian 63,752、Stormcaller 52,237、Kaddrak 41,001、Gaze 17,995。关键反证是坦克仍在 Protector 可见施压时保持非 Protector：313.888/314.888 秒仍选 Stormcaller 27984，同时 Protector 造成 2,543/5,127 伤害。故 comparator 只影响重新选目标，不能抢占仍活的当前 Stormcaller，变量**执行无效**，不得开正式样本或把 wipe 当疗效/反疗效。cycle 23 排除“value 缓存”解释：`TankTargetValue` 的 `checkInterval=1`，每次 `Get()` 都重算；`TankAssistTrigger` 在 current target 与 tank target 不同且当前目标有仇恨时才以 relevance 50 排入 `tank assist`。现有决策日志没有逐 tick action 结果，不能从 snapshot 判断是该 gate、动作竞争还是候选集缺失；但 r33 `Playerbots.log` 明记多个 Protector 的 reach-leash 拒绝（anchor 距 39.1–60.3、leash 38.5），说明“存活/造成伤害”不等于安全可追，原 100% 生命周期快照口径本身过宽。不能用更高 preemption 去逼坦克越过该正常组队安全边界；应回退这次未通过 smoke 的 comparator，之后只按原稳定性证据继续或另立含距离/LOS门槛的假说。cycle 24 已完成回退：`TankTargetValue.cpp` 对该 comparator 的 diff 已为零；以 `cmake --build var/build/obj --target worldserver -j4` 成功重编译/链接，并用 FIFO relay 受控重启为 `r32-restored`（PID 48353，world ready 后 `raidtest status=IDLE`）。没有启动新 attempt，r33/run749 仍只保留为不计分的执行失败证据。cycle 25 对 r32 三场（run745/746/748）的每个 27983 spawn 用此前最近坦克位置量到出生点 `(943.09,401.38)` 的平面距离，并关联 spawn→death：成功 run745 均距 42.3、平均存活 12.781 秒；两场 wipe 分别 40.5/13.945 秒（run746）与 42.7/14.971 秒（run748）。合并距离桶亦不支持简单门槛：<30 码 22/27 死、14.188 秒；30–40 码 30/33、13.592 秒；>=40 码 39/39、13.832 秒。故“坦克离出生点远/LOS”既未区分 DONE 与 wipe，也未给出可执行的距离门槛；不立新空间策略。cycle 26 已在 r32-restored、未改 bot 策略下排入一次 `heroic-hos-tribunal-event-n5 --attempts 1 --force-recreate`；该 runner 的 force-recreate 按既有场景 roster blueprint 重建了五个 normal5-v1 bot（新 GUID 821–825），不涉及 cheat/装备/难度或 boss 改动，但身份重建须在终态记录中保留。30 秒一次有界观察确认 run750/seq1/attempt `1788427973` 为 `ATTEMPT_RUNNING`、stage=`prerequisites`、elapsed=21.300 秒、`hp_min=100%`；此时 5/5 存活且已在首只 Raging Construct 正常战斗。cycle 27 的一次有界 60 秒等待后仍非终态：六前置已于 178.922 秒完成、recovery 1.631 秒后真实 scripted-event gossip 0 于 180.553 秒触发；185.592 秒状态为 `ATTEMPT_RUNNING/observing`、`hp_min=100%`。cycle 28 再作一次有界 60 秒等待：真实 gossip 1 于 204.746 秒到达，343.933 秒仍为 `ATTEMPT_RUNNING/observing`、`hp_min=100%`。cycle 29 的第三次有界 60 秒等待后，496.311 秒仍 `ATTEMPT_RUNNING/observing`、`hp_min=100%`；日志的 5 bot online/in-combat、0 dead 与该状态一致。DB 仍为 `aborted,duration=0,deaths=0` 的运行中占位，绝非失败。cycle 30 终态已确认：run750/seq1/attempt `1788427973` 为 **499.753 秒 wipe、5/5 roster deaths、boss_hp_min=100%**；日志先有 `AttemptObserver` all-5-dead，随后 runner/event-bus 写入 wipe，且 status 已回到 IDLE，故是有效动态 lifecycle 失败。它完成前置和 gossip 0/1 后才全灭，纳入同配置分母；虽 roster GUID 是重建边界，配置仍为同一 normal5-v1/heroic/无 cheat/无 fixture/300 秒前置预算。因此 r32 现为 **1/4 DONE**，仍不能声明稳定或 HoS 完成。cycle 31 已完成首死分层：动态首死是坦克 821 @ 476.863 秒，随后 825/823/治疗822/824/825 于 481.609/483.814/491.297/493.664/499.745 秒级联。其前 12 秒坦克可计承伤为 Protector 10,362、Stormcaller 10,057、Custodian 4,308、Kaddrak 373（合计 25,100）；另有 Kaddrak 对 822/824/823 的 1,719/1,076/573 与 Gaze 对 824 的 1,556。治疗 822 在 465.767–471.173 秒多次对坦克施法，但 472.520–475.994 秒施法集中在 824；这是新的单场目标竞争窗口，却与 run748 已拒绝的治疗归因相同，且伤害来自多种敌人，不能授权治疗或单一敌人优先级改动。cycle 32 的同口径比较以失败场 gossip1 后首死年龄（run746 253.342 秒、run748 262.403 秒、run750 272.117 秒）为锚，并以 run745 gossip1 后 263 秒的 12 秒窗作成功对照：run745 roster 总承伤仅 13,155（Custodian 7,950、Stormcaller 3,748、Kaddrak 1,457）；run746 61,473（Protector 36,550 最大，Custodian 13,350）；run748 48,776（Custodian 24,211 最大，Protector 12,856）；run750 30,191（Protector 10,362、Stormcaller 10,057、Custodian 4,475、Kaddrak 3,741）。三 wipe 都比成功窗压力大，但主导敌方在失败场间不一致，且 run750 总压只有 run746 的约半数仍灭。因此证据只支持“该事件在高且多源压力下不稳定”，不支持 Protector、Custodian、Stormcaller、Gaze 或 healer 的单变量归因；不再为本窗口设计 bot policy。cycle 33 已以无 `--force-recreate` 的 `heroic-hos-tribunal-event-n5 --attempts 1` 启动 r32 无变量复验，保留 run750 的 GUID 821–825 roster。8 秒确认 run751/seq1/attempt `1788427974` 是 `ATTEMPT_RUNNING/prerequisites`、7.501 秒、`hp_min=100%`，五人正常首拉；cycle 34 的一次有界 60 秒等待后仍在前置：163.404 秒 `ATTEMPT_RUNNING/prerequisites`、`hp_min=100%`；第六只 Lightning Construct 的五人均 `alive=true`、距离0–2.36且 LOS=true，故为正常清怪推进而非减员/LOS blocker。cycle 35 再等60秒，前置167.023秒完成、recovery 5.203秒，真实 gossip 0/1 于172.226/196.410秒到达；315.962秒为 `ATTEMPT_RUNNING/observing`、hp_min=100%。DB `aborted/0` 仍是运行中占位；cycle 36 再等60秒，470.565秒仍 `ATTEMPT_RUNNING/observing`、`hp_min=100%`，但 bot stats 已为4 in-combat、1 dead；尚不是全灭或 runner终态，DB仍 `aborted/0` 占位，不能据此计为 wipe。cycle 37 终态已确认：run751/seq1/attempt `1788427974` 是 **473.432 秒动态 wipe、5/5 roster deaths、boss_hp_min=100%**；all-5-dead observer、runner/event-bus、DB 与回到IDLE相互确认。此前前置和真实gossip0/1均已完成，且本场未 force-recreate、保留GUID821–825，故为同 roster 的有效 lifecycle 失败，纳入分母。r32 现为 **1/5 DONE**；不能宣称 Tribunal 或 HoS 完成。cycle 38 分层：首死为824@439.560秒，之后治疗822@457.249、坦克821@470.272、823@470.619、825@473.430级联。首死前12秒824吃 Custodian 13,387（6击）及Kaddrak 0；另有Gaze/Kaddrak分别对治疗822 2,792/1,131、对坦克821 954。治疗822在428.827–438.181秒多次施824；这与run748首死前 Custodian 13,592 的形态相似，但run746首死窗以Protector、run750以混合坦克承压为主，故2场相似仍不能将Custodian或治疗定为单变量。cycle 39 的目标/坦克对照否定 Custodian 优先级：成功run745同年龄 Custodian伤害为819 6,530、坦克816 1,420，且816先持续选Stormcaller至433.861秒、434.864秒才选Custodian；run748 Custodian为818 13,592、816 7,881、817 2,738，坦克至432.452秒才选Custodian（首死后）；run751 Custodian全数13,387均打824，但坦克821在427.705–438.735秒连续`victim=0/select=0`、engine多为1、无威胁，位置(929,361)距boss40.1，而824死在(950,393)。故run751并非“坦克改打Custodian可救”的证据，而是 tank/group 脱离时远端承压；对已有Protector comparator结论亦不能外推。cycle 40 追溯：821在400.652秒仍打Protector206，402.654秒变`victim=0`（select仍206），403.660秒engine转1、select=0，直至469.787秒才再选Custodian236，约67.1秒未重新接战。动态段没有reach-leash/action拒绝日志，故不能声称具体动作失败；但402–439秒821固定(929,361)，823/825约(927/923,363/360)，而治疗822/首死824约(949/953,383/389)，两团相距约30–38码。可确认“Protector接战结束后坦克未重获目标且团体分裂”，但不能由现有日志归因移动、leash或选择器；禁止强制追击/改优先级。cycle 41 确认206在402.572秒死亡；同批204/205已于401.045/401.065死亡，故821失去victim发生在三只Protector全部清空之后。关键是两团并非此时才分裂：398.652–402.654每秒位置已固定为821/823/825约(929/928/923,361–363)和822/824约(949/953,383–389)，全部`moving=false`；无移动跃迁或reach-leash/action日志。故这是正常本批清空后处于既有双点站位，不能把206死亡或“脱团移动”称为根因；但清空后坦克未重接战仍是事实。cycle 42 量出有效敌人接管缺口：三Protector清空后，Stormcaller210/211于412.421秒spawn，210于418.658秒首次打824（1,726）；Custodian221于423.424秒spawn、427.535秒首次打824（5,787）。坦克821直到441.740秒才重新选Protector228（其spawn436.418），即对首个新Stormcaller存在29.319秒spawn→接战、23.082秒首伤→接战空窗；期间没有动态reach/action拒绝日志。故已否定“单纯正常空波等待”：至少Stormcaller/Custodian存活并伤害同队时，坦克仍无目标；但尚未证明其在821位置是安全可攻击候选，不能直接做追击/优先级变更。cycle43静态路径检查否定“`TankAssistTrigger`因current为空或非战斗engine未安装”的假说：触发器先要求`attacker count>0`，随后`current target==nullptr`即返回true；其`tank assist` action relevance=50，tank target在combat及non-combat engine均安装。`AttackersValue`会收集100码sight内全队威胁单位；run751中821在(929.03,361.04)，27985/221在(964.30,381.94)，约41码，且221在427.535已打824，而821从427.705至440.736确在combat=true但engine=1(non-combat)、victim/select=0。故该敌人若经AttackersValue可见，现有非战斗tank-assist本应尝试；`TankTargetValue`也无reach过滤，实际Attack才检查LOS。没有tick级attacker-count/trigger/action结果，不能在“候选集未纳入、trigger未入队或relevance被抢占”间归因，不能改reacquisition策略或开正式样本。cycle44/45已实现且收紧为无行为诊断：`GenericTriggers.cpp`在map599/in-combat tank记录attacker-count/current/active；仅在原本已有current-target路径读取tank-target，避免为空target的诊断读取污染其缓存。`TankAssistAction`在实际被选中时记录target entry、LOS、Attack结果，因此target只在原执行路径读取；不改返回决策。cycle45再次MTHREADS=4 build成功且三文件diff-check通过。全树`python3 apps/codestyle/codestyle-cpp.py`失败仅报既有core空行/tab/qualifier，未报本次文件。无live session可归属，且mod-playerbots仍有8个非本cycle未提交的行为变更（HoS Gaze移动、Tribunal reach-leash例外）；共同重启/执行会破坏单变量baseline，故未重启/未smoke。cycle46复核仍IDLE，且无live session可确定归属；外来集合稳定为`ReachTargetActions.cpp`及HoS的ActionContext/Actions/Strategy/TriggerContext/Triggers共8文件（本诊断仅另3文件）。它们含两项行为策略，不能当作诊断基线。cycle47不触碰原worktree，已以`mod-playerbots` HEAD `2dba88eb`建立独立detached worktree `/tmp/mod-playerbots-tribunal-diag`，只应用本诊断三文件patch；其`git status`恰为这三文件，且对外来8文件patch为空，故诊断代码已可隔离。AzerothCore CMake把modules路径硬编码为source root下`modules/`，现有build不能直接链接该worktree；不得交换原目录。下一步在不改原worktree的独立source/build树中挂接此module，再编译/重启其诊断binary并跑一次不计lifecycle smoke。n=5 只证明现有 Gaze 离点/窄 leash 形态有完成能力、但不稳定；不与早期不同阶段的样本混算，也不由两场动态 wipe 推出新的治疗、嘲讽或转火变量。

## run747：前置减员后 300 秒超时（非 lifecycle 样本）

- run747/seq1 在 **300.000 秒**以 `prerequisite_failed: clearing timeout` 中止，1 名 roster 玩家（`Qzozpvcnfive`）死亡；没有 gossip 或动态事件，**不加入** r32 的 1/2 lifecycle 分母。
- 终态日志显示第六只 Lightning Construct 仍存活、其余四人反复因 `los=false` 无法拉起；这与 run746 的同类前置接近抖动相符，但 run747 多了减员。**死亡窗口已重新对齐，不能再把末段 59038/61528 当死因**：runner 指定死者为盗贼 818 (`Qzozpvcnfive`)；其可见最后两次承伤是在 84.307 / 88.324 秒来自此前 126746（27972）的 5,193 / 9,786，且该 bot 此后最后事件在 98.735 秒。event bus 没有玩家 death 行，故只能把该伤害窗口与 runner 名单并列，不能声称精确一击。末段 59038 是该 27972 的 `Just Died` Electrical Overload（SmartAI），在其 143.852 秒死亡前 1.208 秒施放；它不是可通过打断来避免的在场读条。尽管 61528 Chain Lightning 有 counterspell/wind-shear 候选，两个对应 spell action 在该窗均为 0，且不与 818 的早期死亡时间重合。故“漏断导致本次死亡”被时间线否定，不能据此改 interrupt 策略。

## 下一步

1. run747 的 interrupt/死亡时间线已完成：没有把末段 Electrical Overload 或漏断作为靶子。保持 r32 的相同二进制、场景、300 秒前置预算和正常规则基线，再补一个 bounded lifecycle 复验；仅累计 Brann 存活、两次 gossip、`EventCompletionBossState=2 DONE` 的完成样本。
2. 若再次发生前置减员，先按死者的最后状态/伤害和具体 spawn 对齐；不得从 `interrupt_watch` 候选反推动作未执行或死因。
3. `mod-raidtest` 不得代打或代选目标；任何新的 `mod-playerbots` 策略改动都须在上述只读结论后单变量验证。
