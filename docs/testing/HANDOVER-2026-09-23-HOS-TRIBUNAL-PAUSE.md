# HoS / Tribunal 暂停交接（2026-09-23）

## 结论

- Heroic HoS 的当前可计分进度仍是 Tribunal r32 lifecycle **1/5 DONE**：仅 run745 完成；run746/748/750/751 为合格动态 wipe。
- 没有任何后续变量获得效果验收：固定 Dark Matter cohort 为 0/4（候选耗尽），Dark Matter + survivor-retry R1 为 0/5（已关闭）。两者均不得重开或混算。
- Sjonnir 已因 normal-rule 无自主 post-Tribunal 路线而跳过；没有可切换的后续 boss。
- 用户要求在此暂停：不要再启动 Gaze/其他诊断或 cohort，除非重新授权一个直接影响完成率、预先定义执行门槛的独立假说。

## 最新 Gaze 观测（均永久排除所有 cohort）

- run779：483.925s、5-death wipe。既有 Gaze flee action 16 次（13 true/3 false）；28265 有 10 条 damage event，830 的 8 条非零共 11,058。该 action 确实被调度，不能再以“未执行”作为假说。
- run780：0ms teleport-stage abort，`enter_reason=8`，不消费 smoke gate。
- 自然等待 instance-time 的最早 expiry（未清理 DB）后，run781 成功进入 map599；终态 468.984s、5-death wipe。其 timing telemetry 已把 action 和 Gaze tick 对齐：例如 826 在 tick `ms=886020` 后记录 action `ms=886447`；827 在 tick `ms=901020` 前记录 action `ms=900691`，但 tick 仍为 0 距离。该 smoke 达到“受伤 bot 可与 action 关联”的观测门槛，但没有证明任何安全行为改动会提高完成率。

## 代码与二进制状态（未提交）

- live worldserver 是 telemetry-only timing binary：SHA-256 `dae4aafbbe7db9e30af973930765fb39894f3b34eaf11019675b8cbe312f0536`，基于 core `c747f55ca`。
- `/tmp/mod-playerbots-tribunal-retry-clean`（detached `2dba88eb`）有 7 个 HoS 文件未提交：既有 Dark Matter、Searing Gaze action/trigger/context/strategy，以及 Gaze `getMSTime`、GUID、MoveAway 前后 `isMoving` INFO。不要把它误称为单一效果变量。
- `azerothcore-wotlk/modules/mod-raidtest/src/Observer/CombatEventBus.cpp` 有未提交纯观测改动：Gaze spawn/tick detail 增加同一 `getMSTime`。
- 这些改动均不改 raidtest 编排决策、bot 目标/仇恨、trigger、priority、距离或 MoveAway 行为；构建曾以 `MTHREADS=4` 通过。
- 先前 binary 备份：`/tmp/wow335-worldserver-gaze-telemetry-before-timing-cycle81`；R1 binary 备份：`/tmp/wow335-worldserver-r1-before-gaze-telemetry-cycle76`。

## 运行与文档

- 当前 server/FIFO：ready/IDLE；run781 已终态。不要把 idle 当作可以无假说继续跑的授权。
- 新旧 lifecycle、effect、smoke 的边界详见 `bosses/heroic-hos-tribunal/README.md`。该文件已记录 run779–781 和暂停决定。
- 本文件为新的暂停交接；旧 `HANDOVER-2026-09-21-HOS-TRIBUNAL.md` 是预先存在的修改，未覆盖、未整理或提交。
- 本次未提交任何内容，也未删除 `account_instance_times`、日志、roster、scene 或其他生成物。

## 若恢复工作

1. 先确认用户希望恢复，并重新审视是否值得继续 Tribunal。
2. 从 README 的失败变量排除表开始，不重跑 R1、固定 Dark Matter、r34 LOS、Protector comparator 或现有 Gaze smoke。
3. 新假说必须是单一 normal-rule playerbot 行为，明确安全边界、执行门槛和独立 cohort；先 smoke，再决定是否建 effect cohort。
4. 逐仓库确认 status，特别避免提交旧 handover、runtime logs 或不属于本人的改动。
