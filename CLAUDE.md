# Wow335 — WoW 3.3.5a 机器人团本项目

> 本文件是**接手续航文档**：任何新会话从阅读本文件开始，即可完全接手当前工作。
> 配套文档在 `docs/`（见 §7），进度台账在 `.superpowers/sdd/progress.md`。

## 1. 项目是什么

在 AzerothCore Playerbot fork 上，用 **mod-playerbots 的智能机器人** 打通 WotLK（巫妖王之怒）全部团队副本，**不修改伤害倍率 / 装备属性 / boss 机制**——机器人使用既有 AI 机制真实战斗，通过"战斗日志 → 策略验证 → 反复优化"的闭环逐副本攻坚。

**核心载体**：`mod-raidtest` 自动化团测框架——它**编排与观察**（建号/组队/传送/开怪/判定/记录/位置采样），**不代写任何 bot 行为逻辑**（见 §4 边界原则）。

## 2. 仓库拓扑（三层 git）

```
~/IdeaProjects/github/wow335/                  ← 管理库（本文件所在；文档+脚本，get 可管）
├── docs/                                       ← 设计/手册/计划（见 §7）
├── scripts/                                    ← setup-macos.sh / sync-upstream.sh
├── .superpowers/sdd/progress.md                ← ★ 实施进度台账（接手必读）
├── azerothcore-wotlk/                          ← 核心 fork（独立 git，Playerbot 分支）
│   └── modules/
│       ├── mod-playerbots/                     ← 机器人模块（独立 git，master 分支；研究对象）
│       └── mod-raidtest/                       ← ★ 我们的团测框架（独立 git，main=dev 双分支）
├── clientmpq/                                  ← 客户端 MPQ（gitignore，不入库）
└── data/world/                                 ← 客户端提取数据（gitignore）
```

**分支纪律**：`mod-raidtest` 的 `main` 是发布线（已合并 A+B1+B2-1~3），`dev` 是开发线（当前修复提交在 dev，未合并 main）；上游 `Playerbot`/`master` 只读，改动走 `dev` 分支。

## 3. 环境怎么跑（已搭好，一条命令回到工作状态）

```bash
# 1) 启动数据库（mysql@8.4，不要用 brew mysql 9.x——protobuf 依赖崩）
# 2) 启动服务器（FIFO 控制台模式，日志与命令分离）
pgrep -f worldserver | xargs kill 2>/dev/null; sleep 2
cd ~/IdeaProjects/github/wow335/azerothcore-wotlk/env/dist/bin
rm -f /tmp/ac_world_fifo && mkfifo /tmp/ac_world_fifo
nohup ./worldserver < /tmp/ac_world_fifo > /tmp/worldserver.log 2>&1 &
nohup bash -c 'exec 8>/tmp/ac_world_fifo; while true; do sleep 60; done' >/dev/null 2>&1 &
# 3) 等 ~30s 到 "World Initialized"（日志见 /tmp/worldserver.log）
# 4) 发命令（经 FIFO）：
echo ".raidtest run naxx-loatheb --attempts 3" > /tmp/ac_world_fifo
```

- 数据库：4 库 `acore_auth/characters/world/playerbots`；账号 `acore/acore`；`mysql -uacore -pacore acore_characters` 查结果
- 结果表：`raidtest_runs / raidtest_attempts / raidtest_events`（约 16 万行事件积累至今）
- 已注册场景：`naxx-patchwerk`、`naxx-loatheb`（场景=配置文件，加新 boss 丢一个 `.conf.dist` 即可）
- **重启/复用回归（2026-09-06更新）**：run67已验证重启后首次原角色、原实例连续两次零死亡击杀，无需热身或force-recreate。传送离队窗口、显式主坦、动态boss恢复修复见 `docs/investigations/run55/LIFECYCLE-FIX.md`（mod-raidtest/dev提交 `931758e`）。

- **角色配置优化（2026-09-06）**：十人 fixture-v1 固定装备/宝石/附魔/雕文，传送后补齐 71 点天赋；开战前角色/团队门禁与实际配置快照已落地。run72–74 与修复后 run77–78 角色指纹 10/10 一致。战前团队丢失已定位为登录清理包迟到拆新团，建团等待 holder 注册及包队列处理完成后修复；run77 连续两场、run78 同进程复用均零死亡击杀 Loatheb（122774 / 105958 / 121639ms），核心与 mod-playerbots 未改。根因与证据见 `docs/investigations/roster-fixture/GROUP-LOGIN-RACE.md`。完整实施、已知限制和下一步见 `docs/investigations/roster-fixture/README.md`。

## 4. 框架定位与边界原则（★ 项目最重要的工作准则）

`mod-raidtest` 是**自动化测试框架**，不是 bot 逻辑的一部分：
- ✅ **框架职责**：编排（建号/组队/传送/开怪/判定/记录）+ 观察（战斗事件/胜负判定/归因/**位置采样**）
- ❌ **禁止**：在框架里写"移动 bot 站位 / 改仇恨 / 代选技能"等 bot 行为逻辑来绕过底层缺陷
- 若底层机制不足 → **如实记录为 mod-playerbots 的发现**，修复落在 mod-playerbots（研究对象）或记为已知限制

**为什么**：这个框架的目的就是验证 mod-playerbots 底层机制能否正确处理各种 boss 机制并最终击杀。框架一旦代写了 bot 逻辑，就污染了观察对象，验证失效。

## 5. 历史进度（2026-09-04；最新结果见 §3）

### 已完成并合并 main

| 阶段 | 内容 | 关键提交 |
|---|---|---|
| **A** | 框架全链路：建号/登录/组队/传送/开战/判定/事件流/命令层 | `66af8ce` |
| **B1** | 攻坚底座：AI 激活（方案 b）/ 最高档装备(ilvl284) / 实例重置 / **可信判定**（修复假 kill bug） | `e9cf348..bff00be` |
| **B2-1** | **输出循环激活**：模块侧启用 `attack tagged` → DPS 施法 4→205-321 次/场，boss 血开始下降 | `8beff62` |
| **B2-3** | **位置采样**：框架能记录 bot/boss 坐标，站位验证有据可依 | `e09f2af` |

### 关键技术发现（被数据证实）

1. **底层站位机制成熟且逐 boss 定制**：Loatheb 位置采样证实坦克站 `mainTankPos`、远程站 `rangePos` ✅
2. **Patchwerk 是全叠近战的"特例"**：它的站位动作被上游注释（`NaxxActions_Patchwerk.cpp` 整段 `//`），不是底层缺失
3. **当时瓶颈（现已解决，见 §3）**：Loatheb 站位正确但 attempt 仍 aborted（~28s，boss lost combat, hp 98%）——战斗流程层面问题，**下一步深挖对象**
4. **判定可信**：Kill 需"boss 死亡事件+血量=0"双条件，杜绝假阳性（曾有 `!bossKnown` 误判 bug 已修）

### 当时 git 状态
- `mod-raidtest`: `main = dev = e09f2af`
- 管理库：docs 已整理提交

## 6. 下一步（2026-09-06 更新）

1. **扩展验证**：先用固定十人配置复测 Patchwerk，再逐 boss 扩展；建立副本阶段装备基线和机制覆盖记录。当前就绪范围与验收流程见 `docs/investigations/roster-fixture/READINESS.md`。
2. **已知底缺陷清单**（可向 mod-playerbots 上报/研究）：
   - Patchwerk 站位动作未启用（`PatchwerkRangedPositionAction` 被注释）
   - 无 master bot 的输出循环依赖 `attack tagged` 策略（已模块侧启用，可考虑上游化）

## 7. 文档索引

| 文档 | 内容 |
|---|---|
| `docs/01-构建体系分析.md` | 上游工程/macOS 构建/已知坑（mysql@8.4、config.sh、Apple Silicon 路径） |
| `docs/02-环境搭建手册-macOS.md` | 新机器从零搭建（照做即可） |
| `docs/03-上游同步与分支策略.md` | git 模型、`sync-upstream.sh` |
| `docs/04-mod-raidtest-设计.md` | 框架整体设计（场景驱动/事件流/命令层） |
| `docs/05-mod-raidtest-B1-攻坚底座-设计.md` | B1 设计 |
| `docs/06-mod-raidtest-B2-激活输出循环-设计.md` | B2 设计（方案 b：模块侧 attack tagged） |
| `.superpowers/sdd/progress.md` | ★ 完整实施台账（每阶段/每审查/每 Minor） |

## 8. 记忆与习惯

- **编译前必须征得用户同意**（本机编译会卡死）；默认低负载 `MTHREADS=4` + ccache，`./acore.sh compiler build`
- 全流程有编译授权时用 `sync-upstream.sh` 同步上游，绝不直接改上游分支
- 语言：用户用中文交流，文档用中文
- 数据库查询走 `export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"`