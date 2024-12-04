import asyncio
import time
import random

async def long_running_task():
    """Simulates a long-running asynchronous task with variable duration."""
    duration = random.choice([5])
    print(f"Long-running task started (duration: {duration} seconds)...")
    for i in range(1, duration + 1):
        await asyncio.sleep(1)
        print(f"Long-running task: {i} seconds")
    print("Long-running task done.")

async def main():
    count = 0
    task_running = asyncio.Event()  # Use an asyncio.Event
    task_running.set() #Initialize to not running

    while True:
        print(f"Count: {count}")
        count += 1

        if count % 3 == 0 and task_running.is_set():  # Check the Event
            task_running.clear()  # Set the Event to False
            asyncio.create_task(long_running_task()).add_done_callback(
                lambda task: task_running.set()  # Set it back to True when done
            )

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())