# Wow335 — 项目接手入口

新会话先读 [docs/START-HERE.md](docs/START-HERE.md)。它提供当前基线、已验证结果、限制和下一步；再读 [boss 台账](docs/testing/BOSS-LEDGER.md) 及对应 boss 记录。

项目目标：验证 mod-playerbots 在正常规则下处理副本机制并通关，必要时在自己的开发分支优化底层。mod-raidtest 只编排和观察。

- 根目录 AGENTS.md 是会话工作约定；核心及模块各自的 AGENTS.md 同样适用。
- [测试/fork/交接流程](docs/testing/WORKFLOW.md)
- [真人实机验证流程（Windows 客户端连 Mac）](docs/testing/HUMAN-SESSION.md)
- [逐 boss 记录模板](docs/testing/BOSS-TEMPLATE.md)
- [源码覆盖与辅助行为](docs/testing/SOURCE-COVERAGE.md)
- [环境搭建](docs/02-环境搭建手册-macOS.md)
- [上游与分支](docs/03-上游同步与分支策略.md)
- [框架设计](docs/04-mod-raidtest-设计.md)

旧 run55 文档和本地 .superpowers 台账用于历史调查，不作为当前状态入口。跨机器恢复还需要独立源码仓库、数据库、客户端数据及实际运行配置；管理库不包含这些产物。
