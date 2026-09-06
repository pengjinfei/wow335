# 新会话接手（更新：2026-09-06）

## 目标与阅读顺序

验证机器人能否按正常规则处理 WLK 副本机制并通关，必要时在自己的 mod-playerbots/core 开发分支修复。框架不得代选技能、代走位、修改仇恨或削弱 boss。

1. 本文件：当前状态与下一步。
2. [boss 台账](testing/BOSS-LEDGER.md)：哪些结果已证实。
3. [测试与修复流程](testing/WORKFLOW.md)：新 boss、复现、fork 修复和交接。
4. [代码覆盖与辅助行为](testing/SOURCE-COVERAGE.md)：不能把策略文件存在当作正常机制通关。
5. 仅按需要读取 [角色验收](investigations/roster-fixture/README.md)、[登录竞态](investigations/roster-fixture/GROUP-LOGIN-RACE.md)、[就绪评估](investigations/roster-fixture/READINESS.md)。

## 已知基线（接手时重新核对，不当作运行中进程的自动证明）

| 仓库 | 分支 | 最近确认的 HEAD |
|---|---|---|
| 管理库 | main | cf295fc 为上一轮五人配置提交；本交接更新之后以 git log 为准 |
| azerothcore-wotlk | Playerbot | 47960183bb03b83e8943eb2f0f39c16df9710c9d |
| modules/mod-playerbots | master | 2f7d9f774987d0157c6a0d0cc08c40bec3db3945 |
| modules/mod-raidtest | dev | 3b9203b（清怪前置与范围重置；完整HEAD见git log） |

核心与机器人代码未做本地修改；框架 dev 尚未合并 main。此前提交未 push。机器人 origin 指向上游，尚未配置自己的 fork remote；不能把“本地克隆”称为已建立远端 fork。

## 最新结论

- 十人 fixture-v1 固定装备/宝石/附魔/雕文/技能要求；全员 71 点天赋、六雕文，实际快照校验通过。
- 这是 ICC/红玉级别混合高装等能力基线，血 DK 使用橙斧；不是 NAXX 同阶段配装。
- run77 两场和 run78 同进程复用：122774 / 105958 / 121639ms，均零死亡击杀 Loatheb；30 份快照与旧固定基线一致。
- 登录清理离队包晚于新团建立是前次回归失败根因；8f06a10 等待 holder 注册及会话包处理完成再建团。
- **2026-09-06 读取实际配置发现 `AiPlayerbot.BotCheats = "food,taxi,raid"`**（`env/dist/etc/modules/playerbots.conf`）。这是磁盘配置核验，不能替代运行时逐 bot 有效掩码与动作触发核验。已有结果不证明无辅助通关，也未证明 cheat 导致 Loatheb 击杀；角色指纹当前不包含 cheat 开关。
- ICC/奥杜尔/红玉还发现直接加减光环、击杀单位或回蓝的源码路径，部分有 cheat 开关，部分不能假定受该开关控制。

## 当前任务（2026-09-06：用户调整方向）

用户决定先从五人本开始，明确选择早期英雄本毕业档位，不含冠军试炼和 ICC 三本。已新增防骑/神牧/战斗贼/火法/元素萨满，固定 ilvl200；五人/英雄难度框架适配已构建并实测。凯雷塞斯 run91/a1、run92/a1、run92/a2 连续三场零死亡击杀（再拉怪门槛修复）；斯卡瓦德&达尔隆 run94/96 三场击杀（KillGateSpawn 框架改动，双 boss 双杀判定）；因格瓦尔 run95/97 两次 P2 团灭（机制完整运行，bots 打不过=mod-playerbots 绕背策略缺陷，未改策略）。UK 三 boss 机制审计通过（与官方一致）。详见[UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)及各 boss 记录。下一步：修因格瓦尔绕背策略（触发器/远程/斧子规避）后复测；连续多场与冰墓机制验收；双 boss/因格瓦尔房间小怪清怪前置调优。

入口：[heroic5-v1 配置](testing/fixtures/heroic5-v1/README.md)、[凯雷塞斯王子记录](testing/bosses/heroic-uk-keleseth/README.md)、[斯卡瓦德&达尔隆](testing/bosses/heroic-uk-skarvald-dalronn/README.md)、[因格瓦尔](testing/bosses/heroic-uk-ingvar/README.md)。当前运行配置已从 food,taxi,raid 改为空，run79/80及run86 实际五人快照有效掩码均为0；旧 run77/78 的结论不追溯改写。构建后须重核该配置，不能假设持续关闭。

之前的“先复测 Patchwerk”计划暂后移。新会话优先接续五人英雄本台账，并查实际运行是否已结束；不要同时启动另一轮。

## 新会话第一轮

- 逐库读 git status/branch/HEAD；检查是否有其他测试占用 worldserver。
- 先读 `raidtest status`，再查询数据库 run 的 finished_at。活动 attempt 行可能暂为 aborted/0/NULL，占位行不代表最终失败。
- 进程、FIFO 和 /tmp 日志均需重新核验，不能依赖上一会话 PID。
- 提交结果保存在 docs；完整事件在本地 MySQL，角色 TSV 在 worldserver 工作目录。跨机器需另行导出数据/配置/快照；只克隆管理库无法重现全部运行环境。

## 可复制给新会话的启动指令

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md 和 docs/testing/BOSS-LEDGER.md，再检查各仓库状态与当前运行任务。按文档中的下一步推进，区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。每轮把证据、提交状态及下一步写回 boss 记录，不依赖旧聊天。
