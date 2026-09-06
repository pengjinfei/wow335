# 主坦旗标、传送与击杀后实例恢复（2026-09-06）

延续TAKEOVER-VALIDATION.md。目标是同一角色组在重启后直接开战，并在击杀后继续下一attempt/run，不依赖force-recreate或热身。

## 第一轮改动

- TickLoginAndGroup按蓝图第一个role=tank的槽位设置MEMBER_FLAG_MAINTANK；组队失败立即以编排失败收尾，不再继续传送。
- ResetInstance从ObjectMgr原始CreatureData查找场景boss的map/entry/spawnMask，加载出生格子；已有活boss复用，死/缺失boss清本实例该spawn的重生计时后走LoadCreatureFromDB（禁止活体重复）。原始出生点/模板/难度不变，不修改伤害或AI技能逻辑。
- 传送失败日志补核心enter_reason、来源map/instance、存活/传送状态、团队及难度，待运行时确认根因。
- 原run64日志实际出现force-respawned后boss not found，因此不只是“开始就缺少已加载boss”：动态Respawn会移除尸体并排队，后续重生还受linked_respawn等检查。新版在战前编排阶段恢复原始spawn，绕过长等待，不插入战斗期干预。

第一轮四线程增量编译及安装通过。运行结果待补充。


## run66传送诊断与第二轮修改

重启后直接复用706–715（未force-recreate）。建团日志10人成功并指定DK706主坦；传送时防骑714已group=0，enter_reason=5=CANNOT_ENTER_NOT_IN_RAID，来源571、alive=true。其余角色保存于副本，714是run65死亡角色。两次attempt均未进入战斗。

源码：LeaveFarAwayAction::isUseful在机器人与队长地图不同或距离过大时允许Leave；LeaveOrDisbandGroup排队CMSG_GROUP_DISBAND。框架以前在TickLoginAndGroup建团/Begin后返回，直到下一世界tick才发传送，存在离队窗口。日志直接证实“组队成功到传送间成员脱团”，具体LeaveFarAway动作未打开动作日志，机制归因为源码推断，需修复回归支持。

修复：AttemptRunner::Begin在全部上下文初始化后立即Tick(ctx,0)，同一次编排调用内执行首轮复活、传送、ACK；后续等待仍逐tick非阻塞，不禁用AI退队策略。AllOnMapNow额外要求IsInWorld及同一Map*，避免仅mapid相同却分处不同实例被误判全员到齐。

第二轮四线程增量编译、安装通过，run67安排重启后原角色连续两次attempt验证。


run67第一场已进入战斗（attempt1788426369，boss869），首个245ms采样：DK706 mt=true explicit=true，防骑714 mt=false explicit=false；两者engine=0、victim=boss、melee=true。重启后首次直接复用原角色已经通过传送；后续击杀/第二attempt待验证。


第一场于189449ms零死亡击杀。worldserver日志确认重启首次恢复spawn128066、instance4、bossGUID869；第一场结束后再次恢复同spawn/同instance，bossGUID938，进入attempt1788426370（seq2）。没有force-recreate、没有切换到新实例，也没有依靠另一次热身。

第二场首个boss_hp为99（进入事件观测前开怪动作已经产生伤害），不能把首次采样硬说成100；恢复代码在开怪前调用SetFullHealth。约15.6秒血量95%，已真实推进。


## run67 完整验收结果

同一组角色706–715、同一团队1、同一实例4，重启后第一次运行 `.raidtest run naxx-loatheb --attempts 2`，未热身、未force-recreate。

| 指标 | attempt 1 | attempt 2 |
|---|---:|---:|
| attempt id |1788426369|1788426370|
| boss原始spawn / 运行时GUID |128066 / 869|128066 / 938|
| 结果 |kill，189449ms|kill，188002ms|
| 队员死亡 |0|0|
| DK主坦/显式主坦成立采样 |233/233|231/231|
| DK对boss伤害次数 / 合计 |338 / 221609|335 / 186002|
| boss目标为DK采样 |170/189|174/187|
| boss目标为防骑采样 |17/189|12/187|
| boss真实死亡事件时间 |189441ms|187989ms|

两场均有entry16011的真实死亡事件与HP=0。第二场是在第一场kill后恢复同实例原spawn，不是找了新副本或复用了旧死亡判定。DK主坦旗标稳定，实际主要承伤也转移到DK。首场87997ms两坦各有一次非战斗引擎/空目标采样，随后恢复；不能说首场所有采样都是combat。第二场DK231/231均combat。没有重现长期停攻。

### 三项结论

1. 主坦旗标：已实现，按蓝图首个tank明确指定，运行时与主要承伤相符。
2. 重启后首次传送：本次直接复用上轮死亡/离场角色通过；修复建团与首次传送间的时间窗口。同实例指针和IsInWorld纳入到达校验。日志证明原失败时成员已离队，LeaveFarAway是源码支持的机制解释，并非已单独抓到动作记录。
3. 击杀后旧实例恢复：已通过同实例连续两场击杀验证。恢复原数据库spawn，清该spawn在本实例的重生时间，不批量删实例存档、不改变boss机制。

### 交付

- 修改限mod-raidtest/dev；core/Playerbot与mod-playerbots/master无改动。
- 四线程增量编译、安装通过；git diff --check通过；功能修改已装载运行。服务器保持运行，日志配置仍为原值AiPlayerbot.LogInGroupOnly=1。
- 本地原始events-run67.tsv、worldserver-run66.log、worldserver-run67.log、build-lifecycle-fix.log已归档（日志/TSV按gitignore不提交）。
- 复算：`python3 docs/investigations/run55/audit_tanks.py docs/investigations/run55/events-run67.tsv`，脚本已支持一个run多个attempt。
- 验证范围为现有Loatheb阵容及上述复用路径，未据此宣称其他团本全部完成回归。已观测到的三项问题在此路径关闭。

代码提交：mod-raidtest/dev `931758e`（fix: register raid groups and restore repeatable tank encounters）。
