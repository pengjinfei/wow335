# 新会话接手（更新：2026-09-08）

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
| azerothcore-wotlk | Playerbot | `413bea61a85e20d9caef7d66fc601a661fdddd9d` |
| modules/mod-playerbots | codex/heroic-uk-ingvar | `22c1beab2aa08fd3e685cedff4aa08754fca9545`（基于 `b949b50b` 的三项因格瓦尔策略修复） |
| modules/mod-raidtest | dev | `ef037da`（导航节点到达确认与仅导航探针；`origin/dev` 之前 5 个提交） |

2026-09-08 四个工作区均干净。core 未作本地改动；因格瓦尔策略修复在本地 `mod-playerbots` 分支，框架改动在本地 `mod-raidtest` `dev`，两者均未合并到各自上游基线。

## 当前进展与待办（2026-09-08）

五人基线为 heroic、5 人、early-WLK heroic 装备（ilvl 200 上限）；已核验的 run79/80/86 五人快照有效 cheat 掩码均为 0。历史 Loatheb 使用的十人高装等基线和其 cheat 审计保留在台账中，不作为当前五人线的通关证据。

- 凯雷塞斯：run86 完整链路零死亡击杀，run91/92 共三场零死亡击杀；冰墓与连续稳定性尚待验收。
- 斯卡瓦尔德与达隆：run127 重启后同实例零死亡击杀；房间小怪清理与更多冷启动样本尚待验收。
- 因格瓦尔：run116、run130 在 ilvl 200 戒律牧队中完成 P1→复活→P2 击杀。`mod-playerbots` 的开局嫁祸/误导、绕背与暗影斧规避修复已在隔离战中得到击杀证据；`mod-raidtest` 的前置、重置和导航到达确认也已有单项验证。完整链路尚未通过：斯卡瓦尔德与达隆房间到骑手平台的当前 MMap 没有严格路线。

接续顺序：

1. 只用服务端做下层与平台两端的双向连通分量/过渡机制分析；不写入猜测的楼梯坐标、不用跨层传送替代行走。客户端仅在服务端资产与实际可达性矛盾时作为最终核验。
2. 找到可复现根因后，再提交最小的地图资产、寻路或框架修复；以冷启动、含三名骑手前置怪的完整链路回归验证。
3. 因格瓦尔完整链路通过后，回到凯雷塞斯冰墓和双 boss 房间清怪的机制验收，再按台账逐个扩展五人本 boss。

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
