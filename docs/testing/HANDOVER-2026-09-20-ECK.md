# 交接：艾克收尾 → 英雄岩石大厅接手（2026-09-20）

## 本轮已收尾：英雄古达克·凶残的艾克（29932）

- **正常规则已验证通过**：累计有效 **10/10 kill、零死亡、68.869–90.714s**。
- 场景：`heroic-gd-eck-n5`，英雄、normal5-v1、`AiPlayerbot.BotCheats = ""`、无 fixture。
- 原生链已实测：Dweller 编队 **127203/127201/127202** 全灭 → instance script summon 29932 → 原生 auto-engage → kill。
- `BossSpawnMode=script` 已落地：允许无 DB spawn 的 boss，以前置 spawn 作为 reset 合约，解析临时 creature，支持显式 `ScriptBossAcceptAutoEngage=1`。
- run691 seq5 是历史无效：前置完成、无 29932 事件、appearance timeout；不混入胜率。run692 连续 5/5 未复现。
- 临时 core 诊断日志已**移除**，`instance_gundrak.cpp` 恢复原样；无 core 机制改动。
- DB 默认路径最小烟测：run693 `heroic-gd-galdarah-disc-n5` kill，86.991s，零死；run694 Sladran wipe 14%（既有不稳定），run695 Moorabi kill，run696 Colossus kill。全量跨副本回归仍在 `TODO-8c197583`。

详细证据：`bosses/heroic-gd-eck/README.md`、`BOSS-LEDGER.md`。

## 代码与运行状态

- 已运行 `MTHREADS=4 ./acore.sh compiler build`，成功。
- worldserver 当前为 `IDLE`，FIFO relay 正常。
- **不要假定工作树干净或已提交**：
  - `mod-raidtest` 保留本轮 `BossSpawnMode=script` 改动，以及此前莫拉比未提交改动；
  - `mod-playerbots` 也有此前未提交改动；
  - core 只应有运行日志/raidtest 输出等 untracked 文件（先 `git status` 核对）。
- 不推 fork、不提交，除非用户单独指示。

## 下一个新副本：英雄岩石大厅（HoS，map 599）

目标是**全新副本接手**，不是继续古达克回归。推荐先做首个 boss **克莱斯塔卢斯 Krystallus** 的勘测和场景设计：

1. 先审计 core 脚本、DB spawn/difficulty entry、mod-playerbots HoS 注册/trigger/action；
2. 勘测房间、前置怪、准备点/开怪点；`raidtest los` 必须逐点自探针读取真实地面 z；
3. 首场必须明确标为“隔离 boss 基线”或“正常规则完整房间”，不可混用口径；
4. 正常装备 normal5-v1、英雄、`AiPlayerbot.BotCheats=""`；不改装备/难度/cheat/boss 数值求击杀；
5. 未获新编译授权前不要编译（本轮授权仅覆盖已完成的艾克实现/验证）。

## 首读顺序

1. `docs/testing/LESSONS.md`
2. 本文件
3. `docs/testing/BOSS-LEDGER.md`
4. 开始 HoS 后，建立并持续更新 `docs/testing/bosses/heroic-hos/README.md`。
