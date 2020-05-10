from concurrent.futures.thread import ThreadPoolExecutor
import logging
import asyncio

async def execute_blocking(fun, *args):
    executor = ThreadPoolExecutor(1)
    loop = asyncio.get_event_loop()
    blocking_tasks = [loop.run_in_executor(executor, fun, *args)]
    completed, pending = await asyncio.wait(blocking_tasks)
    for t in completed:
        result = t.result()
        return result