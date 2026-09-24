# 测试文档索引与组织规则

本目录按“入口 → 当前状态 → 遭遇记录 → 证据/历史”组织；不要再把完整实验叙事追加到总台账。

## 读者入口

| 目的 | 先读 |
|---|---|
| 新会话接手 | [`../START-HERE.md`](../START-HERE.md) → [`BOSS-LEDGER.md`](BOSS-LEDGER.md) → 当前 campaign handover/encounter README |
| 推进一个 boss | 该 boss 的 `bosses/<scenario>/README.md` → [`LESSONS.md`](LESSONS.md) → [`WORKFLOW.md`](WORKFLOW.md) |
| 新建 5 人或团队 campaign | [`CAMPAIGN-TEMPLATE.md`](CAMPAIGN-TEMPLATE.md) → [`BOSS-TEMPLATE.md`](BOSS-TEMPLATE.md) → [`WORKFLOW.md`](WORKFLOW.md) |
| 查历史论证 | `archive/` 的冻结入口，或对应 boss README 的历史章节 |
| 查跨 boss 缺陷/方法 | [`LESSONS.md`](LESSONS.md)、[`SOURCE-COVERAGE.md`](SOURCE-COVERAGE.md) |
| 查已识别、未排期的后续优化项 | [`BACKLOG.md`](BACKLOG.md) |

## 信息分层

1. **START-HERE**：当前唯一工作面、运行状态、下一步和硬约束；保持短小。
2. **BOSS-LEDGER**：跨 campaign 的结果索引，只保留当前口径、证据链接和状态。
3. **campaign README**（例如 `bosses/heroic-hos/README.md`）：副本范围、boss 列表、共享前置/场景边界。
4. **encounter README**（例如 `bosses/heroic-hos-tribunal/README.md`）：唯一的实验叙事、假说、样本、决策与下一步。
5. **HANDOVER**：一次会话的紧凑增量；下一次交接应把仍有效的结论折回 encounter README，而不是无限增长。
6. **LESSONS**：仅可迁移的方法/缺陷；不能复制某个 boss 的逐 run 叙事。
7. **BACKLOG**：已识别但未排期的后续优化项，每项一句问题 + 证据链接 + 方向；排期后移入设计文档或 encounter README。
8. **archive/**：冻结的旧入口和被替换的大型历史台账，只读追溯，不作为当前事实来源。

## 状态词（全项目统一）

- **待审计**：尚未确认场景、机制或框架可承载性。
- **框架阻断**：未得到有效战斗样本；先修/验证编排前提。
- **调查中**：已有有效样本，但没有受证据支持的单一变量。
- **候选未验收**：变量已实现或提出，但尚未满足执行/效果验收。
- **当前配置击杀**：有有效 kill；样本不足以称稳定或机制验收。
- **稳定击杀**：预先声明的样本/边界已满足；仍须写清是完整、隔离或 fixture 口径。
- **完成**：campaign 预先声明的每个必需 encounter 都已达目标。不得由单 boss 或隔离样本外推。

## 写入规则

- 每次有效结论只写一次：**详情在 encounter README，摘要在 ledger，当前动作在 START-HERE**。
- 每条结果必须写：场景、装备档、难度、cheat、fixture/范围、版本或二进制边界、样本分母，以及证据路径。
- 同一分母只收同一基线的 lifecycle 样本；smoke、诊断、abort、fixture 或基线变更样本明确分列。
- 代码改动先写假说与执行验收，再写效果；`mod-raidtest` 不代打。
- 大型逐 run 原始叙事、临时日志路径和已否定路线放 encounter README 或 archive；ledger 不重复。
- 新团队副本使用 `bosses/<raid-key>/README.md` 作为 campaign README；每个 encounter 另建 `bosses/<raid-key>-<boss-key>/README.md`。团队规模/roster 另在 campaign README 固定，不能与 5 人样本混算。

旧入口冻结于 [`archive/START-HERE-2026-09-21.md`](archive/START-HERE-2026-09-21.md) 与 [`archive/BOSS-LEDGER-2026-09-21.md`](archive/BOSS-LEDGER-2026-09-21.md)。
