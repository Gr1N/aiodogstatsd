import asyncio

import pytest

import aiodogstatsd

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def statsd_client(unused_udp_port):
    client = aiodogstatsd.Client(
        host="0.0.0.0",
        port=unused_udp_port,
        constant_tags={"whoami": "batman"},
    )
    await client.connect()
    yield client
    await client.close()


@pytest.fixture
async def statsd_client_samplerate(unused_udp_port):
    client = aiodogstatsd.Client(
        host="0.0.0.0",
        port=unused_udp_port,
        constant_tags={"whoami": "batman"},
        sample_rate=0.3,
    )
    await client.connect()
    yield client
    await client.close()


class TestClient:
    async def test_gauge(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.gauge("test_gauge", value=42, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_gauge:42|g|#whoami:batman,and:robin"]

    async def test_set(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.set("test_set", value="hello", tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_set:hello|s|#whoami:batman,and:robin"]

    async def test_increment(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.increment("test_increment", tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_increment:1|c|#whoami:batman,and:robin"]

    async def test_decrement(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.decrement("test_decrement", tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_decrement:-1|c|#whoami:batman,and:robin"]

    async def test_histogram(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.histogram("test_histogram", value=21, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_histogram:21|h|#whoami:batman,and:robin"]

    async def test_distribution(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.distribution(
                "test_distribution", value=84, tags={"and": "robin"}
            )
            await wait_for(collected)

        assert collected == [b"test_distribution:84|d|#whoami:batman,and:robin"]

    async def test_timing(self, statsd_client, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with udp_server:
            statsd_client.timing("test_timing", value=42, tags={"and": "robin"})
            await wait_for(collected)

        assert collected == [b"test_timing:42|ms|#whoami:batman,and:robin"]

    async def test_skip_if_sample_rate(self, mocker, statsd_client_samplerate):
        mocked_queue = mocker.patch.object(statsd_client_samplerate, "_pending_queue")

        statsd_client_samplerate.increment("test_sample_rate_1", sample_rate=1)
        mocked_queue.put_nowait.assert_called_once_with(
            b"test_sample_rate_1:1|c|#whoami:batman"
        )

        mocker.patch("aiodogstatsd.client.random", return_value=1)
        statsd_client_samplerate.increment("test_sample_rate_2", sample_rate=0.5)
        mocked_queue.put_nowait.assert_called_once_with(
            b"test_sample_rate_1:1|c|#whoami:batman"
        )

        mocked_queue.put_nowait.reset_mock()
        mocker.patch("aiodogstatsd.client.random", return_value=0.4)
        statsd_client_samplerate.increment("test_sample_rate_4")
        mocked_queue.put_nowait.assert_not_called()

    async def test_message_send_on_close(self, mocker):
        statsd_client = aiodogstatsd.Client()
        await statsd_client.connect()

        mocked_queue = mocker.patch.object(statsd_client, "_pending_queue")
        mocked_queue.empty = mocker.Mock()
        mocked_queue.empty.side_effect = [0, 1]
        mocked_queue.get = mocker.Mock()
        mocked_queue.get.side_effect = asyncio.Future

        await asyncio.sleep(0)
        mocked_queue.get.assert_called_once()
        await statsd_client.close()

        assert mocked_queue.get.call_count == 2
        assert mocked_queue.empty.call_count == 2

    async def test_skip_if_closing(self, mocker):
        statsd_client = aiodogstatsd.Client()
        await statsd_client.connect()
        await statsd_client.close()

        mocked_queue = mocker.patch.object(statsd_client, "_pending_queue")
        statsd_client.increment("test_closing")
        mocked_queue.assert_not_called()

    async def test_context_manager(self, unused_udp_port, statsd_server, wait_for):
        udp_server, collected = statsd_server

        async with aiodogstatsd.Client(
            host="0.0.0.0", port=unused_udp_port, constant_tags={"whoami": "batman"}
        ) as statsd_client:
            async with udp_server:
                statsd_client.gauge("test_gauge", value=42, tags={"and": "robin"})
                await wait_for(collected)

        assert collected == [b"test_gauge:42|g|#whoami:batman,and:robin"]

    async def test_timeit(self, statsd_client, statsd_server, wait_for, mocker):
        udp_server, collected = statsd_server

        loop = mocker.patch("aiodogstatsd.client.get_event_loop")
        loop.return_value.time.return_value = 1.0
        with statsd_client.timeit("test_timer", tags={"and": "robin"}):
            loop.return_value.time.return_value = 2.0

        # This shouldn't be logged.
        loop.return_value.time.return_value = 1.0
        with statsd_client.timeit(
            "test_timer", tags={"and": "robin"}, threshold_ms=3000.0
        ):
            loop.return_value.time.return_value = 2.0

        async with udp_server:
            await wait_for(collected)
        assert collected == [b"test_timer:1000|ms|#whoami:batman,and:robin"]

    async def test_timeit_task(self, statsd_client, statsd_server, wait_for, mocker):
        udp_server, collected = statsd_server

        async def do_nothing():
            pass

        loop = mocker.patch("aiodogstatsd.client.get_event_loop")
        loop.return_value.create_task = asyncio.get_event_loop().create_task

        # Metric will be sent
        loop.return_value.time.return_value = 1.0
        task = statsd_client.timeit_task(
            do_nothing(), "test_timer", tags={"and": "robin"}, threshold_ms=500
        )
        loop.return_value.time.return_value = 2.0
        await task

        # Metric wont be sent because of not meeting the threshold
        loop.return_value.time.return_value = 1.0
        task = statsd_client.timeit_task(
            do_nothing(), "test_timer", tags={"and": "robin"}, threshold_ms=1100
        )
        loop.return_value.time.return_value = 2.0
        await task

        async with udp_server:
            await wait_for(collected)
        assert collected == [b"test_timer:1000|ms|#whoami:batman,and:robin"]
