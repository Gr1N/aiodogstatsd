import asyncio
from asyncio.transports import DatagramTransport
from random import random
from typing import Optional

from aiodogstatsd import protocol, types

__all__ = ("Client",)


class Client:
    __slots__ = (
        "_host",
        "_port",
        "_namespace",
        "_constant_tags",
        "_closing",
        "_protocol",
        "_queue",
        "_queue_timeout",
        "_listen_future",
        "_listen_future_join",
    )

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 9125,
        namespace: Optional[types.MNamespace] = None,
        constant_tags: Optional[types.MTags] = None,
        queue_timeout: float = 0.5,
    ) -> None:
        self._host = host
        self._port = port
        self._namespace = namespace
        self._constant_tags = constant_tags or {}

        self._closing = False

        self._protocol = DatagramProtocol()

        self._queue: asyncio.Queue = asyncio.Queue()
        self._queue_timeout = queue_timeout
        self._listen_future: asyncio.Future
        self._listen_future_join: asyncio.Future = asyncio.Future()

    async def connect(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: self._protocol, remote_addr=(self._host, self._port)
        )

        self._listen_future = asyncio.ensure_future(self._listen())

    async def close(self) -> None:
        self._closing = True

        await self._listen_future_join
        self._listen_future.cancel()

        await self._protocol.close()

    def gauge(
        self,
        name: types.MName,
        *,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        self._report(name, types.MType.GAUGE, value, tags, sample_rate)

    def increment(
        self,
        name: types.MName,
        *,
        value: types.MValue = 1,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        self._report(name, types.MType.COUNTER, value, tags, sample_rate)

    def decrement(
        self,
        name: types.MName,
        *,
        value: types.MValue = 1,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        value = -value if value else value
        self._report(name, types.MType.COUNTER, value, tags, sample_rate)

    def histogram(
        self,
        name: types.MName,
        *,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        self._report(name, types.MType.HISTOGRAM, value, tags, sample_rate)

    def distribution(
        self,
        name: types.MName,
        *,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        self._report(name, types.MType.DISTRIBUTION, value, tags, sample_rate)

    def timing(
        self,
        name: types.MName,
        *,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        self._report(name, types.MType.TIMING, value, tags, sample_rate)

    async def _listen(self) -> None:
        while not self._closing:
            await self._listen_and_send()

        # Try to send remaining enqueued metrics if any
        while not self._queue.empty():
            await self._listen_and_send()
        self._listen_future_join.set_result(True)

    async def _listen_and_send(self) -> None:
        coro = self._queue.get()

        try:
            buf = await asyncio.wait_for(coro, timeout=self._queue_timeout)
        except asyncio.TimeoutError:
            pass
        else:
            self._protocol.send(buf)

    def _report(
        self,
        name: types.MName,
        type_: types.MType,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        # If client in closing state, then ignore any new incoming metric
        if self._closing:
            return

        if sample_rate != 1 and random() > sample_rate:
            return

        # Resolve full tags list
        all_tags = dict(self._constant_tags, **tags or {})

        # Build and enqueue metric
        self._queue.put_nowait(
            protocol.build(
                name=name,
                namespace=self._namespace,
                value=value,
                type_=type_,
                tags=all_tags,
                sample_rate=sample_rate,
            )
        )


class DatagramProtocol(asyncio.DatagramProtocol):
    __slots__ = ("_transport", "_closed")

    def __init__(self) -> None:
        self._transport: Optional[DatagramTransport] = None
        self._closed: asyncio.Future = asyncio.Future()

    async def close(self) -> None:
        if self._transport is None:
            return

        self._transport.close()
        await self._closed

    def connection_made(self, transport):
        self._transport = transport

    def connection_lost(self, _exc):
        self._transport = None
        self._closed.set_result(True)

    def send(self, data: bytes) -> None:
        if self._transport is None:
            return

        try:
            self._transport.sendto(data)
        except Exception:
            # Errors should fail silently so they don't affect anything else
            pass
