from http import HTTPStatus

from sanic import Sanic, response
from sanic.exceptions import Unauthorized
from sanic.request import Request
from sanic.response import HTTPResponse

from aiodogstatsd.contrib import sanic as aiodogstatsd


async def handler_hello(request: Request) -> HTTPResponse:
    return response.json({"hello": "aiodogstatsd"})


async def handler_bad_request(request: Request) -> HTTPResponse:
    return response.json({"hello": "bad"}, status=HTTPStatus.BAD_REQUEST)


async def handler_internal_server_error(request: Request) -> HTTPResponse:
    raise NotImplementedError()


async def handler_unauthorized(request: Request) -> HTTPResponse:
    raise Unauthorized("Unauthorized")


def get_application() -> Sanic:
    app = Sanic()

    listener_setup_statsd, listener_close_statsd = aiodogstatsd.listeners_factory(
        host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
    )
    app.register_listener(listener_setup_statsd, "before_server_start")
    app.register_listener(listener_close_statsd, "after_server_stop")

    (
        middleware_request_statsd,
        middleware_response_statsd,
    ) = aiodogstatsd.middlewares_factory()
    app.register_middleware(middleware_request_statsd, attach_to="request")
    app.register_middleware(middleware_response_statsd, attach_to="response")

    app.add_route(handler_hello, "/hello")
    app.add_route(handler_bad_request, "/bad_request")
    app.add_route(handler_internal_server_error, "/internal_server_error")
    app.add_route(handler_unauthorized, "/unauthorized")

    return app


if __name__ == "__main__":
    app = get_application()
    app.run()
