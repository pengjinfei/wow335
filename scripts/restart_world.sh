#!/bin/bash
# usage: restart_world.sh <logname>   -- graceful exit (fifo, then SIGTERM), verify gone, start one instance
#
# 2026-09-18：读端从 `tail -n 0 -f` 换成 scripts/fifo_relay.py。`tail` 往管道写是块缓冲
# （16KB），`raidtest run ...` 这类短命令永远填不满一块，会一直卡在 tail 的缓冲区里，
# worldserver 一条都收不到 —— 表现为「发完命令日志和数据库都没动静」，很容易误判成
# 「启动期吞命令」。也不能用 perl 逐行打印：写端关闭时它会读到 EOF 退出，relay 一退出
# worldserver 的 stdin 就断了。详见 fifo_relay.py 头部注释。
set -u
SELF_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SELF_DIR/../azerothcore-wotlk"
LOG=/tmp/wow335-worldserver-$1.log
OLD=$(pgrep -x worldserver | head -1)
if [ -n "$OLD" ]; then
  python3 -c "import os; fd=os.open('/tmp/ac_world_fifo', os.O_WRONLY|os.O_NONBLOCK); os.write(fd,b'server exit\n'); os.close(fd)" 2>/dev/null
  for i in $(seq 1 12); do kill -0 $OLD 2>/dev/null || break; sleep 5; done
  if kill -0 $OLD 2>/dev/null; then echo "fifo exit ignored, SIGTERM $OLD"; kill -TERM $OLD; for i in $(seq 1 20); do kill -0 $OLD 2>/dev/null || break; sleep 5; done; fi
  if kill -0 $OLD 2>/dev/null; then echo "STILL ALIVE $OLD - aborting"; exit 1; fi
  echo "old $OLD exited"
fi
pkill -f "tail -n 0 -f /tmp/ac_world_fifo"; pkill -f "fifo_relay.py"; sleep 1
if pgrep -x worldserver >/dev/null; then echo "another worldserver alive - aborting"; exit 1; fi
[ -n "${S_ARCHIVE:-}" ] && cp Playerbots.log "$S_ARCHIVE" 2>/dev/null
( nohup sh -c "python3 -u $SELF_DIR/fifo_relay.py | ./var/build/obj/src/server/apps/worldserver" > "$LOG" 2>&1 & )
sleep 3; pgrep -x worldserver | head -1
