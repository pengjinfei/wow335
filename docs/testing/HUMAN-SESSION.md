# 真人 + bot 实机验证流程（Windows 客户端连 Mac 服务端）

用途：真人登录一个角色，带上 4 个 bot 进副本，用 `.raidtest observe` 采集与
masterless 基线同口径的证据。**观察会话不编排、不传送、不开怪、不判定**，只采样。

本文件记录的是实测踩通的流程，不是设计意图。每条「坑」都真实发生过。

## 0. 前提

- Mac 上 worldserver + authserver 已运行（见 [环境搭建手册](../02-环境搭建手册-macOS.md)）。
- Mac 与 Windows 在同一局域网。**不要**把 3724/8085 转发到公网。
- Windows 客户端路径（本机实测）：`F:\games\tianlan\WOW335Client`。

## 1. 确认 Mac 的局域网 IP —— 每次都要重新查

IP 会变，这是本项目连不上的第一大原因。

```
ipconfig getifaddr en0          # 无输出就试 en1
```

查到的 IP 必须同时出现在**三个**地方，缺一不可：

| 位置 | 怎么改 |
|---|---|
| `acore_auth.realmlist.address` | `UPDATE acore_auth.realmlist SET address='<IP>';` 改完 `.server restart` 或重启 authserver |
| 客户端 `realmlist.wtf` | `set realmlist <IP>` |
| 客户端 `WTF\Config.wtf` | 见下面的坑 |

核对当前值：

```
/opt/homebrew/opt/mysql@8.4/bin/mysql -uroot acore_auth -e "SELECT address,port FROM realmlist;"
```

> **2026-09-10 状态**：`realmlist` 表里是 `192.168.50.192`，而 Mac 当前实际 IP 是
> `192.168.52.45`。下次连之前必须先同步，否则必然连不上。

### 坑 1：`WTF\Config.wtf` 会覆盖 `realmlist.wtf`

客户端根目录的 `realmlist.wtf` 改了也可能没用——`WTF\Config.wtf` 里如果有
`SET realmlist "..."`，它优先级更高。两个文件都要改成同一个 IP。

### 坑 2：`单机登陆器.bat` 会把 realmlist 改回 127.0.0.1

天蓝客户端自带的启动器每次运行都会重写 realmlist 指回本地。**直接双击
`Wow.exe` 启动**，不要用那个 bat。这是「显示无法连接 / 登录服务器无法连接」
的实际原因。

### 坑 3：防火墙

macOS 需放行 3724（auth）与 8085（world）。在 Windows 上验证连通：

```
Test-NetConnection <IP> -Port 3724
Test-NetConnection <IP> -Port 8085
```

## 2. 账号与角色

5 个账号，每个账号下有多套角色（历史 force-recreate 留下的）。**当前基线是
normal5-v1（普通五人本毕业装备，guid 771-775）**：

| guid | 角色名 | 账号 | 种族/职业 | 专精 | 谁来操作 |
|---|---|---|---|---|---|
| 771 | Raidteanfive | 52 RAIDTEST0 | 矮人 圣骑士 | paladin_prot | bot（坦克） |
| 772 | Raidtebnfive | 53 RAIDTEST1 | 矮人 牧师 | priest_disc | bot（治疗） |
| 773 | **Raidtecnfive** | **54 RAIDTEST2** | 人类 盗贼 | rogue_combat | **真人** |
| 774 | Raidtednfive | 55 RAIDTEST3 | 人类 法师 | mage_fire | bot |
| 775 | Raidteenfive | 56 RAIDTEST4 | 德莱尼 萨满 | shaman_elem | bot |

全员联盟，不需要动 `AllowTwoSide` 的任何开关。

旧的英雄档一套是 `751-755`（`Raidte?hfivc`，ilvl 200），`756-770` 是更早的几批。
**别登错**——账号里角色很多，认准 `n` 那一套（`Raidte[a-e]nfive`）。

### 设置密码 / 关联小弟面板

```
scripts/setup-human-session.sh --password <密码> --ip <IP>        # dry run，只打印
scripts/setup-human-session.sh --password <密码> --ip <IP> --apply
```

脚本做三件事：同步 realmlist 地址、把 bot 账号（52/53/55/56）关联到真人账号
（54）好让小弟面板能上线它们、通过 console FIFO 设置密码。脚本头部注释里写的是
旧的 751-755 一套，用于 normal5 时需要按上表核对。

## 3. 进副本

1. 真人登录 `Raidtecnfive`。
2. 用小弟面板（或 `.playerbots bot add <名字>`）把 4 个 bot 拉上线并组队。
3. 组队后**真人必须是队长**，否则排不了副本。
4. 进副本前先清两样东西，否则会报「已与该副本锁定」或不是队长：

```sql
-- 残留的持久化队伍与副本绑定
DELETE FROM acore_characters.groups WHERE guid=<残留组ID>;
DELETE FROM acore_characters.character_instance WHERE guid IN (771,772,773,774,775);
DELETE FROM acore_characters.instance WHERE map=574;
-- 连续开本会触发创建限流（每账号每小时 5 个）
DELETE FROM acore_characters.account_instance_times;
```

### 坑 4：bot 名字大小写敏感

`CharacterCache::GetCharacterGuidByName` 是 `std::map::find`，大小写敏感。
必须输入 `Raidtecnfive` 而不是 `raidtecnfive`，否则报「未找到名为 X 的在线玩家」。

## 4. 指挥 bot

底层的聊天命令派发（`ExternalEventHelper::HandleCommand`）按 **英文触发器名精确匹配**，
不认中文。所以插件里的「坦克攻击」不会生效，要发英文。

最省事的办法是做一个宏，在小队频道喊：

```
/p attack
```

其它常用：`follow`、`stay`、`flee`、`grind`。调试用 `debug <cmd>`（state/position/
target/hp/strategy/action/values 等）。

中文别名与自定义插件交互是**待办**，不是现状。

## 5. 采集证据

真人自己开观察会话（命令已降到 `SEC_PLAYER`，不需要 GM）：

```
.raidtest observe start heroic-uk-ingvar-n5
... 打完 ...
.raidtest observe stop
```

- 成员取的是 observer **当前队伍**（含真人自己），boss 每 tick 重新解析。
- 落库到 `raidtest_events`，attempt 行的 `result` 记为 `'observed'`，**不计入击杀率**。
- `run`/`status`/`stop` 仍是 `SEC_ADMINISTRATOR` + 仅控制台，真人用不了，也不该用。

场景名用当前基线的：`heroic-uk-ingvar-n5`（普通装备）或 `heroic-uk-ingvar-disc`（英雄装备）。

## 6. 查结果

**必须等 run 收尾**，跑动中的 attempt 行会显示为 `aborted/0/NULL` 占位值：

```sql
SELECT finished_at FROM acore_characters.raidtest_runs WHERE id=<run>;   -- 非空才算完
SELECT seq,result,duration_ms,boss_hp_min,deaths,notes
FROM acore_characters.raidtest_attempts WHERE run_id=<run> ORDER BY seq;
```

## 已知未做

- 中文命令别名
- 自定义插件与 bot 的双向交互
- 阵型 / 集火 / 散开一类的新增指令
