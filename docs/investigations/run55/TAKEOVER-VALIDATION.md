# run60 起接手诊断与修复（2026-09-06）

> 最新验收：[LIFECYCLE-FIX.md](LIFECYCLE-FIX.md)。run67重启后原角色、原实例连续两次零死亡击杀；DK显式主坦、首次传送、击杀后恢复三项通过。下文历史状态保留供审计。

本记录延续 TANK-ANALYSIS.md。run59 没有内部状态采样，不能把后续观测回写为 run59 的已测事实。

## 改动范围

只改 mod-raidtest 编排与观察。新增 tank_state（引擎、目标、实际攻击对象、攻击标志、主坦身份）、tank_range（距离/朝向）和策略/动作历史；首15秒每250ms，之后每秒。动作历史仅是有限环形文本，跨引擎切换会切换历史来源，不能据缺失认定某动作没有执行。临时打开 AiPlayerbot.LogInGroupOnly=0，让无真人master机器人的动作历史可见。

## run60：战前崩溃，不是战斗样本

复用 run59 角色，在 ResetInstance 强制复活旧 boss 后崩溃，没有 attempt 行，run 行 finished_at 为 NULL；保留原始数据库状态，未伪造终态。

系统报告 worldserver-2026-09-06-081318.ips：EXC_BAD_ACCESS，Object::GetGuidValue -> AttemptRunner::ResetInstance+704。对实际二进制反汇编确认 +700 是 force-respawned 日志读取 creature GUID 的调用，+704 是返回地址。原循环以结构化绑定引用 spawn store 的 creature。动态重生路径调用 AddObjectToRemoveList -> Map::AddObjectToRemoveList -> CleanupsBeforeDelete，移除世界关系；Respawn 后继续引用和迭代不安全。

修复：先收集 boss GUID 快照，再逐个重新查找；调用 Respawn 前缓存名字，之后日志使用缓存，不再读取 creature。run61 已越过同样的重置阶段进入战斗。

## run61：观察到 DK 真正掉出战斗引擎

沿用血DK686、防骑694，boss 新 lowguid869。此轮重启后复用旧角色，不能当作 run59 的严格等装备重复（装备流程仍会运行）。

- 250ms：两坦 engine=0、combat=true、victim=869、melee=true。DK mt=false，防骑 mt=true；二者 explicit=false。
- 2521ms：DK 动作历史记录 reset botAI - OK，重新加载默认策略。
- 12113ms：DK仍为战斗引擎且攻击boss。
- 12374ms：DK engine=1，但 combat=true；current target、victim、selection均为空，melee=false。非战斗策略历史中能看到先前 +attack tagged，然后整个默认策略集重载，当前策略已无 attack tagged。
- 此后仍执行 loatheb position；choose target 反复失败；不能称为整个AI停摆，也不支持单纯站位动作饿死职业循环。

ResetAiAction 重置策略本身没有切到非战斗引擎。DropTargetAction 则同时清目标、切非战斗引擎、AttackStop，符合观测状态；当前动作历史在换引擎时切换，尚未直接记录该动作，不能写成已直接抓到 drop target。

run61终态：300002ms timeout，boss最低70%，10个队员曾死亡。DK对boss11次/5356，最后一次11175ms；防骑138次/100143，最后一次47986ms。DK样本engine=0/1/2分别53/284/6；死亡与后续复活会影响全场引擎占比。

## 确认的建团缺陷与因果链

RosterLogin::FormGroup 调用 Group::Create 后没有 sGroupMgr->AddGroup。核心 Group::Create 不负责注册；GroupHandler 正常接受邀请及 mod-playerbots 的建团流程都另外调用 AddGroup。

Creature 保存 lootRecipientGroup GUID，但 GetLootRecipientGroup 通过 GroupMgr 查找。框架新建团未注册，团队归属无法解析，isTappedBy 对非首个归属玩家不能凭同团通过。AttackersValue::IsPossibleTarget 对有归属目标依赖 isTappedBy、master仇恨或 attack tagged 等条件；主坦DK的默认策略重置又会丢失框架一次性加入的 attack tagged。

InvalidTargetValue 使用该合法性检查；失败可以触发优先级99的 drop target；非战斗 LoathebChooseTarget 又从过滤后的 attackers 找boss，因而不能正常恢复。这比“DK职业循环坏了”更符合现有证据。

待对照验证：补齐 AddGroup 后，直接记录 registered、loot_group、tapped、attack_tagged；若 DK 即使失去 attack tagged 仍持续攻击，证明无需通过框架强推攻击来修复。此轮先不改主坦旗标，不改任何职业/选目标动作。


## run62 / run63

run62复用角色在重启后传送被拒，attempt1788426363以teleport stage timeout中止，duration=0，不能计入战斗效果。

run63使用force-recreate正式验证（DK696、防骑704、boss106、attempt1788426364）。已观测到group=7 registered=true loot_group=7 tapped=true。至35924ms，DK attack_tagged=false但仍engine=0、victim=106、melee=true，并记录icy touch/blood strike成功；到36331ms已造成73次/43695伤害。该状态直接支持：正确团队归属使DK不再依赖attack tagged才能持续攻击。完整终态见下表。


为何leader最先暴露：Group::Create会AddMember(leader)，AddMember调用SendUpdate，SMSG_GROUP_LIST内的membersCount是GetMembersCount()-1，即此时为0。ResetAiAction对该包的membersCount非0直接返回false，0才继续ResetStrategies。因此建团阶段的一人包可能在开战后被leader处理并清掉一次性加入的策略；run61已记录leader的reset botAI成功与策略丢失。这里修复的是团队创建契约缺失，不靠每tick重加策略掩盖问题。

后续角色问题：运行时DK mt=false、防骑mt=true且二者explicit=false，符合GetMainTankGuid无旗标时按成员引用遍历找首个活坦克。当前蓝图“DK主坦”的文字/leader身份并不等于AI主坦旗标。该问题独立于持续攻击恢复，本轮未改旗标，以保持注册修复的归因单一。


## 修复后完整战斗验证

| run | 角色处理 | 结果 | DK对boss次数/伤害 | 最后一次DK伤害 | DK战斗引擎采样 |
|---|---|---|---|---|---|
|63|force-recreate|kill 182435ms，零死亡|366 / 216903|182096ms|226/226|
|65|force-recreate|kill 181672ms，1死亡|344 / 177450|181165ms|225/225|

run63 DK有160条显式boss目标spell事件，包括冰冷触摸49909（30）、鲜血打击49930（25）、符文打击56815（21）、死亡打击49924（13）等；每个30秒区间都有伤害，非开局少量白字。防骑648次/669771，最后伤害182246ms。boss死亡事件182417ms、actor_entry=16011，后续HP=0及kill确认一致。

DK的attack_tagged在210/226次采样为false，但tapped=true、registered=true始终成立，且全部采样engine=0。boss victim采样：DK67、防骑111、猎人701两次、法师699一次。DK的AI主坦识别仍为false（226/226），说明默认主坦身份不等于该坦克能否通过真实技能争取到仇恨；本轮同时恢复了攻击与实际承伤能力。

复算：`python3 docs/investigations/run55/audit_tanks.py docs/investigations/run55/events-run61.tsv docs/investigations/run55/events-run63.tsv`。导出的原始TSV在本地，gitignore不提交。


## 未关闭的编排问题

run64复用刚击杀的角色，attempt1788426365战前以boss not found on map中止（duration=0），不能计入战斗验证。它与run62的teleport stage timeout是不同失败，不应合并归因。ResetInstance目前只处理spawn store内已加载的boss；已死亡且卸载/动态重生等待中的boss可能不在该容器，仍需单独调查实例恢复流程。此次消除了run60的悬垂引用崩溃，但没有宣称旧实例复用已完全可用。run65转回force-recreate做第二个有效战斗样本并成功击杀。


run65（attempt1788426366）DK706有154条显式boss目标spell；208/225次采样attack_tagged=false，所有归属采样registered=true、tapped=true。每个30秒区间都有伤害。防骑714在158508ms死亡；从159388到181443ms的全部23次boss victim采样均为DK706，直至181669ms boss死亡、181672ms确认kill。全场boss victim：DK24、防骑154、猎人711三次。防骑590次/503238伤害包含死亡后持续效果，不等于活到最后伤害时刻163723ms。

### 验证结论与交付状态

- 两场独立重建角色战斗均恢复DK全场攻击，且第二场在防骑死亡后由DK承伤完成击杀；没有改伤害倍率、装备属性、boss机制或职业行为。不能把击杀加速的全部幅度归于本修复（重建角色会重走装备流程）。
- 功能修改仅mod-raidtest：FormGroup补GroupMgr注册；ResetInstance避免Respawn后容器引用失效。新增只读坦克观测，没有SQL schema变更。
- `cmake --build var/build/obj --target worldserver -j 4`、安装均成功；`git diff --check`通过。mod-playerbots/master、core/Playerbot均未修改。
- 临时AiPlayerbot.LogInGroupOnly已由0恢复为原值1，并重启修复版本。后续若要动作历史，须重新临时开启0；状态/目标/归属采样仍可记录。
- 原始事件events-run61.tsv、events-run63.tsv、events-run65.tsv及worldserver-run61.log、worldserver-run62-run65.log已保存本目录（gitignore）。所有SQL操作为只读；run60未完成行保持原状。
- 仍未解决：旧实例复用的传送/找boss流程；蓝图DK主坦与AI默认识别防骑主坦不一致。持续攻击问题已经有修复及重复验证，不应继续误报为血DK职业循环普遍失效。
