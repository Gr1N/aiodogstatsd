import asyncio

import aiodogstatsd


async def do_something():
    await asyncio.sleep(1)


async def main():
    client = aiodogstatsd.Client(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    )
    await client.connect()

    for _ in range(5000):
        await client.timeit(do_something(), "task_finished")

    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
