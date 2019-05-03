from http import HTTPStatus

from aiohttp import web

from aiodogstatsd.contrib import aiohttp as aiodogstatsd


async def handler_hello(request: web.Request) -> web.Response:
    return web.json_response({"hello": "aiodogstatsd"})


async def handler_bad_request(request: web.Request) -> web.Response:
    return web.json_response({"hello": "bad"}, status=HTTPStatus.BAD_REQUEST)


async def handler_internal_server_error(request: web.Request) -> web.Response:
    raise NotImplementedError()


async def handler_unauthorized(request: web.Request) -> web.Response:
    raise web.HTTPUnauthorized()


def get_application() -> web.Application:
    app = web.Application(middlewares=[aiodogstatsd.middleware_factory()])
    app.cleanup_ctx.append(
        aiodogstatsd.cleanup_context_factory(
            host="0.0.0.0", port=9125, constant_tags={"whoami": "I am Batman!"}
        )
    )
    app.add_routes(
        [
            web.get("/hello", handler_hello),
            web.get("/bad_request", handler_bad_request),
            web.get("/internal_server_error", handler_internal_server_error),
            web.get("/unauthorized", handler_unauthorized),
        ]
    )

    return app


if __name__ == "__main__":
    app = get_application()
    web.run_app(app)
