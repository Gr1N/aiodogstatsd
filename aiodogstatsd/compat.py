import asyncio
import sys

__all__ = ("get_event_loop",)


def _get_event_loop_factory():  # pragma: no cover
    if sys.version_info >= (3, 7):
        return asyncio.get_running_loop  # type: ignore

    return asyncio.get_event_loop


get_event_loop = _get_event_loop_factory()
