import asyncio
from asyncio import DatagramProtocol
from typing import List

import pytest

import aiodogstatsd

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def statsd_client(unused_udp_port):
    client = aiodogstatsd.Client(
        host="localhost", port=unused_udp_port, constant_tags={"whoami": "batman"}
    )
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
async def statsd_server(udp_server_factory, unused_udp_port):
    collected = []

    class ServerProtocol(DatagramProtocol):
        def datagram_received(self, data, addr):
            collected.append(data)

    udp_server = udp_server_factory(
        host="localhost", port=unused_udp_port, protocol=ServerProtocol
    )

    yield udp_server, collected


async def wait_for(collected: List[str], *, count: int = 1, attempts: int = 5) -> None:
    while attempts:
        if len(collected) == count:
            break

        attempts -= 1
        await asyncio.sleep(0.1)


class TestClient:
    async def test_gauge(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.gauge("test_gauge", value=42, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_gauge:42|g|#whoami=batman,and=robin"]

    async def test_increment(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.increment("test_increment", tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_increment:1|c|#whoami=batman,and=robin"]

    async def test_decrement(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.decrement("test_decrement", tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_decrement:-1|c|#whoami=batman,and=robin"]

    async def test_histogram(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.histogram("test_histogram", value=21, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_histogram:21|h|#whoami=batman,and=robin"]

    async def test_distribution(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.distribution(
                "test_distribution", value=84, tags={"and": "robin"}
            )
            await wait_for(collected)

        assert collected == [b"test_distribution:84|d|#whoami=batman,and=robin"]

    async def test_timing(self, statsd_client, statsd_server):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.timing("test_timing", value=42, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_timing:42|ms|#whoami=batman,and=robin"]

    async def test_skip_if_sample_rate(self, mocker, statsd_client):
        mocked_queue = mocker.patch.object(statsd_client, "_queue")

        statsd_client.increment("test_sample_rate_1")
        mocked_queue.put_nowait.assert_called_once_with(
            b"test_sample_rate_1:1|c|#whoami=batman"
        )

        mocker.patch("aiodogstatsd.client.random", return_value=1)
        statsd_client.increment("test_sample_rate_2", sample_rate=0.5)
        mocked_queue.put_nowait.assert_called_once_with(
            b"test_sample_rate_1:1|c|#whoami=batman"
        )

    async def test_skip_if_closing(self, mocker):
        statsd_client = aiodogstatsd.Client()
        await statsd_client.connect()
        await statsd_client.close()

        mocked_queue = mocker.patch.object(statsd_client, "_queue")
        statsd_client.increment("test_closing")
        mocked_queue.assert_not_called()
