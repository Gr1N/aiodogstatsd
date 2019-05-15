from asyncio import AbstractEventLoop
from http import HTTPStatus
from typing import Awaitable, Callable, Optional, Tuple

from sanic import Sanic
from sanic.exceptions import MethodNotSupported, NotFound
from sanic.request import Request
from sanic.response import HTTPResponse

from aiodogstatsd import Client, typedefs
from aiodogstatsd.compat import get_event_loop

__all__ = (
    "DEFAULT_CLIENT_APP_KEY",
    "DEAFULT_REQUEST_DURATION_METRIC_NAME",
    "listeners_factory",
    "middlewares_factory",
)


DEFAULT_CLIENT_APP_KEY = "statsd"
DEAFULT_REQUEST_DURATION_METRIC_NAME = "http_request_duration_seconds"


ListenerCallable = Callable[[Sanic, AbstractEventLoop], Awaitable]
MiddlewareCallable = Callable[..., Awaitable]


def listeners_factory(
    *,
    client_app_key: str = DEFAULT_CLIENT_APP_KEY,
    host: str = "localhost",
    port: int = 9125,
    namespace: Optional[typedefs.MNamespace] = None,
    constant_tags: Optional[typedefs.MTags] = None,
    read_timeout: float = 0.5,
    close_timeout: Optional[float] = None,
) -> Tuple[ListenerCallable, ListenerCallable]:
    async def listener_setup(app: Sanic, loop: AbstractEventLoop) -> None:
        client = Client(
            host=host,
            port=port,
            namespace=namespace,
            constant_tags=constant_tags,
            read_timeout=read_timeout,
            close_timeout=close_timeout,
        )
        await client.connect()

        setattr(app, client_app_key, client)

    async def listener_close(app: Sanic, loop: AbstractEventLoop) -> None:
        client = getattr(app, client_app_key)
        await client.close()

    return listener_setup, listener_close


def middlewares_factory(
    *,
    client_app_key: str = DEFAULT_CLIENT_APP_KEY,
    request_duration_metric_name: str = DEAFULT_REQUEST_DURATION_METRIC_NAME,
    collect_not_allowed: bool = False,
    collect_not_found: bool = False,
) -> Tuple[MiddlewareCallable, MiddlewareCallable]:
    async def middleware_request(request: Request) -> None:
        request["_statsd_request_started_at"] = get_event_loop().time()

    async def middleware_response(request: Request, response: HTTPResponse) -> None:
        if _proceed_collecting(
            request, response, collect_not_allowed, collect_not_found
        ):
            request_duration = (
                get_event_loop().time() - request["_statsd_request_started_at"]
            )
            getattr(request.app, client_app_key).timing(
                request_duration_metric_name,
                value=request_duration,
                tags={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status,
                },
            )

    return middleware_request, middleware_response


def _proceed_collecting(
    request: Request,
    response: HTTPResponse,
    collect_not_allowed: bool,
    collect_not_found: bool,
) -> bool:
    try:
        request.match_info
    except (MethodNotSupported, NotFound):
        request_match_info_error = True
    else:
        request_match_info_error = False

    if request_match_info_error and (
        (response.status == HTTPStatus.METHOD_NOT_ALLOWED and not collect_not_allowed)
        or (response.status == HTTPStatus.NOT_FOUND and not collect_not_found)
    ):
        return False

    return True
