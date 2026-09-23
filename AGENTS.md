# 项目接手入口

每个新会话先读 `docs/START-HERE.md`，再读当前任务对应的调查或 boss 记录。

- 项目验证 mod-playerbots 在正常游戏规则下的副本策略；mod-raidtest 只编排和观察。
- 管理库、核心、mod-playerbots、mod-raidtest 是独立 Git 仓库，逐库确认分支、HEAD、未提交改动。
- 当前状态以 `docs/START-HERE.md` 和 `docs/testing/BOSS-LEDGER.md` 为入口；旧 run55 启动词与本地 `.superpowers` 台账仅作历史证据。
- 编译遵循用户当前授权；没有编译授权时先询问。默认四线程 `MTHREADS=4`。子仓库另有 AGENTS.md 时一并遵守。
- 不自动同步上游或改变装备/cheat/难度来获得击杀。基线改变须单独记录和回归。
- 每轮完成更新 boss 记录、台账及下一步；临时路径和聊天记录不能是唯一证据。持久化不等于每轮提交：只在完整、可复核的阶段性结论（例如 cohort 开闭、已验证修复、明确 blocker）提交；运行中状态、构建进度和单次等待应随下一阶段合并。
