import asyncio
from asyncio.transports import DatagramTransport
from random import random
from typing import Optional

from aiodogstatsd import protocol, typedefs
from aiodogstatsd.compat import get_event_loop

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
        "_listen_future",
        "_listen_future_join",
        "_read_timeout",
        "_close_timeout",
    )

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 9125,
        namespace: Optional[typedefs.MNamespace] = None,
        constant_tags: Optional[typedefs.MTags] = None,
        read_timeout: float = 0.5,
        close_timeout: Optional[float] = None,
    ) -> None:
        """
        Initialize a client object.

        You can pass host and port of the DogStatsD server, namespace to prefix all
        metric names, constant tags to attach to all metrics.

        Also, you can specify default read timeout which will be used to read messages
        from an AsyncIO queue, and you can specify close timeout which will be used
        as wait time for client closing.
        """
        self._host = host
        self._port = port
        self._namespace = namespace
        self._constant_tags = constant_tags or {}

        self._closing = False

        self._protocol = DatagramProtocol()

        self._queue: asyncio.Queue = asyncio.Queue()
        self._listen_future: asyncio.Future
        self._listen_future_join: asyncio.Future = asyncio.Future()

        self._read_timeout = read_timeout
        self._close_timeout = close_timeout

    async def __aenter__(self) -> "Client":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def connect(self) -> None:
        loop = get_event_loop()
        await loop.create_datagram_endpoint(
            lambda: self._protocol, remote_addr=(self._host, self._port)
        )

        self._listen_future = asyncio.ensure_future(self._listen())

    async def close(self) -> None:
        self._closing = True

        try:
            await asyncio.wait_for(self._close(), timeout=self._close_timeout)
        except asyncio.TimeoutError:
            pass

    async def _close(self) -> None:
        await self._listen_future_join
        self._listen_future.cancel()

        await self._protocol.close()

    def gauge(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Record the value of a gauge, optionally setting tags and a sample rate.
        """
        self._report(name, typedefs.MType.GAUGE, value, tags, sample_rate)

    def increment(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue = 1,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Increment a counter, optionally setting a value, tags and a sample rate.
        """
        self._report(name, typedefs.MType.COUNTER, value, tags, sample_rate)

    def decrement(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue = 1,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Decrement a counter, optionally setting a value, tags and a sample rate.
        """
        value = -value if value else value
        self._report(name, typedefs.MType.COUNTER, value, tags, sample_rate)

    def histogram(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Sample a histogram value, optionally setting tags and a sample rate.
        """
        self._report(name, typedefs.MType.HISTOGRAM, value, tags, sample_rate)

    def distribution(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Send a global distribution value, optionally setting tags and a sample rate.
        """
        self._report(name, typedefs.MType.DISTRIBUTION, value, tags, sample_rate)

    def timing(
        self,
        name: typedefs.MName,
        *,
        value: typedefs.MValue,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
    ) -> None:
        """
        Record a timing, optionally setting tags and a sample rate.
        """
        self._report(name, typedefs.MType.TIMING, value, tags, sample_rate)

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
            buf = await asyncio.wait_for(coro, timeout=self._read_timeout)
        except asyncio.TimeoutError:
            pass
        else:
            self._protocol.send(buf)

    def _report(
        self,
        name: typedefs.MName,
        type_: typedefs.MType,
        value: typedefs.MValue,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: typedefs.MSampleRate = 1,
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
