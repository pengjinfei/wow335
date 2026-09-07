# Boss 验证台账

更新：2026-09-07。每行结果限定版本、装备、难度和辅助配置；未填不代表支持。

| 场景 | 最近证据 | 当前判定 | 下一步 |
|---|---|---|---|
| heroic-uk-keleseth，五人 heroic5-v1 | run91/a1、run92/a1、run92/a2 连续三场零死亡击杀（再拉怪门槛修复）；run86/a1 完整链路零死亡击杀；框架3b9203b+未提交修复 | 前置/重置/保护实测；连续稳定与冰墓未验收 | 连续多场与冰墓机制验收 |
| heroic-uk-skarvald-dalronn，五人 heroic5-disc-v1 | run127/a1 重启后同实例零死亡击杀（48.555s）；历史 run94/a1、run96/a1、run96/a2 共三场击杀 | 双 boss 隔离战正常规则可通关；队长目标实例传送已实测；房间小怪清理未纳入 | 房间清怪前置调优、更多场次 |
| heroic-uk-ingvar，五人 heroic5-disc-v1 | 隔离 Boss：run116/a1 112.716s（2 死）、run130/a1 115.014s（3 死）击杀，均覆盖 P1→复活→P2；路线勘测 run145/a1 在 0ms 被 MMap 完整性核验拒绝 | 隔离 Boss 可击杀；前置 3 骑手、旧实例 worldport、全灭后夹具恢复均有单项证据。map 574 重建后斯卡瓦尔德房间→上层平台仍只有 `PATHFIND_NOT_USING_PATH` 直线 fallback，故真实路线和含前置怪冷启动未验收 | 修复/确认该段 MMap 覆盖后再写楼梯点，完成至少一次含前置怪的冷启动回归，再评估伤亡与稳定率 |
| naxx-loatheb，十人 fixture-v1 | run77/a1,a2、run78/a1；3 次零死亡击杀；框架 8f06a10 | 当前配置编排回归通过；无辅助、同阶段装备及完整机制覆盖未验收 | cheat 审计后建立正常规则对照 |
| naxx-patchwerk | 已有场景配置和历史测试；未做 8f06a10 固定角色回归 | 待本版本验证 | 完成基线口径核验后复测 |
| 其他 WLK boss | 仅源码覆盖初查 | 未验收 | 按 WORKFLOW 新建逐 boss 记录 |

Loatheb 证据：[终局与登录竞态](../investigations/roster-fixture/GROUP-LOGIN-RACE.md)、[角色指纹](../investigations/roster-fixture/FINGERPRINTS.json)。历史 run 不按记忆追补“通过”。

新 boss 的记录放 `docs/testing/bosses/<scenario>/README.md`，复制 [模板](BOSS-TEMPLATE.md)。状态采用：待审计 / 待运行 / 框架阻断 / 策略失败 / 当前配置击杀 / 正常规则机制验收通过。完整记录应同时保留失败尝试。

当前优先五人线：[凯雷塞斯王子记录](bosses/heroic-uk-keleseth/README.md)。用户已将 Patchwerk 复测后移。
