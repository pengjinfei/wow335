# Campaign 模板：<难度 / 副本名 / map>

> 本文件是副本级索引；逐次实验写进各 encounter README。

## 固定边界

| 字段 | 值 |
|---|---|
| campaign key | `<key>` |
| map / 难度 | `<map> / <difficulty>` |
| roster 与装备档 | `<roster/profile>` |
| cheat / fixture | `<value>` |
| 验收目标 | `<per-boss / full-clear / other>` |
| 二进制/配置边界 | `<commit or build>` |

## Encounter 矩阵

| encounter | scenario | 范围（完整/隔离） | 当前状态 | 证据与记录 | 下一步 |
|---|---|---|---|---|---|
| `<boss>` | `<scenario>` | `<scope>` | 待审计 | `[README](../bosses/<key>-<boss>/README.md)` | `<action>` |

## 共用场景事实

只记录会影响多个 encounter 的路径、前置、instance script、roster 或 fixture 事实；单 boss 的伤害、假说和 run 时间线留在 encounter README。

## Campaign 完成条件

- 明确哪些 encounter 必须达到何种状态。
- 明确是否需要完整副本链式验证；若当前只验 boss 机制，写明其不等于全本通关。
- 团队本必须额外固定 raid size、职业构成、分组、锁定/CD 与战斗复位政策。

## 变更日志

| 日期 | 变化 | 影响的口径 | 链接 |
|---|---|---|---|
| YYYY-MM-DD | `<change>` | `<new separate cohort / none>` | `<evidence>` |
