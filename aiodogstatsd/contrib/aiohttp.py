from http import HTTPStatus
from typing import AsyncIterator, Callable, Optional

from aiohttp import web
from aiohttp.web_app import _Middleware
from aiohttp.web_routedef import _SimpleHandler
from aiohttp.web_urldispatcher import MatchInfoError

from aiodogstatsd import Client, typedefs
from aiodogstatsd.compat import get_event_loop

__all__ = (
    "DEFAULT_CLIENT_APP_KEY",
    "DEAFULT_REQUEST_DURATION_METRIC_NAME",
    "cleanup_context_factory",
    "middleware_factory",
)


DEFAULT_CLIENT_APP_KEY = "statsd"
DEAFULT_REQUEST_DURATION_METRIC_NAME = "http_request_duration_seconds"


def cleanup_context_factory(
    *,
    client_app_key: str = DEFAULT_CLIENT_APP_KEY,
    host: str = "localhost",
    port: int = 9125,
    namespace: Optional[typedefs.MNamespace] = None,
    constant_tags: Optional[typedefs.MTags] = None,
    read_timeout: float = 0.5,
    close_timeout: Optional[float] = None,
) -> Callable[[web.Application], AsyncIterator[None]]:
    async def cleanup_context(app: web.Application) -> AsyncIterator[None]:
        app[client_app_key] = Client(
            host=host,
            port=port,
            namespace=namespace,
            constant_tags=constant_tags,
            read_timeout=read_timeout,
            close_timeout=close_timeout,
        )
        await app[client_app_key].connect()
        yield
        await app[client_app_key].close()

    return cleanup_context


def middleware_factory(
    *,
    client_app_key: str = DEFAULT_CLIENT_APP_KEY,
    request_duration_metric_name: str = DEAFULT_REQUEST_DURATION_METRIC_NAME,
    collect_not_allowed: bool = False,
    collect_not_found: bool = False,
) -> _Middleware:
    @web.middleware
    async def middleware(
        request: web.Request, handler: _SimpleHandler
    ) -> web.StreamResponse:
        loop = get_event_loop()
        request_started_at = loop.time()

        try:
            response = await handler(request)
            response_status = response.status
        except web.HTTPException as e:
            response_status = e.status
            raise e
        except Exception as e:
            response_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
            raise e
        finally:
            if _proceed_collecting(  # pragma: no branch
                request, response_status, collect_not_allowed, collect_not_found
            ):
                request_duration = loop.time() - request_started_at
                request.app[client_app_key].timing(
                    request_duration_metric_name,
                    value=request_duration,
                    tags={
                        "method": request.method,
                        "path": request.path,
                        "status": response_status,
                    },
                )

        return response

    return middleware


def _proceed_collecting(
    request: web.Request,
    response_status: int,
    collect_not_allowed: bool,
    collect_not_found: bool,
) -> bool:
    if isinstance(request.match_info, MatchInfoError) and (
        (response_status == HTTPStatus.METHOD_NOT_ALLOWED and not collect_not_allowed)
        or (response_status == HTTPStatus.NOT_FOUND and not collect_not_found)
    ):
        return False

    return True
