import asyncio

import aiodogstatsd


async def main():
    client = aiodogstatsd.Client(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    )
    await client.connect()

    with client.timeit("fire"):
        # Do action we want to time
        pass

    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
