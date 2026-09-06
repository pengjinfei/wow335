# Boss 验证台账

更新：2026-09-06。每行结果限定版本、装备、难度和辅助配置；未填不代表支持。

| 场景 | 最近证据 | 当前判定 | 下一步 |
|---|---|---|---|
| heroic-uk-keleseth，五人 heroic5-v1 | run86/a1清怪→恢复→boss零死亡击杀，总212.818秒；a2恢复五个出生点后清怪误伤boss被拦截；框架3b9203b | 前置/重置/保护实测；未认证连续稳定通关 | 修正清怪误伤boss，复测恢复预算，再验收冰墓 |
| naxx-loatheb，十人 fixture-v1 | run77/a1,a2、run78/a1；3 次零死亡击杀；框架 8f06a10 | 当前配置编排回归通过；无辅助、同阶段装备及完整机制覆盖未验收 | cheat 审计后建立正常规则对照 |
| naxx-patchwerk | 已有场景配置和历史测试；未做 8f06a10 固定角色回归 | 待本版本验证 | 完成基线口径核验后复测 |
| 其他 WLK boss | 仅源码覆盖初查 | 未验收 | 按 WORKFLOW 新建逐 boss 记录 |

Loatheb 证据：[终局与登录竞态](../investigations/roster-fixture/GROUP-LOGIN-RACE.md)、[角色指纹](../investigations/roster-fixture/FINGERPRINTS.json)。历史 run 不按记忆追补“通过”。

新 boss 的记录放 `docs/testing/bosses/<scenario>/README.md`，复制 [模板](BOSS-TEMPLATE.md)。状态采用：待审计 / 待运行 / 框架阻断 / 策略失败 / 当前配置击杀 / 正常规则机制验收通过。完整记录应同时保留失败尝试。

当前优先五人线：[凯雷塞斯王子记录](bosses/heroic-uk-keleseth/README.md)。用户已将 Patchwerk 复测后移。
