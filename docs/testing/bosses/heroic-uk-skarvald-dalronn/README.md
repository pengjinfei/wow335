# 英雄乌特加德城堡：斯卡瓦德 & 达尔隆

更新：2026-09-07；当前状态：双 boss 正常规则击杀；run127 在重启后的干净实例中零死亡击杀。房间 10 只小怪清理未纳入（隔离 boss 战验证）。

## 基线

- 场景 `heroic-uk-skarvald-dalronn`；map=574，BossEntry=24200（斯卡瓦德），KillGateSpawn=126024（达尔隆生成点）。
- 英雄模板双 boss：斯卡瓦德 24200 @ (109.5,-33.7,118.86)、达尔隆 24201 @ (112.0,-40.3,118.86)。
- 五人普通小队，DungeonDifficulty=heroic(1)，PartySize=5，配置 heroic5-v1。
- 首次验证**隔离 boss 战**（无 PrerequisiteSpawns，bots 直接传送到拉怪点打 boss）。房间 10 只小怪（4 吞噬者 24084 + 6 狂怒幽灵 28419，生成点 125971/125962/125956/125967/125881/125877/125882/125880/125879/125878）留作后续：准备点难避开全部小怪的仇恨范围，需调优后再纳入清怪前置。
- 机制审计见 [UK 机制审计](../heroic-uk/MECHANICS-AUDIT.md)。

## 框架改动：KillGateSpawn（mod-raidtest）

原框架是单 boss 模型（BossEntry 单值，击杀=被跟踪 creature 血 0 + 死亡事件）。双 boss 斯卡瓦德先死会变幽灵、达尔隆继续，框架会**提前误判 Kill**。新增场景字段：

```
KillGateSpawn = 126024
```

- 击杀判定（AttemptObserver）：BossEntry 死后仍需 KillGateSpawn 的目标收到真实死亡事件才判 Kill（`hpPct==0 && BossDeathSeen() && !gatePending`）。
- 卡壳判定（AttemptObserver）：gate 未死期间 encounter 仍进行，`boss lost combat` 的 abort 挂起，终态交给 Kill/Wipe/Timeout。
- 启动（AttemptRunner AwaitAttemptRow）：解析 gate 生成点→登记死亡跟踪；允许 gate 已参战（它是必打目标）。
- 重置（ResetInstance）：gate 生成点纳入重置范围，逐场恢复。

改动文件：`src/Scenario/Scenario.{h,cpp}`、`src/Orchestrator/RunContext.h`、`src/Orchestrator/AttemptRunner.cpp`、`src/Observer/AttemptObserver.cpp`。

## 验证

| run / attempt | 结果 | 时长 | deaths | boss 最低 HP |
|---|---|---|---|---|
| 94 / 1 | kill | 58.8s | 0 | 0% |
| 96 / 1 | kill | 56.0s | 0 | 0% |
| 96 / 2 | kill | 59.1s | 1 | 0% |
| 127 / 1 | kill | 48.6s | 0 | 0% |

连续 4 次击杀。双 boss 均被击杀：达尔隆先死→召唤幽灵→斯卡瓦德后死→击杀判定（KillGateSpawn 生效）。run127 使用戒律牧、ilvl 200 基线，并在重启后由队长先建实例、其余成员进入该实例；无死亡完成击杀。run96/a2 有 1 死（bot 阵亡但队伍仍完成击杀）。

## 机制

冲锋 43651、石击 48583、英雄版狂暴 48193（≤60%）；暗影箭 43649、衰弱 43650、英雄版召唤骷髅 52611；一方死亡召唤幽灵(27390/27389)继续战，双杀才过关。全部与官方一致（审计见上）。

## 遗留

- 房间 10 只小怪的清怪前置未纳入（准备点仇恨范围问题），后续调优。
- 连续稳定通关（更多场次）未验收。
