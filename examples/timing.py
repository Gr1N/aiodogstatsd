import asyncio
from random import random

import aiodogstatsd


async def main():
    client = aiodogstatsd.Client(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    )
    await client.connect()

    for _ in range(5000):
        client.timing("fire", value=random())

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
