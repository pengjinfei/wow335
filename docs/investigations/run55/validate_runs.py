"""Three sequential Loatheb samples after warm-up run56; DB access is SELECT only.

Starts real tests through the existing worldserver FIFO. Run only with authorization.
"""
import os
import subprocess
import time

MYSQL = '/opt/homebrew/opt/mysql@8.4/bin/mysql'


def query(sql):
    result = subprocess.run(
        [MYSQL, '-uacore', '-pacore', '--batch', '--skip-column-names',
         'acore_characters', '-e', sql], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def wait_finished(run_id):
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        result = query(f'SELECT finished_at IS NOT NULL FROM raidtest_runs WHERE id={run_id}')
        if result == '1':
            print(query(f'SELECT run_id,result,duration_ms,boss_hp_min,deaths '
                        f'FROM raidtest_attempts WHERE run_id={run_id}'), flush=True)
            return
        if result != '0':
            raise RuntimeError(f'Missing run {run_id}')
        time.sleep(10)
    raise TimeoutError(f'Run {run_id} did not finish; no further run dispatched')


if __name__ == '__main__':
    # Guard against rerunning this one-time sequence or overlapping other work.
    if query('SELECT MAX(id) FROM raidtest_runs') != '56':
        raise RuntimeError('Expected warm-up run56 to be the latest run')
    wait_finished(56)
    for previous in (56, 57, 58):
        if query('SELECT MAX(id) FROM raidtest_runs') != str(previous):
            raise RuntimeError('Another run appeared; stop instead of overlapping')
        fd = os.open('/tmp/ac_world_fifo', os.O_WRONLY | os.O_NONBLOCK)
        try:
            os.write(fd, b'.raidtest run naxx-loatheb --attempts 1 --force-recreate\n')
        finally:
            os.close(fd)
        print(f'Dispatched sample after run{previous}', flush=True)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if query('SELECT MAX(id) FROM raidtest_runs') == str(previous + 1):
                break
            time.sleep(5)
        else:
            raise TimeoutError('Command did not start a new run')
        wait_finished(previous + 1)
