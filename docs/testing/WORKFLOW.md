# 单 boss 测试 → 策略修复 → 交接

## 1. 接手与基线

从仓库根目录阅读 docs/START-HERE.md，逐库记录 git status、branch、rev-parse HEAD。不要自动 fetch/merge 或更换装备。读取目标策略的注册、trigger、action、multiplier 和附加 Script；检索直接 Kill/DealDamage/SetPower/AddAura/RemoveAura/TeleportTo 后逐处核验上下文，不能只按关键词判定作弊。

运行前记录实际配置中的 cheat、服务器倍率、难度和机器人行为开关；当前角色指纹不覆盖这些值。发现辅助路径后，分清受开关控制与无条件执行的路径；正常规则验收需要排除绕过机制的行为，并保留证据。

## 2. 扩展场景

复制 BOSS-TEMPLATE.md 到 bosses/<scenario>/README.md。核对 boss entry、难度、坐标、门和前置事件、实例恢复逻辑。默认单 boss 死亡判定不适合所有遭遇（例如治疗目标或多个首领）；先适配编排/判定，再实测。禁止让框架代替机器人完成机制。

场景模板在 azerothcore-wotlk/modules/mod-raidtest/conf/；实际加载 env/dist/etc/modules/ 下的 .conf，模板文件不等于运行配置。安装可能覆盖运行配置，构建前后对照保存。编译需遵循当前用户授权，已授权时在核心目录运行 `MTHREADS=4 ./acore.sh compiler build`，按子仓库 AGENTS.md 做适用检查。保存构建结果及启动记录，确认服务加载了对应二进制。

## 3. 运行与观察

优先复用已存在的空闲服务器，先查询状态；不要按旧 PID 杀进程或无条件重建 FIFO。控制台使用无前导点命令，游戏聊天使用 .raidtest。

已核验 FIFO /tmp/ac_world_fifo 且有 reader 后，非阻塞发送示例：

```python
import os
fd = os.open('/tmp/ac_world_fifo', os.O_WRONLY | os.O_NONBLOCK)
try:
    os.write(fd, b'raidtest status\n')
finally:
    os.close(fd)
```

先 `raidtest scenario list` / `raidtest scenario show <scenario>`，空闲后 `raidtest run <scenario> --attempts 1`；冒烟成功后做连续尝试及同进程下一 run。`raidtest stop` 是软停止，不能当作立刻中断。需重启时先确认当前 run 收尾，识别准确进程，正常退出后再启动并核验版本。

本机 MySQL 客户端 /opt/homebrew/opt/mysql@8.4/bin/mysql；连接凭据按本地环境获取，不写进证据归档。结果库 acore_characters。基础 SQL：

```sql
SELECT id, finished_at FROM raidtest_runs ORDER BY id DESC LIMIT 5;
SELECT run_id, seq, result, duration_ms, deaths, boss_hp_min, notes
FROM raidtest_attempts WHERE run_id = <run_id> ORDER BY seq;
SELECT e.* FROM raidtest_events e
JOIN raidtest_attempts a ON a.id=e.attempt_id
WHERE a.run_id = <run_id> ORDER BY e.rel_ms, e.id;
```

运行中的 aborted/0/NULL 可能仅是占位；必须结合 finished_at 和状态判断。事件按相对时间分析。伤害统计限定当场 boss GUID，避免混入小怪；记录角色/团队/主坦旗标、归属、首末输出和机制响应。

角色快照在 env/dist/bin/raidtest-rosters/，用 `python3 -B scripts/audit_roster_snapshots.py <快照路径...>` 验收和比较。导出的证据放 boss 目录；不要只留 /tmp 路径，日志归档为 .txt 或显式跟踪，避免 *.log 被忽略。保留失败样本；新配置另建基线，不覆盖旧证据。

## 4. 策略缺陷与 fork

先分层：框架/角色/数据/底层策略。最小复现成立后，只在所属仓库修复。mod-playerbots 的 master 和核心 Playerbot 为上游基线，不直接提交；遵循 docs/03 的 dev 开发线，具体任务可从已记录基线建 codex/<boss>-<fix> 分支。已有 dev 含补丁时不得随意重置。共享同一构建目录时，切分支后必须确认源码与二进制对应，不与其他测试同时操作。

远端 fork 当前尚未配置；获得目标账号及用户授权后再创建并增加独立 remote（例如 mine），保留 origin 上游地址。记录 fork URL、base SHA、补丁 SHA、PR 和同步状态；本地开发不依赖先创建远端 fork。不要因准备修复自动同步上游，先保留稳定复现基线；同步单独形成变更和回归。

修复前后固定配置对照，检查目标机制确实触发，并回归受影响的旧 boss。上游合并补丁后验证再移除本地补丁，避免静默丢失行为。SQL 改动遵循所在子仓库当前 AGENTS.md，不能照旧文档直接修改历史/base SQL。

## 5. 每轮收尾

更新 boss 记录、BOSS-LEDGER 和必要的 START-HERE；写清事实、推断、未覆盖机制、下一条操作。逐库记录提交与 push 状态，保存关键配置/事件/快照。无辅助与同阶段装备验收未完成时，只标“当前配置击杀”。文档不能依赖聊天记录或 Git 忽略的个人台账。
