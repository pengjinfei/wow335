# 英雄魔枢 / 整本通关 / `heroic-nexus-run-h5g`

设计：[08-整本通关与AI带队](../../../08-整本通关与AI带队-设计.md)。第二个整本通关副本，用来验证路线工具与领队逻辑是否通用。
阵容 `heroic5gear-n5talents-v2`（ilvl 200 档）。

## 机制

- 场景与乌特加德城堡相同（`DungeonRun = 1`，入口准备点 145.9,-10.6,-16.6）；完成判据 `KillOnBossState = 3`（凯瑞斯塔萨）。
- 路线 `mod-playerbots data/dungeon-routes/576-the-nexus.route`：TravelNode 链 入口 → 大厅 → 泰蕾丝塔 → 阿诺玛鲁斯 → 奥莫洛克 → 回大厅，
  2514 码骨架、86 组；`tools/route-gen/overrides/576-the-nexus.txt` 把凯瑞斯塔萨挪到最后，并加三个 `object` 条目：
  三个封印球体要在各自的 boss 死后由玩家点一下，全部点过凯瑞斯塔萨才离开冰封牢笼。领队走过去用它（`object` 是新加的路线条目）。

## 逐次记录（2026-09-30）

| 版本 | run | 到达 | 结果 | 原因 → 修复 |
|---|---|---|---|---|
| v1 | 1814 | 大厅 | 115 秒团灭 | 凯瑞斯塔萨一开场就出手：raidtest 重置场景 `RemoveAllAuras` 清掉了她的冰封牢笼，又没跑 AI `Reset`（只有带前置怪的场景才跑）→ 清完光环总是 `Reset`（共享改动，需回归其他 boss 场景）；另加封印球体 `object` 条目 |
| v2 | 1815 | 630 码（泰蕾丝塔） | 卡住中止 | 引力井脚本 `MoveJump` 把目标抛到地面上 5–15 码的空中点，客户端会自己落地，bot 停在空中；坦克悬在 z −3，同层守卫拒绝下落 13 码 → playerbots `AiPlayerbot.EmulateGravity`：停在离地 2 码以上的空中时 `MoveFall` |
