# 新会话接手（更新：2026-09-09）

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
| 管理库 | main | `a54e636`（本次收尾前的文档状态） |
| azerothcore-wotlk | Playerbot | `516b14df1`（map 574 诊断与长路线容量） |
| modules/mod-playerbots | codex/heroic-uk-ingvar | `c23bd70e`（Ingvar 紧急移动、斧安全环与控制观察） |
| modules/mod-raidtest | dev | `7841ba2`（角色分离 fixture、动作/生命/治疗与机制观察） |

2026-09-09 上述源码提交均为本地分支提交，尚未同步或合并上游。`env/dist` 下的日志、角色 TSV 与场景快照为可再生成测试工件，不纳入提交；接手时仍需逐库执行 `git status`。

## 当前进展与待办（2026-09-09）

五人基线为 heroic、5 人、early-WLK heroic 装备（ilvl 200 上限）；已核验的 run79/80/86 五人快照有效 cheat 掩码均为 0。历史 Loatheb 使用的十人高装等基线和其 cheat 审计保留在台账中，不作为当前五人线的通关证据。

- 凯雷塞斯：run86 完整链路零死亡击杀，run91/92 共三场零死亡击杀；冰墓与连续稳定性尚待验收。
- 斯卡瓦尔德与达隆：run127 重启后同实例零死亡击杀；房间小怪清理与更多冷启动样本尚待验收。
- 因格瓦尔：平台角色分离 fixture 已持续通过 5/5 位置门禁；新基线的三次独立 cold start 为 **2/3 击杀**，尚不能称为稳定。P1 的旧共同前方出生点问题已由 fixture 隔离；P2 仍有暗影斧、治疗余量和 `59709` 控制窗口的组合风险。最新 run249 证明斧可在英雄暗影猛击 `59709` 后 13ms 出现：`CanMove=false` 是正常 stun，并非旧移动等待，禁止用框架强制走位绕过它。详见 Ingvar 记录末尾。
- 寻径：map 574 的上下端已实测在同一 4,562-poly Detour 连通分量；此前失败分别是 1,024 查询节点耗尽与 148-poly 输出截断，而非已证实的楼梯断网。核心现为长路线提供 4,096 节点查询和 playerbots 512-poly/point 容量；run168 已取得完整地面路径。首段 NavigationOnly 通过同实例门禁，但会进入斯卡瓦尔德/达隆近战范围，故尚不能作为完整副本安全通行证据。

接续顺序：

1. Ingvar：只读比较每把斧首次进入危险半径与 `59709` 控制窗口的先后。可行动时仍未预离开，才可针对预站位/时机做最小 playerbots 修复；首次出现即已受控则记录为正常机制风险，再分析前置站位和治疗余量。
2. 以同一 fixture、heroic、ilvl 200、零 cheat 做新的独立 cold-start 回归；不得与 6577–6579 之前或单场诊断样本混算稳定率。稳定标准与样本数在执行前写入 Ingvar 记录。
3. 完整副本自主通关：在安全的前置怪清理链与可验证移动段下，继续验证斯卡瓦尔德/达隆房间至平台的实际行走。利用已确认的完整 Detour 路线做分段到达和危险半径门禁；不得用猜测楼梯点、跨层传送或空房间传送伪造行走。
4. Ingvar 机制稳定且跨房间移动安全后，才将“凯雷塞斯→双 boss→三骑手→Ingvar”的完整链路列入验收；随后回到凯雷塞斯冰墓和双 boss 房间清怪的机制验收。

## 记录与提交规则

临时扫描、探针、日志和猜测性实现只用于定位，完成当轮后删除或保留在未提交工作区；不要为它们单独提交文档或代码。只在以下节点提交：可复现的问题根因及其已验证修复、改变复现基线的框架/配置、或 boss 验收结论与其必要证据。文档与代码在同一关键节点一起更新，避免按试验次数堆叠提交。

入口：[heroic5-v1 配置](testing/fixtures/heroic5-v1/README.md)、[凯雷塞斯王子记录](testing/bosses/heroic-uk-keleseth/README.md)、[斯卡瓦德&达尔隆](testing/bosses/heroic-uk-skarvald-dalronn/README.md)、[因格瓦尔](testing/bosses/heroic-uk-ingvar/README.md)、[UK 机制审计](testing/bosses/heroic-uk/MECHANICS-AUDIT.md)。

之前的“先复测 Patchwerk”计划暂后移。新会话优先接续五人英雄本台账，并查实际运行是否已结束；不要同时启动另一轮。

## 新会话第一轮

- 逐库读 git status/branch/HEAD；检查是否有其他测试占用 worldserver。
- 先读 `raidtest status`，再查询数据库 run 的 finished_at。活动 attempt 行可能暂为 aborted/0/NULL，占位行不代表最终失败。
- 进程、FIFO 和 /tmp 日志均需重新核验，不能依赖上一会话 PID。
- 提交结果保存在 docs；完整事件在本地 MySQL，角色 TSV 在 worldserver 工作目录。跨机器需另行导出数据/配置/快照；只克隆管理库无法重现全部运行环境。

## 可复制给新会话的启动指令

> 接手这个项目。先读根目录 AGENTS.md、docs/START-HERE.md 和 docs/testing/BOSS-LEDGER.md，再检查各仓库状态与当前运行任务。按文档中的下一步推进，区分框架回归和正常规则机制验收；不要自动同步上游或改变基线。只在已验证修复、基线变化或关键验收节点更新文档并提交，不依赖旧聊天。
