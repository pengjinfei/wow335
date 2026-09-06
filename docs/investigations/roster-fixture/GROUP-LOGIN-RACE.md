# 战前离队：登录完成条件过早（2026-09-06）

## 原因

`IsInWorld()` 只表示角色对象已进入地图，不表示 Playerbots 的登录收尾完成。

实际顺序：

1. `HandlePlayerBotLoginCallback` 加载角色，并排队 `OnBotLoginOperation`。
2. `PlayerbotHolder::OnBotLogin` 注册 bot；无真人 master 且旧团队不符合保留条件时，调用 `LeaveOrDisbandGroup()`。
3. 该调用仅向会话队列放入 `CMSG_GROUP_DISBAND`，离队尚未执行。
4. 框架只以 `IsInWorld()` 判定登录完成，提前解散旧团、组建新团、准备角色。
5. 下一次 `PlayerbotHolder::UpdateSessions → HandleBotPackets` 消费离队包；包不携带旧团队身份，移除的是角色当前的新团队。成员依次离队，最后团队自动解散。

这解释了首次启动可能成功、同一进程内复用失败。不能归因为装备、天赋或 DPS 战斗策略。

## 证据

- run75：诊断版本首次运行，115153ms、0 死亡击杀；团队和 loot group 一致。
- run76：紧接着复用相同角色，原团队 1 在 LOGIN_AND_GROUP 由框架正常解散，新团队 3 建立。
- 随后新团队 3 在等待 pull 时逐个移除角色 716–724，method=2（LEAVE），最后剩余 2 人时解散。
- 只读 GroupScript 捕获栈：`World::Update → OnPlayerbotUpdate → PlayerbotHolder::UpdateSessions → HandleBotPackets → Player::RemoveFromGroup → Group::RemoveMember`。
- 对照源码，`OnBotLogin` 的登录清理调用会排入该离队包；`IsInWorld` 原条件未等待后置登录注册和包消费。
- 已保存调用栈证据：[run76-group-trace.log](run76-group-trace.log)；完整观测日志：`/tmp/wow335-group-trace-world.log`。堆栈诊断当前仅 `RaidTest.LogLevel >= 3` 启用，普通成员移除/解散事件保留日志。

## 修复

框架新建团队前统一检查 `RosterLogin::IsReadyForGroup`：

- 角色已在世界、未处于传送中；
- `sRandomPlayerbotMgr.GetPlayerBot(guid)` 已注册为当前 Player 对象；
- PlayerbotAI 和会话已存在；
- 会话客户端包队列已空，由正常 `UpdateSessions` 消费登录清理包。

`AllLoggedIn` 与 orchestrator 的登录轮询共享该条件。没有清空/丢弃数据包，没有强制重组，没有禁止 AI 离队，没有修改 mod-playerbots 或核心。保留原有登录超时和开怪前团队门禁。

## 修复验证

最终源码四线程构建安装通过，模块 C++ codestyle 和 git diff --check 通过。

- run77：重启后连续两场，分别 122774ms、105958ms，均零死亡击杀。
- run78：同一进程复用相同角色。登录阶段先消费旧团队 1 的离队包，之后新建团队 3 正常进入战斗；见 [run78-login-cleanup.log](run78-login-cleanup.log)。121639ms、零死亡击杀，run 已正常收尾。
- 三场共 30 份快照全部通过，逐角色 SHA-256 与 run72–74 基线一致，详见 [FINGERPRINTS.json](FINGERPRINTS.json)。

这些结果验证的是当前十人高装等配置下 Loatheb 的编排回归，不等于所有副本或同阶段装备策略均已通过。

### 数据库终局核验

| run / attempt | 结果 | 时长 ms | 死亡 | 血 DK 对 boss 伤害事件 | 血 DK 对 boss 总伤害 | 首/末伤害 ms |
|---|---|---:|---:|---:|---:|---|
| 77 / 1 | kill | 122774 | 0 | 154 | 290411 | 1 / 122261 |
| 77 / 2 | kill | 105958 | 0 | 131 | 336315 | 2006 / 105441 |
| 78 / 1 | kill | 121639 | 0 | 153 | 357780 | 1 / 121630 |

均 `boss_hp_min=0`，notes 为空；run77、run78 的 finished_at 均已落库，每场只有一条 attempt。伤害统计限定 source_guid=716，boss target_guid 分别为 106、906、926。
