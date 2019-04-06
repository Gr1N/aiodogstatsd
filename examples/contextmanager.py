import asyncio
from random import random

import aiodogstatsd


async def main():
    async with aiodogstatsd.Client(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    ) as client:
        for _ in range(5000):
            client.timing("fire", value=random())


if __name__ == "__main__":
    asyncio.run(main())
