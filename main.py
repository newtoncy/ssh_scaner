# -*- coding: utf-8 -*-

# @File    : main.py
# @Date    : 2021-07-01
# @Author  : 王超逸
# @Brief   : 


from check_ssh_open import check_ssh_open
import asyncio
from asyncio import create_task
from asyncio.locks import Semaphore
from logging import getLogger
from typing import TextIO
from functools import partial

logger = getLogger()
result_logger = getLogger("result")


def int_to_ip(num: int):
    result = []
    while num > 0:
        result.append(num % 256)
        num //= 256
    result.reverse()
    return ".".join(map(str, result))


def ip_to_int(ip: str):
    nums = [i for i in ip.split(".")]
    assert len(nums) == 4
    result = 0
    for i in map(int, nums):
        result *= 256
        result += i
    return result


def get_all_ip(start: str, end: str):
    start = ip_to_int(start)
    end = ip_to_int(end)
    for i in range(start, end):
        yield int_to_ip(i)


def clear_last_line():
    # 移动光标到开头，然后用空格刷掉内容
    print(f"\r{' ' * 100}\r", end="")


class ScanContext:
    def __init__(self, total_task):
        self.finished_task = 0
        self.total_task = total_task
        self.unfinished_tasks = set()
        self.all_done = asyncio.get_running_loop().create_future()

    def on_task_finish(self, task):
        self.unfinished_tasks.remove(task)
        self.finished_task += 1
        if self.finished_task == self.total_task:
            self.all_done.set_result(None)


WORKER = 300
semaphore = ...


def display_progress(task, context: ScanContext):
    assert task.done()
    context.on_task_finish(task)
    if task.exception():
        logger.error(f"{str(task.exception())}\n"
                     f"{task.get_stack()}")
        return

    # clear_last_line()
    print("\r", end="")
    if task.result():
        ip, version = task.result()
        clear_last_line()
        result_logger.info(f"{ip}->{version}")
    print(f"完成{context.finished_task}/{context.total_task}", end="")


async def scan(start, end, context):
    global semaphore
    print(f"将扫描{context.total_task}"
          f"个ip")
    for i in get_all_ip(start, end):
        await semaphore.acquire()
        task = create_task(check_ssh_open(i))
        task.add_done_callback(partial(display_progress, context=context))
        task.add_done_callback(lambda x: semaphore.release())
        context.unfinished_tasks.add(task)


async def main(f: TextIO):
    global WORKER, semaphore
    semaphore = Semaphore(WORKER)
    all_line = [line for line in f]
    if not all_line:
        return
    context = None
    for i, line in enumerate(all_line):
        start, end = tuple(map(lambda x: x.strip(), line.split(" ")))
        logger.info(f"第{i + 1}/{len(all_line)}个区间, {start}...{end}")
        context = ScanContext(ip_to_int(end) - ip_to_int(start))

        def f(task, i, all_line, start, end):
            logger.info(f"第{i + 1}/{len(all_line)}组完成, {start}...{end}")

        context.all_done.add_done_callback(partial(f, i=i, all_line=all_line, start=start, end=end))
        await scan(start, end, context)
    if context and not context.all_done.done():
        await context.all_done
    await asyncio.sleep(10)


if __name__ == '__main__':
    import sys
    from logging_config import config_logging

    config_logging()
    assert len(sys.argv) > 2
    for i in sys.argv[1:-1]:
        if i.startswith("-w"):
            WORKER = int(i[len("-w"):])
    asyncio.run(main(open(sys.argv[-1])))
