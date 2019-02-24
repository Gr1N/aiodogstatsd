import asyncio
from asyncio.transports import DatagramTransport
from random import random
from typing import Optional

from aiodogstatsd import protocol, types

__all__ = ("Client",)


class Client:
    __slots__ = ("_host", "_port", "_namespace", "_constant_tags", "_protocol")

    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 9125,
        namespace: Optional[types.MNamespace] = None,
        constant_tags: Optional[types.MTags] = None,
    ) -> None:
        self._host = host
        self._port = port
        self._namespace = namespace
        self._constant_tags = constant_tags or {}

        self._protocol = DatagramProtocol()

    async def connect(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: self._protocol, remote_addr=(self._host, self._port)
        )

    async def close(self) -> None:
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

    def _report(
        self,
        name: types.MName,
        type_: types.MType,
        value: types.MValue,
        tags: Optional[types.MTags] = None,
        sample_rate: types.MSampleRate = 1,
    ) -> None:
        if sample_rate != 1 and random() > sample_rate:
            return

        # Resolve full tags list
        all_tags = dict(self._constant_tags, **tags or {})

        # Create metric packet
        payload = protocol.build(
            name=name,
            namespace=self._namespace,
            value=value,
            type_=type_,
            tags=all_tags,
            sample_rate=sample_rate,
        )

        # Send it
        self._protocol.send(payload.encode())


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
