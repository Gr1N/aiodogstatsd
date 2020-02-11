from http import HTTPStatus
from typing import Awaitable, Callable, Optional, Tuple, cast

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match as RouteMatch, Route, Router

from aiodogstatsd import Client
from aiodogstatsd.compat import get_event_loop

__all__ = (
    "DEAFULT_REQUEST_DURATION_METRIC_NAME",
    "StatsDMiddleware",
)


DEAFULT_REQUEST_DURATION_METRIC_NAME = "http_request_duration"


class StatsDMiddleware(BaseHTTPMiddleware):
    __slots__ = (
        "_client",
        "_request_duration_metric_name",
        "_collect_not_allowed",
        "_collect_not_found",
    )

    def __init__(
        self,
        app: Starlette,
        *,
        client: Client,
        request_duration_metric_name: str = DEAFULT_REQUEST_DURATION_METRIC_NAME,
        collect_not_allowed: bool = False,
        collect_not_found: bool = False,
    ) -> None:
        super().__init__(app)

        self._client = client
        self._request_duration_metric_name = request_duration_metric_name
        self._collect_not_allowed = collect_not_allowed
        self._collect_not_found = collect_not_found

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        loop = get_event_loop()
        request_started_at = loop.time()

        # By default response status is 500 because we don't want to write any logic for
        # catching exceptions except exceptions which inherited from `HTTPException`.
        # And also we will override response status in case of any successful handler
        # execution.
        response_status = cast(int, HTTPStatus.INTERNAL_SERVER_ERROR.value)

        try:
            response = await call_next(request)
            response_status = response.status_code
        except HTTPException as e:  # pragma: no cover
            # We kept exception handling here (just in case), but code looks useless.
            # We're unable to cover that part of code with tests because the framework
            # handles exceptions somehow different, somehow deeply inside.
            response_status = e.status_code
            raise e
        finally:
            request_path, request_path_template = _derive_request_path(request)
            if _proceed_collecting(  # pragma: no branch
                request_path_template,
                response_status,
                self._collect_not_allowed,
                self._collect_not_found,
            ):
                request_duration = (loop.time() - request_started_at) * 1000
                self._client.timing(  # pragma: no branch
                    self._request_duration_metric_name,
                    value=request_duration,
                    tags={
                        "method": request.method,
                        "path": request_path_template or request_path,
                        "status": response_status,
                    },
                )

        return response


def _proceed_collecting(
    request_path_template: Optional[str],
    response_status: int,
    collect_not_allowed: bool,
    collect_not_found: bool,
) -> bool:
    if (
        request_path_template is None
        and response_status == HTTPStatus.NOT_FOUND
        and not collect_not_found
    ):
        return False
    elif response_status == HTTPStatus.METHOD_NOT_ALLOWED and not collect_not_allowed:
        return False

    return True


def _derive_request_path(request: Request) -> Tuple[str, Optional[str]]:
    # We need somehow understand request path in templated view this needed in case of
    # parametrized routes. Current realization is not very efficient, but for now, there
    # is no better way to do such things.
    router: Router = request.scope["router"]
    for route in router.routes:
        match, _ = route.matches(request.scope)
        if match == RouteMatch.NONE:
            continue

        return request["path"], cast(Route, route).path

    return request["path"], None
