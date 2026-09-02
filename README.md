# WoW 3.3.5a 机器人团本项目（wow335）

基于 AzerothCore + mod-playerbots，目标：不修改伤害倍率/装备/BOSS 机制，
用机器人打通 WLK 全部团队副本。

## 本目录是什么

这是**项目管理库**：只放文档和脚本。上游源码克隆在 `azerothcore-wotlk/`
子目录（独立 git 仓库，已被 .gitignore 排除）。

## 目录

| 文件 | 说明 |
|---|---|
| [docs/01-构建体系分析.md](docs/01-构建体系分析.md) | 上游工程结构、cmake/DB/配置/模块机制拆解 |
| [docs/02-环境搭建手册-macOS.md](docs/02-环境搭建手册-macOS.md) | 从零到服务器跑起来的分步手册（新机器照这个来） |
| [docs/03-上游同步与分支策略.md](docs/03-上游同步与分支策略.md) | git 分支模型、上游更新同步流程 |
| [scripts/setup-macos.sh](scripts/setup-macos.sh) | 一键搭建（依赖→克隆→配置→编译→建库） |
| [scripts/sync-upstream.sh](scripts/sync-upstream.sh) | 上游同步（报告/应用两种模式） |

## 快速开始（新机器）

```bash
git clone <本仓库> wow335 && cd wow335
./scripts/setup-macos.sh          # 依赖、克隆、编译、建库
# 然后按 docs/02 第 6~8 步：客户端数据提取、配置、启动
```

## 上游仓库

| 仓库 | 分支 | 作用 |
|---|---|---|
| mod-playerbots/azerothcore-wotlk | `Playerbot` | 核心服务端（必须用此 fork，标准 AC 编不了） |
| mod-playerbots/mod-playerbots | `master` | 机器人模块（策略代码在其 `src/Ai/`） |

## 项目阶段

- [x] 阶段 0：可行性分析、副本覆盖现状调研
- [ ] **阶段 1：环境构建 + 文档（进行中）**
- [ ] 阶段 2：10 人小队成型，纳克萨玛斯首 BOSS 流程跑通
- [ ] 阶段 3：团测自动化框架（无客户端闭环验证）
- [ ] 阶段 4：按副本逐个攻坚
