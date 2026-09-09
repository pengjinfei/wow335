#!/bin/zsh
# 为「真人 + 4 个已验证 bot」的会话准备本机环境。
#
# 设计取舍：不新建账号/角色/配装。ingvar-disc 那套五人（guid 741-745）已经
# 持有 ilvl 200 蓝图装备、对应天赋与雕文，并且是 Ingvar 9/9 击杀的那一批。
# 重建一套等价角色只会引入与验证基线的偏差，所以这里复用它们：
#   741 raidteahfivc  血精灵 圣骑士  paladin_prot  坦克   -> bot
#   742 raidtebhfivc  矮人   牧师    priest_disc   治疗   -> bot
#   743 raidtechfivc  人类   盗贼    rogue_combat  DPS    -> 真人操作
#   744 raidtedhfivc  人类   法师    mage_fire     DPS    -> bot
#   745 raidteehfivc  德莱尼 萨满    shaman_elem   DPS    -> bot
#
# 用法：
#   scripts/setup-human-session.sh --password <你的密码> [--ip <LAN IP>] [--apply]
# 不带 --apply 时只打印将要做的改动（dry run）。
set -e

ROOT=/Users/nowcoder/IdeaProjects/github/wow335/azerothcore-wotlk
MYSQL=/opt/homebrew/opt/mysql@8.4/bin/mysql
FIFO=/tmp/ac_world_fifo
ROGUE_ACCOUNT=54          # RAIDTEST2，拥有 743 raidtechfivc（人类盗贼）
BOT_ACCOUNTS=(52 53 55 56)
APPLY=0
PASSWORD=""
LAN_IP=""

while [ $# -gt 0 ]; do
  case "$1" in
    --password) PASSWORD="$2"; shift 2 ;;
    --ip)       LAN_IP="$2";   shift 2 ;;
    --apply)    APPLY=1;       shift ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

[ -z "$LAN_IP" ] && LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || true)
if [ -z "$LAN_IP" ]; then echo "无法自动获取 LAN IP，请用 --ip 指定"; exit 1; fi
if [ -z "$PASSWORD" ]; then echo "必须用 --password 指定账号密码（不写进脚本）"; exit 1; fi

ACCOUNT_NAME=$($MYSQL -uroot acore_auth -N -e "SELECT username FROM account WHERE id=$ROGUE_ACCOUNT;")
ROGUE_GUID=743             # 精确定位：账号 54 上有多套 roster 的同类角色，只有 743 是 9/9 验证过的那个
ROGUE_NAME=$($MYSQL -uroot acore_characters -N -e "SELECT name FROM characters WHERE guid=$ROGUE_GUID AND account=$ROGUE_ACCOUNT;")
if [ -z "$ROGUE_NAME" ]; then echo "guid $ROGUE_GUID 不在账号 $ROGUE_ACCOUNT 上，请核对"; exit 1; fi

echo "==== 将要做的改动 ===="
echo "1. realmlist.address / localAddress -> $LAN_IP"
echo "   （认证后服务器告诉客户端连哪里；现在是 127.0.0.1，局域网客户端必然失败）"
echo "   注意：本机应用防火墙已关闭，改完后局域网内任何设备都能连 3724/8085。"
echo "   不要在路由器上把这两个端口转发到公网。"
echo "2. worldserver.conf: AllowTwoSide.Interaction.Group 0 -> 1"
echo "   （坦克是血精灵=部落，其余四人是联盟；raidtest 程序化建组绕过了阵营检查，"
echo "     真人必须靠这个开关才能与坦克同队。这是一处基线改动，已记录。）"
echo "3. playerbots_account_links: 账号 $ROGUE_ACCOUNT 与 ${BOT_ACCOUNTS[*]} 双向互链"
echo "   （让你能用 .playerbots bot add 控制另外四个账号上的角色）"
echo "4. account set password $ACCOUNT_NAME <你指定的密码>（经 worldserver 控制台）"
echo
echo "你登录后使用：账号 $ACCOUNT_NAME / 角色 $ROGUE_NAME（人类盗贼，rogue_combat，ilvl 200）"

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "==== dry run，未做任何改动。加 --apply 执行。===="
  exit 0
fi

echo
echo "==== 执行 ===="

# 1. realmlist
$MYSQL -uroot acore_auth -e \
  "UPDATE realmlist SET address='$LAN_IP', localAddress='$LAN_IP' WHERE id=1;"
echo "realmlist 已更新："
$MYSQL -uroot acore_auth -e "SELECT id,name,address,localAddress,port,gamebuild FROM realmlist;"

# 2. 跨阵营组队
CONF=$ROOT/env/dist/etc/worldserver.conf
if grep -qE "^AllowTwoSide\.Interaction\.Group *= *0" $CONF; then
  /usr/bin/sed -i '' 's/^AllowTwoSide\.Interaction\.Group *= *0/AllowTwoSide.Interaction.Group = 1/' $CONF
  echo "AllowTwoSide.Interaction.Group -> 1（需重启 worldserver 生效）"
else
  echo "AllowTwoSide.Interaction.Group 已非 0，跳过"
fi

# 3. 账号互链（PlayerbotMgr 查 playerbots_account_links 判断能否控制他人角色）
for acc in "${BOT_ACCOUNTS[@]}"; do
  $MYSQL -uroot acore_playerbots -e \
    "INSERT IGNORE INTO playerbots_account_links (account_id, linked_account_id) VALUES ($ROGUE_ACCOUNT,$acc),($acc,$ROGUE_ACCOUNT);"
done
echo "账号链接已写入："
$MYSQL -uroot acore_playerbots -e "SELECT * FROM playerbots_account_links ORDER BY account_id, linked_account_id;"

# 4. 密码（需要 worldserver 在运行，且 FIFO 有 reader）
if pgrep -f "apps/worldserver$" >/dev/null 2>&1; then
  PASSWORD="$PASSWORD" ACCOUNT_NAME="$ACCOUNT_NAME" python3 -c "
import os
cmd = 'account set password ' + os.environ['ACCOUNT_NAME'] + ' ' + os.environ['PASSWORD'] + ' ' + os.environ['PASSWORD'] + '\n'
fd = os.open('$FIFO', os.O_WRONLY | os.O_NONBLOCK)
try: os.write(fd, cmd.encode())
finally: os.close(fd)
"
  echo "密码设置命令已发送到控制台（在 worldserver 日志确认结果）"
else
  echo "worldserver 未运行：请先启动，再手动在控制台执行"
  echo "  account set password $ACCOUNT_NAME <密码> <密码>"
fi

cat <<INFO

==== 你那边的步骤 ====
1. 客户端 realmlist.wtf 改为：  set realmlist $LAN_IP
   （端口 3724 是默认，不用写；客户端必须是 3.3.5a build 12340）
2. 两台机器需在同一网段。
3. 登录：账号 $ACCOUNT_NAME，密码为你刚指定的那个；选角色 $ROGUE_NAME。
4. 进游戏后逐个加 bot（它们必须处于离线状态）：
     .playerbots bot add raidteahfivc      # 圣骑士坦克（已验证）
     .playerbots bot add raidtebhfivc      # 戒律牧治疗（已验证）
     .playerbots bot add raidtedhfivc      # 法师 DPS
     .playerbots bot add raidteehfivc      # 萨满 DPS
5. 组队后可用的指挥命令（私聊单个 bot，或队伍频道指挥全队）：
     tank attack / attack / follow / stay / flee
   千万不要用 init=epic 之类的配装命令——会重配装备，毁掉 ilvl 200 基线。

==== 注意 ====
- 你登录期间不要跑 raidtest：它用的正是这五个角色，会冲突。
- 角色名可用 .character rename 改（需 GM 权限）；本脚本没给你 GM 等级，
  以免误用 cheat 命令影响验证结果。需要的话再说。
INFO
