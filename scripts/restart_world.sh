#!/bin/bash
# usage: restart_world.sh <logname>   -- graceful exit (fifo, then SIGTERM), verify gone, start one instance
set -u
cd /Users/nowcoder/IdeaProjects/github/wow335/azerothcore-wotlk
LOG=/tmp/wow335-worldserver-$1.log
OLD=$(pgrep -x worldserver | head -1)
if [ -n "$OLD" ]; then
  python3 -c "import os; fd=os.open('/tmp/ac_world_fifo', os.O_WRONLY|os.O_NONBLOCK); os.write(fd,b'server exit\n'); os.close(fd)" 2>/dev/null
  for i in $(seq 1 12); do kill -0 $OLD 2>/dev/null || break; sleep 5; done
  if kill -0 $OLD 2>/dev/null; then echo "fifo exit ignored, SIGTERM $OLD"; kill -TERM $OLD; for i in $(seq 1 20); do kill -0 $OLD 2>/dev/null || break; sleep 5; done; fi
  if kill -0 $OLD 2>/dev/null; then echo "STILL ALIVE $OLD - aborting"; exit 1; fi
  echo "old $OLD exited"
fi
pkill -f "tail -n 0 -f /tmp/ac_world_fifo"; sleep 1
if pgrep -x worldserver >/dev/null; then echo "another worldserver alive - aborting"; exit 1; fi
cp Playerbots.log "$S_ARCHIVE" 2>/dev/null
( nohup sh -c 'tail -n 0 -f /tmp/ac_world_fifo | ./var/build/obj/src/server/apps/worldserver' > "$LOG" 2>&1 & )
sleep 3; pgrep -x worldserver | head -1
