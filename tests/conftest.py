import asyncio
from typing import List

import pytest


@pytest.fixture
async def statsd_server(udp_server_factory, unused_udp_port):
    collected = []

    class ServerProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            collected.append(data)

    udp_server = udp_server_factory(
        host="0.0.0.0", port=unused_udp_port, protocol=ServerProtocol
    )

    yield udp_server, collected


@pytest.fixture
def wait_for():
    async def _wait_for(
        collected: List[str], *, count: int = 1, attempts: int = 5
    ) -> None:
        while attempts:
            if len(collected) == count:
                break

            attempts -= 1
            await asyncio.sleep(0.1)

    return _wait_for
