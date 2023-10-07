import asyncio
import time
from typing import Tuple
from files.api.openai import aquery


async def worker(id, queue: asyncio.Queue, GPT_MODEL: str) -> Tuple[int, str]:
  prompt = await queue.get()
  response = await aquery(prompt, GPT_MODEL)
  queue.task_done()
   
  return id, response


async def generate_prompts(prompt_list: list[str], GPT_MODEL: str):
  queue = asyncio.Queue(5)

  for prompt in prompt_list:
    queue.put_nowait(prompt)
  
  tasks = []
  for i in range(len(prompt_list)):
    task = asyncio.create_task(worker(i, queue, GPT_MODEL))
    tasks.append(task)

  started_at = time.monotonic()
  await queue.join()
  time_taken = time.monotonic() - started_at

  # cancel tasks when done
  for task in tasks:
    task.cancel()

  result = await asyncio.gather(*tasks, return_exceptions=True)

  # ensure responses are sorted
  sorted_result = sorted(result)

  # return only the string
  responses = [response for id, response in sorted_result]

  return responses