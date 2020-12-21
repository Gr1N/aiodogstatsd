import asyncio
from asyncio.transports import DatagramTransport
from contextlib import contextmanager
from random import random
from typing import Any, Awaitable, Iterator, Optional, TypeVar

from aiodogstatsd import protocol, typedefs
from aiodogstatsd.compat import get_event_loop

__all__ = ("Client",)

_T = TypeVar("_T")


class Client:
    __slots__ = (
        "_host",
        "_port",
        "_namespace",
        "_constant_tags",
        "_state",
        "_protocol",
        "_pending_queue",
        "_pending_queue_size",
        "_listen_future",
        "_listen_future_join",
        "_read_timeout",
        "_close_timeout",
        "_sample_rate",
    )

    @property
    def connected(self) -> bool:
        return self._state == typedefs.CState.CONNECTED

    @property
    def closing(self) -> bool:
        return self._state == typedefs.CState.CLOSING

    @property
    def disconnected(self) -> bool:
        return self._state == typedefs.CState.DISCONNECTED

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 9125,
        namespace: Optional[typedefs.MNamespace] = None,
        constant_tags: Optional[typedefs.MTags] = None,
        read_timeout: float = 0.5,
        close_timeout: Optional[float] = None,
        sample_rate: typedefs.MSampleRate = 1,
        pending_queue_size: int = 2 ** 16,
    ) -> None:
        """
        Initialize a client object.

        You can pass `host` and `port` of the DogStatsD server, `namespace` to prefix
        all metric names, `constant_tags` to attach to all metrics.

        Also, you can specify: `read_timeout` which will be used to read messages from
        an AsyncIO queue; `close_timeout` which will be used as wait time for client
        closing; `sample_rate` can be used for adjusting the frequency of stats sending.
        """
        self._host = host
        self._port = port
        self._namespace = namespace
        self._constant_tags = constant_tags or {}

        self._state = typedefs.CState.DISCONNECTED

        self._protocol = DatagramProtocol()

        self._pending_queue: asyncio.Queue
        self._pending_queue_size = pending_queue_size

        self._listen_future: asyncio.Future
        self._listen_future_join: asyncio.Future

        self._read_timeout = read_timeout
        self._close_timeout = close_timeout
        self._sample_rate = sample_rate

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

        self._pending_queue = asyncio.Queue(maxsize=self._pending_queue_size)
        self._listen_future = asyncio.ensure_future(self._listen())
        self._listen_future_join = asyncio.Future()

        self._state = typedefs.CState.CONNECTED

    async def close(self) -> None:
        self._state = typedefs.CState.CLOSING

        try:
            await asyncio.wait_for(self._close(), timeout=self._close_timeout)
        except asyncio.TimeoutError:
            pass

        self._state = typedefs.CState.DISCONNECTED

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
        sample_rate: Optional[typedefs.MSampleRate] = None,
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
        sample_rate: Optional[typedefs.MSampleRate] = None,
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
        sample_rate: Optional[typedefs.MSampleRate] = None,
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
        sample_rate: Optional[typedefs.MSampleRate] = None,
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
        sample_rate: Optional[typedefs.MSampleRate] = None,
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
        sample_rate: Optional[typedefs.MSampleRate] = None,
    ) -> None:
        """
        Record a timing, optionally setting tags and a sample rate.
        """
        self._report(name, typedefs.MType.TIMING, value, tags, sample_rate)

    async def _listen(self) -> None:
        try:
            while self.connected:
                await self._listen_and_send()
        finally:
            # Note that `asyncio.CancelledError` raised on app clean up
            # Try to send remaining enqueued metrics if any
            while not self._pending_queue.empty():
                await self._listen_and_send()
            self._listen_future_join.set_result(True)

    async def _listen_and_send(self) -> None:
        coro = self._pending_queue.get()

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
        sample_rate: Optional[typedefs.MSampleRate] = None,
    ) -> None:
        # Ignore any new incoming metric if client in closing or disconnected state
        if self.closing or self.disconnected:
            return

        sample_rate = sample_rate or self._sample_rate
        if sample_rate != 1 and random() > sample_rate:
            return

        # Resolve full tags list
        all_tags = dict(self._constant_tags, **tags or {})

        # Build metric
        metric = protocol.build(
            name=name,
            namespace=self._namespace,
            value=value,
            type_=type_,
            tags=all_tags,
            sample_rate=sample_rate,
        )

        # Enqueue metric
        try:
            self._pending_queue.put_nowait(metric)
        except asyncio.QueueFull:
            pass

    @contextmanager
    def timeit(
        self,
        name: typedefs.MName,
        *,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: Optional[typedefs.MSampleRate] = None,
        threshold_ms: Optional[typedefs.MValue] = None,
    ) -> Iterator[None]:
        """
        Context manager for easily timing methods.
        """
        loop = get_event_loop()
        started_at = loop.time()

        try:
            yield
        finally:
            value = (loop.time() - started_at) * 1000
            if not threshold_ms or value > threshold_ms:
                self.timing(name, value=int(value), tags=tags, sample_rate=sample_rate)

    def timeit_task(
        self,
        coro: Awaitable[_T],
        name: typedefs.MName,
        *,
        tags: Optional[typedefs.MTags] = None,
        sample_rate: Optional[typedefs.MSampleRate] = None,
        threshold_ms: Optional[typedefs.MValue] = None,
    ) -> "asyncio.Task[_T]":
        """
        Creates a task and returns it, adds a done callback for sending time metric when
        done and if exceeds threshold.
        """
        loop = get_event_loop()
        started_at = loop.time()

        def _callback(_: Any) -> None:
            duration = (loop.time() - started_at) * 1000
            if threshold_ms and duration < threshold_ms:
                return
            self.timing(name, value=int(duration), tags=tags, sample_rate=sample_rate)

        task = loop.create_task(coro)
        task.add_done_callback(_callback)
        return task


class DatagramProtocol(asyncio.DatagramProtocol):
    __slots__ = ("_transport", "_closed")

    def __init__(self) -> None:
        self._transport: Optional[DatagramTransport] = None
        self._closed: asyncio.Future

    async def close(self) -> None:
        if self._transport is None:
            return

        self._transport.close()
        await self._closed

    def connection_made(self, transport):
        self._transport = transport
        self._closed = asyncio.Future()

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
