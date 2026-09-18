#!/usr/bin/env python3
"""FIFO -> stdout 逐行转发，给 worldserver 当控制台输入。

为什么需要它（2026-09-18 踩的坑）：
`tail -n 0 -f /tmp/ac_world_fifo | ./worldserver` 看起来能用，但 `tail` 往管道写是
**块缓冲**（16KB）。`raidtest run ...` 这类短命令永远填不满一个块，于是永远停在
`tail` 的缓冲区里，worldserver 一条都收不到 —— 表现为「发完命令日志和数据库都没动静」，
很容易误判成「启动期吞命令」。

也不能用 `perl -e '$|=1; while(<STDIN>){print}'`：它在写端关闭时读到 EOF 就退出，
而 FIFO 的写入方是一次性打开/写入/关闭的（见 restart_world.sh 的 server exit），
relay 一退出 worldserver 的 stdin 就断了。

本脚本用 O_RDWR 打开 FIFO：自己持有一个写端，读端就永远看不到 EOF；
读到多少转多少并立即 flush，命令实时到达。
"""
import os
import sys
import time

FIFO = os.environ.get("AC_WORLD_FIFO", "/tmp/ac_world_fifo")


def main() -> int:
    # O_RDWR：自持写端。若只 O_RDONLY，最后一个写入方关闭时这里会读到 EOF 并退出。
    fd = os.open(FIFO, os.O_RDWR)
    out = sys.stdout.buffer
    buf = b""
    while True:
        try:
            data = os.read(fd, 4096)
        except InterruptedError:
            continue
        except OSError:
            # FIFO 被重建（重启流程会 rm + mkfifo）：重新打开继续服务。
            time.sleep(0.2)
            fd = os.open(FIFO, os.O_RDWR)
            buf = b""
            continue
        if not data:
            # 没有写入方时的空读；稍等再试，不要退出。
            time.sleep(0.05)
            continue
        buf += data
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            out.write(line + b"\n")
            out.flush()


if __name__ == "__main__":
    sys.exit(main())
