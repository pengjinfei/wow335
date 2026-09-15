#!/bin/bash
# usage: ingvar_action_counts.sh [playerbots.log]
# 新动作上线先看「排不排得上队」：PUSH 次数 vs A:<名> - OK 次数（LESSONS 一.2）。
LOG=${1:-/Users/nowcoder/IdeaProjects/github/wow335/azerothcore-wotlk/Playerbots.log}
echo "===== ingvar 动作结果分布"
grep -ao "A:ingvar [a-z ]* - [A-Z]*" "$LOG" | sort | uniq -c | sort -rn
echo "===== ingvar regain los / spread 的推入次数"
grep -aco "PUSH:ingvar regain los" "$LOG"
grep -aco "PUSH:ingvar spread" "$LOG"
echo "===== 触发器：视线丢失（按 bot）"
grep -ao "Ingvar diagnostic: los lost bot=[A-Za-z]*" "$LOG" | sort | uniq -c
echo "===== regain los 选点结果"
grep -a "Ingvar diagnostic: regain los" "$LOG" | sed -E 's/.*selected=([a-z]+) moved=([a-z]+).*rejected_ground=([0-9]+) rejected_boss=([0-9]+) rejected_los=([0-9]+)/sel=\1 moved=\2 g=\3 b=\4 l=\5/' | sort | uniq -c | sort -rn | head
echo "===== spread 落点被视线否掉的次数分布"
grep -a "Ingvar diagnostic: spread bot=" "$LOG" | sed -E 's/.*selected=([a-z]+).*los_rejected=([0-9]+)/sel=\1 los_rejected=\2/' | sort | uniq -c | sort -rn | head
